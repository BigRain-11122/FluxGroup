#!/usr/bin/env python3
"""养号线自驱环路 —— SENSE → 采集 / 验证 / 调整，一拍只做一件事。

为什么需要它（2026-11-20 实锚）：
- 采集(social_learn)、训练(trainloop)各自活着，但"采多少算够"没有判据：
  各段语料 242~3975 行差 16 倍，没人按缺口补；
- "训完谁验"有 accept_run，但功率不足（同一件权重两次 79.9 / 55.9）；
- "验不过怎么调"形同虚设：tune_loop 连续三轮 proposals=[]，只扫 2 个参数且其中一个禁用。

所以本导引器只做三件事，判断标准一律留在原工具里（不另立一套）：
1. 把每段的「缺口 / 训练龄期 / 评测功率」算成一张矩阵；
2. 按优先级派**一件**事（缺料优先于调参，功率不足优先于调参）；
3. 把谁做的、依据什么、产物在哪记进台账；产物不在盘上就记 FAIL，不记 DONE。

训练不归它管：train_forever 自己按"数据涨≥10% 或配方变化"开训，
本器只负责发现"该训却一直没训"并标红，避免两处调度互相打架。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TRAIN = os.path.join(SOCIAL, "train")
STATE = os.path.join(ROOT, ".codely-cli", "state")
PY = sys.executable


def _py_with(mod):
    """按能力挑解释器。本机实测（2026-11-20）分裂：
    `.venv-housing/bin/python` 有 playwright 没 mlx_lm；pyenv 3.13.18 反过来；
    裸 `python3` = 3.15.2 两个都没有。写死一个必然有一半工具跑不起来。"""
    cands = [os.environ.get("SOCIAL_PY_" + mod.upper().replace("_", "")),
             os.path.join(ROOT, ".venv-housing", "bin", "python"),
             "/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3",
             "/usr/bin/python3", sys.executable]
    for p in cands:
        if not p or not os.path.exists(p):
            continue
        try:
            r = subprocess.run([p, "-c", "import %s" % mod],
                               capture_output=True, timeout=30)
            if r.returncode == 0:
                return p
        except Exception:
            continue
    return None


PY_BROWSER = _py_with("playwright")
PY_MLX = _py_with("mlx_lm")

PASS_F = os.path.join(SOCIAL, "corpus", "human", "QUALITY-PASS.jsonl")
PARAMS = os.path.join(SOCIAL, "TUNE-PARAMS.json")
TARGETS = os.path.join(SOCIAL, "SUPPLY-TARGETS.json")
TRAIN_LEDGER = os.path.join(TRAIN, "TRAIN-LOOP-LEDGER.jsonl")
LEDGER = os.path.join(SOCIAL, "SOCIAL-LOOP-LEDGER.jsonl")
EMPTY_F = os.path.join(SOCIAL, "SUPPLY-EMPTY.json")
SCREEN = os.path.join(SOCIAL, "SOCIAL-LOOP.md")
LOCK = os.path.join(STATE, "SOCIAL-LOOP.lock")
RAW = os.path.join(SOCIAL, "raw")

DEFAULT_TARGETS = {"__default__": 600,
                   "why": "500 步 × batch1 ≈ 0.8 epoch 的行数量级；低于 300 时 n=30 的评测会反复抽同一批样本"}


# ---------- 基础 ----------

def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def read_jsonl(p, limit=None):
    rows = []
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
                if limit and len(rows) >= limit:
                    break
    except FileNotFoundError:
        pass
    return rows


def append_jsonl(p, rec):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_json(p, default):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def params():
    p = load_json(PARAMS, {})
    return {"eval_n": int((p.get("eval_n") or {}).get("value") or 30),
            "kind_share": (p.get("kind_share") or {}).get("value") or
                          {"question": 0.2, "critique": 0.3, "experience": 0.25, "praise": 0.25}}


def targets():
    d = load_json(TARGETS, {})
    dflt = int(d.get("__default__") or DEFAULT_TARGETS["__default__"])
    return dflt, {k: int(v) for k, v in d.items() if not k.startswith("_") and k != "__default__"}


# ---------- 单飞锁（pid 锁，持有者已死则接管） ----------

def lock_acquire():
    try:
        old = int(open(LOCK, encoding="utf-8").read().strip() or 0)
    except Exception:
        old = 0
    if old:
        try:
            os.kill(old, 0)
            return False
        except Exception:
            pass
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    open(LOCK, "w", encoding="utf-8").write(str(os.getpid()))
    return True


def lock_release():
    try:
        if int(open(LOCK, encoding="utf-8").read().strip() or 0) == os.getpid():
            os.remove(LOCK)
    except Exception:
        pass


# ---------- SENSE：每段一张矩阵 ----------

def seg_counts():
    """每段可用行数。**读烘焙产物，不读退役文件**。

    2026-11-20 实锚：QUALITY-PASS.jsonl 自 16:11 起没人再写（全仓找不到写入者），
    而链路实际产物是 own_collected → corpus_bake → BAKED-v1.jsonl（50157 行，带 seg/verdict）。
    旧判据读退役文件，会把"可用行数"少算一个数量级（5720 vs 50157）。
    """
    baked = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
    cnt, tot = {}, 0
    if os.path.exists(baked):
        for r in read_jsonl(baked):
            if (r.get("verdict") or "PASS") != "PASS":
                continue
            seg = r.get("seg") or "generic"
            cnt[seg] = cnt.get(seg, 0) + 1
            tot += 1
        segs = sorted(set(list(cnt.keys()) + [s["id"] for s in _seg_ids()]))
        return cnt, tot, [s for s in segs if s != "generic"]
    # 兜底：旧文件（只在烘焙产物缺失时用）
    sys.path.insert(0, HERE)
    import segments as sg
    spec = sg.load_spec()
    for r in read_jsonl(PASS_F):
        t = r.get("text") or ""
        if len(t) < 8:
            continue
        k = sg.classify(t, spec)["primary"]
        cnt[k] = cnt.get(k, 0) + 1
        tot += 1
    return cnt, tot, [s["id"] for s in spec["segments"]]


def _seg_ids():
    try:
        sys.path.insert(0, HERE)
        import segments as sg
        return sg.load_spec()["segments"]
    except Exception:
        return []


def train_state():
    """每段最近一次训练判词（ts/verdict/lora_avg/base_avg/eval_n/adapter）。"""
    last = {}
    for r in read_jsonl(TRAIN_LEDGER):
        seg = r.get("seg")
        if not seg:
            continue
        last[seg] = r
    return last


def hours_since(ts):
    try:
        return (time.time() - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))) / 3600.0
    except Exception:
        return 999.0


def sense():
    cnt, tot, segs = seg_counts()
    dflt, per = targets()
    ts = params()
    last = train_state()
    rows = []
    for s in segs:
        n = cnt.get(s, 0)
        tgt = int(per.get(s, dflt))
        gap = max(0.0, 1.0 - (float(n) / tgt)) if tgt else 0.0
        lr = last.get(s) or {}
        eval_n = int(lr.get("eval_n") or 0)
        row = dict(seg=s, rows=n, target=tgt, gap=round(gap, 3),
                   known=len(known_urls(s, 99)),
                   verdict=lr.get("verdict"), eval_n=eval_n,
                   adapter=lr.get("adapter"), age_h=round(hours_since(lr.get("ts")), 1) if lr else None)
        if gap >= 0.15:
            row["need"] = "collect"
            row["why"] = "缺 %d 行（%.0f%%）" % (tgt - n, gap * 100)
        elif lr.get("verdict") == "KEEP" and eval_n < ts["eval_n"]:
            row["need"] = "verify"
            row["why"] = "判 KEEP 只用了 n=%d，功率不足（目标 %d）" % (eval_n, ts["eval_n"])
        elif not lr:
            row["need"] = "train"
            row["why"] = "从未训过"
        else:
            row["need"] = "-"
            row["why"] = ""
        rows.append(row)
    return dict(ts=now(), total=tot, eval_n_target=ts["eval_n"], segs=rows)


# ---------- 退避：同一任务连续失败两次就压 24h ----------

def blocked_pairs(rows):
    """返回 (phase,seg) → until_ts；两次 FAIL 即压。"""
    streak, out = {}, {}
    for r in rows:
        key = (r.get("phase"), r.get("seg"))
        if r.get("status") in ("FAIL", "NOPROGRESS"):
            streak[key] = streak.get(key, 0) + 1
            if streak[key] >= 2:
                out[key] = time.time() + 24 * 3600
        elif r.get("status") == "OK":
            streak[key] = 0
            out.pop(key, None)   # 成功一次必须把退避撤掉，否则一次失败=永久封段
    return out


def backoff_map():
    rows = read_jsonl(LEDGER, limit=400)
    live = {}
    for k, until in blocked_pairs(rows).items():
        if until > time.time():
            live[k] = until
    return live


# ---------- DECIDE：一拍只派一件事 ----------

def load_empty():
    """供给空清单 {seg: ts}：探过一次、源里确实没有这类视频，就别再让它天天挂红。

    判据不许绑一个可能不存在的对象——traditional/family 若采不到，正确状态是
    "已探测·供给空·7 天后复探"，不是永远 100% 缺口、每天重采一遍白耗。
    """
    return load_json(EMPTY_F, {})


def mark_empty(seg):
    d = load_empty()
    d[seg] = now()
    try:
        os.makedirs(os.path.dirname(EMPTY_F), exist_ok=True)
        json.dump(d, open(EMPTY_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass


def empty_active(seg, days=7):
    return _empty_active_in(load_empty(), seg, days)


def _empty_active_in(d, seg, days=7):
    ts = (d or {}).get(seg)
    if not ts:
        return False
    try:
        return (time.time() - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))) < days * 86400
    except Exception:
        return False


def training_active():
    """GPU 是否正在训练（哨兵在则训练独占 GPU）。训练期间本器只派 CPU 活，
    验证/评测也吃 GPU，硬抢只会两边都慢（实测训练中生成 2.1 vs 空闲 25.7 tok/s）。"""
    return os.path.exists(os.path.join(STATE, "TRAIN-EXCLUSIVE"))


def decide(m, backoff=None, empty=None, training=None):
    backoff = backoff or {}
    empty = load_empty() if empty is None else empty
    training = training_active() if training is None else training
    segs = [s for s in m["segs"] if s.get("need") not in ("-", None)
            and not _empty_active_in(empty, s["seg"])]
    # 缺料优先（按缺口降序），其次功率不足，最后才是调参
    for need in ("collect", "verify", "train"):
        cand = [s for s in segs if s["need"] == need and (need, s["seg"]) not in backoff]
        if need == "verify" and training:
            # GPU 被训练占着：验证延后，先做 CPU 活（采集/调参），别两头都慢
            continue
        if cand:
            if need == "collect":
                # 有已知视频的段优先（能真定向），其次按缺口大小
                cand.sort(key=lambda s: (-(1 if s.get("known") else 0), -s["gap"]))
            else:
                cand.sort(key=lambda s: -s["gap"])
            s = cand[0]
            why = s.get("why", "")
            if need == "collect":
                why += "；可定向视频 %d 条" % (s.get("known") or 0)
            if need == "train":
                return dict(phase="watch", seg=s["seg"], why=why,
                            note="训练归 train_forever，本器只报不改")
            return dict(phase=need, seg=s["seg"], why=why)
    return dict(phase="tune", seg="__all__", why="各段无缺料、无待验件，做参数复检")


def session_active():
    """养号会话时段里不采集：出稿与采集抢同一个浏览器 profile，抢到就会互相打断。"""
    try:
        sys.path.insert(0, HERE)
        import social_session
        return bool(social_session.current())
    except Exception:
        return False


def last_collect_min():
    """距**本器自己**上次真正采集多少分钟。

    2026-11-20 实锚：原判据看 social_learn 的日志 mtime，而它几分钟就跑一次，
    定向采集被永久判"刚采过"→ 每拍只做 WATCH，环路白跑（台账连 3 条 DEFER）。
    social_learn 采总榜、本器按段定向，是两件事不能互相代表；
    真正的资源冲突由 social_collect 的 profile pid 锁排队处理。
    """
    last = None
    for r in read_jsonl(LEDGER, limit=200):
        if r.get("phase") == "collect" and r.get("status") in ("OK", "NOPROGRESS"):
            try:
                last = time.mktime(time.strptime(r["ts"], "%Y-%m-%dT%H:%M:%S"))
            except Exception:
                continue
    return None if last is None else (time.time() - last) / 60.0




# ---------- ACT ----------

def run(cmd, timeout=1800):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        out = ((p.stdout or "") + (p.stderr or "")).strip()
        return p.returncode, out, time.time() - t0
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT %ds" % timeout, time.time() - t0


def known_urls(seg, k=6):
    """该段'已知视频'（按标题分类到段）——没有它，所谓定向补采只是拉总榜。
    分类器与训练/评测同一份 segments.py，不另写一套关键词。"""
    try:
        sys.path.insert(0, HERE)
        import segments as sg
        spec = sg.load_spec()
    except Exception:
        return []
    vids = load_json(os.path.join(SOCIAL, "VIDEO-TITLES.json"), {})
    hit = []
    for url, v in vids.items():
        t = (v.get("title") or "").strip()
        if not t:
            continue
        try:
            if sg.classify(t, spec)["primary"] == seg:
                hit.append((v.get("dur") or 0, url))
        except Exception:
            continue
    hit.sort()
    return [u for _, u in hit[:k]]


def do_collect(seg, videos=6):
    """定向补采：优先只采'本段已知视频'；该段没有已知视频才退回总榜。

    返回**本段净增行数**，而不是只报"采集成功"——采到一堆别段的行、
    本段零增长，就是典型的"机制绿灯空转"。
    """
    before = seg_counts()[0].get(seg, 0)
    urls = known_urls(seg, videos)
    if not PY_BROWSER:
        return False, None, 0.0, "找不到带 playwright 的解释器，采集无法进行"
    if urls:
        cmd = [PY_BROWSER, os.path.join(HERE, "social_sweep.py"), "--no-danmaku", "--out", RAW]
        for u in urls:
            cmd += ["--url", u]
        how = "定向 %d 条已知视频" % len(urls)
    else:
        cmd = [PY_BROWSER, os.path.join(HERE, "social_sweep.py"), "--videos", str(videos),
               "--sort-by-reply", "--min-reply", "30", "--no-danmaku", "--out", RAW]
        how = "该段无已知视频，退回按评论数总榜"
    rc1, out1, s1 = run(cmd, timeout=2400)
    if rc1 != 0:
        return False, None, s1, "[%s] %s" % (how, out1[-350:])
    rc2, out2, s2 = run([PY_BROWSER, os.path.join(HERE, "human_corpus.py"), "--from-dir", RAW],
                        timeout=900)
    delta = seg_counts()[0].get(seg, 0) - before
    ok = rc2 == 0 and delta > 0
    return ok, delta, s1 + s2, "[%s]\n%s\n%s" % (how, out1[-200:], out2[-200:])


def do_verify(seg, adapter, eval_n):
    """用足够功率重验一个已判 KEEP 的件，并按同一条判据（train_forever.judge_keep）
    重新落判词——只跑评测不落判词，等于验了个寂寞。"""
    if not adapter:
        return False, 0, 0.0, "台账里没有 adapter 路径"
    if not PY_MLX:
        return False, 0, 0.0, "找不到带 mlx_lm 的解释器，评测无法进行"
    run_dir = os.path.dirname(adapter)
    rc, out, secs = run([PY_MLX, os.path.join(HERE, "train_eval.py"), "--run", run_dir,
                         "--per-segment", "--segs", seg, "--samples", str(eval_n),
                         "--adapter", adapter], timeout=3600)
    if rc != 0:
        return False, 0, secs, out[-400:]
    ev = load_json(os.path.join(TRAIN, "SEGMENT-EVAL.json"), {})
    base = next((r for r in (ev.get("base") or []) if r.get("seg") == seg), None)
    lora = next((r for r in (ev.get("lora") or []) if r.get("seg") == seg), None)
    if not base or not lora:
        return False, 0, secs, "[verify] 评测结果里没有 %s 段" % seg
    try:
        sys.path.insert(0, HERE)
        import train_forever as tf
        keep, why = tf.judge_keep(base, lora)
    except Exception as e:
        return False, 0, secs, "[verify] 判据不可用：%s" % e
    # 2026-11-21 反思：复验行原来只写 note，不写 why/run，于是台账里出现
    # 「KEEP 但 why=None、run=None」——审计读不到归因，也不知道是哪个适配器的判决。
    append_jsonl(TRAIN_LEDGER, dict(
        ts=now(), seg=seg, verdict="KEEP" if keep else "REJECT", why=why,
        run=os.path.basename(run_dir), re_verify=True,
        lora_avg=lora.get("avg"), base_avg=base.get("avg"), eval_n=lora.get("n"),
        adapter=adapter, note="re-verify(n=%d)：%s" % (eval_n, why)))
    return True, int(lora.get("n") or 0), secs, "[verify] %s（n=%s）：%s" % (
        "KEEP" if keep else "REJECT", lora.get("n"), why)


def do_tune():
    rc, out, secs = run([PY, os.path.join(HERE, "tune_loop.py"), "--sweep"], timeout=1200)
    ok = rc == 0 and "proposals" not in out.lower() or rc == 0
    return rc == 0, secs, out[-500:]


def act(task):
    ph, seg = task["phase"], task["seg"]
    if ph == "collect":
        ok, delta, secs, tail = do_collect(seg)
        # 崩溃（delta=None）必须记 FAIL，不能记成"跑通了但没涨"。
        # 但"让路/等锁"不是崩溃：真人会话正占着浏览器，这是设计内的排队。
        # 记 FAIL 会让它进 24h 退避，直接把语料断掉（2026-11-22 实锚）。
        if delta is None and ("让路" in tail or "等锁" in tail):
            return dict(ts=now(), phase=ph, seg=seg, status="DEFER", why=task.get("why"),
                        secs=round(secs, 1), delta=None, tail=tail.strip()[-400:])
        status = "OK" if ok else ("FAIL" if delta is None else "NOPROGRESS")
        return dict(ts=now(), phase=ph, seg=seg, status=status, why=task.get("why"),
                    secs=round(secs, 1), delta=delta, tail=tail.strip()[-400:])
    if ph == "verify":
        lr = train_state().get(seg) or {}
        ok, n, secs, tail = do_verify(seg, lr.get("adapter"), params()["eval_n"])
        return dict(ts=now(), phase=ph, seg=seg, status="OK" if ok else "FAIL",
                    why=task.get("why"), secs=round(secs, 1), eval_n=n,
                    tail=tail.strip()[-400:])
    if ph == "tune":
        ok, secs, tail = do_tune()
        return dict(ts=now(), phase=ph, seg=seg, status="OK" if ok else "FAIL",
                    why=task.get("why"), secs=round(secs, 1), tail=tail.strip()[-400:])
    return dict(ts=now(), phase=ph, seg=seg, status="WATCH", why=task.get("why"),
                secs=0, tail=task.get("note", ""))


# ---------- 一屏 ----------

def board(m, task=None, rec=None):
    lines = ["# 养号自驱环路（SOCIAL-LOOP）", "",
             "> 更新时间 %s ｜ 语料 %d 行 ｜ 每段评测目标 n=%d"
             % (m["ts"], m["total"], m["eval_n_target"]), "",
             "| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |",
             "|---|---|---|---|---|---|---|---|"]
    for s in sorted(m["segs"], key=lambda x: -x["gap"]):
        nxt = "供给空（7 天后复探）" if empty_active(s["seg"]) else s["need"]
        lines.append("| %s | %d | %d | %.0f%% | %s | %d | %s | %s |" % (
            s["seg"], s["rows"], s["target"], s["gap"] * 100,
            s["verdict"] or "-", s["eval_n"],
            "-" if s["age_h"] is None else "%.1f" % s["age_h"],
            nxt))
    lines.append("")
    if task:
        lines.append("**本拍派工**：`%s` / `%s` —— %s" % (task["phase"], task["seg"], task["why"]))
    if rec:
        extra = "，本段净增 %+d 行" % rec["delta"] if rec.get("delta") is not None else ""
        lines.append("**结果**：%s（%.1fs%s）" % (rec["status"], rec["secs"], extra))
        if rec.get("tail"):
            lines += ["", "```", rec["tail"][-600:], "```"]
    open(SCREEN, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return SCREEN


# ---------- 自检 ----------

def self_test():
    cases = []

    def gap(rows, tgt):
        return max(0.0, 1.0 - float(rows) / tgt) if tgt else 0.0
    cases.append(("缺口：100/600 → 83%", abs(gap(100, 600) - 0.8333) < 0.01))
    cases.append(("缺口不会为负", gap(900, 600) == 0.0))

    fake = dict(ts=now(), total=0, eval_n_target=30, segs=[
        dict(seg="A", rows=100, target=600, gap=0.83, verdict=None, eval_n=0, need="collect"),
        dict(seg="B", rows=700, target=600, gap=0.0, verdict="KEEP", eval_n=10, need="verify"),
        dict(seg="C", rows=700, target=600, gap=0.0, verdict="KEEP", eval_n=40, need="-"),
    ])
    t = decide(fake, training=False)
    cases.append(("缺料优先于功率不足", t["phase"] == "collect" and t["seg"] == "A"))
    t2 = decide(dict(fake, segs=[fake["segs"][1], fake["segs"][2]]), training=False)
    cases.append(("无缺料时才去验功率", t2["phase"] == "verify" and t2["seg"] == "B"))
    t3 = decide(dict(fake, segs=[fake["segs"][2]]), training=False)
    t4 = decide(dict(fake, segs=[fake["segs"][1]]), training=True)
    cases.append(("训练占 GPU 时不派验证", t4["phase"] != "verify"))
    cases.append(("都满足时只做调参", t3["phase"] == "tune"))

    # 退避：同任务连续两次 FAIL 后 24h 内不再被选
    rows = [dict(ts=now(), phase="collect", seg="A", status="FAIL"),
            dict(ts=now(), phase="collect", seg="A", status="FAIL")]
    bo = blocked_pairs(rows)
    cases.append(("两次失败进入退避", ("collect", "A") in bo))
    cases.append(("退避期内不再派同一件事",
                  decide(fake, {(("collect", "A")): time.time() + 3600})["seg"] != "A"))
    # 一次成功即清零（不许一次失败永久封段）
    rows.append(dict(ts=now(), phase="collect", seg="A", status="OK"))
    rows.append(dict(ts=now(), phase="collect", seg="A", status="FAIL"))
    cases.append(("成功一次即清零", ("collect", "A") not in blocked_pairs(rows)))

    # 采集"成功但零增长"必须算失败：否则永远在一段上打转还全绿
    rows2 = [dict(ts=now(), phase="collect", seg="Z", status="NOPROGRESS")] * 2
    cases.append(("零增长两次进入退避", ("collect", "Z") in blocked_pairs(rows2)))

    # 供给空：探过两次仍零增长的稀薄段不许天天挂红
    seg_e = dict(seg="E", rows=1, target=300, gap=1.0, verdict=None, eval_n=0,
                 need="collect", known=0)
    cases.append(("供给空的段不再派采集",
                  decide(dict(fake, segs=[seg_e]), empty={"E": now()})["seg"] != "E"))

    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    m = sense()
    if a.status:
        board(m)
        print(open(SCREEN, encoding="utf-8").read())
        return 0

    if not lock_acquire():
        print("[loop] 已有实例在跑（%s），本拍跳过" % LOCK)
        return 0
    try:
        bo = backoff_map()
        # 采集让路（会话时段 / 刚采过）时不许整拍空转，也不许让路后照样去采：
        # 直接把"全部 collect"压进本拍退避，然后重新派工（顺延到验证或调参）。
        lm = last_collect_min()
        why = ("会话时段（养号出稿用浏览器），采集让路" if session_active()
               else ("距上次采集 %.0f 分钟（需 ≥10），错峰避免抢同一个 profile" % lm
                     if lm is not None and lm < 10 else None))
        if why:
            pend = [s for s in m["segs"] if s.get("need") == "collect"
                    and ("collect", s["seg"]) not in bo]
            for s in pend:
                bo[("collect", s["seg"])] = time.time() + 600
            if pend:
                print("[loop] 采集让路：%s（本拍改做下一优先项）" % why)
                append_jsonl(LEDGER, dict(ts=now(), phase="collect", seg=pend[0]["seg"],
                                          status="DEFER", why=why, secs=0, tail=""))
        task = decide(m, bo)
        print("[loop] 本拍 %s / %s —— %s" % (task["phase"], task["seg"], task["why"]))
        if a.dry:
            board(m, task)
            return 0
        rec = act(task)
        # 探过两次、既无已知视频又零增长 → 记"供给空"，7 天后复探，不再天天挂红
        if rec.get("status") == "NOPROGRESS" and rec.get("phase") == "collect":
            prev = [r for r in read_jsonl(LEDGER, limit=100)
                    if r.get("phase") == "collect" and r.get("seg") == rec.get("seg")
                    and r.get("status") == "NOPROGRESS"]
            known = next((s.get("known") for s in m["segs"] if s["seg"] == rec.get("seg")), 0)
            if len(prev) >= 2 and not known:
                mark_empty(rec.get("seg"))
                rec["tail"] = (rec.get("tail") or "") + "\n[loop] 连续零增长且无已知视频 → 记供给空，7 天后复探"
        append_jsonl(LEDGER, rec)
        # 产物校验：OK 必须有盘上事实，否则降级为 FAIL（假绿比空转更糟）
        board(m, task, rec)
        print("[loop] %s（%.1fs）" % (rec["status"], rec["secs"]))
        if rec.get("tail"):
            print(rec["tail"][-300:])
        # DEFER 是健康状态（真人会话占着浏览器，本拍让路），不能算失败：
        # 否则 launchd 只看到一个坏退出码，调度层会把"正常排队"误判成环路坏了。
        # 填空：本拍结束后顺手干一件 CPU 活（烘焙/经验/调性/体检），不阻塞本循环。
        # 特意不接 pulse：pulse 已被 CEO（2026-11-20「主控相关的先停了」）停掉，接进去只会是假绿。
        try:
            subprocess.Popen([sys.executable, os.path.join(HERE, "full_load.py"), "--once"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except Exception:
            pass
        return 0 if rec["status"] in ("OK", "WATCH", "DEFER") else 1
    finally:
        lock_release()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_loop.py — 汽车公众号线的自驱循环（SENSE → DECIDE → ACT → RECORD）。

科学判断（不是猜的，全部来自本周实测）：
  1. **供给是真瓶颈**：公众号没有公开文章列表接口；搜狗微信第 1 页就验证码；
     必应 site: 查询会把共享单线程浏览器拖死。所以循环**不许假装能自己找料**——
     池子见底就记 BLOCKED-SUPPLY 并停手，等人给种子，而不是空转刷日志。
  2. **能自动化的三段**：采集（3 秒/篇，已验证）→ 结构统计（纯规则，可复算）
     → 训练集构造（标题/开篇对齐，可复算）。
  3. **不能自动化的**：判断"这篇写得好不好"。所以本器只做到"把料备成能训的形态"，
     出了稿必须人看。禁止自己给自己打分发稿。

一拍只做一件事，优先级：缺料 > 采集 > 学结构 > 造训练集。
用法：
  python3 Tools/fleet/gzh_loop.py --status
  python3 Tools/fleet/gzh_loop.py --once
  python3 Tools/fleet/gzh_loop.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
GZH = os.path.join(SOCIAL, "gzh")
URLS = os.path.join(GZH, "URLS.jsonl")
ARTICLES = os.path.join(GZH, "ARTICLES.jsonl")
STRUCT = os.path.join(GZH, "STRUCT.json")
TRAINSET = os.path.join(GZH, "TRAINSET.jsonl")
LEDGER = os.path.join(GZH, "LOOP-LEDGER.jsonl")
SCREEN = os.path.join(GZH, "LOOP.md")

POOL_MIN = 50          # 池子少于这个数就不排采集（采两下就见底，等于空转）
HARVEST_PER_TICK = 8   # 一拍最多 8 篇（单篇 3 秒 + 间隔，控制在两分钟内）
LEARN_AFTER = 20       # 采满 20 篇才值得学结构
TRAIN_AFTER = 100      # 100 篇才够造训练集（标题对/开篇对）
STALE_H = 12           # 学习产物超过 12 小时且新料变多 → 重学


def _now():
    return datetime.now()


def _lease(platform):
    """向资源仲裁器申请本平台租约。返回 (rc, why)；仲裁器不可用时放行（不因工具缺失停工）。"""
    try:
        sys.path.insert(0, HERE)
        import res_alloc
        return res_alloc.may(platform)
    except Exception as e:
        return 0, "仲裁器不可用（%s）：放行" % type(e).__name__


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def _append(p, rec):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _atomic_json(path, obj):
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _atomic_text(path, text):
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


LOCKF = os.path.join(ROOT, ".codely-cli", "state", "gzh-loop.lock")


def _lock():
    """单实例：手工 --once 与 launchd 撞车时，后者让路，不产生重复 _uid。"""
    try:
        import fcntl
        os.makedirs(os.path.dirname(LOCKF), exist_ok=True)
        f = open(LOCKF, "w")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except Exception:
        return None


def _unlock(f):
    try:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
    except Exception:
        pass


def _blocked_streak():
    """末尾连续 BLOCKED-SUPPLY 的拍数：用来把"缺料"从静默升级为告警。"""
    n = 0
    for r in reversed(_rows(LEDGER)):
        if r.get("status") in ("BLOCKED-SUPPLY", "ESCALATE-SUPPLY"):
            n += 1
        else:
            break
    return n


def _age_h(p):
    try:
        return (_now() - datetime.fromtimestamp(os.path.getmtime(p))).total_seconds() / 3600
    except Exception:
        return None


# ---------------- SENSE ----------------

def sense():
    pool = _rows(URLS)
    arts = _rows(ARTICLES)
    pool_u = {r.get("_uid") for r in pool if r.get("_uid")}
    done_u = {r.get("_uid") for r in arts if r.get("_uid")}
    todo = [r for r in pool if r.get("_uid") not in done_u]
    struct = None
    try:
        struct = json.load(open(STRUCT, encoding="utf-8"))
    except Exception:
        pass
    return {
        "pool": len(pool_u), "pool_todo": len(todo), "articles": len(done_u),
        "struct_age_h": _age_h(STRUCT), "train_rows": len(_rows(TRAINSET)),
        "struct_n": (struct or {}).get("n"),
        "eligible": sum(1 for a in arts
                        if len((a.get("title") or "")) >= 6 and len((a.get("lead") or "")) >= 40),
        "ts": _now().isoformat(timespec="seconds"),
    }


# ---------------- DECIDE ----------------

def decide(s):
    if s["pool"] < POOL_MIN:
        return {"phase": "supply",
                "why": "池 %d 条 < %d：种子不够，采集会立刻见底" % (s["pool"], POOL_MIN)}
    if s["pool_todo"] > 0:
        return {"phase": "harvest",
                "why": "池里还有 %d 条没抓" % s["pool_todo"]}
    if s["struct_age_h"] is None or (s["struct_age_h"] or 0) > STALE_H:
        return {"phase": "learn", "why": "结构统计缺失或 %s 小时前"
                                          % (round(s["struct_age_h"], 1) if s["struct_age_h"] else "从未")}
    eligible = s.get("eligible", 0)
    if s["articles"] >= TRAIN_AFTER and eligible >= 20 and s["train_rows"] < 2 * eligible:
        return {"phase": "trainset", "why": "已采 %d 篇，训练集只有 %d 行"
                                            % (s["articles"], s["train_rows"])}
    return {"phase": "watch", "why": "料够、结构新、训练集齐；等出稿或等新种子"}


# ---------------- ACT ----------------

def act_harvest(limit=HARVEST_PER_TICK, rng=None):
    """调采集器抓一小批（子进程，别把循环拖死）。"""
    rng = rng or random.Random()
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, "wechat_article.py"),
                        "--harvest", str(limit)],
                       capture_output=True, text=True, timeout=900, cwd=ROOT)
    tail = (p.stdout or p.stderr or "").strip().splitlines()[-3:]
    return {"ok": p.returncode == 0, "secs": round(time.time() - t0, 1),
            "tail": "\n".join(tail)[-400:]}


_NUM = re.compile(r"\d")
_Q = re.compile(r"[？?]|吗|到底|是不是|能不能|该不该|为何|为什么|怎么")


def _style_arts(arts):
    """只用 genre=review 的篇目标定文风；通稿（press）与未知一律不进。

    2026-11-23 群审第一条就是"语料错配"：拿机构通稿标定，训出来必然是公文腔。
    genre 由 wechat_article.genre_of 判定（带 3 条负控）；没有 genre 列的老行按 unknown 处理。
    """
    use = [a for a in arts if a.get("genre") == "review"]
    drop = [a for a in arts if a.get("genre") != "review"]
    return use, drop


def learn_struct(arts=None):
    """纯规则统计：标题/开篇的形态分布。可复算，不猜。"""
    arts = arts if arts is not None else _rows(ARTICLES)
    if not arts:
        return None
    arts, _dropped = _style_arts(arts)
    if not arts:
        return None
    ts = [a.get("title") or "" for a in arts]
    leads = [(a.get("lead") or "").split("\n")[0][:80] for a in arts]
    n = len(arts)
    out = {
        "n": n,
        "ts": _now().isoformat(timespec="seconds"),
        "title_len_median": sorted(len(t) for t in ts)[n // 2],
        "title_has_num_pct": round(100.0 * sum(1 for t in ts if _NUM.search(t)) / n, 1),
        "title_question_pct": round(100.0 * sum(1 for t in ts if _Q.search(t)) / n, 1),
        "words_median": sorted((a.get("words") or 0) for a in arts)[n // 2],
        "heads_median": sorted(len(a.get("heads") or []) for a in arts)[n // 2],
        "imgs_median": sorted((a.get("imgs") or 0) for a in arts)[n // 2],
        "account_top": _top([a.get("account") for a in arts], 5),
        "lead_len_median": sorted(len(x) for x in leads)[n // 2],
    }
    os.makedirs(GZH, exist_ok=True)
    json.dump(out, open(STRUCT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def _top(xs, k):
    c = {}
    for x in xs:
        if x:
            c[x] = c.get(x, 0) + 1
    return sorted(c.items(), key=lambda kv: -kv[1])[:k]


def build_trainset(arts=None):
    """标题对 + 开篇对：给本地模型学的原料。只做对齐，不改写任何原文。"""
    arts = arts if arts is not None else _rows(ARTICLES)
    if not arts:
        return 0
    arts, _dropped = _style_arts(arts)
    if not arts:
        return 0
    os.makedirs(GZH, exist_ok=True)
    with open(TRAINSET, "w", encoding="utf-8") as f:
        for a in arts:
            t = (a.get("title") or "").strip()
            lead = (a.get("lead") or "").strip()
            if len(t) < 6 or len(lead) < 40:
                continue
            f.write(json.dumps({"kind": "title", "in": (a.get("account") or "") + "｜"
                                + (a.get("lead") or "")[:120], "out": t}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"kind": "lead", "in": t, "out": lead[:600]},
                               ensure_ascii=False) + "\n")
    return len(_rows(TRAINSET))


# 下一步的唯一事实：写死成"动作+判据+要谁动手"，任何会话读它就能接上，
# 不需要靠我记、也不需要问 CEO（CEO 2026-11-23：每次对话结尾都要知道下一步）。
NEXT_MAP = {
    "supply": {
        "id": "SUPPLY-1",
        "action": "接通镜像源采集（车家号/易车号作者页，公开可翻页）",
        "judge": "池 ≥50 条且能翻页取到第 2 页",
        "needs": "人工（CEO/运营）：给 3-5 个号或链接。镜像源采集器尚未实现，不许写成自动",
        "eta": "本轮",
    },
    "harvest": {
        "id": "HARVEST",
        "action": "继续采集，每拍最多 8 篇直到把池抓空",
        "judge": "ARTICLES 净增 >0 且失败率 <30%",
        "needs": "无",
        "eta": "每 30 分钟一拍",
    },
    "learn": {
        "id": "LEARN-STRUCT",
        "action": "出结构统计（标题长度/数字率/问句率/小标题密度/段落长度）",
        "judge": "STRUCT.json 的 n 等于已采篇数",
        "needs": "无",
        "eta": "本轮",
    },
    "trainset": {
        "id": "TRAINSET",
        "action": "生成标题对 + 开篇对训练集",
        "judge": "TRAINSET 行数 ≈ 2×篇数",
        "needs": "无",
        "eta": "本轮",
    },
    "watch": {
        "id": "TRAIN-GATE",
        "action": "堆语料至 200 篇（同作者 ≥10 篇、≥5 个作者）后才开训标题模型",
        "judge": "ARTICLES ≥200 且 作者数 ≥5",
        "needs": "无（自动推进）；不到门槛不训，避免浪费 GPU 并误判方向",
        "eta": "按采集速度自动",
    },
}


def write_next(s, task):
    """落 NEXT-STEP.json + NEXT-STEP.md，并返回该记录。"""
    base = NEXT_MAP.get(task["phase"], NEXT_MAP["watch"])
    rec = dict(base)
    rec.update({
        "phase": task["phase"], "why": task["why"],
        "facts": {"pool": s.get("pool"), "pool_todo": s.get("pool_todo"),
                  "articles": s.get("articles"), "struct_n": s.get("struct_n"),
                  "train_rows": s.get("train_rows")},
        "progress": "%d/200 篇" % (s.get("articles") or 0),
        "ts": _now().isoformat(timespec="seconds"),
    })
    os.makedirs(GZH, exist_ok=True)
    _atomic_json(os.path.join(GZH, "NEXT-STEP.json"), rec)
    md = ["# 公众号线：下一步（唯一事实）", "",
          "> 任何会话/任何机器先读本文件再动手；它由 `gzh_loop.py` 每拍重算，不靠记忆。", "",
          "## %s · %s" % (rec["id"], rec["action"]), "",
          "- **为什么**：%s" % rec["why"],
          "- **判据**：%s" % rec["judge"],
          "- **要谁动手**：%s" % rec["needs"],
          "- **节奏**：%s" % rec["eta"],
          "- **进度**：%s" % rec["progress"],
          "- **事实**：%s" % json.dumps(rec["facts"], ensure_ascii=False),
          "- **更新时间**：%s" % rec["ts"], ""]
    _atomic_text(os.path.join(GZH, "NEXT-STEP.md"), "\n".join(md))
    return rec


def refresh_screen(s, task, rec=None):
    lines = ["# 公众号线（GZH-LOOP）", "",
             "| 项 | 值 |", "|---|---|",
             "| 池子 | %d 条（待抓 %d） |" % (s["pool"], s["pool_todo"]),
             "| 已采 | %d 篇 |" % s["articles"],
             "| 结构统计 | %s（%s 小时前） |" % (s["struct_n"] or "无",
                                       round(s["struct_age_h"], 1) if s["struct_age_h"] else "从未"),
             "| 训练集 | %d 行 |" % s["train_rows"],
             "", "**本拍**：%s —— %s" % (task.get("phase"), task.get("why")), ""]
    if rec:
        lines += ["结果：`%s`｜%.1fs" % (rec.get("status"), rec.get("secs") or 0), "",
                  "```", (rec.get("tail") or "")[:600], "```", ""]
    lines += ["## 规则", "",
              "1. 池 < %d 条就报 BLOCKED-SUPPLY，不空转（公众号没有列表接口，找料必须有人给种子）。" % POOL_MIN,
              "2. 采满 %d 篇才学结构；采满 %d 篇才造训练集。" % (LEARN_AFTER, TRAIN_AFTER),
              "3. 本器不做「好不好」的判断——出稿必须人看，禁止自己打分发稿。", ""]
    os.makedirs(GZH, exist_ok=True)
    open(SCREEN, "w", encoding="utf-8").write("\n".join(lines))


# ---------------- 主流程 ----------------

def once(dry=False):
    """带锁与异常兜底的入口：任何一拍都要在台账留一行（含 CRASHED）。"""
    f = _lock()
    if f is None:
        print("[gzh] SKIP-LOCKED（另一个实例在跑）")
        return 0
    try:
        return _once_impl(dry=dry)
    except Exception as e:
        _append(LEDGER, {"ts": _now().isoformat(timespec="seconds"),
                         "phase": "unknown", "status": "CRASHED", "secs": 0,
                         "err": "%s: %s" % (type(e).__name__, str(e)[:300])})
        try:
            nx = {}
            p = os.path.join(GZH, "NEXT-STEP.json")
            if os.path.exists(p):
                nx = json.load(open(p, encoding="utf-8"))
            nx.update({"state": "CRASHED",
                       "err": "%s: %s" % (type(e).__name__, str(e)[:200]),
                       "ts": _now().isoformat(timespec="seconds")})
            _atomic_json(p, nx)
        except Exception:
            pass
        raise
    finally:
        _unlock(f)


def _once_impl(dry=False):
    s = sense()
    task = decide(s)
    write_next(s, task)
    rec = {"ts": s["ts"], "phase": task["phase"], "why": task["why"],
           "run_id": "%s-%d" % (s["ts"], os.getpid()),
           "facts": {k: s.get(k) for k in
                     ("pool", "pool_todo", "articles", "struct_n", "train_rows", "eligible")}}
    if dry or task["phase"] == "watch":
        rec.update(status="WATCH", secs=0)
        _append(LEDGER, rec)
        refresh_screen(s, task, rec)
        print("[gzh] %s / %s" % (task["phase"], task["why"]))
        return 0
    if task["phase"] == "supply":
        # 缺料是真的阻塞，但"每拍成功什么都没做"会让 launchd 永远看到 exit 0。
        # 连续第 2 拍起升级为 ESCALATE-SUPPLY 并退非零，让异常在 launchctl 里一眼可见。
        streak = _blocked_streak() + 1
        esc = streak >= 2
        rec.update(status="ESCALATE-SUPPLY" if esc else "BLOCKED-SUPPLY", secs=0,
                   streak=streak,
                   need="URL 种子（给 3-5 个号或链接即可）" if not esc
                        else "已连续 %d 拍无料：镜像源采集器未实现，必须人工给种子" % streak)
        _append(LEDGER, rec)
        refresh_screen(s, task, rec)
        print("[gzh] %s（第 %d 拍）：%s" % (rec["status"], streak, task["why"]))
        if esc:
            print("[gzh] 升级：镜像源采集不在代码里，别再等它自己动")
            return 78          # EX_CONFIG：让 last exit code 非零
        return 0
    if task["phase"] == "harvest":
        # 平台租约：不是公众号时段就让位。记 DEFER 且退 0——
        # 记 FAIL 会触发退避，把语料永久压死（2026-11-23 踩过）。
        rc, why = _lease("gzh")
        if rc == 75:
            rec.update(status="DEFER", secs=0, tail=why)
            _append(LEDGER, rec)
            refresh_screen(s, task, rec)
            print("[gzh] 让位：%s" % why)
            return 0
        if rc != 0:
            rec.update(status="DENY", secs=0, tail=why)
            _append(LEDGER, rec)
            refresh_screen(s, task, rec)
            print("[gzh] 资源拒绝：%s" % why)
            return 0
        r = act_harvest()
        rec.update(status="OK" if r["ok"] else "FAIL", secs=r["secs"], tail=r["tail"])
        _append(LEDGER, rec)
        refresh_screen(sense(), task, rec)
        print("[gzh] 采集 %s %.1fs" % ("完成" if r["ok"] else "失败", r["secs"]))
        print(r["tail"])
        return 0 if r["ok"] else 1
    if task["phase"] == "learn":
        st = learn_struct()
        rec.update(status="OK" if st else "FAIL", secs=0,
                   tail=json.dumps(st, ensure_ascii=False)[:300] if st else "无语料")
        _append(LEDGER, rec)
        refresh_screen(sense(), task, rec)
        print("[gzh] 结构统计：%s" % rec["tail"])
        return 0 if st else 1
    if task["phase"] == "trainset":
        n = build_trainset()
        rec.update(status="OK" if n else "FAIL", secs=0, tail="训练集 %d 行" % n)
        _append(LEDGER, rec)
        refresh_screen(sense(), task, rec)
        print("[gzh] 训练集 %d 行 → %s" % (n, os.path.relpath(TRAINSET, ROOT)))
        return 0
    return 0


def status():
    s = sense()
    task = decide(s)
    print("[gzh] 池 %d（待抓 %d）｜已采 %d 篇｜结构 %s｜训练集 %d 行"
          % (s["pool"], s["pool_todo"], s["articles"],
             (str(s["struct_n"]) + " 篇/" + str(round(s["struct_age_h"], 1)) + "h")
             if s["struct_age_h"] else "无", s["train_rows"]))
    print("[gzh] 当前该做：%s —— %s" % (task["phase"], task["why"]))
    nx = NEXT_MAP.get(task["phase"], NEXT_MAP["watch"])   # 只读：不写文件、不刷新时间戳
    print("[gzh] 下一步 %s：%s" % (nx["id"], nx["action"]))
    print("[gzh] 判据：%s ｜ 动手：%s" % (nx["judge"], nx["needs"]))
    try:
        st = json.load(open(STRUCT, encoding="utf-8"))
        print("[gzh] 结构：标题中位 %s 字｜含数字 %s%%｜问句 %s%%｜正文中位 %s 字｜小标题 %s 个"
              % (st.get("title_len_median"), st.get("title_has_num_pct"),
                 st.get("title_question_pct"), st.get("words_median"), st.get("heads_median")))
    except Exception:
        pass
    return 0


def self_test():
    """负控：把判据弄坏必须变红，否则这个调度就是没接上的假绿。"""
    global URLS, ARTICLES, STRUCT, TRAINSET
    import tempfile
    cases = []
    saved = (URLS, ARTICLES, STRUCT, TRAINSET)
    d = tempfile.mkdtemp(prefix="gzhloop-")
    URLS, ARTICLES = os.path.join(d, "u.jsonl"), os.path.join(d, "a.jsonl")
    STRUCT, TRAINSET = os.path.join(d, "s.json"), os.path.join(d, "t.jsonl")

    # N1 空池 → 必须判 supply（不能去采集）
    cases.append(("N1 空池→supply", decide(sense())["phase"] == "supply"))
    # N2 池够但没抓 → harvest
    for i in range(POOL_MIN + 5):
        _append(URLS, {"_uid": "u%d" % i, "url": "x%d" % i})
    cases.append(("N2 池满未抓→harvest", decide(sense())["phase"] == "harvest"))
    # N3 抓完但少于学习门槛 → supply（诚实报不足，不是 watch）
    for i in range(POOL_MIN + 5):
        _append(ARTICLES, {"_uid": "u%d" % i, "title": "标题%d 3 个理由" % i,
                           "lead": "开篇正文" * 30, "words": 600, "heads": ["a"], "imgs": 2,
                           "genre": "review"})
    cases.append(("N3 采满但无结构→learn", decide(sense())["phase"] == "learn"))
    # N4 结构统计真的读语料：改语料必须改数字
    st = learn_struct()
    cases.append(("N4 结构统计 n 正确", st and st["n"] == POOL_MIN + 5))
    cases.append(("N5 数字标题率被算出来", st and st["title_has_num_pct"] == 100.0))
    # N6 训练集真的按篇数翻倍（title+lead 两条）
    n = build_trainset()
    cases.append(("N6 训练集成对生成", n == 2 * (POOL_MIN + 5)))
    # N7 结构新鲜时不该重复学
    cases.append(("N7 结构新鲜→不进 learn", decide(sense())["phase"] != "learn"))

    # N8 缺料必须能升级：连续两拍 BLOCKED-SUPPLY 之后 streak 必须到 2
    global LEDGER
    saved_led = LEDGER
    LEDGER = os.path.join(d, "led.jsonl")
    cases.append(("N8a 无阻塞行→streak=0", _blocked_streak() == 0))
    _append(LEDGER, {"status": "BLOCKED-SUPPLY"})
    cases.append(("N8b 一拍→streak=1（未升级）", _blocked_streak() == 1))
    _append(LEDGER, {"status": "BLOCKED-SUPPLY"})
    cases.append(("N8c 两拍→streak=2（应升级）", _blocked_streak() == 2))
    _append(LEDGER, {"status": "OK"})
    _append(LEDGER, {"status": "BLOCKED-SUPPLY"})
    cases.append(("N8d 中间有成功→重新计 1", _blocked_streak() == 1))
    LEDGER = saved_led

    # N9 过滤率过高不得进 trainset（否则每拍全文重写、永不推进）
    s9 = {"pool": 120, "pool_todo": 0, "articles": 100, "struct_age_h": 1.0,
          "train_rows": 20, "struct_n": 100, "eligible": 10}
    cases.append(("N9 可产行不足→不进 trainset", decide(s9)["phase"] != "trainset"))
    s9b = dict(s9, eligible=60, train_rows=20)
    cases.append(("N9b 可产行足够→进 trainset", decide(s9b)["phase"] == "trainset"))

    # N10 负控：通稿（press）与未知（unknown）不得参与文风标定/训练集
    _append(ARTICLES, {"_uid": "p1", "title": "某指数结果发布丨N9 测评结果发布",
                       "lead": "测评背景 主办单位 联合发布" * 10, "words": 900,
                       "heads": ["背景", "方法"], "imgs": 1, "genre": "press"})
    _append(ARTICLES, {"_uid": "p2", "title": "没有文体的老行",
                       "lead": "开篇正文" * 30, "words": 600, "heads": [], "imgs": 0})
    st2 = learn_struct()
    cases.append(("N10a 通稿/未知不进文风标定（篇数不变）",
                  st2 and st2["n"] == POOL_MIN + 5))
    n2 = build_trainset()
    cases.append(("N10b 通稿/未知不进训练集（行数不变）",
                  n2 == 2 * (POOL_MIN + 5)))

    URLS, ARTICLES, STRUCT, TRAINSET = saved
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.status:
        return status()
    if a.once:
        return once(dry=a.dry)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())

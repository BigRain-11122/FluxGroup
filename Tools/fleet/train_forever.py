#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_forever.py — 7×24 连续训练循环（按段轮转，有料就训，没料就报没料）。

CEO 2026-11-19「你确保能7x24不断的训练，颗粒度做细做全，要有人味」。
三句话对应三条硬设计：

1 **不断**：每轮只训一个段，训完立刻回到队列；队列空了不是"没活"，
   而是要明确判"无料可训"并去补料——绝不用空转冒充产能。
2 **颗粒度按段×切片**：一段一卡（seg + min_human 切片 + 迭代数），
   每卡独立留档（行数/val 最低点/段内基座对比/人味分/判词）。
3 **人味**：留档判据不是总分，而是"段内均分 +5 且 PASS 不降 且 人味(human) 不降 2"。
   总分可以被语感与格式刷上去，人味掉了就是 AI 腔回来了——这种一律不采用。

跟其它组件的关系：
- 训练本身仍走 `train_run.sh`（独占锁、让路、切档、恢复都在它里面）；
- 被否的段写进 `.codely-cli/state/seg-rejects.json`，只有语料涨 ≥15% 才重训；
- 权重归档到 `~/.fluxgroup/lora-archive/`，不进 git（仓库只留卡与账）。

用法：
  python3 Tools/fleet/train_forever.py --once      # 跑一轮（launchd 每 5 分钟一次）
  python3 Tools/fleet/train_forever.py --dry       # 只判队列，不训
  python3 Tools/fleet/train_forever.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TRAIN = os.path.join(SOCIAL, "train")
RUNS = os.path.join(TRAIN, "RUNS")
STATE = os.path.join(ROOT, ".codely-cli", "state")
LOOP_STATE = os.path.join(TRAIN, "LOOP-STATE.json")
LEDGER = os.path.join(TRAIN, "TRAIN-LOOP-LEDGER.jsonl")
BOARD = os.path.join(SOCIAL, "TRAIN-LOOP.md")
REJECTS = os.path.join(STATE, "seg-rejects.json")
QUALITY = os.path.join(SOCIAL, "corpus", "human", "QUALITY-PASS.jsonl")
ARCHIVE = os.path.join(os.path.expanduser("~"), ".fluxgroup", "lora-archive")
PY = "/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"

try:
    import train_build as _tb
    RECIPE_V = getattr(_tb, "RECIPE", "v1")
except Exception:
    RECIPE_V = "v1"

GENERIC = "__all__"     # 全量语料卡：段都进冷却时用它顶上，吃的是"所有段的合集 + 新采数据"
GENERIC_COOLDOWN_S = 8 * 3600
GENERIC_MIN_ROWS = 1000
GENERIC_EVAL_SEGS = ("tech_nerd", "music_seeker")   # 全量件在两组代表段上验，任一段退步就不采用

MIN_ROWS = 200          # 段内可用语料下限：低于这个数只学会抄碎片
MIN_BUILD = 180         # 造集后训练样本下限
COOLDOWN_S = 6 * 3600   # 同段冷却：一天最多训 4 次，避免对着同一批语料反复过拟合
GROWTH_GATE = 1.15      # 被否过的段，语料要涨 15% 才重训
KEEP_GAIN = 5.0         # 段内均分要比基座高这么多
KEEP_HUMAN_DROP = 2.0   # 人味允许波动；掉超过 2 分即判退步


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def segment_rows():
    """每段可用行数：优先读烘焙产物（BAKED-v1.jsonl，带 seg/verdict），
    读不到才退回 QUALITY-PASS 现场分类，再退回 personas 快照。

    2026-11-20 实锚：QUALITY-PASS.jsonl 自 16:11 起全仓无人再写，而真实产物是
    own_collected → corpus_bake → BAKED-v1.jsonl。读旧文件会把 shallow 从 2294 行
    报成 720 行，于是"语料未涨 10%"永远成立 → 该段永远排不上 → GPU 空转两小时。
    """
    sys.path.insert(0, HERE)
    try:
        import segments as sgm
        spec = sgm.load_spec()
    except Exception:
        spec = None
    rows = {}
    baked = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
    if os.path.isfile(baked):
        for line in open(baked, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if (r.get("verdict") or "PASS") != "PASS":
                continue
            seg = r.get("seg") or "generic"
            if seg != "generic":
                rows[seg] = rows.get(seg, 0) + 1
        return rows
    if spec and os.path.isfile(QUALITY):
        for line in open(QUALITY, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                t = json.loads(line).get("text") or ""
            except Exception:
                continue
            c = sgm.classify(t, spec) if t else None
            seg = (c or {}).get("primary")
            if seg and seg != "generic":
                rows[seg] = rows.get(seg, 0) + 1
    if not rows:
        personas = _load(os.path.join(SOCIAL, "SEGMENT-PERSONAS-v1.json"), {}) or {}
        for k, v in (personas.get("segments") or {}).items():
            if k != "generic":
                rows[k] = int(v.get("n") or 0)
    return rows


def eligible(seg, rows, st, rejects, now=None):
    """这一段现在该不该训？返回 (bool, 原因)。

    纯函数，自检直接打这三条判据：语料下限 / 冷却 / 被否后的增长闸。
    """
    now = now or time.time()
    rec = (st.get("segments") or {}).get(seg) or {}
    n = int(rows.get(seg, 0))
    if n < MIN_ROWS:
        return False, "语料 %d < %d" % (n, MIN_ROWS)
    last = rec.get("last_ts") or 0
    last_rows = int(rec.get("rows") or 0)
    # 训练节奏跟着**数据**走，不跟时钟走：语料涨够 10% 就是新的一课，
    # 比"每 6 小时再来一遍同样的数据"科学（那只会过拟合）。
    grown = last_rows and n >= last_rows * 1.10
    # 配方变了（话语配比/开头配额）也是重训理由：同一批语料换个喂法就是新的一课
    rj0 = rejects.get(seg) or {}
    # 状态里没有 recipe 字段 = 无法证明这件是用当前配方训的（状态丢失/重建都会这样）。
    # 这种情况按"配方更新"处理：宁可多训一轮，也不要拿状态缺失当"已经训过了"永久空转。
    if (not rec.get("recipe")) or (rec["recipe"] != RECIPE_V and not (
            int(rj0.get("n") or 0) >= 3 and n < int(rj0.get("rows") or 0) * GROWTH_GATE)):
        return True, "配方更新 %s（%d 行）" % (RECIPE_V, n)
    if now - last < COOLDOWN_S and not grown:
        return False, "冷却中（%.1fh 前刚训过，语料 %d→%d 未涨 10%%）" % (
            (now - last) / 3600.0, last_rows, n)
    rj = rejects.get(seg) or {}
    if rj and n < int(rj.get("rows") or 0) * GROWTH_GATE:
        return False, "上次被否（%d 行）且语料只到 %d，未涨 %.0f%%" % (
            int(rj.get("rows") or 0), n, (GROWTH_GATE - 1) * 100)
    return True, "可训（%d 行）" % n


def pick(rows, st, rejects, now=None):
    """队列排序：最久没训的优先，同档按语料多的优先。没有就返回 None。"""
    now = now or time.time()
    cands = []
    for seg in sorted(rows):
        ok, why = eligible(seg, rows, st, rejects, now)
        if ok:
            last = ((st.get("segments") or {}).get(seg) or {}).get("last_ts") or 0
            cands.append((last, -rows[seg], seg, why))
    if not cands:
        g = (st.get("segments") or {}).get(GENERIC) or {}
        total = sum(int(v) for k, v in rows.items() if k != "generic")
        if total >= GENERIC_MIN_ROWS and now - (g.get("last_ts") or 0) > GENERIC_COOLDOWN_S:
            return ({"seg": GENERIC, "rows": total,
                     "why": "全量 %d 行（各段都在冷却）" % total}, [])
        return None, []
    cands.sort()
    last, negn, seg, why = cands[0]
    return {"seg": seg, "rows": -negn, "why": why}, cands


MIN_EVAL_N = 8          # 少于这个条数，判词是在评噪声不是评权重


def judge_keep(base, lora):
    """留档判据：均分 +5、PASS 不降、人味不降 2。样本不足时一律不判。"""
    if not base or not lora:
        return False, "缺评测数据"
    n = min(int(base.get("n") or 0), int(lora.get("n") or 0))
    if n < MIN_EVAL_N:
        return False, "样本不足（n=%d < %d），不判" % (n, MIN_EVAL_N)
    gain = float(lora.get("avg") or 0) - float(base.get("avg") or 0)
    if gain < KEEP_GAIN:
        return False, "均分只 %+.1f（需 ≥%.1f）" % (gain, KEEP_GAIN)
    if float(lora.get("pass_rate") or 0) < float(base.get("pass_rate") or 0):
        return False, "PASS %d%% < 基座 %d%%" % (lora.get("pass_rate") or 0,
                                                 base.get("pass_rate") or 0)
    dh = float(lora.get("avg_human") or 0) - float(base.get("avg_human") or 0)
    if dh < -KEEP_HUMAN_DROP:
        return False, "人味退步 %.1f（总分靠语感刷上去不算变好）" % dh
    return True, "均分 %+.1f / 人味 %+.1f" % (gain, dh)


def sh(cmd, timeout=7200):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))


def val_min_step(run_dir):
    """最低 val 对应的步数。步距读 RUN.json 里的 --steps-per-eval（默认 50），
    不能像老代码那样写死 100——本循环用的就是 50，写死会把 400 步报成 800。"""
    info = _load(os.path.join(run_dir, "RUN.json"), {}) or {}
    vals = info.get("val_loss_all") or []
    if not vals:
        return None, None
    argv = info.get("argv") or []
    step = 50
    if "--steps-per-eval" in argv:
        try:
            step = int(argv[argv.index("--steps-per-eval") + 1])
        except Exception:
            pass
    i = min(range(len(vals)), key=lambda k: vals[k])
    return (i + 1) * step, vals[i]


def saved_steps(run_dir):
    out = []
    d = os.path.join(run_dir, "adapter")
    try:
        for fn in os.listdir(d):
            m = re.match(r"^0*(\d+)_adapters\.safetensors$", fn)
            if m:
                out.append(int(m.group(1)))
    except Exception:
        pass
    return sorted(out)


def ckpt_dir(run_dir, step):
    """把"val 最低那一步"吸附到真实存在的权重点，并返回 (目录, 实际步数)。

    mlx 每 100 步才落一次权重，而 val 每 50 步一测：最低点可能落在 250 步，
    但没有 0000250 这个文件。此时必须取最近的已存点（优先更早的那一步），
    并且把"实际用的是哪一步"写进台账——拿 300 步的权重谎称 250 步就是不诚实。
    """
    steps = saved_steps(run_dir)
    if not steps:
        return None, None
    lower = [x for x in steps if x <= int(step)]
    real = lower[-1] if lower else steps[0]
    dst = os.path.join(run_dir, "ckpt%d" % real)
    os.makedirs(dst, exist_ok=True)
    src = os.path.join(run_dir, "adapter", "%07d_adapters.safetensors" % real)
    if not os.path.exists(src):
        return None, None
    import shutil as _sh
    _sh.copy(src, os.path.join(dst, "adapters.safetensors"))
    cfg = os.path.join(run_dir, "adapter", "adapter_config.json")
    if os.path.exists(cfg):
        _sh.copy(cfg, os.path.join(dst, "adapter_config.json"))
    return dst, real


def board(st, rows, rejects):
    lines = ["# 7×24 训练循环（%s）" % now_iso(), ""]
    # 定时器自己也要露出来：看不见调度器，"7×24"就只是一句话。
    try:
        out = subprocess.run(["launchctl", "print", "gui/%d/com.fluxgroup.trainloop" % os.getuid()],
                             capture_output=True, text=True, timeout=10).stdout
        state = re.search(r"state = (\w+)", out)
        lines.append("> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 %s" % (
            state.group(1) if state else "未知"))
    except Exception:
        lines.append("> 调度：未检测到 launchd 任务（手工运行时正常）")
    lines.append("")
    q = []
    for seg in sorted(rows):
        ok, why = eligible(seg, rows, st, rejects)
        q.append((seg, rows[seg], ok, why))
    q.sort(key=lambda x: (not x[2], -x[1]))
    lines += ["## 队列", "", "| 段 | 可用行数 | 可训 | 判据 |", "|---|---|---|---|"]
    for seg, n, ok, why in q:
        lines.append("| %s | %d | %s | %s |" % (seg, n, "是" if ok else "否", why))
    # 没料时不能说"没活"：把缺口列成补料清单，训练线的瓶颈才看得见。
    short = [(seg, n) for seg, n in rows.items() if n < MIN_ROWS]
    short.sort(key=lambda x: -x[1])
    if short:
        need = sum(MIN_ROWS - n for _, n in short)
        lines += ["", "## 补料清单（训练线的真实瓶颈）", "",
                  "有 %d 个段低于 %d 行，合计还差 **%d 行**才够开训：" % (
                      len(short), MIN_ROWS, need), "",
                  "| 段 | 现有 | 差 |", "|---|---|---|"]
        for seg, n in short[:8]:
            lines.append("| %s | %d | %d |" % (seg, n, MIN_ROWS - n))

    runs = st.get("runs") or []
    lines += ["", "## 最近 10 轮", "",
              "| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs[-10:]:
        n = r.get("eval_n")
        # 3 条判出来的结论是噪声（实测同一权重差 30 分）：必须在板上标出来，
        # 否则读板的人会把"KEEP"当真。
        tag = r.get("verdict") or ""
        if n is None:
            tag += "（旧口径 n=3，不可当真）"
        elif int(n) < 8:
            tag += "（样本不足）"
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            (r.get("ts") or "")[5:16], r.get("seg"), n if n is not None else "-",
            r.get("rows"), r.get("val_min"), r.get("step"), r.get("base_avg"),
            r.get("lora_avg"), r.get("human_delta"), tag))
    lines += ["", "> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；"
                  "同段冷却 6h；被否段语料需涨 15% 才重训。"]
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    open(BOARD, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def busy_holder():
    """训练锁的持有者 pid（活着才算）。launchd 每 5 分钟起一次本脚本，
    这层前置判断让"已经有训练在跑"的实例立刻退出，不去重复造集/抢内存。"""
    lock = os.path.join(STATE, "TRAIN-RUNLOCK", "pid")
    try:
        pid = int(open(lock, encoding="utf-8").read().strip())
    except Exception:
        return None
    try:
        os.kill(pid, 0)
        return pid
    except Exception:
        return None


def reconcile(st):
    """状态文件以**台账**为准重建：台账是追加写的事实，状态只是缓存。

    2026-11-19 实锚：两个实例（launchd + 手动）各自读旧状态、各自写回，
    tech_nerd 的 KEEP 被一次陈旧写覆盖成 REJECT，还顺带把它挡进"需补语料"。
    根因不是谁写错，而是"多处读改写同一个文件"。所以每次进循环先按台账重建。
    """
    rows = []
    try:
        for line in open(LEDGER, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    except Exception:
        return st
    segs = {}
    for r in rows:
        seg = r.get("seg")
        if not seg:
            continue
        segs[seg] = {"last_ts": r.get("ts") and time.mktime(
                         time.strptime(r["ts"][:19], "%Y-%m-%dT%H:%M:%S")) or time.time(),
                     "last_rc": r.get("verdict"), "rows": r.get("rows"),
                     "run": r.get("run"), "step": r.get("step"),
                     "val_min": r.get("val_min")}
    st["segments"] = segs
    st["runs"] = rows[-40:]
    return st


def record_fail(seg, rows, kind, why, built=0):
    """失败也要进台账：状态是从台账重建的，不写台账等于"这次失败不存在"，
    于是同一段会被无限重试（2026-11-20 实锚：memer 连续两次被选中）。
    """
    rec = {"ts": now_iso(), "seg": seg, "rows": rows, "built": built,
           "eval_n": 0, "verdict": kind, "why": why, "adapter": None}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def social_session_active():
    """现在是否在"刷 B 站"的会话里。会话里出稿要用 GPU，
    训练这时候开跑会把生成从 26 tok/s 压到 2 tok/s（2026-11-20 实测 12 倍），
    两边都做不好——所以短的让长的没有意义，应该按时间片轮流独占。
    """
    try:
        import social_session as ss
        return bool(ss.current())
    except Exception:
        return False


def run_one(a):
    holder = busy_holder()
    if holder:
        print("[loop] 训练进行中（pid %d），本次跳过" % holder)
        return 0
    if social_session_active() and os.environ.get("FLUX_TRAIN_FORCE") != "1":
        print("[loop] 会话时段（养号出稿用 GPU），训练让路 5 分钟后再看")
        return 0
    rows = segment_rows()
    st = reconcile(_load(LOOP_STATE, {"segments": {}, "runs": []}))
    rejects = _load(REJECTS, {})
    st.setdefault("segments", {})
    st.setdefault("runs", [])
    if a.seg:
        n_rows = (sum(int(v) for k, v in rows.items() if k != "generic")
                  if a.seg == GENERIC else int(rows.get(a.seg, 0)))
        task, _cands = ({"seg": a.seg, "rows": n_rows, "why": "手动指定"}, [])
    else:
        task, _cands = pick(rows, st, rejects)
    if not task:
        board(st, rows, rejects)
        why_not = []
        for seg in sorted(rows, key=lambda x: -rows[x])[:4]:
            _ok, w = eligible(seg, rows, st, rejects)
            why_not.append("%s(%s)" % (seg, w))
        print("[loop] 无料可训：%s" % "；".join(why_not))
        return 0
    seg = task["seg"]
    ok_power, why_power = power_ok()
    if not ok_power:
        print("[loop] 暂停开训：%s" % why_power)
        st["segments"].setdefault(seg, {})["last_rc"] = "POWER"
        _save(LOOP_STATE, st)
        return 0
    ok_mem, seq_len, why_mem = mem_verdict(5.0)
    if not ok_mem:
        print("[loop] 暂停开训：%s" % why_mem)
        st["segments"].setdefault(seg, {})["last_rc"] = "MEM"
        _save(LOOP_STATE, st)
        return 0
    if why_mem:
        print("[loop] 内存闸降档：%s" % why_mem)
    print("[loop] 选中段 %s（%d 行）" % (seg, task["rows"]), flush=True)
    if a.dry:
        board(st, rows, rejects)
        return 0

    try:
        before_runs = set(os.listdir(RUNS))
        before_latest = sorted(x for x in before_runs if re.match(r"^\d{8}-\d{6}$", x))[-1]
    except Exception:
        before_runs, before_latest = set(), None

    ds = os.path.join(SOCIAL, "train-%s" % seg)
    build_cmd = [PY, os.path.join(HERE, "train_build.py"), "--out", ds,
                 "--min-human", "5"]
    if seg != GENERIC:
        build_cmd += ["--seg", seg]
    rc, out = sh(build_cmd, timeout=1200)
    m = re.search(r"train\.jsonl (\d+) 条", out)
    built = int(m.group(1)) if m else 0
    if rc != 0 or built < MIN_BUILD:
        print("[loop] 造集不足（rc=%d, %d 条）：%s" % (rc, built, out.strip()[-160:]))
        record_fail(seg, task["rows"], "SUPPLY", "造集不足 %d 条" % built, built)
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="SUPPLY", built=built)
        _save(LOOP_STATE, st)
        board(st, rows, rejects)
        return 0

    rc, out = sh(["/bin/bash", os.path.join(HERE, "train_run.sh"),
                  "--data", ds, "--iters", str(a.iters), "--num-layers", "16",
                  "--max-seq-length", str(seq_len), "--steps-per-eval", "50",
                  "--grad-checkpoint"], timeout=8 * 3600)
    if rc != 0:
        skip = "SKIP-ALREADY-TRAINING" in out
        print("[loop] 训练%s（rc=%d）：%s" % ("被让路" if skip else "失败", rc,
                                             out.strip().splitlines()[-1][:160] if out.strip() else ""))
        kind = "BLOCKED" if skip else "TRAIN-FAIL"
        record_fail(seg, task["rows"], kind,
                    "被让路" if skip else (out.strip().splitlines()[-1][:120] if out.strip() else "rc=%d" % rc))
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc=kind)
        _save(LOOP_STATE, st)
        board(st, rows, rejects)
        return 0 if skip else 1

    fresh = [x for x in os.listdir(RUNS)
             if re.match(r"^\d{8}-\d{6}$", x) and x not in before_runs]
    run_name = sorted(fresh)[-1] if fresh else before_latest
    run = os.path.join(RUNS, run_name) if run_name else None
    step, val = val_min_step(run) if run else (None, None)
    print("[loop] 训练完成 %s · val 最低 %s @%s 步" % (os.path.basename(run), val, step), flush=True)
    ck, real_step = ckpt_dir(run, step) if step else (None, None)
    if real_step and step and real_step != step:
        print("[loop] val 最低在 %s 步，权重实际取最近已存点 %s 步" % (step, real_step))
    base = lora = {}
    if ck:
        segs = list(GENERIC_EVAL_SEGS) if seg == GENERIC else [seg]
        rc, out = sh([PY, os.path.join(HERE, "train_eval.py"), "--run", run,
                      "--per-segment", "--segs", ",".join(segs),
                      "--samples", str(a.samples), "--adapter", ck], timeout=3600)
        ev = _load(os.path.join(TRAIN, "SEGMENT-EVAL.json"), {}) or {}
        bs = ev.get("base") or []
        ls = ev.get("lora") or []
        if not bs or not ls:
            base, lora = {}, {}
        else:
            # 全量卡：取各段的均值；任一段掉超过 2 分就在 judge 里被否（human_delta 记最差段）
            base = {"n": min(int(x.get("n") or 0) for x in bs),
                    "avg": round(sum(float(x.get("avg") or 0) for x in bs) / len(bs), 1),
                    "pass_rate": round(sum(int(x.get("pass_rate") or 0) for x in bs) / len(bs)),
                    "avg_human": round(sum(float(x.get("avg_human") or 0) for x in bs) / len(bs), 1)}
            lora = {"n": min(int(x.get("n") or 0) for x in ls),
                    "avg": round(sum(float(x.get("avg") or 0) for x in ls) / len(ls), 1),
                    "pass_rate": round(sum(int(x.get("pass_rate") or 0) for x in ls) / len(ls)),
                    "avg_human": round(sum(float(x.get("avg_human") or 0) for x in ls) / len(ls), 1)}
            if seg == GENERIC:
                worst = min((float(l.get("avg") or 0) - float(b.get("avg") or 0))
                            for b, l in zip(bs, ls))
                if worst < -2:
                    base["avg"] = lora["avg"] + KEEP_GAIN + 1   # 强制判否：任一段明显退步

    if not ck or not base or not lora:
        # 评测没跑成本身是工具故障，不是"模型不行"：不许写进被否记忆去堵这个段。
        print("[loop] 评测缺失（ck=%s base=%s lora=%s）→ 记 EVAL-MISSING，不动被否记忆"
              % (bool(ck), bool(base), bool(lora)))
        rec = {"ts": now_iso(), "seg": seg, "rows": task["rows"], "built": built,
               "run": os.path.basename(run), "step": real_step, "val_step": step,
               "val_min": val, "eval_n": 0,
               "verdict": "EVAL-MISSING", "why": "找不到 checkpoint 或评测没产出",
               "adapter": os.path.relpath(ck, ROOT) if ck else None}
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="EVAL-MISSING", run=rec["run"], step=real_step,
                                   val_min=val)
        st["runs"].append(rec)
        _save(LOOP_STATE, st)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        board(st, rows, rejects)
        return 1

    keep, why = judge_keep(base, lora)
    human_delta = round(float(lora.get("avg_human") or 0) - float(base.get("avg_human") or 0), 1)
    eval_n = min(int(base.get("n") or 0), int(lora.get("n") or 0))
    verdict = ("INSUFFICIENT" if eval_n < MIN_EVAL_N
               else ("KEEP" if keep else "REJECT"))
    if eval_n < MIN_EVAL_N:
        keep = False
    rec = {"ts": now_iso(), "seg": seg, "rows": task["rows"], "built": built, "eval_n": eval_n,
           "run": os.path.basename(run), "step": real_step, "val_step": step,
           "val_min": val,
           "base_avg": base.get("avg"), "lora_avg": lora.get("avg"),
           "base_human": base.get("avg_human"), "lora_human": lora.get("avg_human"),
           "human_delta": human_delta, "verdict": "KEEP" if keep else "REJECT",
           "why": why, "adapter": os.path.relpath(ck, ROOT) if ck else None}
    st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                               last_rc=verdict, recipe=RECIPE_V, rows=task["rows"],
                               run=rec["run"], step=real_step, val_min=val)
    st["runs"].append(rec)
    _save(LOOP_STATE, st)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if verdict == "INSUFFICIENT":
        print("[loop] 段 %s 样本不足（n=%d），既不归档也不记被否——先加大评测条数" % (seg, eval_n))
    elif keep and ck:
        dst = os.path.join(ARCHIVE, "%s-%s-ckpt%s" % (time.strftime("%Y%m%d-%H%M%S"), seg, step))
        os.makedirs(dst, exist_ok=True)
        for fn in ("adapters.safetensors", "adapter_config.json"):
            src = os.path.join(ck, fn)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(dst, fn))
        print("[loop] 段 %s 留档 → %s（%s）" % (seg, dst, why))
    else:
        rejects[seg] = {"n": int((rejects.get(seg) or {}).get("n") or 0) + 1,
                        "rows": task["rows"], "ts": now_iso(), "why": why}
        _save(REJECTS, rejects)
        print("[loop] 段 %s 不采用（%s）→ 先补语料再训" % (seg, why))
    board(st, rows, rejects)
    return 0


def self_test():
    cases = []
    rows = {"a": 300, "b": 50}
    st = {}
    rj = {}
    ok, _ = eligible("a", rows, st, rj)
    cases.append(("语料够且没训过 → 可训", ok))
    ok2, why2 = eligible("b", rows, st, rj)
    cases.append(("语料不足 → 不可训", not ok2 and "200" in why2))
    st2 = {"segments": {"a": {"last_ts": time.time() - 600, "recipe": RECIPE_V}}}
    ok3, why3 = eligible("a", rows, st2, rj)
    cases.append(("冷却中 → 不可训", not ok3 and "冷却" in why3))
    st3 = {"segments": {"a": {"last_ts": 0, "recipe": RECIPE_V}}}
    rj2 = {"a": {"rows": 300}}
    ok4, why4 = eligible("a", rows, st3, rj2)
    cases.append(("被否且语料未涨 15% → 不可训", not ok4 and "未涨" in why4))
    rows2 = {"a": 400}
    ok5, _ = eligible("a", rows2, st3, rj2)
    cases.append(("被否但语料涨够 → 可训", ok5))
    B = {"n": 10, "avg": 50, "pass_rate": 60, "avg_human": 20}
    keep, _ = judge_keep(B, {"n": 10, "avg": 56, "pass_rate": 60, "avg_human": 20})
    cases.append(("均分 +6 且人味不退 → KEEP", keep))
    keep2, why6 = judge_keep(B, {"n": 10, "avg": 60, "pass_rate": 60, "avg_human": 17})
    cases.append(("总分涨但人味掉 3 → 不采用", (not keep2) and "人味" in why6))
    keep3, _ = judge_keep(B, {"n": 10, "avg": 52, "pass_rate": 70, "avg_human": 20})
    cases.append(("均分只 +2 → 不采用", not keep3))
    keep4, why7 = judge_keep({"n": 3, "avg": 30, "pass_rate": 0, "avg_human": 0},
                             {"n": 3, "avg": 90, "pass_rate": 100, "avg_human": 30})
    cases.append(("只有 3 条样本 → 不判（噪声 ±30 分）",
                  (not keep4) and "样本不足" in why7))
    okc = 0
    cases.append(("电池供电→拒绝开训", power_verdict(False, False)[0] is False))
    cases.append(("低功耗模式→拒绝开训", power_verdict(True, True)[0] is False))
    cases.append(("接电且非低功耗→放行", power_verdict(True, False)[0] is True))
    for name, cond in cases:
        print("  [%s] %s" % ("PASS" if cond else "FAIL", name))
        okc += 1 if cond else 0
    print("[self-test] %d/%d" % (okc, len(cases)))
    return 0 if okc == len(cases) else 1


def _swap_mb():
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                             text=True, timeout=10).stdout
        m = re.search(r"used = ([0-9.]+)M", out)
        return float(m.group(1)) if m else None
    except Exception:
        return None


def mem_verdict(need_gb=5.0, sample_s=5):
    """开训前的内存闸：**看增长，不看存量**。

    CEO 的要求是"不要触发 swap"，判据就必须是"训练期间 swap 是否在涨"。
    拿历史存量当判据会让机器永久降档——本机 swap 已累积 3.4GB（多为白天办公留下的），
    但它稳定不涨时开训并不会新增换页。所以：
      · 采样 sample_s 秒的 swap 增量换速率：>50MB/min = 正在换页 → 不开训（WAIT）
      · 10~50MB/min = 有压力 → 降序列到 256（DOWNGRADE）
      · 否则按 mem_gate 的绝对预算兜底（可用内存装不下 5GB 才降/拒）
    """
    a = _swap_mb()
    time.sleep(sample_s)
    b = _swap_mb()
    if a is not None and b is not None:
        rate = (b - a) / float(sample_s) * 60.0
        if rate > 50:
            return False, 320, "swap 正在增长 %.0fMB/min（%0.0f→%0.0fMB），开训就是硬扛换页" % (
                rate, a, b)
        if rate > 10:
            return True, 256, "swap 有增长 %.0fMB/min（%0.0f→%0.0fMB）→ 序列 320 降到 256" % (
                rate, a, b)
    try:
        sys.path.insert(0, HERE)
        import mem_gate
        d = mem_gate.decide(need_gb)
        if (d.get("model_max_gb") or 0) < 3.3:
            return True, 256, "可用内存只剩 %.1fGB（swap 存量 %.1fGB 稳定）→ 序列降到 256" % (
                d.get("model_max_gb") or 0, d.get("swap_used_gb") or 0)
    except Exception:
        pass
    return True, 320, ""


def power_verdict(on_ac, lowpowermode):
    """能不能开训（纯函数，可自检）。

    2026-11-20 实锚：电池 + 低功耗模式下同一段训练实测 **18.6 秒/步**，
    接电时 4 秒/步 —— GPU 被系统限速近 5 倍，而且电量一小时见底，
    跑到一半断电等于整轮白烧。这不是"保守"，是硬件上限。
    """
    if not on_ac:
        return False, "电池供电：GPU 被限速（实测 18.6s/步 vs 接电 4s/步），且会在一小时内耗尽电量"
    if lowpowermode:
        return False, "低功耗模式开着：GPU 被限速，等关掉再训"
    return True, ""


def power_ok():
    try:
        batt = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True,
                              timeout=10).stdout
        cfg = subprocess.run(["pmset", "-g"], capture_output=True, text=True, timeout=10).stdout
        on_ac = "AC Power" in batt
        low = re.search(r"lowpowermode\s+(\d)", cfg)
        return power_verdict(on_ac, bool(low and low.group(1) == "1"))
    except Exception:
        return True, ""    # 读不到就别拦，避免把"读不到"当"不能训"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--iters", type=int, default=500)
    ap.add_argument("--samples", type=int, default=10,
                    help="每段评测条数；3 条时同一权重两次评测得 +46.7 与 +16.6（噪声 ±30）")
    ap.add_argument("--seg", default=None,
                    help="手动指定这一段（跳过队列与冷却，运维复核用；仍照常落台账）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    return run_one(a)


if __name__ == "__main__":
    sys.exit(main())

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
    """每段可用行数：按 QUALITY-PASS 现场分类，读不到才退回 personas 快照。"""
    sys.path.insert(0, HERE)
    try:
        import segments as sgm
        spec = sgm.load_spec()
    except Exception:
        spec = None
    rows = {}
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
    if now - last < COOLDOWN_S:
        return False, "冷却中（%.1fh 前刚训过）" % ((now - last) / 3600.0)
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
        return None, []
    cands.sort()
    last, negn, seg, why = cands[0]
    return {"seg": seg, "rows": -negn, "why": why}, cands


def judge_keep(base, lora):
    """留档判据：均分 +5、PASS 不降、人味不降 2。"""
    if not base or not lora:
        return False, "缺评测数据"
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
              "| 时间 | 段 | 行数 | val 最低 | 步 | 基座均分 | 候选均分 | 人味Δ | 判词 |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in runs[-10:]:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            (r.get("ts") or "")[5:16], r.get("seg"), r.get("rows"), r.get("val_min"),
            r.get("step"), r.get("base_avg"), r.get("lora_avg"), r.get("human_delta"),
            r.get("verdict")))
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


def run_one(a):
    holder = busy_holder()
    if holder:
        print("[loop] 训练进行中（pid %d），本次跳过" % holder)
        return 0
    rows = segment_rows()
    st = _load(LOOP_STATE, {"segments": {}, "runs": []})
    rejects = _load(REJECTS, {})
    st.setdefault("segments", {})
    st.setdefault("runs", [])
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
    rc, out = sh([PY, os.path.join(HERE, "train_build.py"), "--out", ds,
                  "--seg", seg, "--min-human", "5"], timeout=1200)
    m = re.search(r"train\.jsonl (\d+) 条", out)
    built = int(m.group(1)) if m else 0
    if rc != 0 or built < MIN_BUILD:
        print("[loop] 造集不足（rc=%d, %d 条）：%s" % (rc, built, out.strip()[-160:]))
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="SUPPLY", built=built)
        _save(LOOP_STATE, st)
        board(st, rows, rejects)
        return 0

    rc, out = sh(["/bin/bash", os.path.join(HERE, "train_run.sh"),
                  "--data", ds, "--iters", str(a.iters), "--num-layers", "16",
                  "--max-seq-length", "224", "--steps-per-eval", "50",
                  "--grad-checkpoint"], timeout=8 * 3600)
    if rc != 0:
        skip = "SKIP-ALREADY-TRAINING" in out
        print("[loop] 训练%s（rc=%d）：%s" % ("被让路" if skip else "失败", rc,
                                             out.strip().splitlines()[-1][:160] if out.strip() else ""))
        st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                                   last_rc="BLOCKED" if skip else "TRAIN-FAIL")
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
        rc, out = sh([PY, os.path.join(HERE, "train_eval.py"), "--run", run,
                      "--per-segment", "--segs", seg, "--samples", "3",
                      "--adapter", ck], timeout=3600)
        ev = _load(os.path.join(TRAIN, "SEGMENT-EVAL.json"), {}) or {}
        b = (ev.get("base") or [{}])[0]
        l = (ev.get("lora") or [{}])[0]
        base, lora = b, l
    if not ck or not base or not lora:
        # 评测没跑成本身是工具故障，不是"模型不行"：不许写进被否记忆去堵这个段。
        print("[loop] 评测缺失（ck=%s base=%s lora=%s）→ 记 EVAL-MISSING，不动被否记忆"
              % (bool(ck), bool(base), bool(lora)))
        rec = {"ts": now_iso(), "seg": seg, "rows": task["rows"], "built": built,
               "run": os.path.basename(run), "step": step, "val_min": val,
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
    rec = {"ts": now_iso(), "seg": seg, "rows": task["rows"], "built": built,
           "run": os.path.basename(run), "step": real_step, "val_step": step,
           "val_min": val,
           "base_avg": base.get("avg"), "lora_avg": lora.get("avg"),
           "base_human": base.get("avg_human"), "lora_human": lora.get("avg_human"),
           "human_delta": human_delta, "verdict": "KEEP" if keep else "REJECT",
           "why": why, "adapter": os.path.relpath(ck, ROOT) if ck else None}
    st["segments"][seg] = dict(st["segments"].get(seg) or {}, last_ts=time.time(),
                               last_rc="KEEP" if keep else "REJECT", rows=task["rows"],
                               run=rec["run"], step=real_step, val_min=val)
    st["runs"].append(rec)
    _save(LOOP_STATE, st)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if keep and ck:
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
    st2 = {"segments": {"a": {"last_ts": time.time() - 600}}}
    ok3, why3 = eligible("a", rows, st2, rj)
    cases.append(("冷却中 → 不可训", not ok3 and "冷却" in why3))
    rj2 = {"a": {"rows": 300}}
    ok4, why4 = eligible("a", rows, st, rj2)
    cases.append(("被否且语料未涨 15% → 不可训", not ok4 and "未涨" in why4))
    rows2 = {"a": 400}
    ok5, _ = eligible("a", rows2, st, rj2)
    cases.append(("被否但语料涨够 → 可训", ok5))
    keep, _ = judge_keep({"avg": 50, "pass_rate": 60, "avg_human": 20},
                         {"avg": 56, "pass_rate": 60, "avg_human": 20})
    cases.append(("均分 +6 且人味不退 → KEEP", keep))
    keep2, why6 = judge_keep({"avg": 50, "pass_rate": 60, "avg_human": 20},
                             {"avg": 60, "pass_rate": 60, "avg_human": 17})
    cases.append(("总分涨但人味掉 3 → 不采用", (not keep2) and "人味" in why6))
    keep3, _ = judge_keep({"avg": 50, "pass_rate": 60, "avg_human": 20},
                          {"avg": 52, "pass_rate": 70, "avg_human": 20})
    cases.append(("均分只 +2 → 不采用", not keep3))
    okc = 0
    for name, cond in cases:
        print("  [%s] %s" % ("PASS" if cond else "FAIL", name))
        okc += 1 if cond else 0
    print("[self-test] %d/%d" % (okc, len(cases)))
    return 0 if okc == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--iters", type=int, default=500)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    return run_one(a)


if __name__ == "__main__":
    sys.exit(main())

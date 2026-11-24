#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ab_matrix.py - 用空余算力跑"数据切法"对照实验，回答"为什么训不出增益"。

背景（2026-11-19）：两次训练（965 行 1600 步 → 29/43；2655 行 600 步 → 25/43）
都低于基座 26/43 与旧基线 35/43。重复同一配置只会把 GPU 占满而不产结论，
所以把空余算力用在**可判读的对照**上：同一段语料、同一迭代数，只变数据切法。

判读口径：取每臂 val loss 的最低点（不是末点——末点必然回升，那是过拟合），
再比"最低点出现在第几步"：出现得早＝数据不够撑这么多步。

用法：
  .venv-housing/bin/python Tools/fleet/ab_matrix.py --seg craft_learner --iters 900
  .venv-housing/bin/python Tools/fleet/ab_matrix.py --seg craft_learner --iters 900 --arms 5,8
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
PY = sys.executable
TRAIN_PY = "/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3"
SENT = os.path.join(ROOT, ".codely-cli", "state", "TRAIN-EXCLUSIVE")


def sh(cmd, timeout=7200):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def val_curve(log_path):
    """从训练日志取 (step, loss) 序列。

    2026-11-19 实锚：mlx_lm 当前版本**没有** "Iter N: Val loss" 这种句子，
    真实行是被 ANSI 上色的表格：
        100    val 3.585    6.80s      ← 验证损失
        10    4.379 ▼        8   0.2k  ← 训练损失
    原正则找 "Iter ... Val loss" 一条都匹配不到，于是两臂都记 val_best=None、
    points=0，实验白烧 58 分钟。现在按真实格式解析，并优先取 val 行。
    """
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    vals, trains = [], []
    try:
        for line in open(log_path, encoding="utf-8", errors="replace"):
            s2 = ansi.sub("", line).strip()
            m = re.match(r"^(\d+)\s+val\s+([0-9.]+)", s2)
            if m:
                vals.append((int(m.group(1)), float(m.group(2))))
                continue
            m = re.match(r"^(\d+)\s+([0-9.]+)\s*[▼▲]", s2)
            if m:
                trains.append((int(m.group(1)), float(m.group(2))))
    except FileNotFoundError:
        pass
    # 验证损失是选点依据；没有 val 行时退回训练损失（并让调用方能看出来源）
    return vals or trains


def run_arm(seg, min_human, iters, tag):
    ds = os.path.join(SOCIAL, "train-ab-%s-h%d" % (seg, min_human))
    rc, o = sh([PY, os.path.join(HERE, "train_build.py"), "--out", ds,
                "--min-human", str(min_human), "--seg", seg], timeout=900)
    if rc != 0:
        return {"arm": tag, "verdict": "BUILD-FAIL", "why": o[-200:]}
    m = re.search(r"train\.jsonl (\d+) 条", o)
    built = int(m.group(1)) if m else 0
    # 2026-11-19 实锚：数据集目录曾被机队 clean 扫掉，训练器启动即 "缺 train.jsonl"
    # 而 rc=1 里看不出原因（连 train.log 都没建）。落盘后必须自己验一遍。
    for need in ("train.jsonl", "valid.jsonl"):
        if not os.path.exists(os.path.join(ds, need)):
            return {"arm": tag, "verdict": "DATASET-MISSING", "why": "%s 缺 %s" % (ds, need)}
    t0 = time.time()
    rc, o2 = sh([TRAIN_PY, "-u", os.path.join(HERE, "train_lora.py"),
                 "--data", ds, "--iters", str(iters), "--num-layers", "16",
                 "--max-seq-length", "224", "--steps-per-eval", "100",
                 "--grad-checkpoint", "--keep-models"], timeout=4 * 3600)
    wall = round((time.time() - t0) / 60.0, 1)
    runs = re.findall(r"RUNS/(\d{8}-\d{6})", o2)
    run = runs[-1] if runs else ""
    log = os.path.join(SOCIAL, "train", "RUNS", run, "train.log") if run else ""
    cur = val_curve(log)
    best = min(cur, key=lambda x: x[1]) if cur else (None, None)
    return {"arm": tag, "min_human": min_human, "rows": built, "iters": iters,
            "run": run, "train_rc": rc, "wall_min": wall,
            "val_best": best[1], "best_at_step": best[0], "val_last": cur[-1][1] if cur else None,
            "points": len(cur)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", default="craft_learner")
    ap.add_argument("--iters", type=int, default=900)
    ap.add_argument("--arms", default="5,8", help="min_human 的取值，逗号分隔")
    a = ap.parse_args()

    # 与 24x7 的训练共用同一个哨兵：实验也是训练，不能两个训练同时跑
    # （两个 mlx_lm 同时驻留会互相换出，2026-11-18 实锚）。已有哨兵就让路。
    waited = 0
    while os.path.exists(SENT) and waited < 1800:
        time.sleep(30)
        waited += 30
    open(SENT, "w").write("%s ab_matrix" % datetime.now().isoformat(timespec="seconds"))
    t0 = datetime.now()
    rec = {"ts": t0.isoformat(timespec="seconds"), "seg": a.seg, "iters": a.iters, "arms": []}
    for h in [x.strip() for x in a.arms.split(",") if x.strip()]:
        arm = run_arm(a.seg, int(h), a.iters, "min_human=%s" % h)
        rec["arms"].append(arm)
        print("[ab] %s → rows=%s val_best=%s@%s (rc=%s, %.1f min)"
              % (arm.get("arm"), arm.get("rows"), arm.get("val_best"),
                 arm.get("best_at_step"), arm.get("train_rc"), arm.get("wall_min") or 0))
    os.makedirs(STATE, exist_ok=True)
    try:
        if os.path.exists(SENT):
            os.remove(SENT)          # 实验结束必须摘哨兵，否则机队所有出稿都被挡
    except Exception:
        pass
    out = os.path.join(STATE, "ab-matrix-%s.json" % t0.strftime("%Y%m%d-%H%M%S"))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[ab] 报告 %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

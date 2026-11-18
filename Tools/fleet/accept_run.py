#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""accept_run.py - 训练跑完后自动验收：选点 → 切换 → 闭环验收 → 留或回滚。

为什么要自动化这一段（CEO 2026-11-18「不要让我来管你」）：
训练结束后有三步是纯机械判断，等人来做只会拖时间或凭印象挑点：
  1 读 val_loss_all 取最低步（不挑末尾——已实测末尾是过拟合段）
  2 把该 checkpoint 整理成可加载目录并切到 8788
  3 跑 43 题集 e2e；ACCEPT 记基线，REJECT 立刻切回上一版

判词与门槛完全复用 e2e_gate（覆盖率≥40/43 且品味中位≥80），本脚本不做第二套标准。

用法：
  python3 Tools/fleet/accept_run.py --run cph4/fleet/social/train/RUNS/20261118-163441
  python3 Tools/fleet/accept_run.py --run ... --wait 7200     # 等 RUN.json 最多 2 小时
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
ACTIVE = os.path.join(SOCIAL, "train", "ACTIVE.json")
LEDGER = os.path.join(SOCIAL, "TUNE-LEDGER.jsonl")
PY = sys.executable
FALLBACK = "cph4/fleet/social/train/RUNS/20261118-113014/best"


def sh(cmd, timeout=3600, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, env=e)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def wait_run(run_dir, max_wait):
    f = os.path.join(ROOT, run_dir, "RUN.json")
    t0 = time.time()
    while time.time() - t0 < max_wait:
        if os.path.exists(f):
            try:
                d = json.load(open(f, encoding="utf-8"))
                if d.get("val_loss_all"):
                    return d
            except Exception:
                pass
        time.sleep(120)
    return None


def best_step(val_loss_all):
    """返回 (最低 loss 的步数, 最低 loss)。步数 = (序号+1)*100（mlx 每 100 步存一次）。"""
    if not val_loss_all:
        return None, None
    i = min(range(len(val_loss_all)), key=lambda k: val_loss_all[k])
    return (i + 1) * 100, val_loss_all[i]


def find_ckpt(run_dir, step):
    d = os.path.join(run_dir, "adapter")
    for name in ("%05d_adapters.safetensors" % step, "%d_adapters.safetensors" % step,
                 "0000%d_adapters.safetensors" % step):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def make_ckpt_dir(run_dir, step, src):
    dst = os.path.join(run_dir, "ckpt%d" % step)
    os.makedirs(dst, exist_ok=True)
    shutil.copy(src, os.path.join(dst, "adapters.safetensors"))
    cfg = os.path.join(run_dir, "adapter", "adapter_config.json")
    if os.path.exists(cfg):
        shutil.copy(cfg, os.path.join(dst, "adapter_config.json"))
    return dst


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=False, help="RUNS/<ts> 目录（相对仓根）")
    ap.add_argument("--wait", type=int, default=10800, help="等 RUN.json 的秒数")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    run_dir = a.run
    print("[accept] 等 %s 的 RUN.json（最多 %ds）" % (run_dir, a.wait), flush=True)
    info = wait_run(run_dir, a.wait)
    if not info:
        print("[accept] 等不到 RUN.json，退出（训练可能失败）")
        return 2
    step, loss = best_step(info["val_loss_all"])
    print("[accept] 步数 %s 验证 loss 最低 %s（末点 %s）"
          % (step, loss, info["val_loss_all"][-1]), flush=True)

    src = find_ckpt(run_dir, step)
    if not src:
        print("[accept] 找不到第 %d 步 checkpoint，退出" % step)
        return 2
    ck = make_ckpt_dir(run_dir, step, src)
    print("[accept] 整理 checkpoint → %s" % ck, flush=True)

    rc, out = sh(["/bin/bash", os.path.join(HERE, "lora_switch.sh"), ck], timeout=600)
    print("[accept] 切换 rc=%d %s" % (rc, out.strip().splitlines()[-1] if out.strip() else ""), flush=True)
    if rc != 0:
        return 2

    # 训练已结束：清哨兵，让 ollama 车道能装载
    sent = os.path.join(ROOT, ".codely-cli", "state", "TRAIN-EXCLUSIVE")
    if os.path.exists(sent) and subprocess.run(["pgrep", "-f", "mlx_lm lora"],
                                               capture_output=True).returncode != 0:
        os.remove(sent)

    rc, out = sh([PY, os.path.join(HERE, "e2e_gate.py"), "--videos", "43"],
                 timeout=3600, env={"FLUX_ALLOW_DURING_TRAIN": "1"})
    verdict = "ACCEPT" if "判词：ACCEPT" in out else (
        "REJECT" if "判词：REJECT" in out else "INCONCLUSIVE")
    line = [x for x in out.strip().splitlines() if x.startswith("[e2e] 覆盖率")]
    print("[accept] 验收 %s ｜ %s" % (verdict, line[0] if line else "无数字"), flush=True)

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "run": run_dir, "step": step,
           "val_loss": loss, "verdict": verdict,
           "e2e": line[0] if line else "", "adapter": ck}
    if verdict == "ACCEPT":
        sh([PY, os.path.join(HERE, "e2e_gate.py"), "--videos", "43", "--record-baseline"],
           timeout=3600, env={"FLUX_ALLOW_DURING_TRAIN": "1"})
        try:
            cur = json.load(open(ACTIVE, encoding="utf-8"))
        except Exception:
            cur = {}
        cur.update({"adapter": ck, "run": os.path.basename(run_dir), "dataset": "train-h5",
                    "eval": {"note": line[0] if line else ""},
                    "why": "accept_run 自动验收通过（val 拐点 step=%d）" % step})
        json.dump(cur, open(ACTIVE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        rec["action"] = "keep"
    else:
        sh(["/bin/bash", os.path.join(HERE, "lora_switch.sh"), FALLBACK], timeout=600)
        rec["action"] = "rollback"
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[accept] 已记账：%s → %s" % (verdict, rec["action"]))
    return 0 if verdict == "ACCEPT" else 1


def self_test():
    """判据要能红：三组 val 曲线必须选出正确步数。"""
    cases = [
        ("末点最差时选中间", best_step([5.0, 3.0, 3.5, 4.0])[0] == 200),
        ("单调下降时选末点", best_step([5.0, 4.0, 3.0])[0] == 300),
        ("空曲线返回 None", best_step([])[0] is None),
        ("回滚目标存在", os.path.exists(os.path.join(ROOT, FALLBACK, "adapters.safetensors"))),
    ]
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())

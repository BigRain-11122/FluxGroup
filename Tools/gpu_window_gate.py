#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gpu_window_gate.py - GPU 重活点火前的共用显存门（D-20261117-02 落地）。

背景（2026-11-16/17 实测）：桌面常驻约占 10.2GB 显存，krea2 int8 本体 12.57GB，
剩 1.8GB 时点火不会崩，只会「GPU 100% 利用率但不出图」——白烧工时且污染失败计数。
CEO 用机让路律优先，所以**不得杀桌面程序**，只能判窗。

纪律：
  1) 任何 GPU 重活（krea2/i2v/KF 批）点火前必经本闸：free_mb >= need_mb * margin（默认 1.15）；
  2) 不达判 BLOCKED-NO-GPU-WINDOW —— 不点火、不换页硬跑、**不计入失败重试**、不写 chronic 违例；
  3) 读数取不到（无 nvidia-smi / 解析失败）判 UNKNOWN，**不默认放行**；
  4) 复活条件可测：free >= need 持续窗口（默认 600s）内每次采样都成立。

用法：
  from gpu_window_gate import check
  ok, info = check(12870)            # info = {"verdict":..., "free_mb":..., "need_mb":...}
  python3 Tools/gpu_window_gate.py --need 12870 [--margin 1.15] [--hold 600]
退出码：0 放行 / 3 BLOCKED-NO-GPU-WINDOW / 4 UNKNOWN（读数不可得）
"""
import argparse
import json
import subprocess
import sys
import time

DEFAULT_MARGIN = 1.15
DEFAULT_HOLD_S = 0


def free_mb():
    """返回 (free_mb, total_mb)；取不到返回 (None, None)。"""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode != 0:
            return None, None
        line = (out.stdout or "").strip().splitlines()[0]
        total, free = [int(float(x)) for x in line.split(",")[:2]]
        return free, total
    except Exception:
        return None, None


def check(need_mb, margin=DEFAULT_MARGIN, hold_s=DEFAULT_HOLD_S, poll_s=10):
    """判定当前是否有窗口。返回 (ok, info)。hold_s>0 时要求整个窗口内持续成立。"""
    required = int(need_mb * margin)
    deadline = time.time() + max(0, hold_s)
    samples = []
    while True:
        free, total = free_mb()
        if free is None:
            return False, {"verdict": "UNKNOWN", "why": "nvidia-smi 读数不可得",
                           "need_mb": need_mb, "required_mb": required, "free_mb": None}
        samples.append(free)
        if free < required:
            return False, {"verdict": "BLOCKED-NO-GPU-WINDOW", "need_mb": need_mb,
                           "required_mb": required, "free_mb": free, "total_mb": total,
                           "samples": samples}
        if time.time() >= deadline:
            return True, {"verdict": "WINDOW-OK", "need_mb": need_mb,
                          "required_mb": required, "free_mb": free, "total_mb": total,
                          "samples": samples}
        time.sleep(poll_s)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--need", type=int, required=True, help="重活本体所需显存 MB（如 krea2 int8=12870）")
    ap.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    ap.add_argument("--hold", type=int, default=DEFAULT_HOLD_S, help="持续成立秒数，默认 0=即取即判")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    ok, info = check(a.need, a.margin, a.hold)
    print(json.dumps(info, ensure_ascii=False) if a.json else
          "%s need=%s required=%s free=%s" % (info["verdict"], info.get("need_mb"),
                                              info.get("required_mb"), info.get("free_mb")))
    if info["verdict"] == "UNKNOWN":
        return 4
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""job_kf_batch.py - the missing actuator for a KF production job.

One command replaces the manual sequence (stop resident LLM -> free VRAM -> start
ComfyUI lowvram -> emit/run batch -> release):
  acquire GPU lease -> ensure ComfyUI -> run mv_kf_batch -> write receipt -> release.

Usage:
  python3 job_kf_batch.py --node bm-a --prompts P.json --out D:\\...\\batch1 [--limit 30]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import gpu_lease  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default="bm-a")
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--need-mb", type=int, default=12000)
    ap.add_argument("--keep-gpu", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    rc = gpu_lease.acquire(a.node, a.need_mb, True)
    if rc != 0:
        print("JOB-KF ABORT lease rc=%d" % rc)
        return 1
    cmd = [sys.executable, os.path.join(ROOT, "Tools", "mv_kf_batch.py"),
           "--prompts", a.prompts, "--out", a.out, "--limit", str(a.limit)]
    if a.only:
        cmd += ["--only", a.only]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        tail = "\n".join((p.stdout or "").splitlines()[-15:])
        print(tail)
        receipt = {
            "job": "kf_batch", "node": a.node, "prompts": a.prompts, "out": a.out,
            "limit": a.limit, "rc": p.returncode, "seconds": round(time.time() - t0, 1),
            "ts": datetime.now().isoformat(timespec="seconds"),
            "stdout_tail": tail,
            "stderr_tail": "\n".join((p.stderr or "").splitlines()[-10:]),
        }
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, "_job_receipt.json"), "w", encoding="utf-8") as f:
            json.dump(receipt, f, ensure_ascii=False, indent=1)
        return p.returncode
    finally:
        if not a.keep_gpu:
            gpu_lease.release(a.node)


if __name__ == "__main__":
    sys.exit(main())
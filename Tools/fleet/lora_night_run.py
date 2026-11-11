#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lora_night_run.py - 夜窗跑一次角色 LoRA 训练，并把"到底有没有出件"写成回执。

Why（2026-11-11）：`Tools/lora_pipeline.py train` 只把日志写到 TRAIN_HOME\\logs\\<name>，
不出回执——队列判"deliverable 是否存在"时无从判真假，容易出现"卡标 DONE、盘上没有
.safetensors"。本壳只做三件事：调既有流水线、找产物、写回执（rc/产物/体积/日志尾）。

用法：
  python Tools/fleet/lora_night_run.py --name ch01 [--out <receipt.json>] [--skip-cache]
Exit: 0 = 找到产物；1 = 没产物（回执照样写，含日志尾，供下轮判因）
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRAIN_HOME = os.environ.get("LORA_HOME", r"D:\FluxGroup-Offload\15-training")


def tail(path, n=40):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return "".join(fh.readlines()[-n:])
    except Exception as exc:  # noqa: BLE001 - reported in the receipt
        return "<no log: %s>" % exc


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--skip-cache", action="store_true")
    a = ap.parse_args(argv)

    out = a.out or os.path.join(ROOT, "cph4", "fleet", "queue-receipts",
                                "lora-%s-%s.json" % (a.name, time.strftime("%Y%m%d")))
    cmd = [sys.executable, os.path.join(ROOT, "Tools", "lora_pipeline.py"),
           "train", "--name", a.name]
    if a.skip_cache:
        cmd.append("--skip-cache")
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
    secs = round(time.time() - t0, 1)

    outdir = os.path.join(TRAIN_HOME, "outputs", a.name)
    arts = []
    if os.path.isdir(outdir):
        for n in sorted(os.listdir(outdir)):
            if n.lower().endswith((".safetensors", ".pt")):
                p = os.path.join(outdir, n)
                arts.append({"file": p, "bytes": os.path.getsize(p)})
    log = os.path.join(TRAIN_HOME, "logs", a.name, "train.log")

    rec = {
        "id": "LORA-TRAIN-%s-%s" % (a.name, time.strftime("%Y%m%d")),
        "name": a.name,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rc": proc.returncode,
        "seconds": secs,
        "artifacts": arts,
        "artifact_exists": bool(arts),
        "verdict": "PASS" if arts and proc.returncode == 0 else "FAIL",
        "stdout_tail": (proc.stdout or "")[-1500:],
        "stderr_tail": (proc.stderr or "")[-800:],
        "train_log_tail": tail(log, 40),
    }
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("[lora-night] %s rc=%d seconds=%s artifacts=%d -> %s"
          % (rec["verdict"], proc.returncode, secs, len(arts), out))
    return 0 if rec["artifact_exists"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

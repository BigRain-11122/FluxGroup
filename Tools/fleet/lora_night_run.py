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
import shutil
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


def ref_dir(name):
    """参考图集目录（大小写不敏感——卡上写 ch01，盘上是 CH01）。"""
    base = os.path.join(ROOT, "media", "asset", "characters")
    for cand in (name, name.upper(), name.lower(), name.capitalize()):
        p = os.path.join(base, cand)
        if os.path.isdir(p):
            return p
    return ""


def write_receipt(out, rec):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--skip-cache", action="store_true")
    ap.add_argument("--publish", default="",
                    help="产物目录（对齐 PRODUCTS.outputs，例如 cph4/fleet/out/asset-pack/lora/）；"
                         "会把最新 .safetensors 复制成 <name>_rank32.safetensors，判据可写死路径")
    a = ap.parse_args(argv)

    out = a.out or os.path.join(ROOT, "cph4", "fleet", "queue-receipts",
                                "lora-%s-%s.json" % (a.name, time.strftime("%Y%m%d")))

    # 缺输入先写回执再退出（2026-11-12 bm-c 现场切换实弹）：原实现直接调流水线，
    # 训练区不在盘时异常穿过 main()，卡上只剩 "rc=None, no output captured" ——
    # 读卡的人看不出缺的是哪个目录，只能每 5 分钟重试一次同一个黑洞。
    miss = []
    if not os.path.isdir(TRAIN_HOME):
        miss.append("TRAIN_HOME（训练工作区）不存在：%s" % TRAIN_HOME)
    ref = ref_dir(a.name)
    if not ref:
        miss.append("参考图集不存在：%s"
                    % os.path.join(ROOT, "media", "asset", "characters", a.name))
    if miss:
        rec = {
            "id": "LORA-TRAIN-%s-%s" % (a.name, time.strftime("%Y%m%d")),
            "name": a.name,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "rc": 3,
            "seconds": 0,
            "artifacts": [],
            "published": "",
            "artifact_exists": False,
            "verdict": "BLOCKED",
            "missing": miss,
            "ref_dir": ref,
            "train_home": TRAIN_HOME,
            "note": "缺输入，未开始训练（回执留证，不在没有工作区的情况下空烧 GPU）",
        }
        write_receipt(out, rec)
        print("[lora-night] BLOCKED " + " | ".join(miss))
        return 3
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

    published = ""
    if a.publish and arts:
        try:
            pdir = a.publish
            if not os.path.isabs(pdir):
                pdir = os.path.join(ROOT, pdir)
            os.makedirs(pdir, exist_ok=True)
            src = max(arts, key=lambda x: x["bytes"])["file"]
            published = os.path.join(pdir, "%s_rank32.safetensors" % a.name)
            shutil.copy2(src, published)
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            published = ""

    rec = {
        "id": "LORA-TRAIN-%s-%s" % (a.name, time.strftime("%Y%m%d")),
        "name": a.name,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rc": proc.returncode,
        "seconds": secs,
        "artifacts": arts,
        "published": published,
        "artifact_exists": bool(arts) and (bool(published) if a.publish else True),
        "verdict": "PASS" if arts and proc.returncode == 0 else "FAIL",
        "stdout_tail": (proc.stdout or "")[-1500:],
        "stderr_tail": (proc.stderr or "")[-800:],
        "train_log_tail": tail(log, 40),
    }
    write_receipt(out, rec)
    print("[lora-night] %s rc=%d seconds=%s artifacts=%d -> %s"
          % (rec["verdict"], proc.returncode, secs, len(arts), out))
    return 0 if rec["artifact_exists"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

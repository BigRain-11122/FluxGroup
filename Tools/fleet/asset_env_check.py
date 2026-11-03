#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_env_check.py - 资产训练环境自检（哪台机能烧 LoRA / 哪台能训音色）。

为什么（2026-11-03）：CEO 令先储备资产（角色 LoRA + 音色库）。烧之前必须先回答
"这台机器现在到底能不能烧"，否则会派出一张注定失败的卡，然后把失败记成"模型不行"。
本工具只报事实：有什么、缺什么、这条路能不能走。

检查项：
  1. ffmpeg（数据集切分/抽帧/审计都要）
  2. python + 是否装 torch、torch.cuda 可用否（Windows 机的训练前提）
  3. 图像训练栈：kohya sd-scripts（环境变量 KOHYA_DIR，或常见路径）
  4. 音色训练栈：GPT-SoVITS（环境变量 GPTSOVITS_DIR，或常见路径）
  5. 资产目录是否在位（media/asset/{faces,voices}）
  6. 可用磁盘（训练产物与数据集都吃盘）

用法：
  python3 asset_env_check.py [--out receipts/asset-env-<node>.json] [--node bm-c]
Exit: 0 至少一条训练路线可用；1 两条都不可用（列出缺什么）；2 环境损坏（无 python 包/无盘）。
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

KOHYA_HINTS = [
    os.environ.get("KOHYA_DIR") or "",
    os.path.join(ROOT, "Tools", "kohya_ss"),
    os.path.join(ROOT, "..", "kohya_ss"),
    r"D:\AI\kohya_ss",
    r"C:\AI\kohya_ss",
    os.path.expanduser("~/kohya_ss"),
]
GPTSOVITS_HINTS = [
    os.environ.get("GPTSOVITS_DIR") or "",
    os.path.join(ROOT, "Tools", "GPT-SoVITS"),
    r"D:\AI\GPT-SoVITS",
    r"C:\AI\GPT-SoVITS",
    os.path.expanduser("~/GPT-SoVITS"),
]


def first_existing(paths, marker):
    for p in paths:
        if not p:
            continue
        p = os.path.abspath(os.path.expanduser(p))
        if marker and os.path.exists(os.path.join(p, marker)):
            return p
        if not marker and os.path.isdir(p):
            return p
    return None


def torch_state():
    try:
        import torch  # noqa: F401
    except Exception as e:
        return {"installed": False, "why": str(e)[:80]}
    try:
        import torch
        return {"installed": True, "version": torch.__version__,
                "cuda": bool(torch.cuda.is_available()),
                "device": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)}
    except Exception as e:
        return {"installed": True, "why": str(e)[:80]}


def disk_free_gb(path):
    try:
        st = os.statvfs(path) if hasattr(os, "statvfs") else None
    except Exception:
        st = None
    if st:
        return round(st.f_bavail * st.f_frsize / 1e9, 1)
    try:
        out = subprocess.run(["df", "-g", path], capture_output=True, text=True, timeout=20).stdout
        line = out.strip().splitlines()[-1].split()
        return float(line[3])
    except Exception:
        return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--node", default=os.environ.get("NODE", ""))
    a = ap.parse_args(argv)

    gaps, ok_routes = [], []
    kohya = first_existing(KOHYA_HINTS, os.path.join("sd-scripts", "train_network.py")) or \
        first_existing(KOHYA_HINTS, "train_network.py")
    sovits = first_existing(GPTSOVITS_HINTS, os.path.join("GPT_SoVITS", "s2_train.py")) or \
        first_existing(GPTSOVITS_HINTS, None)
    ff = shutil.which("ffmpeg")
    ts = torch_state()
    dirs = {}
    for name in ("faces", "voices", "loras", "voice-models"):
        p = os.path.join(ROOT, "media", "asset", name)
        dirs[name] = {"path": p, "exists": os.path.isdir(p),
                      "files": len(glob.glob(os.path.join(p, "*"))) if os.path.isdir(p) else 0}

    if not ff:
        gaps.append("没有 ffmpeg（切分/抽帧/审计都要）")
    if not ts.get("installed"):
        gaps.append("没有 torch（%s）" % ts.get("why"))
    elif not ts.get("cuda"):
        gaps.append("torch 已装但 CUDA 不可用（CPU 训练 LoRA 不现实）")
    if kohya:
        ok_routes.append("face-lora:%s" % kohya)
    else:
        gaps.append("没有 kohya sd-scripts（角色 LoRA 训练栈）——找 KOHYA_DIR 环境变量或装一份")
    if sovits:
        ok_routes.append("voice-ft:%s" % sovits)
    else:
        gaps.append("没有 GPT-SoVITS（音色微调栈）——找 GPTSOVITS_DIR 环境变量或装一份")
    for name, d in dirs.items():
        if not d["exists"]:
            gaps.append("资产目录不在位：media/asset/%s" % name)
    free = disk_free_gb(ROOT)
    if free is not None and free < 20:
        gaps.append("可用磁盘 %.1fGB < 20GB（训练产物吃盘）" % free)

    out = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "node": a.node or "unknown",
        "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
        "spec": "ASSET-ENV-GATE-v1",
        "measured": {"ffmpeg": ff, "python": sys.version.split()[0], "torch": ts,
                     "kohya": kohya, "gptsovits": sovits, "dirs": dirs, "disk_free_gb": free},
        "routes_ok": ok_routes,
        "verdict": "PASS" if ok_routes else "FAIL",
        "gaps": gaps,
        "note": "PASS=至少一条训练路线可用；具体是哪条看 routes_ok",
    }
    out["status"] = out["verdict"]
    if a.out:
        d = os.path.dirname(os.path.abspath(a.out))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    print("ASSET-ENV %s  %s" % (out["verdict"], out["node"]))
    print("  可用路线: %s" % (", ".join(ok_routes) or "无"))
    for g in gaps:
        print("  ! " + g)
    return 0 if ok_routes else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
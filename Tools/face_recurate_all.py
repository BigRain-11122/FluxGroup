# -*- coding: utf-8 -*-
"""face_recurate_all.py — 用当前挑选口径把已有 raw 池全部重挑一遍（不下载、不训练、不碰 GPU）。

为什么有它（2026-11-17）：
  挑选口径当天改了两处——合影跳过阈值 40%→60%（写真/剧照旁边常有人，旧口径把好图当废图扔）、
  新增 pHash 近重复剔除（同一原图的不同裁切会重复占配额）。
  改完必须把已有池子重挑，否则此前判成 insufficient 的人会一直等下一轮采集，
  而它们的 raw 里其实已经有 80-400 张可用候选。

用法：
  py Tools/face_recurate_all.py                 # 全部批次
  py Tools/face_recurate_all.py --only ql05,tm01
  py Tools/face_recurate_all.py --keep 45 --out-name curated
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup"
FACES = os.path.join(ROOT, "media", "faces")
PREP = os.path.join(ROOT, "Tools", "face_lora_prep.py")
PY = r"C:\Users\sjs20\train-lora\.venv\Scripts\python.exe"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def batches():
    out = []
    for name in sorted(os.listdir(FACES)):
        d = os.path.join(FACES, name)
        if not os.path.isdir(d) or name.startswith(("_", ".")) or name.endswith("-ds"):
            continue
        raw = os.path.join(d, "raw")
        if not os.path.isdir(raw):
            continue
        n = sum(1 for f in os.listdir(raw) if f.lower().endswith(IMG_EXT))
        if n >= 20:
            out.append((name, raw, n))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", type=int, default=45)
    ap.add_argument("--out-name", default="curated")
    ap.add_argument("--only", default="")
    ap.add_argument("--board", action="store_true", default=True)
    a = ap.parse_args()

    only = {x.strip() for x in a.only.split(",") if x.strip()}
    rows = []
    for name, raw, n in batches():
        if only and name not in only:
            continue
        out = os.path.join(FACES, name, a.out_name)
        board = os.path.join(FACES, "_boards", "%s.jpg" % name)
        t0 = time.time()
        p = subprocess.run([PY, PREP, "curate", raw, "--out", out, "--keep", str(a.keep),
                            "--board", board],
                           capture_output=True)
        # 直接数输出目录，不解析 stdout——curate 的中文打印在 Windows 下是 GBK，
        # 用 utf-8 解会乱码导致"留存 N 张"匹配不到（本脚本首版即踩此坑）。
        picked = sum(1 for f in os.listdir(out) if f.lower().endswith(IMG_EXT)) if os.path.isdir(out) else 0
        raw_out = (p.stdout or b"").decode("utf-8", "replace")
        if "候选" not in raw_out:
            raw_out = (p.stdout or b"").decode("gbk", "replace")
        line = ""
        for ln in raw_out.splitlines():
            if "候选" in ln and "留存" in ln:
                line = ln.strip()
        rows.append((name, n, picked, round(time.time() - t0, 1), line or (p.stderr or b"")[-120:]))
        print("%-14s raw=%3d  选中=%3d  %5.1fs  %s" % (name, n, picked, time.time() - t0, line), flush=True)

    ok = sum(1 for r in rows if r[2] >= 40)
    half = sum(1 for r in rows if 20 <= r[2] < 40)
    bad = sum(1 for r in rows if r[2] < 20)
    print("\n合计 %d 批：达标(>=40) %d · 可训(20-39) %d · 不足(<20) %d" % (len(rows), ok, half, bad))
    print("不足清单：%s" % ", ".join(r[0] for r in rows if r[2] < 20))
    return 0


if __name__ == "__main__":
    sys.exit(main())

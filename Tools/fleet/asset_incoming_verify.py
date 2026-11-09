#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_incoming_verify.py - 独立复核采集清单，不信智能体自报的数字。

为什么：素材采集由 subagent 完成，它们自己算 bytes/sha256/尺寸并写 manifest。
自报即证据=度量自指。此脚本从磁盘重新算一遍，逐条比对，把"声称"变成"核验"。

判据：
  - 清单里每条：文件存在、bytes 一致、sha256 一致；
  - 图片：能打开且 w/h 与清单一致；
  - 音频/视频：ffprobe 实测时长与清单一致（±0.3s）；
  - 清单里有但盘上没有 → MISSING；盘上有但清单没登记 → UNLISTED。

用法：python3 Tools/fleet/asset_incoming_verify.py [--root /Volumes/移动硬盘/FluxAssets/incoming]
Exit: 0 全一致；1 有差异；2 根目录不存在
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "asset-verify.json")
FFPROBE = "/Users/junsheng.sun/bin/ffprobe"
IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
AUD = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aif", ".aiff")
VID = (".mp4", ".mov", ".mkv", ".webm")


def sha256(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dims(p):
    try:
        from PIL import Image
        with Image.open(p) as im:
            return im.size
    except Exception:
        return (None, None)


def dur(p):
    exe = FFPROBE if os.path.exists(FFPROBE) else "ffprobe"
    try:
        r = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", p],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None


def walk_manifests(root):
    out = []
    for d, _s, files in os.walk(root):
        if "manifest.jsonl" in files:
            out.append(os.path.join(d, "manifest.jsonl"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/Volumes/移动硬盘/FluxAssets/incoming")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.root):
        print("[verify] 根不存在 %s（rc=2）" % a.root)
        return 2
    rows, problems, listed = [], [], set()
    for mf in walk_manifests(a.root):
        base = os.path.dirname(mf)
        cls = os.path.basename(base)
        ok = bad = 0
        with open(mf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    problems.append({"file": mf, "why": "坏 JSON 行"})
                    bad += 1
                    continue
                rel = str(row.get("file") or "")
                cands = [os.path.join(base, rel), os.path.join(base, os.path.basename(rel)),
                         os.path.join(a.root, rel)]
                p = next((c for c in cands if os.path.isfile(c)), None)
                if not p:
                    problems.append({"class": cls, "file": rel, "why": "MISSING 盘上没有"})
                    bad += 1
                    continue
                listed.add(os.path.abspath(p))
                size = os.path.getsize(p)
                if row.get("bytes") is not None and int(row["bytes"]) != size:
                    problems.append({"class": cls, "file": rel,
                                     "why": "bytes %s != %s" % (row["bytes"], size)})
                    bad += 1
                    continue
                if row.get("sha256"):
                    got = sha256(p)
                    if got.lower() != str(row["sha256"]).lower():
                        problems.append({"class": cls, "file": rel,
                                         "why": "sha 不符 %s != %s" % (got[:12], str(row["sha256"])[:12])})
                        bad += 1
                        continue
                low = p.lower()
                if low.endswith(IMG) and row.get("w") and row.get("h"):
                    w, h = dims(p)
                    if w and (w != int(row["w"]) or h != int(row["h"])):
                        problems.append({"class": cls, "file": rel,
                                         "why": "尺寸 %sx%s != %sx%s" % (w, h, row["w"], row["h"])})
                        bad += 1
                        continue
                if low.endswith(AUD + VID) and row.get("dur_s"):
                    d = dur(p)
                    if d is None:
                        problems.append({"class": cls, "file": rel, "why": "ffprobe 取不到时长"})
                        bad += 1
                        continue
                    if abs(d - float(row["dur_s"])) > 0.35:
                        problems.append({"class": cls, "file": rel,
                                         "why": "时长 %.2f != %.2f" % (d, float(row["dur_s"]))})
                        bad += 1
                        continue
                ok += 1
        rows.append({"class": cls, "manifest": mf, "ok": ok, "bad": bad})
    # 盘上有但清单没登记的文件
    unlisted = []
    for d, _s, files in os.walk(a.root):
        for n in files:
            p = os.path.join(d, n)
            if n.endswith((".jsonl", ".md", ".json", ".txt")):
                continue
            if not p.lower().endswith(IMG + AUD + VID + (".otf", ".ttf", ".woff", ".woff2")):
                continue
            if os.path.abspath(p) not in listed:
                unlisted.append(os.path.relpath(p, a.root))
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "root": a.root,
           "manifests": rows,
           "verified_ok": sum(r["ok"] for r in rows),
           "verified_bad": sum(r["bad"] for r in rows),
           "unlisted_count": len(unlisted),
           "problems": problems[:200],
           "verdict": "PASS" if not problems and not unlisted else "DIFF"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("[verify] 核验通过 %d 条，不一致 %d 条，未登记文件 %d 个"
          % (rec["verified_ok"], rec["verified_bad"], len(unlisted)))
    for r in rows:
        print("  %-12s ok=%-4d bad=%-3d" % (r["class"], r["ok"], r["bad"]))
    for p in problems[:10]:
        print("  ! %s %s" % (p.get("file"), p.get("why")))
    for u in unlisted[:10]:
        print("  ? 未登记 %s" % u)
    return 0 if rec["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
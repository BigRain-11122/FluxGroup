#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pack_release.py - 把一个目录打成可交付的发布包（产物，不是报告）。

产出：
  <out>/MANIFEST.json     每个文件的字节/时长/分辨率/编码/sha256
  <out>/checksums.sha256  可直接核验
  <out>/RELEASE-NOTES.md  包含什么、怎么验收、已知问题
  <out>/contact-sheet.jpg 视频缩略图拼版（有 ffmpeg 时）
用法：
  python3 Tools/fleet/pack_release.py --dir media/review-720p --name MV-REVIEW-20261110
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def probe(path):
    try:
        p = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                            "-show_format", "-show_streams", path],
                           capture_output=True, text=True, timeout=30)
        d = json.loads(p.stdout or "{}")
        st = next((s for s in d.get("streams") or [] if s.get("codec_type") == "video"), {})
        return {"duration_s": round(float(d.get("format", {}).get("duration") or 0), 2),
                "width": st.get("width"), "height": st.get("height"),
                "codec": st.get("codec_name"), "fps": st.get("r_frame_rate")}
    except Exception:
        return {}


def contact_sheet(files, out_jpg):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False
    thumbs = []
    tmp = tempfile.mkdtemp(prefix="cs-")
    for i, f in enumerate(files[:20]):
        t = os.path.join(tmp, "%02d.jpg" % i)
        try:
            subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", "1", "-i", f,
                            "-frames:v", "1", "-vf", "scale=320:-1", t],
                           capture_output=True, timeout=30)
            if os.path.exists(t):
                thumbs.append((os.path.basename(f), Image.open(t).convert("RGB")))
        except Exception:
            pass
    if not thumbs:
        return False
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    w, h = thumbs[0][1].size
    sheet = Image.new("RGB", (cols * w, rows * (h + 18)), (16, 18, 24))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x, y = (i % cols) * w, (i // cols) * (h + 18)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + h + 3), name[:44], fill=(200, 210, 225))
    sheet.save(out_jpg, quality=88)
    shutil.rmtree(tmp, ignore_errors=True)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    src = os.path.join(ROOT, a.dir) if not os.path.isabs(a.dir) else a.dir
    if not os.path.isdir(src):
        raise SystemExit("not a directory: %s" % src)
    out = a.out or os.path.join(ROOT, "media", "releases", a.name)
    os.makedirs(out, exist_ok=True)
    files = sorted(os.path.join(src, f) for f in os.listdir(src) if os.path.isfile(os.path.join(src, f)))
    man, sums = [], []
    for f in files:
        size = os.path.getsize(f)
        h = sha256(f)
        item = {"file": os.path.relpath(f, ROOT), "bytes": size, "sha256": h}
        if f.lower().endswith((".mp4", ".mov", ".mkv")):
            item.update(probe(f))
        man.append(item)
        sums.append("%s  %s" % (h, os.path.relpath(f, ROOT)))
    json.dump({"name": a.name, "source": a.dir, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "count": len(man), "total_bytes": sum(m["bytes"] for m in man), "files": man},
              open(os.path.join(out, "MANIFEST.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(out, "checksums.sha256"), "w", encoding="utf-8").write("\n".join(sums) + "\n")
    videos = [f for f in files if f.lower().endswith((".mp4", ".mov", ".mkv"))]
    sheet = os.path.join(out, "contact-sheet.jpg")
    made_sheet = contact_sheet(videos, sheet) if videos else False
    total = sum(m["bytes"] for m in man) / 1024 ** 2
    notes = ["# %s 发布包" % a.name, "",
             "- 生成时间：%s" % time.strftime("%Y-%m-%d %H:%M"),
             "- 来源目录：%s" % a.dir,
             "- 文件数：%d，合计 %.1f MB" % (len(man), total),
             "- 校验：checksums.sha256（sha256sum -c 可验）",
             "- 清单：MANIFEST.json（含时长/分辨率/编码）",
             "- 拼版：contact-sheet.jpg" if made_sheet else "- 拼版：未生成（缺 ffmpeg）",
             "", "## 验收", "", "1. 文件数与清单一致；", "2. 校验和全部匹配；",
             "3. 视频分辨率/时长符合预期；", "4. 抽看拼版图无黑帧/花屏。", ""]
    open(os.path.join(out, "RELEASE-NOTES.md"), "w", encoding="utf-8").write("\n".join(notes))
    print("release: %s files=%d %.1fMB sheet=%s" % (out, len(man), total, made_sheet))
    return 0


if __name__ == "__main__":
    sys.exit(main())

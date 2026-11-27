#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vertical_reframe.py - 横屏素材重排成 1080x1920 竖屏（漫剧用）。

做法：主体等比缩到宽 1080，上下用原图放大+高斯模糊填满，避免裁掉画面两侧。
编码走 h264_videotoolbox（GPU），失败回落 libx264。

用法：
  python3 Tools/fleet/vertical_reframe.py --src <dir> --dst <dir> [--jobs 4]
Exit: 0 全部成功；1 有失败；2 无输入
"""
import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

FFMPEG = "/Users/junsheng.sun/bin/ffmpeg" if os.path.exists("/Users/junsheng.sun/bin/ffmpeg") else "ffmpeg"
VF = ("[0:v]scale=1080:-2,split[bg][fg];"
      "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=24[b];"
      "[fg]scale=1080:-2[f];[b][f]overlay=(W-w)/2:(H-h)/2[vout]")


def encode(src, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return True, "SKIP"
    tmp = dst + ".part.mp4"
    for codec in (["-c:v", "h264_videotoolbox", "-b:v", "6M"],
                  ["-c:v", "libx264", "-crf", "20", "-preset", "medium"]):
        cmd = [FFMPEG, "-y", "-v", "error", "-i", src, "-filter_complex", VF,
               "-map", "[vout]", "-map", "0:a?", "-c:a", "aac", "-b:a", "128k"] + codec + [tmp]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            if p.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                os.replace(tmp, dst)
                return True, "%s %dKB" % (codec[1], os.path.getsize(dst) // 1024)
        except Exception as e:
            last = str(e)[:80]
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    return False, "失败"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.src):
        print("[vref] 源目录不存在 %s（rc=2）" % a.src)
        return 2
    files = sorted(f for f in os.listdir(a.src) if f.lower().endswith((".mp4", ".mov")))
    if not files:
        print("[vref] 无视频（rc=2）")
        return 2
    os.makedirs(a.dst, exist_ok=True)
    t0 = time.time()
    ok, bad = 0, []
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(encode, os.path.join(a.src, f),
                          os.path.join(a.dst, os.path.splitext(f)[0] + "-vertical.mp4")): f
                for f in files}
        for fu in futs:
            f = futs[fu]
            try:
                good, why = fu.result()
            except Exception as e:
                good, why = False, str(e)[:80]
            if good:
                ok += 1
                print("[vref] OK   %s %s" % (f, why))
            else:
                bad.append({"file": f, "why": why})
                print("[vref] FAIL %s %s" % (f, why))
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "src": a.src, "dst": a.dst,
           "total": len(files), "ok": ok, "failed": bad,
           "seconds": round(time.time() - t0, 1),
           "verdict": "PASS" if not bad else "PARTIAL"}
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                       "cph4", "fleet", "state", "vertical-reframe.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("[vref] %d/%d 成功，用时 %.0fs" % (ok, len(files), time.time() - t0))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
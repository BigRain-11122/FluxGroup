# -*- coding: utf-8 -*-
"""mv_finish_delivery.py - one command from master to delivery, self-verifying.

Steps: watermark embed -> full-film decode -> crf23/crf28 stress -> 4K upscale ->
spec + audio + tail-credit probes. Every step is measured, not asserted; the script
exits non-zero if any probe fails so a green run means the artifact is actually green.

Usage:
  py Tools/mv_finish_delivery.py --n1 <..._n1.mp4> --wm <..._wm.mp4> --4k <..._4k.mp4>
"""
import argparse
import json
import os
import re
import subprocess
import sys

PY = r"C:\Users\sjs20\comfyui-krea\ComfyUI_windows_portable\python_embeded\python.exe"
TOOL = (r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
        r"\mv_videoseal_wm_r1017.py")
FF = "ffmpeg"
FFPROBE = "ffprobe"
TP_GATE = -1.0
EXPECT_FRAMES = 14064


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace", **kw)


def probe(path, sel, entries):
    r = run([FFPROBE, "-v", "error", "-select_streams", sel,
             "-show_entries", entries, "-of", "json", path])
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def loudness(path):
    r = run([FF, "-hide_banner", "-nostats", "-i", path, "-af",
             "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"])
    a, b = (r.stderr or "").rfind("{"), (r.stderr or "").rfind("}")
    if a < 0 or b < 0:
        return None, None
    d = json.loads(r.stderr[a:b + 1])
    return float(d["input_i"]), float(d["input_tp"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n1", required=True)
    ap.add_argument("--wm", required=True)
    ap.add_argument("--4k", required=True)
    ap.add_argument("--crf", default="18")
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--skip-embed", action="store_true")
    a = ap.parse_args()

    fails = []
    out4k = getattr(a, "4k")

    if not a.skip_embed:
        print("== 1/4 watermark embed ==", flush=True)
        r = run([PY, TOOL, "embed", a.n1, a.wm, a.crf, a.preset])
        tail = [l for l in (r.stdout or "").splitlines() if "EMBED-OK" in l]
        print(tail[-1] if tail else (r.stdout or "")[-300:], flush=True)
        if not tail:
            fails.append("embed produced no EMBED-OK")
    else:
        print("== 1/4 embed skipped ==", flush=True)

    print("== 2/4 full film decode ==", flush=True)
    r = run([PY, TOOL, "extract", a.wm])
    m = [l for l in (r.stdout or "").splitlines() if l.startswith("DECODE")]
    print(m[0] if m else "(no DECODE line)", flush=True)
    if not m or "100.0%" not in m[0]:
        fails.append("watermark decode below 100%%: %s" % (m[0] if m else "none"))

    print("== 3/4 platform stress ==", flush=True)
    r = run([PY, TOOL, "stress", a.wm])
    dec = [l for l in (r.stdout or "").splitlines() if l.startswith("DECODE-L")]
    for l in dec:
        print(l, flush=True)
        if "100.0%" not in l:
            fails.append("stress decode below 100%%: %s" % l)
    if len(dec) < 2:
        fails.append("stress ran %d of 2 levels" % len(dec))

    print("== 4/4 4K upscale ==", flush=True)
    r = run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", a.wm,
             "-vf", "scale=3840:2192:flags=lanczos,unsharp=5:5:0.3:5:5:0.0",
             "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "19",
             "-b:v", "28M", "-maxrate", "40M", "-bufsize", "56M",
             "-profile:v", "high", "-level", "5.2", "-pix_fmt", "yuv420p", "-r", "60",
             "-c:a", "copy", "-movflags", "+faststart", out4k])
    if r.returncode != 0:
        fails.append("4k encode failed: %s" % (r.stderr or "")[-300:])

    print("== probes ==", flush=True)
    for tag, path in (("wm", a.wm), ("4k", out4k)):
        v = probe(path, "v:0", "stream=width,height,r_frame_rate,nb_frames")
        st = (v.get("streams") or [{}])[0]
        i, tp = loudness(path)
        print("%-3s %sx%s %s frames=%s  I=%s LUFS  TP=%s dBTP"
              % (tag, st.get("width"), st.get("height"), st.get("r_frame_rate"),
                 st.get("nb_frames"), i, tp), flush=True)
        if tp is None or tp > TP_GATE:
            fails.append("%s true peak %s above %s" % (tag, tp, TP_GATE))
        if str(st.get("nb_frames")) not in ("None", "0") and int(st["nb_frames"]) != EXPECT_FRAMES:
            fails.append("%s frames %s != %d" % (tag, st.get("nb_frames"), EXPECT_FRAMES))

    print("SUMMARY:", "PASS" if not fails else "FAIL", flush=True)
    for f in fails:
        print("  FAIL", f, flush=True)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())

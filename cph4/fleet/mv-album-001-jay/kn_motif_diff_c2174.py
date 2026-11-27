# kn_motif_diff_c2174.py - assembly-layer differentiation test for the KN motif repeat (zero GPU).
# Why: C2173 measured that KN06/07/10/11/12/13 are six burns of one setup (white paper plane over
# a night city) filling 41 s of cut time, and ruled out a mid-wave re-burn. The director decision
# was to differentiate at assembly with graded punch-ins and alternating speeds, but nothing
# implemented it. This turns that decision into footage plus a number:
#   BEFORE = the six units on their authored windows, authored speed, no punch-in
#   AFTER  = same windows, graded punch-in 1.06 -> 1.35, speeds alternating 0.97 / 1.03
# Both are cut to the identical per-unit durations, so a viewer compares like for like, and the
# plane blob width share (reusing C2173's measure) is reported for both to show whether the run
# actually spreads instead of sitting on one scale.
import io
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kn_motif_repeat_c2173 as mr  # noqa: E402  (reuse the plane-blob measure)

ALBUM = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2174")
OUT = os.path.join(ALBUM, "motif-diff-c2174")
OUTDIR = os.path.dirname(os.path.abspath(__file__))
SHOTS = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\可爱女人-shots-v2.py"
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"
W, H, FPS = 1344, 768, 24
# graded punch-in across the run + alternating speeds: no two neighbours share both scale and pace
# flip on every other unit breaks the repeated left-to-right travel direction, which is what
# makes six burns read as one shot; scale alone only makes the same subject larger.
PLAN = [("KN06", 1.06, 0.97, False), ("KN07", 1.14, 1.03, True),
        ("KN10", 1.12, 0.97, False), ("KN11", 1.20, 1.03, True),
        ("KN12", 1.28, 0.97, False), ("KN13", 1.35, 1.03, True)]


def sh(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("FFMPEG-FAIL rc=%d\n%s\n%s" % (p.returncode, " ".join(cmd[:14]), p.stderr[-1200:]))
        sys.exit(1)


def dur_of(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def windows():
    text = io.open(SHOTS, encoding="utf-8").read()
    first = {}
    for shot, s, e, sp in re.findall(r'\("(KN\d+[a-z]?)",\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)', text):
        first.setdefault(shot, (float(s), float(e), float(sp)))
    return first


def build(shot, zoom, speed, dur, dest, flip=False):
    # explicit even crop keeps yuv420p scaling happy; centered crop = same framing, tighter
    zw = "trunc(iw/%.4f/2)*2" % zoom
    zh = "trunc(ih/%.4f/2)*2" % zoom
    vf = ("setpts=PTS/%.4f,fps=%d,crop=%s:%s:(iw-%s)/2:(ih-%s)/2,scale=%d:%d:flags=lanczos%s"
          % (speed, FPS, zw, zh, zw, zh, W, H, ",hflip" if flip else ""))
    sh([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", os.path.join(CLIPS, "KN_A-%s.mp4" % shot), "-vf", vf, "-t", "%.3f" % dur,
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", dest])


def concat(parts, dest):
    lst = os.path.join(OUT, "_c_%s.txt" % os.path.basename(dest).split(".")[0])
    io.open(lst, "w", encoding="utf-8", newline="\n").write(
        "".join("file '%s'\n" % p.replace("\\", "/") for p in parts))
    sh([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", lst, "-c", "copy", "-movflags", "+faststart", dest])


def spread(seg_paths, durs):
    """Plane blob width share per segment; the point is the RANGE, not the mean."""
    mr.EVID = EVID
    vals = []
    for p, d in zip(seg_paths, durs):
        m = mr.measure(p, d)
        vals.append({"clip": os.path.basename(p), "box_w_frac": m["box_w_frac"],
                     "area_frac": m["area_frac"], "cx": m["cx"], "cy": m["cy"],
                     "face_present": m["face_present"]})
    w = [v["box_w_frac"] for v in vals if not v["face_present"]]
    if len(w) < 2:
        return {"rows": vals, "n": len(w), "std": 0.0, "range": 0.0}
    cxs = [v["cx"] for v in vals if not v["face_present"]]
    return {"rows": vals, "n": len(w), "std": round(float(np.std(w)), 4),
            "range": round(max(w) - min(w), 3), "min": min(w), "max": max(w),
            "cx_std": round(float(np.std(cxs)), 4),
            "cx_range": round(max(cxs) - min(cxs), 3)}


def board(before, after, labels, dest):
    rows, cs = [], (336, 192)
    for group in (before, after):
        cells = []
        for p, d in zip(group[0], group[1]):
            tmp = os.path.join(EVID, "_b_%s.png" % os.path.basename(p).replace(".mp4", ""))
            subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", "%.3f" % (d * 0.45), "-i", p,
                            "-frames:v", "1", "-vf", "scale=%d:%d" % cs, tmp], check=True)
            cells.append(Image.open(tmp).convert("RGB"))
        rows.append(cells)
    pad, top, tagh = 6, 26, 0
    cw, ch = cs
    bw = len(rows[0]) * cw + (len(rows[0]) + 1) * pad
    bh = top + len(rows) * (ch + pad) + pad
    canvas = Image.new("RGB", (bw, bh), (18, 18, 18))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(canvas)
    dr.text((pad, 7), "BEFORE  authored speed, no punch-in", fill=(230, 230, 230))
    for ri, cells in enumerate(rows):
        y = top + ri * (ch + pad)
        if ri == 1:
            dr.text((pad, y - 18), "", fill=(230, 230, 230))
        for ci, im in enumerate(cells):
            canvas.paste(im, (pad + ci * (cw + pad), y))
    dr.text((pad, bh - 18), "AFTER  " + "  ".join(labels), fill=(230, 230, 230))
    canvas.save(dest, quality=90)
    return dest


def main():
    for d in (EVID, OUT):
        os.makedirs(d, exist_ok=True)
    tl = windows()
    bparts, aparts, bdurs, adurs, rows = [], [], [], [], []
    for shot, zoom, speed, flip in PLAN:
        src = os.path.join(CLIPS, "KN_A-%s.mp4" % shot)
        if not os.path.exists(src):
            print("SKIP-NOT-LANDED %s" % shot)
            continue
        start, end, aspeed = tl[shot]
        dur = round(end - start, 3)
        b = os.path.join(OUT, "bef-%s.mp4" % shot)
        a = os.path.join(OUT, "aft-%s.mp4" % shot)
        build(shot, 1.0, aspeed, dur, b)                   # authored look = the problem
        build(shot, zoom, speed, dur, a, flip=flip)        # differentiated
        bparts.append(b)
        aparts.append(a)
        bdurs.append(dur)
        adurs.append(dur)
        rows.append({"shot": shot, "t0": start, "win_s": dur, "authored_speed": aspeed,
                     "punch_in": zoom, "new_speed": speed, "flip": flip})
    if len(bparts) < 2:
        print("NOT-ENOUGH-LANDED")
        return 1
    fb = os.path.join(OUT, "KN-MOTIF-BEFORE-c2174.mp4")
    fa = os.path.join(OUT, "KN-MOTIF-AFTER-c2174.mp4")
    concat(bparts, fb)
    concat(aparts, fa)
    sb = spread(bparts, bdurs)
    sa = spread(aparts, adurs)
    labels = ["%s %.2fx/%.2f%s" % (r["shot"], r["punch_in"], r["new_speed"],
                                   "M" if r["flip"] else "") for r in rows]
    bd = board((bparts, bdurs), (aparts, adurs), labels,
               os.path.join(EVID, "KN-MOTIF-CMP-BOARD-c2174.jpg"))
    rec = {"units": len(rows), "rows": rows,
           "before": {"file": fb, "duration_s": round(dur_of(fb), 3), "spread": sb},
           "after": {"file": fa, "duration_s": round(dur_of(fa), 3), "spread": sa},
           "board": bd,
           "verdict": ("COMPOSITION-BROKEN" if sa.get("cx_range", 0) > sb.get("cx_range", 0) + 0.10
                       else ("SCALE-ONLY-GAIN" if sa.get("std", 0) > sb.get("std", 0) + 0.01
                             else "NO-GAIN"))}
    io.open(os.path.join(EVID, "motif-diff.json"), "w", encoding="utf-8").write(
        json.dumps(rec, ensure_ascii=False, indent=1))
    print("before std=%.4f range=%.3f cx_range=%.3f | after std=%.4f range=%.3f cx_range=%.3f -> %s"
          % (sb.get("std", 0), sb.get("range", 0), sb.get("cx_range", 0), sa.get("std", 0),
             sa.get("range", 0), sa.get("cx_range", 0), rec["verdict"]))
    print("BEFORE %s (%.2fs)  AFTER %s (%.2fs)" % (fb, rec["before"]["duration_s"],
                                                   fa, rec["after"]["duration_s"]))
    print("MOTIF-DIFF-END")
    return 0


if __name__ == "__main__":
    sys.exit(main())
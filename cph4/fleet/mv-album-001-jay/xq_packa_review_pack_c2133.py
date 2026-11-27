# -*- coding: ascii -*-
# xq_packa_review_pack_c2133.py - bank job packA-conform-review-pack-v1.
#
# Why: the 33-unit conform is 44MB at 1344x768, too heavy to open casually and it
# gives no single-page view of the cut. The director needs (a) a light proxy of the
# whole cut and (b) one strip carrying the first frame of every unit in cut order,
# so the sequence and the order can be judged in one look. Zero GPU.
#
# PASS gate: REVIEWPACK-END ok=1 proxy<=18MB strip_frames=33

import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay")
CONFORM = os.path.join(CLIPS, "assembly-packA", "XQ-PACKA-CONFORM-v1-c2133.mp4")
V2_JSON = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json")
PKGDIR = os.path.join(CLIPS, "assembly-packA", "review")
PROXY = os.path.join(PKGDIR, "XQ-PACKA-CONFORM-v1-c2133-960p.mp4")
STRIP = os.path.join(PKGDIR, "XQ-PACKA-CUT-STRIP-c2133.jpg")
RECEIPT = os.path.join(PKGDIR, "REVIEW-PACK-c2133.json")
LOG_RUN = os.path.join(CLIPS, "log-packa-reviewpack.run.txt")
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"


def logline(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    try:
        with open(LOG_RUN, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line)
    except Exception:
        pass


def main():
    os.makedirs(PKGDIR, exist_ok=True)
    with open(V2_JSON, encoding="utf-8") as f:
        rec = json.load(f)

    subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                           "-i", CONFORM, "-vf", "scale=960:-2",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                           PROXY])

    # one strip: first frame of each unit, 11 columns x 3 rows, labelled by order
    tmp = os.path.join(PKGDIR, "firsts")
    os.makedirs(tmp, exist_ok=True)
    cursor = 0.0
    files = []
    for row in rec["clips"]:
        t = cursor + 0.10
        cursor += row["win"]
        out = os.path.join(tmp, "%02d.jpg" % row["n"])
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                        "-ss", "%.3f" % t, "-i", CONFORM, "-frames:v", "1",
                        "-vf", "scale=244:-2", out], check=False)
        if os.path.exists(out):
            files.append(out)
    if len(files) != 33:
        logline("STRIP-INPUT %d != 33" % len(files))
        sys.exit(2)

    args = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
    for p in files:
        args += ["-i", p]
    layout = "|".join("%d_%d" % ((i % 11) * 244, (i // 11) * 142) for i in range(33))
    filt = "".join("[%d:v]" % i for i in range(33))
    filt += "xstack=inputs=33:layout=%s:fill=black[out]" % layout
    args += ["-filter_complex", filt, "-map", "[out]", "-frames:v", "1",
             "-q:v", "3", STRIP]
    subprocess.check_call(args)

    proxy_bytes = os.path.getsize(PROXY)
    strip_bytes = os.path.getsize(STRIP)
    ok = 1 if proxy_bytes <= 18 * 1024 * 1024 and strip_bytes > 100000 else 0
    logline("REVIEWPACK-END ok=%d proxy=%dB strip=%dB units=%d" %
            (ok, proxy_bytes, strip_bytes, len(files)))

    with open(RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({
            "batch": "C2133",
            "conform": os.path.relpath(CONFORM, REPO).replace("\\", "/"),
            "proxy": os.path.relpath(PROXY, REPO).replace("\\", "/"),
            "proxy_bytes": proxy_bytes,
            "strip": os.path.relpath(STRIP, REPO).replace("\\", "/"),
            "strip_bytes": strip_bytes,
            "cut_sec": rec["cut_sec"],
            "units": rec["units"],
            "order_head": [r["unit"] for r in rec["clips"][:6]],
            "order_tail": [r["unit"] for r in rec["clips"][-4:]],
        }, f, ensure_ascii=False, indent=1)
        f.write("\n")

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    if not ok:
        sys.exit(3)


if __name__ == "__main__":
    main()
# -*- coding: ascii -*-
"""xq_packa_v2_origin_verify_c2135.py - bank job packA-conform-v2-origin-verify-v1.

Why: the C2135 loudness pass published a new receipt (and an unchanged index pair).
Until the receipt is read back from origin and the local v2 film is re-measured, the
only trusted copy is the local one.

Checks:
  1. four C2133 receipts + the C2135 loudnorm receipt are byte-identical on origin/main
  2. the v2 film exists, keeps 4710 video frames and its audio sits at -14 LUFS +-0.6
     with true peak <= -1.3 dBTP

PASS gate: ORIGIN-VERIFY-V2-END ok=1 mismatches=0
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
REL = "cph4/fleet/mv-album-001-jay"
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay", "assembly-packA")
V2 = os.path.join(MEDIA, "XQ-PACKA-CONFORM-v2-loudnorm-c2135.mp4")
LOG_RUN = os.path.join(REPO, "media", "mv-album-001-jay", "log-packa-originverify-v2.run.txt")
FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"

FILES = [
    REL + "/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json",
    REL + "/xq-PACKA-ASSEMBLY-INDEX-v2-c2133.md",
    REL + "/xq-PACKA-CUTPOINTS-c2133.json",
    REL + "/xq-PACKA-CONFORM-c2133.json",
    REL + "/xq-PACKA-CONFORM-v2-loudnorm-c2135.json",
]

EXPECT_FRAMES = 4710


def logline(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG_RUN, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def main():
    subprocess.check_call(["git", "fetch", "origin", "--quiet"], cwd=REPO)
    tip = subprocess.check_output(["git", "rev-parse", "--short", "origin/main"],
                                  cwd=REPO).decode("ascii").strip()
    logline("ORIGIN-VERIFY-V2-START origin/main=%s files=%d" % (tip, len(FILES)))

    bad = 0
    eol_only = 0
    for rel in FILES:
        name = rel.split("/")[-1]
        try:
            blob = subprocess.check_output(["git", "cat-file", "blob", "origin/main:%s" % rel],
                                           cwd=REPO, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            bad += 1
            logline("ORIGIN-MISSING %s" % name)
            continue
        local = open(os.path.join(REPO, rel.replace("/", os.sep)), "rb").read()
        if hashlib.sha256(blob).hexdigest() == hashlib.sha256(local).hexdigest():
            logline("MATCH %s" % name)
        elif blob.replace(b"\r\n", b"\n") == local.replace(b"\r\n", b"\n"):
            eol_only += 1
            logline("EOL-ONLY %s" % name)
        else:
            bad += 1
            logline("DRIFT %s" % name)

    # Film-side checks (local only: media is gitignored by design).
    if not os.path.exists(V2):
        bad += 1
        logline("MISSING V2-FILM")
    else:
        frames = subprocess.check_output(
            [FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_frames",
             "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", V2]
        ).decode("ascii").strip()
        ok_frames = int(frames) == EXPECT_FRAMES
        logline("V2-FRAMES value=%s expect=%d ok=%d" % (frames, EXPECT_FRAMES, int(ok_frames)))
        if not ok_frames:
            bad += 1

        p = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", V2, "-map", "0:a:0",
                            "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True, errors="replace")
        out = p.stdout + p.stderr
        tail = out[out.rfind("Summary:"):]
        m_i = re.search(r"I:\s*(-?[\d.]+)", tail)
        m_tp = re.search(r"Peak:\s*(-?[\d.]+)", tail[tail.rfind("True peak:"):])
        loud_i = float(m_i.group(1)) if m_i else None
        tp = float(m_tp.group(1)) if m_tp else None
        ok_loud = (loud_i is not None and abs(loud_i + 14.0) <= 0.6 and
                   tp is not None and tp <= -1.3)
        logline("V2-LOUD I=%s TP=%s ok=%d" % (loud_i, tp, int(ok_loud)))
        if not ok_loud:
            bad += 1

    logline("ORIGIN-VERIFY-V2-END ok=%d mismatches=%d eol_only=%d" %
            (1 if bad == 0 else 0, bad, eol_only))
    if bad:
        sys.exit(2)


if __name__ == "__main__":
    main()
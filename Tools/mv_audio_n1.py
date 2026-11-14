# -*- coding: utf-8 -*-
"""mv_audio_n1.py - delivery audio fix (N1) with a self-verifying true-peak gate.

Why this exists
---------------
The master mux normalises with a SINGLE-PASS `loudnorm=I=-14:TP=-1.5`. Single-pass
loudnorm runs in streaming/dynamic mode and cannot hold the true-peak target: mv0001
v729 measured -13.2 LUFS / **+2.3 dBTP** on all three delivery files (60fps, 4k, wm)
even though the review document claimed "-14/-1.5". A file above 0 dBTP clips on
playback and on platform transcode, so the claim has to be measured, not asserted.

What it does
------------
1. Pass 1 measures the source (input_i / input_tp / input_lra / input_thresh).
2. Pass 2 re-encodes audio with two-pass loudnorm (linear) plus an `alimiter` ceiling,
   video stream copied untouched.
3. The OUTPUT is measured again. If true peak is above -1.0 dBTP or integrated
   loudness drifts outside -14 +/- 0.7 LU, one more trim pass is applied (max 3).
4. Exit code is 0 only when the output is compliant.

Usage:
  py Tools/mv_audio_n1.py <in.mp4> <out.mp4> [--i -14] [--tp -1.5]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

TARGET_I = -14.0
TARGET_TP = -1.5
TP_HARD_GATE = -1.0     # PUBLISH-CHECKLIST: nothing above this may leave the factory
I_TOL = 0.7
ATTEMPTS = 3


def ffmpeg():
    for cand in (shutil.which("ffmpeg"), r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"):
        if cand and (cand == "ffmpeg" or os.path.exists(cand)):
            return cand
    return "ffmpeg"


def measure(ff, path, target_i, target_tp):
    p = subprocess.run(
        [ff, "-hide_banner", "-nostats", "-i", path,
         "-af", "loudnorm=I=%g:TP=%g:LRA=11:print_format=json" % (target_i, target_tp),
         "-f", "null", "-"],
        capture_output=True, text=True, errors="replace")
    txt = p.stderr or ""
    a, b = txt.rfind("{"), txt.rfind("}")
    if a < 0 or b < 0:
        raise RuntimeError("loudnorm measurement failed: %s" % txt[-400:])
    return json.loads(txt[a:b + 1])


def encode(ff, src, dst, af, bitrate="320k"):
    cmd = [ff, "-v", "error", "-y", "-i", src,
           "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
           "-af", af, "-c:a", "aac", "-b:a", bitrate, "-ar", "44100", "-ac", "2",
           "-movflags", "+faststart", dst]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise RuntimeError("audio encode failed: %s" % (r.stderr or "")[-600:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--i", type=float, default=TARGET_I)
    ap.add_argument("--tp", type=float, default=TARGET_TP)
    ap.add_argument("--bitrate", default="320k")
    a = ap.parse_args()

    ff = ffmpeg()
    m = measure(ff, a.src, a.i, a.tp)
    print("src   I=%s LUFS  TP=%s dBTP  LRA=%s" % (m["input_i"], m["input_tp"], m["input_lra"]))

    mid = m
    # The algorithm needs two independent knobs. Ceiling holds the true peak; gain
    # recovers the loudness that limiting costs. Tying them together (first version)
    # overshot: a -2.0 dB sample ceiling measured -0.54 dBTP because aac plus
    # true-peak-vs-sample-peak adds ~1.45 dB, and every correction moved loudness out
    # of tolerance at the same time.
    ceiling_db = a.tp - 1.5          # first guess at the sample-domain ceiling
    gain_db = 0.0
    for attempt in range(1, ATTEMPTS + 1):
        af = ("loudnorm=I=%g:TP=%g:LRA=11:linear=true:"
              "measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s,"
              "volume=%.2fdB,alimiter=limit=%.6f:level=0:attack=5:release=50"
              % (a.i, a.tp, mid["input_i"], mid["input_tp"], mid["input_lra"],
                 mid["input_thresh"], mid.get("target_offset", "0"),
                 gain_db, 10.0 ** (ceiling_db / 20.0)))
        tmp = os.path.join(tempfile.gettempdir(), "mvn1_attempt%d.mp4" % attempt)
        encode(ff, a.src, tmp, af, a.bitrate)
        out = measure(ff, tmp, a.i, a.tp)
        li, ltp = float(out["input_i"]), float(out["input_tp"])
        print("pass%d I=%.2f LUFS  TP=%.2f dBTP  (ceiling=%.2f gain=%+.2f)"
              % (attempt, li, ltp, ceiling_db, gain_db))
        if ltp <= TP_HARD_GATE and abs(li - a.i) <= I_TOL:
            shutil.move(tmp, a.dst)
            print("N1 PASS  %s  I=%.2f  TP=%.2f" % (a.dst, li, ltp))
            return 0
        if ltp > a.tp:
            ceiling_db -= (ltp - a.tp) + 0.15     # observed overshoot, learned live
        if li < a.i - 0.4:
            gain_db += (a.i - li)
        elif li > a.i + 0.4:
            gain_db -= (li - a.i)
        mid = out
        try:
            os.remove(tmp)
        except OSError:
            pass

    print("N1 FAIL  could not reach TP<=%.1f dBTP in %d passes" % (TP_HARD_GATE, ATTEMPTS))
    return 1


if __name__ == "__main__":
    sys.exit(main())

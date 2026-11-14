# -*- coding: utf-8 -*-
"""mv_mux_v730.py - mux-only pass for the V730 24fps master (subs + tail credit).

Why: v730's full rebuild re-renders 73 segments before it muxes, which is the wrong
tool when only the mux needs redoing (the tail credit was silently missing from every
v730 build). This script runs the *same* final mux against the existing
silent_v723.mp4, then asserts the frame count and that the credit line is actually
on screen in the tail (pixel probe, not a promise).

Full path stays mv_rebuild_v730.py; keep both filter graphs in step.
"""
import argparse
import importlib.util
import os
import subprocess
import sys

WORK = r"D:\FleetWorker\rebuild_grade8_v722e"
BASE = r"D:\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SILENT = os.path.join(WORK, "silent_v723.mp4")
SUBS = os.path.join(BASE, "lyric_track.ass")
CREDIT_PNG = os.path.join(BASE, "tail_credit_v510.png")
CREDIT_FROM_S = 231.0
FPS = 24
TARGET_FRAMES = 5623
CRF = "10"


def song_path():
    spec = importlib.util.spec_from_file_location(
        "v5", os.path.join(BASE, "build_full_mv_v5.py"))
    v5 = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    try:
        spec.loader.exec_module(v5)
    except SystemExit:
        pass
    for attr in ("SONG_WAV", "SONG"):
        p = getattr(v5, attr, None)
        if p:
            return p
    raise SystemExit("song path not found in build_full_mv_v5")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(WORK, "full_mv_v730_768_new.mp4"))
    ap.add_argument("--no-subs", action="store_true")
    ap.add_argument("--tail-card", default="",
                    help="full-frame end card PNG (carries its own credit line); "
                         "replaces the tail shot from CREDIT_FROM_S")
    a = ap.parse_args()

    CARD_PNG = a.tail_card or CREDIT_PNG
    for p in (SILENT, CARD_PNG):
        if not os.path.isfile(p):
            sys.exit("missing input: %s" % p)
    song = song_path()
    ass_esc = SUBS.replace("\\", "/").replace(":", "\\:")
    if a.no_subs:
        fc = ("[0:v][2:v]overlay=x=0:y=0:enable='gte(t,%.1f)',"
              "tpad=stop_mode=clone:stop_duration=0.21[v]" % CREDIT_FROM_S)
    else:
        fc = ("[0:v]ass='%s'[b];[b][2:v]overlay=x=0:y=0:enable='gte(t,%.1f)',"
              "tpad=stop_mode=clone:stop_duration=0.21[v]" % (ass_esc, CREDIT_FROM_S))

    print("mux: silent=%s\n     song=%s\n     card=%s from %.1fs%s"
          % (SILENT, song, CARD_PNG, CREDIT_FROM_S,
             " (full-frame tail card)" if a.tail_card else ""), flush=True)
    r = run(["ffmpeg", "-v", "error", "-y",
             "-i", SILENT, "-i", song,
             "-loop", "1", "-framerate", str(FPS),
             "-t", "%.3f" % (TARGET_FRAMES / float(FPS) + 0.5), "-i", CARD_PNG,
             "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
             "-c:v", "libx264", "-preset", "fast", "-crf", CRF, "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "copy", "-frames:v", str(TARGET_FRAMES),
             "-movflags", "+faststart", a.out])
    if r.returncode != 0:
        sys.exit("mux failed: " + (r.stderr or "")[:600])

    probe = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                 "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", a.out])
    n = int(probe.stdout.strip() or 0)
    print("frames=%d (target %d)" % (n, TARGET_FRAMES), flush=True)
    if n != TARGET_FRAMES:
        sys.exit("FRAME ASSERTION FAILED")

    # the credit must actually be on screen: bright text in the y=678 band of the tail.
    # NOTE: metadata=print logs at info level, so this probe must NOT pass -v error -
    # doing that returned YMAX=None and failed a file that was in fact correct.
    chk = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", "232.6", "-i", a.out,
               "-frames:v", "1",
               "-vf", "crop=950:40:200:664,signalstats,metadata=print:key=lavfi.signalstats.YMAX",
               "-f", "null", "-"])
    ymax = None
    for line in (chk.stderr or "").splitlines():
        if "YMAX=" in line:
            try:
                ymax = float(line.split("YMAX=")[1])
            except ValueError:
                pass
    print("credit band YMAX=%s" % ymax, flush=True)
    if ymax is None or ymax < 120:
        sys.exit("CREDIT MISSING on screen (band YMAX=%s)" % ymax)
    print("DONE %s" % a.out)


if __name__ == "__main__":
    main()

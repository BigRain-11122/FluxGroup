# -*- coding: utf-8 -*-
"""mv_take_qc_v727.py - product-nature assertions for the two v727 cloud takes.

One of the four new gates from the 2026-11-09 review-rule post-mortem
(mv-v723-ceo-review-20261109.md §三): existence is not correctness, so a
burned take must prove its own nature before it may enter the assembly:
  A1 container   - decodable, >= MIN_FRAMES frames, >= MIN_BYTES bytes
  A2 identity     - frame-0 dHash vs the source KF dHash <= MAX_HAMMING
                    (first_frame mode must reproduce the KF, else the take
                    baked in a face we never reviewed)
  A3 sample frames- writes first/mid/last frames as jpgs for the director
                    seat's frame-level review (敌对盲审 input)
Usage:
  py Tools/mv_take_qc_v727.py <take.mp4> <kf.png> --tag D03b --json out.json
Exit 0 = PASS, 1 = violation.
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

MIN_FRAMES = 72          # 3.0s @ 24fps - below this the window math is starved
MIN_BYTES = 400_000
MAX_HAMMING = 8          # 64-bit dHash: 8 = strong family, >12 = different picture
FF = "ffmpeg"


def grab_gray(path, ss=None):
    if ss is None:
        cap = cv2.VideoCapture(path)
    else:
        cap = cv2.VideoCapture(path)
        cap.set(cv2.CAP_PROP_POS_MSEC, ss * 1000.0)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("frame grab failed: " + path)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def dhash_bits(gray):
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = small[:, 1:] > small[:, :-1]
    return bits.flatten()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("kf")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()

    rep = {"take": a.take, "tag": a.tag, "fails": []}

    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-count_frames", "-show_entries",
                            "stream=nb_read_frames,width,height,r_frame_rate",
                            "-of", "default=nw=1:nk=1", a.take],
                           capture_output=True, text=True)
    try:
        frames, w, h, fps = probe.stdout.strip().split("\n")
        frames = int(frames)
    except Exception:
        rep["fails"].append("probe_failed:" + probe.stdout.strip()[:80])
        frames = 0
    rep["frames"] = frames
    rep["size_bytes"] = os.path.getsize(a.take)
    rep["dims"] = probe.stdout.strip().replace("\n", " ")
    if frames < MIN_FRAMES:
        rep["fails"].append("frames=%d<%d" % (frames, MIN_FRAMES))
    if rep["size_bytes"] < MIN_BYTES:
        rep["fails"].append("size=%d<%d" % (rep["size_bytes"], MIN_BYTES))

    dh_take = dhash_bits(grab_gray(a.take, ss=0.0))
    dh_kf = dhash_bits(grab_gray(a.kf))
    rep["id_hamming"] = int(np.count_nonzero(dh_take != dh_kf))
    if rep["id_hamming"] > MAX_HAMMING:
        rep["fails"].append("identity dHash=%d>%d (frame0 drifted from KF)"
                            % (rep["id_hamming"], MAX_HAMMING))

    outdir = os.path.dirname(os.path.abspath(a.take))
    tag = a.tag
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", a.take],
                         capture_output=True, text=True).stdout.strip()
    rep["duration"] = dur
    try:
        mid = float(dur) / 2.0
    except Exception:
        mid = 1.5
    for name, ss in (("first", 0.0), ("mid", mid), ("last", max(0.0, float(dur) - 0.4))):
        dst = os.path.join(outdir, "%s_take_%s.jpg" % (tag, name))
        subprocess.run([FF, "-y", "-v", "error", "-ss", "%.3f" % ss, "-i", a.take,
                        "-frames:v", "1", "-q:v", "3", dst], capture_output=True)
        rep["sample_" + name] = dst if os.path.exists(dst) else None

    rep["verdict"] = "PASS" if not rep["fails"] else "FAIL"
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in ("tag", "frames", "duration", "size_bytes",
                                          "id_hamming", "verdict", "fails")},
                     ensure_ascii=False))
    sys.exit(0 if not rep["fails"] else 1)


if __name__ == "__main__":
    main()

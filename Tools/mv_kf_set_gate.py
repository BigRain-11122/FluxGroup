# -*- coding: utf-8 -*-
"""mv_kf_set_gate.py - judge a SET of keyframes the way a viewer sees them.

Per-image similarity against one anchor is the wrong test: an anchor match says
"looks like the reference", while the defect the CEO sees is "these shots are not the
same person as each other" and its twin "these shots are the same picture again".

Two measurements, both inside the set:
  * identity  - mutual SFace cosine between every pair (median must clear --min-sim)
  * staging   - background-only MAD between every pair, subject box excluded
                (every pair must clear --min-bg, otherwise two shots are the same setup)

Usage:
  py Tools/mv_kf_set_gate.py --kf C01:a.png --kf D01:b.png [--min-sim 0.55] [--min-bg 12]
"""
import argparse
import itertools
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
MODEL_SFACE = os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx")


def face_vec(path, rec):
    img = cv2.imread(path)
    if img is None:
        return None
    det = cv2.FaceDetectorYN.create(MODEL, "", (img.shape[1], img.shape[0]), 0.6, 0.3, 5000)
    _, faces = det.detect(img)
    if faces is None or not len(faces):
        return None
    f = max(faces, key=lambda r: r[2] * r[3])
    v = rec.feature(rec.alignCrop(img, f.reshape(1, -1))).flatten().astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def bg_gray(path, size=(336, 192)):
    img = cv2.imread(path)
    if img is None:
        return None
    return cv2.cvtColor(cv2.resize(img, size), cv2.COLOR_BGR2GRAY).astype(np.float32)


def bg_diff(a, b):
    h, w = a.shape
    m = np.ones_like(a, dtype=bool)
    m[int(h * 0.18):int(h * 0.95), int(w * 0.22):int(w * 0.78)] = False
    return float(np.mean(np.abs(a - b)[m]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kf", action="append", required=True, help="LABEL:path")
    ap.add_argument("--min-sim", type=float, default=0.55)
    ap.add_argument("--min-bg", type=float, default=12.0)
    a = ap.parse_args()

    rec = cv2.FaceRecognizerSF.create(MODEL_SFACE, "")
    labels, vecs, grays, missing = [], {}, {}, []
    for spec in a.kf:
        lab, path = spec.split(":", 1)
        v = face_vec(path, rec)
        g = bg_gray(path)
        if v is None or g is None:
            missing.append(lab)
            continue
        labels.append(lab)
        vecs[lab] = v
        grays[lab] = g

    if missing:
        print("NO FACE / unreadable: %s" % ", ".join(missing))
    if len(labels) < 2:
        sys.exit("need at least two usable keyframes")

    print("\nidentity (SFace cosine)  /  staging (background-only MAD)")
    print("%-8s %s" % ("", " ".join("%12s" % l for l in labels)))
    sims, diffs = [], []
    fails = []
    for x in labels:
        row = []
        for y in labels:
            s = float(np.dot(vecs[x], vecs[y]))
            d = bg_diff(grays[x], grays[y])
            row.append("%5.2f/%5.1f" % (s, d))
            if x != y and labels.index(y) > labels.index(x):
                sims.append(s)
                diffs.append(d)
        print("%-8s %s" % (x, " ".join(row)))

    med_sim, min_sim = float(np.median(sims)), float(np.min(sims))
    min_bg = float(np.min(diffs))
    print("\npairs=%d  identity median=%.3f min=%.3f  staging min_bg=%.1f"
          % (len(sims), med_sim, min_sim, min_bg))

    if med_sim < a.min_sim:
        fails.append("identity median %.3f < %.2f" % (med_sim, a.min_sim))
    if min_bg < a.min_bg:
        fails.append("some pair shares a setup: bg %.1f < %.1f" % (min_bg, a.min_bg))

    print("SET-VERDICT:", "PASS" if not fails else "FAIL")
    for f in fails:
        print("  FAIL", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())

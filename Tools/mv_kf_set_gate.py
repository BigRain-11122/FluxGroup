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
  py Tools/mv_kf_set_gate.py --kf C01:a.png --kf D01:b.png [--min-sim 0.47] [--pass-sim 0.55] [--min-bg 15]

Two identity tiers (D-20261117-01): --min-sim 0.47 is the instrument floor (official
SFace same-person threshold is 0.363), --pass-sim 0.55 is the delivery line. A median
between them is MARGINAL: readable but not PASS, and blocked from the i2v entry.
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


def face_vec(path, rec, min_px=90, max_yaw=0.40):
    """Return (vector, note). Profiles are reported, not scored.

    A film needs profile and back-of-head shots; SFace cannot align those and returns
    near-zero similarity even for the same actor (measured 0.019 on a legitimate
    over-the-shoulder frame). Scoring them would fail good shots, so a face that is
    small or strongly turned is marked 'profile' and excluded from the identity median -
    it still has to pass the staging test, and a human looks at it.
    """
    img = cv2.imread(path)
    if img is None:
        return None, "unreadable"
    det = cv2.FaceDetectorYN.create(MODEL, "", (img.shape[1], img.shape[0]), 0.6, 0.3, 5000)
    _, faces = det.detect(img)
    if faces is None or not len(faces):
        return None, "no_face"
    f = max(faces, key=lambda r: r[2] * r[3])
    if min(f[2], f[3]) < min_px:
        return None, "too_small"
    # YuNet row: x, y, w, h, re_x, re_y, le_x, le_y, nose_x, nose_y, rm_x, rm_y, lm_x, lm_y, score
    re, le, nose = np.array(f[4:6]), np.array(f[6:8]), np.array(f[8:10])
    eye_mid = (re + le) / 2.0
    eye_dist = float(np.linalg.norm(le - re)) or 1.0
    yaw = abs(float(nose[0] - eye_mid[0]) / eye_dist)
    if yaw > max_yaw:
        return None, "profile(yaw=%.2f)" % yaw
    v = rec.feature(rec.alignCrop(img, f.reshape(1, -1))).flatten().astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9), "ok"


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
    # D-20261117-01: 0.47 = 仪器档（官方同人阈 0.363；本管线自证中位 0.52 的 90%），
    # 0.55 = 交付档（CEO 观感线，保留不变）。两档之间=噪声带，不得算 PASS、不得进 i2v。
    ap.add_argument("--min-sim", type=float, default=0.47)
    ap.add_argument("--pass-sim", type=float, default=0.55)
    ap.add_argument("--min-bg", type=float, default=15.0)
    a = ap.parse_args()

    rec = cv2.FaceRecognizerSF.create(MODEL_SFACE, "")
    labels, vecs, grays, skipped = [], {}, {}, {}
    for spec in a.kf:
        lab, path = spec.split(":", 1)
        v, note = face_vec(path, rec)
        g = bg_gray(path)
        if g is None:
            skipped[lab] = "unreadable"
            continue
        grays[lab] = g
        if v is None:
            skipped[lab] = note
            continue
        labels.append(lab)
        vecs[lab] = v

    if skipped:
        for k, why in skipped.items():
            print("identity not scored: %-6s %s (staging still checked)" % (k, why))
    if len(grays) < 2:
        sys.exit("need at least two readable keyframes")

    all_l = list(grays)
    print("\nstaging matrix = background-only MAD (all readable frames)")
    print("%-8s %s" % ("", " ".join("%7s" % l for l in all_l)))
    diffs = []
    fails = []
    for i, x in enumerate(all_l):
        row = []
        for y in all_l:
            d = bg_diff(grays[x], grays[y])
            row.append("%7.1f" % d)
            if all_l.index(y) > i:
                diffs.append(d)
        print("%-8s %s" % (x, " ".join(row)))

    sims = []
    if len(labels) >= 2:
        print("\nidentity matrix = SFace cosine (frontable faces only)")
        print("%-8s %s" % ("", " ".join("%7s" % l for l in labels)))
        for i, x in enumerate(labels):
            row = []
            for y in labels:
                s = float(np.dot(vecs[x], vecs[y]))
                row.append("%7.2f" % s)
                if labels.index(y) > i:
                    sims.append(s)
            print("%-8s %s" % (x, " ".join(row)))

    med_sim = float(np.median(sims)) if sims else None
    min_bg = float(np.min(diffs))
    print("\nstaging pairs=%d min_bg=%.1f   identity pairs=%d %s"
          % (len(diffs), min_bg, len(sims),
             ("median=%.3f" % med_sim) if med_sim is not None else "(not enough frontal faces)"))

    marginal = False
    if med_sim is not None and med_sim < a.min_sim:
        fails.append("identity median %.3f < %.2f" % (med_sim, a.min_sim))
    elif med_sim is not None and med_sim < a.pass_sim:
        marginal = True
    if min_bg < a.min_bg:
        fails.append("some pair shares a setup: bg %.1f < %.1f" % (min_bg, a.min_bg))

    verdict = "FAIL" if fails else ("MARGINAL" if marginal else "PASS")
    print("SET-VERDICT:", verdict)
    for f in fails:
        print("  FAIL", f)
    if marginal:
        print("  MARGINAL identity median %.3f in [%.2f,%.2f) = noise band: "
              "not PASS, blocked from i2v" % (med_sim, a.min_sim, a.pass_sim))
    # rc 三态：0=PASS 1=FAIL 2=MARGINAL（阻断但不判缺陷）
    return {"PASS": 0, "FAIL": 1, "MARGINAL": 2}[verdict]


if __name__ == "__main__":
    sys.exit(main())

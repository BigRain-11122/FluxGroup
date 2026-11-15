# -*- coding: utf-8 -*-
"""mv_face_consistency.py - objective male-lead identity audit on the finished cut.

Why: the 閫犲瀷涓€鑷存€?seat passed v730 on a visual read plus one video-model opinion, and
the CEO still saw "鏂板姞鐨勭敺涓讳竴鑷存€уお宸?. Eyeballing is not a gate. This measures the
SFace embedding of every face shot and reports the pairwise cosine similarity, so an
outlier shows up as a number instead of an opinion.

Same-person pairs on this model sit around 0.55-0.85; different people land under 0.30.
Anything below --min-sim against the anchor is reported as a defect.

Usage:
  py Tools/mv_face_consistency.py --video <master.mp4> --shot C01:77.7 --shot D01:143.1 ...
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


def detector(w, h):
    return cv2.FaceDetectorYN.create(MODEL, "", (w, h), 0.6, 0.3, 5000)


def recognizer():
    if not hasattr(cv2, "FaceRecognizerSF"):
        raise SystemExit("[BLOCKED] cv2.FaceRecognizerSF missing")
    return cv2.FaceRecognizerSF.create(MODEL_SFACE, "")


def face_embedding(cap, rec, det_size, t, min_px=90):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
    ok, fr = cap.read()
    if not ok:
        return None, "read_fail"
    return image_embedding(fr, rec, det_size, min_px)


def image_embedding(fr, rec, det_size, min_px=90):
    det = detector(det_size[0], det_size[1])
    _, faces = det.detect(fr)
    if faces is None or not len(faces):
        return None, "no_face"
    f = max(faces, key=lambda r: r[2] * r[3])
    if min(f[2], f[3]) < min_px:
        return None, "face_too_small(%dpx)" % int(min(f[2], f[3]))
    v = rec.feature(rec.alignCrop(fr, f.reshape(1, -1))).flatten().astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9), "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="")
    ap.add_argument("--shot", action="append", default=[],
                    help="LABEL:time[,time...] - several times are averaged per shot")
    ap.add_argument("--image", action="append", default=[],
                    help="LABEL:path - a still (KF or reference photo)")
    ap.add_argument("--anchor", default="")
    ap.add_argument("--min-sim", type=float, default=0.36)
    a = ap.parse_args()

    cap = None
    w = h = 0
    if a.video:
        cap = cv2.VideoCapture(a.video)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if a.shot and cap is None:
        sys.exit("--shot needs --video")
    rec = recognizer()

    embs, notes = {}, {}
    for spec in a.image:
        label, path = spec.split(":", 1)
        img = cv2.imread(path)
        if img is None:
            notes.setdefault(label, []).append("unreadable")
            continue
        v, why = image_embedding(img, rec, (img.shape[1], img.shape[0]))
        if v is not None:
            embs[label] = v
        else:
            notes.setdefault(label, []).append(why)
    for spec in (a.shot if cap is not None else []):
        label, times = spec.split(":", 1)
        vs = []
        for ts in times.split(","):
            v, why = face_embedding(cap, rec, (w, h), float(ts))
            if v is not None:
                vs.append(v)
            else:
                notes.setdefault(label, []).append("%ss:%s" % (ts, why))
        if vs:
            m = np.mean(vs, axis=0)
            embs[label] = m / (np.linalg.norm(m) + 1e-9)
    if cap is not None:
        cap.release()

    labels = []
    for spec in (a.image + a.shot):
        lab = spec.split(":", 1)[0]
        if lab in embs and lab not in labels:
            labels.append(lab)
    print("items measured: %d/%d" % (len(labels), len(a.image) + len(a.shot)))
    for k, v in notes.items():
        print("  note %-6s %s" % (k, "; ".join(v)))
    if len(labels) < 2:
        sys.exit("need at least two usable faces")

    anchor = a.anchor if a.anchor in embs else None
    if anchor is None:
        best, best_mean = None, -2.0
        for c in labels:
            sims = [float(np.dot(embs[c], embs[o])) for o in labels if o != c]
            if np.mean(sims) > best_mean:
                best, best_mean = c, float(np.mean(sims))
        anchor = best
    print("anchor=%s (highest mean similarity)" % anchor)

    print("\n%-6s %8s" % ("shot", "sim_to_anchor"))
    fails = []
    for c in labels:
        s = float(np.dot(embs[anchor], embs[c]))
        flag = "" if (c == anchor or s >= a.min_sim) else "  <== OUTLIER"
        print("%-6s %8.3f%s" % (c, s, flag))
        if c != anchor and s < a.min_sim:
            fails.append((c, s))

    print("\nfull pair matrix (cosine):")
    print("       " + " ".join("%6s" % c for c in labels))
    for c in labels:
        row = " ".join("%6.2f" % float(np.dot(embs[c], embs[o])) for o in labels)
        print("%-6s %s" % (c, row))

    pairs = [(c, o, float(np.dot(embs[c], embs[o])))
             for c, o in itertools.combinations(labels, 2)]
    worst = min(pairs, key=lambda p: p[2])
    med = float(np.median([p[2] for p in pairs]))
    print("\npairs=%d  median=%.3f  worst=%.3f (%s vs %s)"
          % (len(pairs), med, worst[2], worst[0], worst[1]))
    print("VERDICT:", "PASS" if not fails else "FAIL", flush=True)
    for c, s in fails:
        print("  OUTLIER %s sim=%.3f < %.2f" % (c, s, a.min_sim))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())



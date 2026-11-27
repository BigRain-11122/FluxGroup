# -*- coding: utf-8 -*-
"""mv_flag_frames.py - cut per-anomaly evidence strips so a human can adjudicate flags.

Why this exists: mv_jitter_scan.py flags frames (SNAP/POP/FREEZE) but emits numbers only.
Numbers cannot settle "is that a real jump or a fast pan"; the director has to SEE the
frames. Without evidence strips the 28 v717 flags stay unaudited forever.

For each flag it writes one horizontal strip of (2*pad+1) consecutive frames centred on the
flagged frame, labelled with shot/time/frame/tags, plus an index.json.

Usage:
  py mv_flag_frames.py <video> --flags jitter.json --out D:\\FleetWorker\\review\\flags_v717 [--pad 4]
"""
import argparse
import json
import os

import cv2
import numpy as np

FRAME_W = 260          # per-frame thumb width in the strip
GAP = 4
LABEL_H = 26


def strip_for(cap, centre, pad, label, fps):
    frames = []
    lo = max(0, centre - pad)
    for f in range(lo, centre + pad + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, img = cap.read()
        if not ok or img is None:
            frames.append(None)
            continue
        h, w = img.shape[:2]
        nh = max(1, int(h * FRAME_W / float(w)))
        frames.append((f, cv2.resize(img, (FRAME_W, nh), interpolation=cv2.INTER_AREA)))
    real = [x for x in frames if x]
    if not real:
        return None
    fh = max(x[1].shape[0] for x in real)
    total_w = len(frames) * FRAME_W + (len(frames) - 1) * GAP
    canvas = np.full((fh + LABEL_H, total_w, 3), 18, dtype=np.uint8)
    for i, item in enumerate(frames):
        x0 = i * (FRAME_W + GAP)
        if item is None:
            continue
        f, img = item
        canvas[LABEL_H:LABEL_H + img.shape[0], x0:x0 + FRAME_W] = img
        mark = ">>" if f == centre else "  "
        txt = "%s f%d t%.2f" % (mark, f, f / fps if fps else 0.0)
        cv2.putText(canvas, txt, (x0 + 3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                    (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(canvas, label, (GAP, LABEL_H - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                (80, 220, 255), 1, cv2.LINE_AA)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--flags", required=True, help="json from mv_jitter_scan.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pad", type=int, default=4)
    a = ap.parse_args()

    with open(a.flags, encoding="utf-8") as f:
        data = json.load(f)
    flags = data.get("flags") or []
    fps = float(data.get("fps") or 24.0)
    os.makedirs(a.out, exist_ok=True)

    cap = cv2.VideoCapture(a.video)
    if not cap.isOpened():
        raise SystemExit("cannot open video: %s" % a.video)

    index = []
    for i, fl in enumerate(flags, 1):
        frame = int(fl.get("frame") or 0)
        tags = "-".join(fl.get("tags") or [])
        shot = fl.get("shot")
        label = "#%02d shot%s %s mad=%.2f" % (i, shot, tags, float(fl.get("mad") or 0))
        canvas = strip_for(cap, frame, a.pad, label, fps)
        if canvas is None:
            continue
        name = "flag%02d_shot%s_f%04d_%s.jpg" % (i, shot, frame, tags)
        path = os.path.join(a.out, name)
        cv2.imwrite(path, canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        index.append({
            "n": i, "shot": shot, "frame": frame,
            "t": fl.get("t"), "tags": fl.get("tags"),
            "mad": fl.get("mad"), "shift": fl.get("shift"), "resp": fl.get("resp"),
            "run": fl.get("run"), "file": name,
        })
    cap.release()

    with open(os.path.join(a.out, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"video": a.video, "pad": a.pad, "count": len(index), "flags": index},
                  f, ensure_ascii=False, indent=1)
    print("FLAG-FRAMES %d strips -> %s" % (len(index), a.out))


if __name__ == "__main__":
    main()
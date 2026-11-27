# -*- coding: utf-8 -*-
"""mv_event_strip.py - contact strip around suspect events, for human classification.

Each event becomes one PNG: 3x3 frames centred on the event, 2 frames apart, with the
frame index and time burned in. Small (336x189 tiles) so many events can be reviewed fast.

Usage:
  py mv_event_strip.py <video> <outdir> <t1> <t2> ...
"""
import os
import sys

import cv2
import numpy as np

TW, TH = 336, 189
STEP = 2   # frames between tiles


def draw(img, text):
    cv2.rectangle(img, (0, 0), (img.shape[1], 18), (0, 0, 0), -1)
    cv2.putText(img, text, (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)


def main():
    video, outdir = sys.argv[1], sys.argv[2]
    times = [float(x) for x in sys.argv[3:]]
    os.makedirs(outdir, exist_ok=True)
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    for t in times:
        c = int(round(t * fps))
        idxs = [c + (k - 4) * STEP for k in range(9)]
        tiles = []
        for idx in idxs:
            idx = max(0, min(total - 1, idx))
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, fr = cap.read()
            if not ok:
                fr = np.zeros((TH, TW, 3), np.uint8)
            fr = cv2.resize(fr, (TW, TH), interpolation=cv2.INTER_AREA)
            draw(fr, "f%d  %.3fs" % (idx, idx / fps))
            if idx == c:
                cv2.rectangle(fr, (1, 1), (TW - 2, TH - 2), (0, 0, 255), 2)
            tiles.append(fr)
        rows = [np.hstack(tiles[i * 3:(i + 1) * 3]) for i in range(3)]
        sheet = np.vstack(rows)
        out = os.path.join(outdir, "ev_%07.3f.jpg" % t)
        cv2.imwrite(out, sheet, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
        print(out)


if __name__ == "__main__":
    main()
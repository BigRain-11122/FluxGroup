# -*- coding: utf-8 -*-
"""mv_relock.py - re-lock locked-off shots' picture to a static background patch.

Streaming version (no full-film buffering). For each frame t inside a window:
  - pick the patch that is static between t-12 and t+12 (highest variance, sim>0.90)
  - match it in frame t, shift the picture back by the offset
  - keep the burned subtitle band from the original frame (text stays put)

Usage:
  py mv_relock.py <in> <out> --windows t0:t1,t0:t1
"""
import argparse
import subprocess
from collections import deque

import cv2
import numpy as np

W, H, FPS = 1344, 768, 24
BAND, FEATHER, MAX_SHIFT, K = 0.84, 24, 60, 12


def sim(a, b):
    a = a.astype(np.float32) - a.mean()
    b = b.astype(np.float32) - b.mean()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na < 1e-6 or nb < 1e-6 else float((a * b).sum() / (na * nb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--windows", required=True)
    a = ap.parse_args()
    wins = [(float(x.split(":")[0]), float(x.split(":")[1])) for x in a.windows.split(",")]

    cap = cv2.VideoCapture(a.src)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    ycut = int(H * BAND)
    cw, ch = W // 6, ycut // 3

    def in_win(idx):
        t = idx / fps
        return any(t0 <= t < t1 for t0, t1 in wins)

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-crf", "17", "-preset", "fast",
         "-profile:v", "high", "-g", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), a.out],
        stdin=subprocess.PIPE)

    buf = deque()   # (idx, frame, gray)
    written = 0

    def process(tidx):
        # find entries
        d = {x[0]: x for x in buf}
        if tidx not in d:
            return None
        fr = d[tidx][1]
        if (tidx - K) not in d or (tidx + K) not in d:
            return fr
        if not in_win(tidx):
            return fr
        A = d[tidx - K][2]
        B = d[tidx + K][2]
        C = d[tidx][2]
        best = None
        for gy in range(3):
            for gx in range(6):
                x0, y0 = gx * cw, gy * ch
                p = A[y0:y0 + ch, x0:x0 + cw]
                q = B[y0:y0 + ch, x0:x0 + cw]
                if p.size == 0 or p.std() < 12:
                    continue
                if sim(p, q) < 0.90:
                    continue
                if best is None or p.std() > best[0]:
                    best = (float(p.std()), x0, y0, p)
        if best is None:
            return fr
        _, x0, y0, tpl = best
        res = cv2.matchTemplate(C[:ycut], tpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        if score < 0.40:
            return fr
        dx = float(np.clip(loc[0] - x0, -MAX_SHIFT, MAX_SHIFT))
        dy = float(np.clip(loc[1] - y0, -MAX_SHIFT, MAX_SHIFT))
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            return fr
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        w = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_REPLICATE)
        w[ycut:] = fr[ycut:]
        for k in range(FEATHER):
            y = ycut - FEATHER + k
            tt = k / float(FEATHER)
            w[y] = (w[y].astype(np.float32) * tt + fr[y].astype(np.float32) * (1 - tt)).astype(np.uint8)
        return w

    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        buf.append((i, fr, cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)))
        target = i - K
        if target >= 0:
            o = process(target)
            if o is not None:
                enc.stdin.write(o.tobytes())
                written += 1
            buf.popleft()
        i += 1
    cap.release()
    # flush tail
    while buf:
        target = buf[0][0]
        o = process(target)
        if o is not None:
            enc.stdin.write(o.tobytes())
            written += 1
        buf.popleft()

    enc.stdin.close()
    enc.wait()
    print("wrote %d / %d -> %s" % (written, i, a.out))


if __name__ == "__main__":
    main()
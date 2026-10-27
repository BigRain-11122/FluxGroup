import os
import subprocess

import numpy as np
from PIL import Image

FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
MP4 = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\assembly-packB\XQ-PACKB-ASSEMBLY-v%d-c%d.mp4"
TMP = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\assembly-packB\qc-r4-c2159"

for t in (176.9, 180.0):
    row = []
    for name, path in (("v4", MP4 % (4, 2158)), ("v5", MP4 % (5, 2159))):
        out = os.path.join(TMP, "_cmp_%s_%.1f.png" % (name, t))
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", "%.3f" % t,
                        "-i", path, "-frames:v", "1", "-y", out], check=True)
        a = np.asarray(Image.open(out).convert("RGB"), dtype=np.float32)
        luma = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
        row.append((name, luma.mean(), luma.std()))
    d = row[1][1] - row[0][1]
    print("t=%.1f v4 mean=%.2f std=%.2f | v5 mean=%.2f std=%.2f | dv=+%.2f IRE-ish"
          % (t, row[0][1], row[0][2], row[1][1], row[1][2], d))
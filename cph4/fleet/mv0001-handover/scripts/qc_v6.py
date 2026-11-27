# -*- coding: utf-8 -*-
"""v6 机械闸：重复帧 / 黑帧-欠曝 / 首末规格。"""
import os
import subprocess
import sys
from collections import Counter

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FF = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
SRC = r"K:\Fluxgroup\FluxGroup\media\mv0001-handover\deliverable\爱在西元前-30s-v6-优化版.mp4"
TMP = r"K:\Fluxgroup\.codely-cli\tmp\v6check"
os.makedirs(TMP, exist_ok=True)

# 1) 逐帧哈希
fm = os.path.join(TMP, "frames.md5")
subprocess.run([FF, "-y", "-v", "error", "-i", SRC, "-f", "framemd5", fm], check=True)
hashes = []
with open(fm, encoding="utf-8", errors="replace") as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 6:
            hashes.append(parts[-1])
cnt = Counter(hashes)
dups = {h: c for h, c in cnt.items() if c > 1}
print("frames=%d unique=%d dup_hash_groups=%d dup_extra_frames=%d"
      % (len(hashes), len(cnt), len(dups), sum(c - 1 for c in dups.values())))

# 2) 亮度统计（黑帧/欠曝）
rc = subprocess.run([FF, "-v", "error", "-i", SRC, "-vf",
                     "signalstats,metadata=print:file=-", "-f", "null", "-"],
                    capture_output=True, text=True, errors="replace")
yavg = []
for line in (rc.stdout or "").splitlines():
    if "YAVG=" in line:
        try:
            yavg.append(float(line.split("YAVG=")[1].split()[0]))
        except Exception:
            pass
if yavg:
    body = yavg[12:-2] if len(yavg) > 20 else yavg
    print("YAVG frames=%d min=%.2f max=%.2f mean=%.2f  (本体段 min=%.2f)"
          % (len(yavg), min(yavg), max(yavg), sum(yavg) / len(yavg), min(body)))
    dark = [i for i, v in enumerate(body) if v < 8]
    print("dark_frames(<8, 去掉首尾各12帧)=%d" % len(dark))
else:
    print("YAVG 读取失败")

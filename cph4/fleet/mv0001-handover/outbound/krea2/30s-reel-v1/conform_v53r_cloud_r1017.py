# -*- coding: utf-8 -*-
"""conform_v53r_cloud_r1017.py — V53R 云道两镜输出合格化+V5REDO 落位（承 V53R-CLOUD-2shot-r1017 §三）

用法: python conform_v53r_cloud_r1017.py <D04_cloud.mp4> <SIL1_cloud.mp4>
合格化: -an 零音轨 · scale/pad 1344x768 · fps 24 · ≥5.17s（不足=tpad 克隆补尾）· h264 CRF18 yuv420p
落位: V5REDO/D04_her_brush_v5.mp4 + V5REDO/SIL1_stele_backlit_v4b_s9021.mp4
"""
import os
import re
import subprocess
import sys

FF = "ffmpeg"
V5REDO = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\i2v\v5redo"
W, H, MIN_DUR = 1344, 768, 5.17


def dur_of(p):
    r = subprocess.run([FF, "-i", p], capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else 0.0


def conform(src, dst):
    d = dur_of(src)
    assert d > 0, "bad source " + src
    base = "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=24" % (W, H, W, H)
    if d < MIN_DUR:
        vf = base + ",tpad=stop_mode=clone:stop_duration=%.3f" % (MIN_DUR - d + 0.05)
    else:
        vf = base
    subprocess.run([FF, "-y", "-i", src, "-an", "-vf", vf,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p", dst], check=True)
    od = dur_of(dst)
    print("conform %s -> %s  %.2fs (min %.2f)" % (os.path.basename(src), os.path.basename(dst), od, MIN_DUR))
    assert od >= MIN_DUR - 0.01, "duration gate fail: " + dst


if __name__ == "__main__":
    d04_src, sil1_src = sys.argv[1], sys.argv[2]
    os.makedirs(V5REDO, exist_ok=True)
    conform(d04_src, os.path.join(V5REDO, "D04_her_brush_v5.mp4"))
    conform(sil1_src, os.path.join(V5REDO, "SIL1_stele_backlit_v4b_s9021.mp4"))
    print("DONE V5REDO x2")

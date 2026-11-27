# -*- coding: utf-8 -*-
"""V5.3 segment-level fixes (CEO O-20261017-1330):
1) SIL4@207 cold-gray seam -> warm push (TONE review: only color-seam in film).
2) R05_gold_threads entry too dark (CUT #38: black-flash feel + subtitle readability) -> slight lift.
In-place re-encode preserving frame count; then delete stale block G5/G6 + pin caches."""
import os, subprocess, sys, shutil

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
D51 = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\kf-demo-20261012\segments\_cut\v51"
FF = r"C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\hub\ffmpeg.exe"
sys.path.insert(0, HERE)
import build_full_mv_v5 as v5

def dur(p):
    return v5.dur_of(p)

FIX = [
    (os.path.join(D51, "v51_SIL4_at_207.mp4"), "colorbalance=rs=.06:bs=-.06,eq=saturation=1.05"),
    (os.path.join(D51, "v51_R05_gold_threads.mp4"), "eq=brightness=0.045:saturation=1.03"),
]
for p, vf in FIX:
    assert os.path.isfile(p), p
    d0 = dur(p)
    tmp = p + ".fix.mp4"
    r = subprocess.run([FF, "-y", "-i", p, "-an", "-vf", vf,
                        "-c:v", "libx264", "-preset", v5.PRE, "-crf", str(v5.CRF),
                        "-pix_fmt", "yuv420p", tmp], capture_output=True)
    assert r.returncode == 0, r.stderr[-300:]
    d1 = dur(tmp)
    assert abs(d0 - d1) < 0.05, "frame drift %.3f -> %.3f on %s" % (d0, d1, p)
    shutil.move(tmp, p)
    print("SEG-FIX %s  %.2fs frames kept  vf=%s" % (os.path.basename(p), d1, vf))

for blk in ("v51_blockG5.mp4", "v51_blockG5_fx.mp4", "v51_blockG6.mp4", "v51_blockG6_fx.mp4"):
    p = os.path.join(D51, blk)
    if os.path.isfile(p):
        os.remove(p); print("DEL " + blk)
print("SEG-FIX-DONE")

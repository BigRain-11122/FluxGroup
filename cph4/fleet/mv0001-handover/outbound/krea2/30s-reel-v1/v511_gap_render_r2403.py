# -*- coding: utf-8 -*-
# v511_gap_render_r2403.py - detached PROXY=1 render launcher for the V511-GAP batch
import os, subprocess, sys

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.chdir(HERE)
os.environ["PROXY"] = "1"
LOG = os.path.join(HERE, "v511_gap_proxy_r2403.log")
with open(LOG, "wb") as lg:
    lg.write(("launch %s PROXY=1\n" % __file__).encode("utf-8", "replace"))
    lg.flush()
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_full_mv_v511.py")],
                       stdout=lg, stderr=subprocess.STDOUT, cwd=HERE)
    lg.write(("exit rc=%d\n" % r.returncode).encode("utf-8", "replace"))

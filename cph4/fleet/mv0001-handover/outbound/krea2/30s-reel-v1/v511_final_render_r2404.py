# -*- coding: utf-8 -*-
# r2404 detached FINAL (1344x768 crf17) render launcher for the V511-GAP batch.
# PROXY is explicitly unset so build_full_mv_v511.py runs the production path.
import os, subprocess, sys

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.chdir(HERE)
os.environ.pop("PROXY", None)
LOG = os.path.join(HERE, "v511_gap_final_r2404.log")
with open(LOG, "wb") as lg:
    lg.write(("launch %s FINAL=1\n" % __file__).encode("utf-8", "replace"))
    lg.flush()
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_full_mv_v511.py")],
                       stdout=lg, stderr=subprocess.STDOUT, cwd=HERE)
    lg.write(("exit rc=%d\n" % r.returncode).encode("utf-8", "replace"))
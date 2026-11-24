# -*- coding: utf-8 -*-
"""Make Tools/mv_master_v722.py from mv_master_v721c.py.

Same frame-exact chunked 60fps pipeline that produced the v721 1080p master
(minterpolate + lanczos + unsharp, CRF 17, 5 workers); only the source, the output
and the work dir change. Kept as a copy so the v721 master stays reproducible.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
s = io.open(os.path.join(HERE, "mv_master_v721c.py"), encoding="utf-8").read()

s = s.replace('"""mv_master_v721c.py - frame-exact 60fps master, corrected chunking.',
              '"""mv_master_v722.py - frame-exact 60fps master for the V7.22e rebuild.')
s = s.replace('SRC = os.path.join(BASE, "full_mv_v721.mp4")',
              'SRC = r"D:\\FleetWorker\\rebuild_grade8_v722e\\full_mv_v722e_768.mp4"')
s = s.replace('OUT = os.path.join(BASE, "full_mv_v721_60fps_1080p.mp4")',
              'OUT = r"D:\\FleetWorker\\rebuild_grade8_v722e\\full_mv_v722e_60fps_1080p.mp4"')
s = s.replace('WORK = r"D:\\FleetWorker\\master721d"', 'WORK = r"D:\\FleetWorker\\master722e"')
assert "v722e_768.mp4" in s and "master722e" in s
io.open(os.path.join(HERE, "mv_master_v722.py"), "w", encoding="utf-8").write(s)
print("wrote Tools/mv_master_v722.py")
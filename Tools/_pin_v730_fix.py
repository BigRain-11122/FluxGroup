# -*- coding: utf-8 -*-
# _pin_v730_fix.py - the first patch dropped the trailing comma; add it back
import io, re

P = r"C:\Users\sjs20\Desktop\FluxGroup\Tools\mv_rebuild_v730.py"
s = io.open(P, encoding="utf-8").read()
s2 = re.sub(r'(r"[^"\n]*v730-clips[^"\n]*\.mp4")(\s*# v730 pin)', r'\1,\2', s)
io.open(P, "w", encoding="utf-8").write(s2)
print("fixed", s2.count("v730 pin"))

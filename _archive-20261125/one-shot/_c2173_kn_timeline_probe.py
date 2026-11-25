# _c2173_kn_timeline_probe.py - print the authored KN shot timeline (song seconds)
# straight out of 可爱女人-shots-v2.py, so the interim cut can be laid on the real
# song clock instead of an invented order.
import glob
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
src = glob.glob(os.path.join(HERE, "*shots-v2.py"))[0]
text = io.open(src, encoding="utf-8").read()
rows = re.findall(r'\("(KN\d+[a-z]?)",\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)', text)
out = [{"shot": r[0], "start": float(r[1]), "end": float(r[2]), "speed": float(r[3])} for r in rows]
print(json.dumps(out, ensure_ascii=False, indent=0))
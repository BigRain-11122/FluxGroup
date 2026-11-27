# -*- coding: utf-8 -*-
# dump_rows_v57_r1018.py — 导出 V5.7 全镜窗表（逐镜专家团 W1-W4 派工底表）
import os, sys
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.chdir(HERE)
sys.path.insert(0, HERE)
os.environ["DRYRUN"] = "1"
import build_full_mv_v57 as m

rows = sorted(m.build_rows_v56(), key=lambda x: x[1])
out = os.path.join(HERE, "v57_rows_dump_r1018.txt")
with open(out, "w", encoding="utf-8") as f:
    f.write("V5.7 rows total=%d\n" % len(rows))
    f.write("format: t0  t1  shot_id  source\n")
    f.write("XFS cut points (anchor, trans, dur): ")
    f.write("; ".join("%.2f/%s/%.2f" % x for x in m.XFS) + "\n\n")
    for r in rows:
        f.write("%8.3f %8.3f  %-30s %s\n" % (r[1], r[2], r[0], r[4]))
print("WROTE " + out)

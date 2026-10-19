# -*- coding: utf-8 -*-
# dump_v510_rows_r1019.py — V5.10 as-built 镜头窗 dump（CEO 三镜定位取证：刻字闪烁/唱歌傻/女主鬼影）
import os, sys
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.chdir(HERE)
sys.path.insert(0, HERE)
import build_full_mv_v510 as b

rows = b.build_rows_v56()
out = os.path.join(HERE, "v510_probe", "v510_rows_dump.txt")
with open(out, "w", encoding="utf-8") as f:
    f.write("sid\tt0\tt1\tdur\tspeed\tsrc\tis_new\n")
    for r in rows:
        sid, t0, t1, v, src_file, is_new = r
        f.write("%s\t%.3f\t%.3f\t%.3f\t%.3f\t%s\t%s\n" % (sid, t0, t1, t1 - t0, v, src_file, is_new))
    f.write("\nXFS (anchor, transition, D):\n")
    for x in b.XFS:
        f.write("  %.2f %s %.2f\n" % x)
print("rows=%d -> %s" % (len(rows), out))

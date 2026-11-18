# -*- coding: utf-8 -*-
"""Make Tools/mv_rebuild_v722.py from v721 with the era/grade split fixed.

Why: v721's era_of keyed off the first letter, so D* (modern reading / brush) and
R06_museum_verse were graded as ancient, and grade_chain("modern") was a no-op
(eq=saturation=1.0). Measured on the v721 master, R-B was +20..+44 at all ten
sample points - no cool segment existed. CEO 2026-10-19 spec: modern blue-grey
desaturated, ancient amber.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(HERE, "mv_rebuild_v721.py")
dst_path = os.path.join(HERE, "mv_rebuild_v722.py")

s = io.open(src_path, encoding="utf-8").read()
s = s.replace("rebuild_grade3_v720", "rebuild_grade4_v722")
s = s.replace("segments_v721.txt", "segments_v722.txt")
s = s.replace("silent_v721.mp4", "silent_v722.mp4")

OLD = '''ANCIENT_PREFIX = ("S", "N", "C", "R", "D", "B", "T_", "KF", "SIL")


def era_of(sid):
    return "ancient" if sid.startswith(ANCIENT_PREFIX) else "modern"


def grade_chain(era):
    if era == "ancient":
        return ("eq=saturation=0.86:contrast=1.04,"
                "colorbalance=rs=-0.02:gs=-0.01:bs=0.035,"
                "noise=alls=6:allf=t+u,")
    return "eq=saturation=1.0:contrast=1.03:brightness=0.01,"'''

NEW = '''# 2026-11-05 V7.22: era split fixed - see DIRECTOR-REVIEW-V721-REVISE-20261105.md.
# v721 keyed the era off the first letter, so D* (modern reading / brush) and
# R06_museum_verse were graded as ancient, and the "modern" chain was a no-op
# (eq=saturation=1.0). The v721 master measured R-B +20..+44 at ten sample points:
# no cool segment existed at all, while the 10-19 order asks modern blue-grey / ancient amber.
MODERN_IDS = {"R06_museum_verse"}
MODERN_PREFIX = ("INT", "S7_", "S8_", "S9_", "S10_", "D", "E03", "E04a", "Z")
ANCIENT_PREFIX = ("S", "N", "C", "R", "B", "T_", "KF", "SIL", "E0", "E1")


def era_of(sid):
    if sid in MODERN_IDS or sid.startswith(MODERN_PREFIX):
        return "modern"
    return "ancient" if sid.startswith(ANCIENT_PREFIX) else "modern"


def grade_chain(era):
    if era == "ancient":
        return ("eq=saturation=0.86:contrast=1.04,"
                "colorbalance=rs=-0.02:gs=-0.01:bs=0.035,"
                "noise=alls=6:allf=t+u,")
    # modern = blue-grey, desaturated (CEO 2026-10-19 spec: modern cool / ancient amber)
    return ("colorbalance=rs=-0.10:gs=-0.02:bs=0.10:rm=-0.06:bm=0.06:rh=-0.07:bh=0.07,"
            "eq=saturation=0.78:contrast=1.03:brightness=0.01,")'''

assert OLD in s, "era block not found - v721 source changed"
s = s.replace(OLD, NEW)

# dry-run prints the era so the split can be eyeballed before a 30-minute build
s = s.replace(
    'print("  %8.3f %8.3f %-24s v=%.2f %s" % (t0, t1, sid, v, src), flush=True)',
    'print("  %8.3f %8.3f %-24s v=%.2f %-7s %s" % (t0, t1, sid, v, era_of(sid), src), flush=True)')

io.open(dst_path, "w", encoding="utf-8").write(s)
print("written %s (%d bytes)" % (dst_path, len(s)))
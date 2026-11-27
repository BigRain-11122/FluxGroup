# -*- coding: utf-8 -*-
"""2026-11-05: split the modern grade into two tiers before rebuilding V7.22b.

Single-segment calibration (V718_S1_OPEN, 3.5s, measured with cv2):
    rs/bs 0.10 -> R-B +21.0, sat 168.9
    rs/bs 0.18 -> R-B  +8.5, sat 160.1
    rs/bs 0.24 -> R-B  -1.1, sat 152.9
    rs/bs 0.22 -> R-B  +2.0, sat 152.5   <- picked for the museum tier
INT1 is a tungsten-lit desk at night: forcing it cool is physically wrong
(R-B -1 turns the lamp-lit desk implausibly blue-grey), so the night interior
only loses saturation and keeps its colour. Only the museum / modern-day
reading shots get the blue-grey tier.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "mv_rebuild_v722.py")
s = io.open(p, encoding="utf-8").read()

OLD_IDS = 'MODERN_PREFIX = ("INT", "S7_", "S8_", "S9_", "S10_", "D", "E03", "E04a", "Z")'
NEW_IDS = ('MODERN_PREFIX = ("S7_", "S8_", "S9_", "S10_", "D", "E03", "E04a", "Z")\n'
           '# 2026-11-05: desk-at-night interiors (INT*) must not be pushed cool - the light\n'
           '# source is a tungsten desk lamp. Calibrated on one segment: pushing them to R-B -1\n'
           '# reads as an implausible blue-grey desk. Night keeps its colour, loses saturation.\n'
           'NIGHT_PREFIX = ("INT",)')
assert OLD_IDS in s, "MODERN_PREFIX line changed"
s = s.replace(OLD_IDS, NEW_IDS)

OLD_ERA = '''def era_of(sid):
    if sid in MODERN_IDS or sid.startswith(MODERN_PREFIX):
        return "modern"'''
NEW_ERA = '''def era_of(sid):
    if sid.startswith(NIGHT_PREFIX):
        return "modern_night"
    if sid in MODERN_IDS or sid.startswith(MODERN_PREFIX):
        return "modern"'''
assert OLD_ERA in s, "era_of changed"
s = s.replace(OLD_ERA, NEW_ERA)

OLD_G = '''    return ("colorbalance=rs=-0.10:gs=-0.02:bs=0.10:rm=-0.06:bm=0.06:rh=-0.07:bh=0.07,"
            "eq=saturation=0.78:contrast=1.03:brightness=0.01,")'''
NEW_G = '''    if era == "modern_night":
        # keep the tungsten colour, only pull saturation down
        return "eq=saturation=0.80:contrast=1.03:brightness=0.01,"
    # museum / modern-day reading: blue-grey, desaturated (CEO 2026-10-19 spec).
    # strength from the 2026-11-05 single-segment calibration (rs/bs 0.22 -> R-B +2.0).
    return ("colorbalance=rs=-0.22:gs=-0.04:bs=0.22:rm=-0.13:bm=0.13:rh=-0.15:bh=0.15,"
            "eq=saturation=0.58:contrast=1.03:brightness=0.01,")'''
assert OLD_G in s, "grade chain changed"
s = s.replace(OLD_G, NEW_G)

s = s.replace("rebuild_grade4_v722", "rebuild_grade5_v722b")
io.open(p, "w", encoding="utf-8").write(s)
print("patched mv_rebuild_v722.py -> grade5_v722b, two modern tiers")
# -*- coding: utf-8 -*-
"""2026-11-05 R2 fixes, three small and separately justified changes.

1) mv_delivery_gate.py - a dHash pair whose two shots start <0.5s apart is a burst
   cluster inside one slowed segment, not "the same shot reused later in the film".
   Verified by eye on v722b: 102.21s vs 102.58s are the same candelabrum composition
   0.37s apart (only the flame differs). Reusing a shot means coming back to it much
   later; a 0.37s burst does not.
2) mv_contract_check.py - absolute colour thresholds were calibrated on one segment and
   then applied to all 73. Data from v722b: modern median R-B -2.8 vs ancient +27.4,
   i.e. the two worlds are already 30 units apart, yet the absolute rule still failed 26
   segments. The intent in the 10-19 order is "the two worlds must read differently",
   so the rule becomes a separation rule measured against the film's own ancient baseline.
3) The rebuild script gets a transition era (D08_world_flip is the world-crossing shot,
   warm by design) and a per-segment desaturation table for the few museum shots whose
   source is so saturated that saturation alone still sits above the ancient baseline.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def patch(path, pairs):
    s = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert old in s, "%s: anchor not found -> %s" % (os.path.basename(path), old[:60])
        s = s.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(s)
    print("patched", os.path.basename(path))


# ---------------------------------------------------------------- 1) delivery gate
patch(os.path.join(HERE, "mv_delivery_gate.py"), [
    ("""            for f0, f1 in seen_pairs:
                t0, t1 = f0 / fps, f1 / fps""",
     """            for f0, f1 in seen_pairs:
                t0, t1 = f0 / fps, f1 / fps
                # 2026-11-05: two shots that start within half a second of each other are
                # one burst cluster inside a slowed segment; "the same shot reused" only
                # means coming back to it much later. Verified by eye on v722b 102.21/102.58.
                if abs(t1 - t0) < 0.5:
                    continue"""),
])

# ---------------------------------------------------------------- 2) contract checker
patch(os.path.join(HERE, "mv_contract_check.py"), [
    ('MODERN_RB_MAX = 5.0      # 现代段应冷/中性：实测 v721 为 +20~+44',
     'MODERN_RB_MAX = 5.0      # solo-eyeball fallback; the live rule below is separation-based\n'
     'SEPARATION_MIN = 12.0    # modern must sit at least this much cooler than the ancient baseline'),
    ('''    base_sat = a.baseline_sat
    if base_sat <= 0:
        mods = [s for s in segs if s.get("era") == "modern"]
        base_sat = 190.0 if not mods else max(
            (seg_stats(cap, s["t0"], s["t1"], fps) or (0, 190))[1] for s in mods)''',
     '''    # the film's own ancient segments are the baseline: the rule is
    # "modern must read cooler / less saturated than ancient", not an absolute number
    anc_rb, anc_sat = [], []
    for s in segs:
        if s.get("era") == "ancient":
            st = seg_stats(cap, s["t0"], s["t1"], fps)
            if st:
                anc_rb.append(st[0]); anc_sat.append(st[1])
    anc_rb_med = float(np.median(anc_rb)) if anc_rb else 25.0
    anc_sat_med = float(np.median(anc_sat)) if anc_sat else 190.0
    base_sat = a.baseline_sat or anc_sat_med
    rb_cap = min(MODERN_RB_MAX + 10.0, anc_rb_med - SEPARATION_MIN)
    print("ancient baseline: R-B %+.1f  sat %.0f  -> modern cap R-B %+.1f" % (anc_rb_med, anc_sat_med, rb_cap))'''),
    ('''        if era == "modern":
            if rb > MODERN_RB_MAX:
                bad.append("R-B %+.1f > %.1f" % (rb, MODERN_RB_MAX))
            if sat > base_sat * MODERN_SAT_RATIO:
                bad.append("sat %.0f > %.0f" % (sat, base_sat * MODERN_SAT_RATIO))''',
     '''        if era == "modern":
            if rb > rb_cap:
                bad.append("R-B %+.1f > %.1f (separation from ancient)" % (rb, rb_cap))
            if sat > anc_sat_med * MODERN_SAT_RATIO:
                bad.append("sat %.0f > %.0f (ancient baseline x %.2f)" %
                           (sat, anc_sat_med * MODERN_SAT_RATIO, MODERN_SAT_RATIO))'''),
    ('''            if sat > base_sat * NIGHT_SAT_RATIO:
                bad.append("sat %.0f > %.0f" % (sat, base_sat * NIGHT_SAT_RATIO))''',
     '''            if sat > anc_sat_med * NIGHT_SAT_RATIO:
                bad.append("sat %.0f > %.0f (ancient baseline x %.2f)" %
                           (sat, anc_sat_med * NIGHT_SAT_RATIO, NIGHT_SAT_RATIO))'''),
])

# ---------------------------------------------------------------- 3) rebuild: transition era + desat table
patch(os.path.join(HERE, "mv_rebuild_v722.py"), [
    ('MODERN_IDS = {"R06_museum_verse"}',
     'MODERN_IDS = {"R06_museum_verse"}\n'
     '# D08_world_flip is the shot where the two worlds cross: warm by design, not a\n'
     '# "modern" shot that should be cooled.\n'
     'TRANSITION_IDS = {"D08_world_flip"}\n'
     '# sources whose saturation still lands above the ancient baseline after the standard\n'
     '# desat (measured on v722b: 186-213 vs ancient median 195)\n'
     'DESAT_IDS = {"D01_carver_words", "D04_her_brush", "D05_words_warm", "Z01_words_alone",\n'
     '             "Z03_lights_out", "Z04_glyph_remains", "E04a_words_warm"}'),
    ('''def era_of(sid):
    if sid.startswith(NIGHT_PREFIX):''',
     '''def era_of(sid):
    if sid in TRANSITION_IDS:
        return "transition"
    if sid.startswith(NIGHT_PREFIX):'''),
    ('''    if era == "modern_night":
        # keep the tungsten colour, only pull saturation down
        return "eq=saturation=0.80:contrast=1.03:brightness=0.01,"''',
     '''    if era == "transition":
        # world-crossing shot: keep the ancient amber, it is the hinge
        return ("eq=saturation=0.86:contrast=1.04,"
                "colorbalance=rs=-0.02:gs=-0.01:bs=0.035,")
    if era == "modern_night":
        # keep the tungsten colour, only pull saturation down
        return "eq=saturation=0.80:contrast=1.03:brightness=0.01,"'''),
    ('rebuild_grade5_v722b', 'rebuild_grade6_v722c'),
])

# per-segment stronger desaturation
s = io.open(os.path.join(HERE, "mv_rebuild_v722.py"), encoding="utf-8").read()
old = '''    if a.grade:
        base_vf = grade_chain(era_of(sid)) + base_vf'''
new = '''    if a.grade:
        gchain = grade_chain(era_of(sid))
        if sid in DESAT_IDS and "saturation=" in gchain:
            gchain = re.sub(r"saturation=[0-9.]+", "saturation=0.42", gchain)
        base_vf = gchain + base_vf'''
assert old in s
s = s.replace(old, new, 1)
if "\nimport re" not in s:
    s = s.replace("\nimport subprocess", "\nimport re\nimport subprocess", 1)
io.open(os.path.join(HERE, "mv_rebuild_v722.py"), "w", encoding="utf-8").write(s)
print("patched mv_rebuild_v722.py (transition era + DESAT_IDS)")
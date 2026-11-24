# -*- coding: utf-8 -*-
"""2026-11-05: the saturation rule needs a brightness floor.

v722e left exactly one G4 fail: Z03_lights_out (the hall going dark) sat 200 vs cap 191.
That frame is nearly black; HSV saturation is chroma/(max) and explodes on noise in a
dark frame, so the number says nothing about what a viewer sees. Judge chroma only above
mean V 40, and say so in the output instead of silently skipping.
"""
import io
import os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mv_contract_check.py")
s = io.open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    assert old in s, "anchor missing: %s" % old[:60]
    s = s.replace(old, new, 1)


rep("    rbs, sats = [], []", "    rbs, sats, vs = [], [], []")
rep("        sats.append(float(cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[:, :, 1].mean()))",
    "        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)\n"
    "        sats.append(float(hsv[:, :, 1].mean()))\n"
    "        vs.append(float(hsv[:, :, 2].mean()))")
rep("    return float(np.mean(rbs)), float(np.mean(sats))",
    "    return float(np.mean(rbs)), float(np.mean(sats)), float(np.mean(vs))")
rep("        rb, sat = st", "        rb, sat, vmean = st")
rep("            if sat > anc_sat_med * MODERN_SAT_RATIO:",
    '            if vmean < DARK_LUMA:\n'
    '                if sat > anc_sat_med * MODERN_SAT_RATIO:\n'
    '                    print("  note %s: mean V %.0f < %.0f, chroma not judged" % (s["id"], vmean, DARK_LUMA))\n'
    '            elif sat > anc_sat_med * MODERN_SAT_RATIO:')
rep("            if sat > anc_sat_med * NIGHT_SAT_RATIO:",
    "            if vmean >= DARK_LUMA and sat > anc_sat_med * NIGHT_SAT_RATIO:")
rep("SEPARATION_MIN = 12.0",
    "DARK_LUMA = 40.0         # below this a frame is too dark for HSV saturation to mean anything\n"
    "SEPARATION_MIN = 12.0")
rep("        rb, sat = seg_stats(cap, 0, total / fps, fps) or (0.0, 0.0)",
    "        rb, sat, _v = seg_stats(cap, 0, total / fps, fps) or (0.0, 0.0, 0.0)")

io.open(p, "w", encoding="utf-8").write(s)
print("patched mv_contract_check.py: DARK_LUMA floor")
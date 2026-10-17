# -*- coding: utf-8 -*-
"""Generate build_full_mv_v53.py from v52 (anchored patches, each must hit exactly once).
V5.3 = CEO O-20261017-1330 逐镜全审 fixes:
  FX_EVENTS 17->26 sites (E1 bare-hard 57->47/71=66.2%<=70% + review-driven:
  E03 warm-kick leak / S17 dust_z04 denser plate / site7 retuned to cover C05|C06 cut)
  AIGC badge fade-in 1.2s->0.5s (badge floor raise; badge PNG strengthened separately).
"""
import io, os, py_compile

HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
SRC = os.path.join(HERE, "build_full_mv_v52.py")
DST = os.path.join(HERE, "build_full_mv_v53.py")
txt = io.open(SRC, encoding="utf-8").read()

OLD_EVENTS = '''    FX_EVENTS = [
        # (plate, st, dur, peak_alpha, drift, (fade_in, fade_out))  drift: sweepL/sweepR/static/drift
        ("fx_band.png",  38.62, 0.52, 0.85, "sweepL", (0.10, 0.16)),
        ("fx_band.png",  40.02, 0.52, 0.85, "sweepR", (0.10, 0.16)),
        ("fx_leak.png",  47.30, 0.95, 0.55, "static", (0.28, 0.35)),
        ("fx_flash.png", 77.30, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_smoke.png", 80.05, 0.90, 0.45, "drift",  (0.28, 0.35)),
        ("fx_flash.png", 91.02, 0.13, 0.75, "static", (0.04, 0.08)),
        ("fx_dust.png",  93.05, 1.35, 0.55, "drift",  (0.45, 0.55)),
        ("fx_dust.png", 102.80, 1.15, 0.50, "drift",  (0.40, 0.50)),
        ("fx_smoke.png",110.42, 1.50, 0.42, "drift",  (0.45, 0.55)),
        ("fx_leak.png", 110.62, 1.45, 0.40, "static", (0.45, 0.50)),
        ("fx_dust.png", 131.62, 1.25, 0.50, "drift",  (0.40, 0.55)),
        ("fx_flash.png",141.72, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_dust.png", 168.30, 2.20, 0.35, "drift",  (0.70, 0.80)),
        ("fx_echo.png", 187.24, 0.58, 0.60, "static", (0.07, 0.38)),
        ("fx_flash.png",212.62, 0.13, 0.78, "static", (0.04, 0.08)),
        ("fx_smoke.png",219.80, 1.25, 0.45, "drift",  (0.35, 0.50)),
        ("fx_dust.png", 231.90, 2.30, 0.40, "drift",  (0.70, 0.90)),
    ]'''

NEW_EVENTS = '''    FX_EVENTS = [
        # (plate, st, dur, peak_alpha, drift, (fade_in, fade_out))  drift: sweepL/sweepR/static/drift
        # V5.3: 26 sites (CEO O-20261017-1330 full-coverage review). New sites: 17.42/28.76/58.20/
        #   68.62/150.34/159.42/176.76/193.04/199.30. Retuned: 92.56 (covers C05|C06 cut), 231.90 z04 plate.
        #   Exceptions (R-doc T-bridge clause family): 187.24 echo -> 193.04 dust -> 199.30 leak =
        #   replay-opening continuous narrative treatment (5.8s/6.3s spacing, thin alphas).
        ("fx_flash.png",  17.42, 0.13, 0.50, "static", (0.04, 0.07)),
        ("fx_dust.png",   28.76, 1.05, 0.35, "drift",  (0.35, 0.45)),
        ("fx_band.png",   38.62, 0.52, 0.85, "sweepL", (0.10, 0.16)),
        ("fx_band.png",   40.02, 0.52, 0.85, "sweepR", (0.10, 0.16)),
        ("fx_leak.png",   47.30, 0.95, 0.55, "static", (0.28, 0.35)),
        ("fx_smoke.png",  58.20, 1.05, 0.32, "drift",  (0.35, 0.45)),
        ("fx_dust.png",   68.62, 1.00, 0.35, "drift",  (0.35, 0.45)),
        ("fx_flash.png",  77.30, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_smoke.png",  80.05, 0.90, 0.45, "drift",  (0.28, 0.35)),
        ("fx_flash.png",  91.02, 0.13, 0.75, "static", (0.04, 0.08)),
        ("fx_dust.png",   92.56, 1.35, 0.55, "drift",  (0.45, 0.55)),
        ("fx_dust.png",  102.80, 1.15, 0.50, "drift",  (0.40, 0.50)),
        ("fx_smoke.png", 110.42, 1.50, 0.42, "drift",  (0.45, 0.55)),
        ("fx_leak.png",  110.62, 1.45, 0.40, "static", (0.45, 0.50)),
        ("fx_dust.png",  131.62, 1.25, 0.50, "drift",  (0.40, 0.55)),
        ("fx_flash.png", 141.72, 0.14, 0.80, "static", (0.04, 0.08)),
        ("fx_leak.png",  150.34, 0.95, 0.38, "static", (0.30, 0.40)),
        ("fx_smoke.png", 159.42, 0.95, 0.28, "drift",  (0.30, 0.40)),
        ("fx_dust.png",  168.30, 2.20, 0.35, "drift",  (0.70, 0.80)),
        ("fx_smoke.png", 176.76, 1.05, 0.30, "drift",  (0.35, 0.45)),
        ("fx_echo.png",  187.24, 0.58, 0.60, "static", (0.07, 0.38)),
        ("fx_dust.png",  193.04, 0.85, 0.30, "drift",  (0.30, 0.35)),
        ("fx_leak.png",  199.30, 1.60, 0.30, "static", (0.50, 0.55)),
        ("fx_flash.png", 212.62, 0.13, 0.78, "static", (0.04, 0.08)),
        ("fx_smoke.png", 219.80, 1.25, 0.45, "drift",  (0.35, 0.50)),
        ("fx_dust_z04.png", 231.90, 2.30, 0.50, "drift", (0.70, 0.90)),
    ]'''

PATCHES = [
    ("build_full_mv_v52.py — V5.2 特效伴切装配器", "build_full_mv_v53.py — V5.3 特效伴切装配器（逐镜全审修版·CEO 令 O-20261017-1330）"),
    (OLD_EVENTS, NEW_EVENTS),
    ("fade=t=in:st=0:d=1.2:alpha=1,fade=t=out:st=2.4:d=0.6:alpha=1[aigc]",
     "fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st=2.4:d=0.6:alpha=1[aigc]"),
    ('out = os.path.join(HERE, "full_mv_v52.mp4")', 'out = os.path.join(HERE, "full_mv_v53.mp4")'),
]
for old, new in PATCHES:
    n = txt.count(old)
    assert n == 1, "anchor count=%d for: %.60s" % (n, old)
    txt = txt.replace(old, new)
io.open(DST, "w", encoding="utf-8", newline="").write(txt)
py_compile.compile(DST, doraise=True)
print("V53-GEN-OK 26 FX sites -> " + DST)

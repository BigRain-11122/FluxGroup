# -*- coding: utf-8 -*-
# Build xq_packb_assembly_v4_c2159.py from the proven v3 script by copy + targeted
# replacements only (no hand transcription: B1276).
#
# v4 = v3 + two director items:
#   R4  : S1-07 is swapped for the de-humanized take (clips-local-768/XQ_B-S1-07-r4.mp4)
#   R6-a: the 172-186s astronomy window gets +1.5 IRE / small contrast lift
import io
import os
import shutil

SRC = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq_packb_assembly_v3_c2158.py"
DST = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq_packb_assembly_v4_c2159.py"

shutil.copyfile(SRC, DST)
t = io.open(DST, encoding="utf-8").read()

reps = [
    ('OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v3-c2158.json")',
     'OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v4-c2159.json")'),
    ('OUT_MD = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v3-c2158.md")',
     'OUT_MD = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v4-c2159.md")'),
    ('OUT_GRAMMAR_JSON = os.path.join(OUTDIR, "xq-PACKB-EDIT-GRAMMAR-c2158.json")',
     'OUT_GRAMMAR_JSON = os.path.join(OUTDIR, "xq-PACKB-EDIT-GRAMMAR-c2159.json")'),
    ('OUT_GRAMMAR_MD = os.path.join(OUTDIR, "xq-PACKB-EDIT-GRAMMAR-c2158.md")',
     'OUT_GRAMMAR_MD = os.path.join(OUTDIR, "xq-PACKB-EDIT-GRAMMAR-c2159.md")'),
    ('OUT_RECEIPT = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-RECEIPT-c2158.json")',
     'OUT_RECEIPT = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-RECEIPT-c2159.json")'),
    ('OUT_MP4 = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v4-c2158.mp4")',
     'OUT_MP4 = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v5-c2159.mp4")'),
    ('OUT_NOMUX = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v4-c2158.video-only.mp4")',
     'OUT_NOMUX = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v5-c2159.video-only.mp4")'),
    ('LOG_RUN = os.path.join(MEDIA, "log-packb-assembly-c2158.run.txt")',
     'LOG_RUN = os.path.join(MEDIA, "log-packb-assembly-c2159.run.txt")'),
    ('BATCH = "C2158"', 'BATCH = "C2159"'),
    ('PREV = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v3-c2157.mp4")',
     'PREV = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v4-c2158.mp4")'),
    ('    "S1-08": "clips-local-768/XQ_B-S1-08.mp4",',
     '    "S1-07": "clips-local-768/XQ_B-S1-07-r4.mp4",\n    "S1-08": "clips-local-768/XQ_B-S1-08.mp4",'),
    ('"XQ-PACKB-v4-JOINS-c2158.jpg"', '"XQ-PACKB-v5-JOINS-c2159.jpg"'),
]

for old, new in reps:
    n = t.count(old)
    if n != 1:
        raise SystemExit("REPL-COUNT %d for %r" % (n, old))
    t = t.replace(old, new)

# R6-a: lift the 172-186s montage window (director asked for +1-2 IRE there)
anchor = ('        # R5: the tail plate window gets crushed blacks, gate flicker and grain\n'
          '        if r["timeline"][1] > TAIL_START + 0.001:')
add = ('        # R6-a: the 172-186s astronomy montage was reading muddy on a phone\n'
       '        if MONTAGE_LIFT[0] <= r["timeline"][0] < MONTAGE_LIFT[1]:\n'
       '            chain += ",eq=brightness=0.045:contrast=1.03:saturation=1.05"\n'
       '        # R5: the tail plate window gets crushed blacks, gate flicker and grain\n'
       '        if r["timeline"][1] > TAIL_START + 0.001:')
if t.count(anchor) != 1:
    raise SystemExit("TAIL-ANCHOR %d" % t.count(anchor))
t = t.replace(anchor, add)

# constant next to TAIL_START
anchor2 = 'TAIL_START = 218.0'
if t.count(anchor2) != 1:
    raise SystemExit("TAIL-CONST %d" % t.count(anchor2))
t = t.replace(anchor2, 'TAIL_START = 218.0\nMONTAGE_LIFT = (172.0, 186.0)')

io.open(DST, "w", encoding="utf-8", newline="\n").write(t)
print("WROTE", DST, len(t))
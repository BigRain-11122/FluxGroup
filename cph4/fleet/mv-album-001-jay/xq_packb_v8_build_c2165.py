# -*- coding: ascii -*-
# Build xq_packb_assembly_v8_c2165.py from the proven v7 script by copy+replace.
import io

SRC = "xq_packb_assembly_v7_c2163.py"
DST = "xq_packb_assembly_v8_c2165.py"

t = io.open(SRC, encoding="ascii").read()

SUBS = [
    ('BATCH = "C2162"', 'BATCH = "C2165"'),
    ('xq-PACKB-ASSEMBLY-INDEX-v7-c2163.json', 'xq-PACKB-ASSEMBLY-INDEX-v8-c2165.json'),
    ('xq-PACKB-ASSEMBLY-INDEX-v7-c2163.md', 'xq-PACKB-ASSEMBLY-INDEX-v8-c2165.md'),
    ('xq-PACKB-EDIT-GRAMMAR-c2163.json', 'xq-PACKB-EDIT-GRAMMAR-c2165.json'),
    ('xq-PACKB-EDIT-GRAMMAR-c2163.md', 'xq-PACKB-EDIT-GRAMMAR-c2165.md'),
    ('xq-PACKB-ASSEMBLY-RECEIPT-c2163.json', 'xq-PACKB-ASSEMBLY-RECEIPT-c2165.json'),
    ('XQ-PACKB-ASSEMBLY-v7-c2163.mp4', 'XQ-PACKB-ASSEMBLY-v8-c2165.mp4'),
    ('XQ-PACKB-ASSEMBLY-v7-c2163.video-only.mp4',
     'XQ-PACKB-ASSEMBLY-v8-c2165.video-only.mp4'),
    ('filter-c2163.txt', 'filter-c2165.txt'),
    ('log-packb-assembly-c2163.run.txt', 'log-packb-assembly-c2165.run.txt'),
    ('XQ-PACKB-v7-JOINS-c2163.jpg', 'XQ-PACKB-v8-JOINS-c2165.jpg'),
    ('XQ-PACKB-ASSEMBLY-v5-c2159.mp4', 'XQ-PACKB-ASSEMBLY-v7-c2163.mp4'),
]

for a, b in SUBS:
    assert t.count(a) == 1, (a, t.count(a))
    t = t.replace(a, b)

# the newest note take replaces the packA clip inside the 226-232s slot
old = '    "S5-31": "clips-local-768/XQ_B-S5-31.mp4",\n'
new = ('    "S5-31": "clips-local-768/XQ_B-S5-31.mp4",\n'
       '    "F5-33c": "clips-local-768/XQ_B-F5-33c-v8.mp4",\n')
assert t.count(old) == 1
t = t.replace(old, new)

# V8-1 grade constants
old = 'TAIL_START = 218.0\n'
new = ('TAIL_START = 218.0\n'
       '# V8-1: the two shots the director flagged for a colour/detail break.\n'
       'GRADE_V8 = ("S2-10", "S2-11")\n'
       'GRADE_CHAIN = (",colorbalance=rm=-0.10:gm=-0.03:bm=0.10:rh=-0.16:gh=-0.05:bh=0.16"\n'
       '               ":rs=-0.02:bs=0.04,eq=brightness=-0.03:contrast=1.08:saturation=1.08"\n'
       '               ",unsharp=5:5:0.8")\n')
assert t.count(old) == 1
t = t.replace(old, new)

old = '        if r["timeline"][1] > TAIL_START + 0.001:\n'
new = (
    '        # V8-1: S2-10/S2-11 read as a flat amber plate, off the\n'
    '        # Xingqing-GRADE-v1 gold-blue pairing. Measured on the v7 native\n'
    '        # frame 54.0s: sky B-R = -39.5 against +18.9 at 30.4s. Pull the\n'
    '        # yellow cast back, return the sky to blue, recover the detail.\n'
    '        if r["shot"] in GRADE_V8:\n'
    '            chain += GRADE_CHAIN\n'
    '        if r["timeline"][1] > TAIL_START + 0.001:\n')
assert t.count(old) == 1
t = t.replace(old, new)

head_old = '# xq_packb_assembly_v7_c2163.py - PACK-B v7: R4 winning take for S1-07 (C2162).\n'
head_new = ('# xq_packb_assembly_v8_c2165.py - PACK-B v8: closes the two hard items of\n'
            '# DIRECTOR-REVIEW-PACKB-V7-20261024.md and re-cuts the whole picture.\n'
            '#\n'
            '#   V7-1 S2-10/S2-11 (53.417-63.667s) colour+detail break -> local grade\n'
            '#        compensation at the block level (option b of the review).\n'
            '#   V7-2 226-232s note plate pseudo-glyphs -> new note take\n'
            '#        clips-local-768/XQ_B-F5-33c-v8.mp4 (real readable handwriting,\n'
            '#        built by xq_packb_note_fix_c2165.py), slot swapped in.\n'
            '#\n'
            '# Everything else is the proven v7 graph, unchanged.\n')
assert t.count(head_old) == 1
t = t.replace(head_old, head_new)

io.open(DST, "w", encoding="ascii", newline="").write(t)
print("WROTE", DST)
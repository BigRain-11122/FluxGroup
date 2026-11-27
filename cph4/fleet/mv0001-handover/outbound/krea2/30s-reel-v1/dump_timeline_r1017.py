# -*- coding: utf-8 -*-
"""Dump V5.2 authoritative shot timeline for full-coverage review (CEO O-20261017-1340).
Outputs timeline.json: per-shot on-screen windows, all cut events (type + on-screen time),
E1 program counts (bare-hard-cut ratio), luma scan plan inputs.
On-screen math: shift(T) = sum{D_j : anchor_j < T}; boundary cut time uses <= (own fade pulls next block).
"""
import os, sys, json
HERE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
os.chdir(HERE); sys.path.insert(0, HERE)
import build_full_mv_v2 as v2
import build_full_mv_v3 as v3m
import build_full_mv_v5 as v5

SIL1_DUR_V51 = 2.14
XFS = [(21.90, "fade", 0.36)] + list(v5.XFS)
FX_SITES = [38.62, 40.02, 47.30, 77.30, 80.05, 91.02, 93.05, 102.80,
            110.42, 110.62, 131.62, 141.72, 168.30, 187.24, 212.62, 219.80, 231.90]

ins = []
for x in v3m.V3_INSERTS:
    iid, fn, a, d, v = x
    if iid == "SIL1_v4b":
        d = SIL1_DUR_V51
    ins.append((iid, fn, a, d, v))
v3m.V3_INSERTS = ins
rows = v5.build_rows_v5()   # (sid, t0, t1, v, src_file, is_new)
anchors = [a for (a, _, _) in XFS]

def shift_before(T, inclusive=False):
    s = 0.0
    for (a, _, d) in XFS:
        if (a <= T) if inclusive else (a < T):
            s += d
    return s

shots, cuts = [], []
for i, r in enumerate(rows):
    sid, t0, t1 = r[0], r[1], r[2]
    c0 = shift_before(t0, inclusive=(t0 in anchors))
    c1 = shift_before(t1, inclusive=(t1 in anchors))
    os_start, os_end = t0 - c0, t1 - c1
    shots.append({"i": i, "sid": sid, "win": [round(t0, 3), round(t1, 3)],
                  "os": [round(os_start, 3), round(os_end, 3)],
                  "mid": round((os_start + os_end) / 2, 3), "v": r[3]})
    if i + 1 < len(rows):
        b = t1
        soft = b in anchors
        os_t = round((b - shift_before(b, inclusive=True)) if soft else (b - shift_before(b)), 3)
        d_idx = next((k for k, (a, _, _) in enumerate(XFS) if a == b), None)
        cut = {"k": len(cuts), "prev": sid, "next": rows[i + 1][0],
               "win_b": round(b, 3), "os": os_t,
               "type": ("xfade:" + XFS[d_idx][1] + ":%.2f" % XFS[d_idx][2]) if soft else "hard",
               "fx": [f for f in FX_SITES if abs(f - os_t) <= 0.35]}
        cuts.append(cut)

hard = [c for c in cuts if c["type"] == "hard"]
garnished = [c for c in hard if c["fx"]]
bare = [c for c in hard if not c["fx"]]
soft = [c for c in cuts if c["type"] != "hard"]
fam = set()
for c in cuts:
    if c["type"].startswith("xfade"):
        fam.add(c["type"].split(":")[1])
    for f in c["fx"]:
        fam.add({38.62: "band", 40.02: "band", 47.30: "leak", 77.30: "flash", 80.05: "smoke",
                 91.02: "flash", 93.05: "dust", 102.80: "dust", 110.42: "smoke", 110.62: "leak",
                 131.62: "dust", 141.72: "flash", 168.30: "dust", 187.24: "echo", 212.62: "flash",
                 219.80: "smoke", 231.90: "dust"}[f])
report = {
    "n_shots": len(rows), "n_cuts": len(cuts), "n_hard": len(hard),
    "n_hard_garnished": len(garnished), "n_bare_hard": len(bare),
    "bare_ratio": round(len(bare) / len(hard), 4) if hard else 1.0,
    "n_soft": len(soft), "families": sorted(fam),
    "final_len": 234.25,
}
out = {"report": report, "shots": shots, "cuts": cuts}
dst = os.path.join(HERE, "timeline_v52.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False))
print("shots:", " ".join("%s[%.2f-%.2f]" % (s["sid"], s["os"][0], s["os"][1]) for s in shots))
print("bare-hard cuts:", " ".join("%s|%s@%.2f" % (c["prev"], c["next"], c["os"]) for c in bare))
print("TIMELINE -> " + dst)

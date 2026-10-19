# -*- coding: utf-8 -*-
# r1042 bm-b POOL-0019 beats consumption-verify probe (read-only, downstream contract)
# r1041 probe extended to 7/7: 7th mp3 (龙卷风) arrived Downloads 21:34, idempotent
# beats gen completed r1042 00:37 (286 beats / 72 downbeats / 250.36s / 41.2s runtime).
import json, os, sys
sys.stdout.reconfigure(errors="replace")
ANC = r"C:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\anchors"
SONGS = ["可爱女人", "安静", "开不了口", "星晴", "晴天", "简单爱", "龙卷风"]
rows, fails = [], 0
for s in SONGS:
    p = os.path.join(ANC, s + "-beats.json")
    if not os.path.exists(p):
        fails += 1
        rows.append({"song": s, "status": "MISSING"})
        continue
    d = json.load(open(p, encoding="utf-8"))
    beats, down = d["beats"], d["downbeats"]
    t = [b[0] for b in beats]
    pos_ok = all(1 <= b[1] <= 4 for b in beats)
    mono = all(t[i] < t[i + 1] for i in range(len(t) - 1))
    down_ok = all(abs(b[0] - round(b[0], 3)) < 1e-9 for b in beats) and down == sorted(down)
    sub = all(round(dbe, 3) in [round(x, 3) for x in down] for dbe in [b[0] for b in beats if b[1] == 1])
    cover = d["duration_sec"] > 0 and t[0] < 5 and (d["duration_sec"] - t[-1]) < 15
    ok = pos_ok and mono and down_ok and sub and cover and d["n_beats"] == len(beats) and d["n_downbeats"] == len(down)
    if not ok:
        fails += 1
    rows.append({"song": s, "status": "OK" if ok else "FAIL", "n_beats": d["n_beats"],
                 "n_downbeats": d["n_downbeats"], "duration_sec": d["duration_sec"],
                 "bpm_median": round(60.0 / (sorted([t[i+1]-t[i] for i in range(len(t)-1)])[len(t)//2] or 1), 1),
                 "checks": {"pos_range": pos_ok, "mono": mono, "down_subset": sub,
                            "coverage_edges": cover, "count_match": d["n_beats"] == len(beats)}})
doc = {"probe": "POOL-0019 beats consumption-verify (r1042 bm-b, 7/7 first-batch wrap)",
       "ts": "2026-10-20T00:3x+08:00", "contract": "beats[[t,pos]]/downbeats[t]/duration monotonic downstream-readable",
       "rows": rows, "fails": fails,
       "verdict": "PASS" if fails == 0 else "FAIL"}
out = os.path.join(ANC, "..", "POOL-0019-beats-consumption-verify-r1042bmb.json")
json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(doc, ensure_ascii=False, indent=1))
sys.exit(0 if fails == 0 else 1)

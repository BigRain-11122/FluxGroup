# -*- coding: utf-8 -*-
# c2160_bank_claim.py -- mark the S1-07 R4 re-render bank job as claimed by C2160 (harvest next round).
import io
import json
import time

P = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
NOW = time.strftime("%Y-%m-%d %H:%M")

with io.open(P, encoding="utf-8") as f:
    d = json.load(f)

hit = [j for j in d["jobs"] if j["id"] == "packb-s107-r4-rerender-c2159"]
assert len(hit) == 1, "job count=%d" % len(hit)
j = hit[0]
j["status"] = "claimed"
j["claimed_ts"] = NOW
j["claimed_by"] = "tick-C2160-r4-rerender"
j["claim_note"] = ("Runner authored as the 2-unit manifest run-bmc-packB-r4-s107-c2160.json on the proven "
                   "h3_i2v_album lane (1344x768 int8, 226 frames, seeds 21009/21002 inside the 21000-21015 band, "
                   "human-silhouette clause deleted). Long burn lives on the registered repeating task "
                   "MiniGameComfyBurn-S107R4 (every 8m, hidden chain, SKIP-rule re-entry, self-disable when both "
                   "takes land) via c2160_s107r4_runner.ps1; wave-harvest-pending armed at 01:11; observed live at "
                   "01:07 (r4a submitted). Harvest + native-frame read next round, then done.")

with io.open(P, "w", encoding="utf-8", newline="\n") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("BANK OK status=%s claimed_ts=%s" % (j["status"], j["claimed_ts"]))
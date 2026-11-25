# -*- coding: utf-8 -*-
# C2159: bank surgery -- close the stale packB768 harvest claim (harvested in
# C2147/C2148) and pre-stow the R4 re-render as the successor job.
import io
import json

P = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
raw = io.open(P, encoding="utf-8-sig").read()
d = json.loads(raw)
jobs = d["jobs"]

stale = [j for j in jobs if j["id"] == "kfpb-packB768-harvest-c2146"]
assert len(stale) == 1 and stale[0].get("status") == "claimed"
stale[0]["status"] = "done"
stale[0]["done_ts"] = "2026-10-20T17:11:00"
stale[0]["done_note"] = (
    "Claim closed by C2159 bookkeeping: the six 768P pack B clips were harvested in "
    "C2147 (partial, S1-08 MINOR / S3-17 FAIL) and C2148 (6/6 clean) and have been in "
    "the cut since PACK-B EDL v3/v5, so this claim was stale, not open work."
)

assert not any(j["id"] == "packb-s107-r4-rerender-c2159" for j in jobs)
jobs.append({
    "id": "packb-s107-r4-rerender-c2159",
    "status": "blocked",
    "created_ts": "2026-10-24 00:28",
    "priority": 60,
    "auth": (
        "Director R4 (DIRECTOR-REVIEW-PACKB-V2-20261020.md) is the last hard item on the "
        "Xingqing PACK-B cut. C2159 proved picture-side repair impossible: the cloud figure "
        "is a plate-locked overlay (same screen box across 226 frames while the camera moves "
        "from sky to a top-down wheat field), cloud and sky are inseparable by luma "
        "(159.7 vs 157.3) or saturation, and three passes (brightness matte / ellipse + short "
        "smear / long wind smear + shear + aerial haze) all ended as 'still a woman' or 'a "
        "smudge over the field'. Evidence: cph4/fleet/mv-album-001-jay/evidence-c2159/"
        "R4-BEFORE-AFTER-c2159.jpg."
    ),
    "require": {"files_at_least": []},
    "cmd": [],
    "log_out": "media/mv-album-001-jay/logs/s107_r4_rerender.out.log",
    "log_err": "media/mv-album-001-jay/logs/s107_r4_rerender.err.log",
    "note": (
        "BLOCKED until the runner is authored: copy the proven pack A/B 768P mini-wave runner "
        "paradigm (xq_t1r1hd_bmc_20261018.py) and burn S1-07 only, 1344x768, 226 frames, "
        "seed band 21000-21015 (never used band), with the prompt's human-silhouette clause "
        "REMOVED - ask for 'a low cumulus cloud whose whole mass slowly drifts alongside the "
        "riders, wind-eroded ragged edges, warm sun-side rim, thinning into haze near the "
        "ground' instead of 'shaped like a young woman silhouette'. The narrative signified "
        "stays in the edit, not in the pixels. Runner must: lint (NEG/VAGUE zero-hit, <=200 "
        "words), dry-run print the prompt, fire detached through the self-healing long-burn "
        "runner (never a naked Start-Process), arm .codely-cli/engine-tick/wave-harvest-"
        "pending.json, and stop after 2-3 seeds for a native-frame read before the full burn "
        "(low-cost-first law). PASS gate = a take whose native frames read as a cloud at "
        "1344x768 AND whose cloud/sky luma separation is measurable (if the model still paints "
        "cloud and sky as one level, the seed is negative - do not ship it into the cut). "
        "After the verdict: assemble v6, re-check every R item, then the director reads the "
        "whole film; no CEO address before a DIRECTOR-REVIEW-PASS exists."
    ),
    "prestow_ts": "2026-10-24T00:28:00",
    "prestow_note": "C2159 pre-stow (bank law: never empty) - the only hard item left on the Xingqing line.",
})

out = json.dumps(d, ensure_ascii=False, indent=1)
# the file ships with 1-space indent per the opening lines; keep it byte-consistent
io.open(P, "w", encoding="utf-8", newline="\r\n").write(out + "\n")
print("BANK-WROTE jobs=%d" % len(jobs))
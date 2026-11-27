# Bank surgery #2 (tick-C2082): harvest latentsync-trial PASS + pre-stow qcboard successor job
import json
import os
import datetime

FG = r"K:\Fluxgroup\FluxGroup"
BANK = os.path.join(FG, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")

raw = open(BANK, "rb").read()
has_bom = raw[0:3] == b"\xef\xbb\xbf"
text = raw.decode("utf-8-sig")
eol = "\r\n" if "\r\n" in text else "\n"
lines = text.splitlines()
indent = 1
for ln in lines[1:]:
    if ln.strip():
        indent = len(ln) - len(ln.lstrip(" "))
        break

bank = json.loads(text)
jobs = {j["id"]: j for j in bank["jobs"]}
now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# 1. harvest trial: claimed (guard refire 16:35:59) -> done PASS
j = jobs["latentsync-trial"]
assert j["status"] == "claimed", "trial status=%s" % j["status"]
j["status"] = "done"
j["done_ts"] = now
j["done_note"] = ("PASS by tick-C2082 in-round harvest (guard refire 16:35:59 after C2082 soundfile+decord-shim rearm): "
                  "out.mp4 1604658B / 82 frames (ffprobe), j30_no_insightface=true, inference_wall=253s total=311s, "
                  "vram start free 10460MB; 82-face affine+restore chain clean; verdict latentsync_trial_verdict.json ts 16:41:10. "
                  "82f>16f = multi-window sliding inference structurally proven (long-video face OK, no 72f probe needed - musepose "
                  "stitch72 precedent does not apply here). POOL-0016 night-1 CLOSED -> LatentSync lip-sync upgraded direct-use "
                  "(R-stack night series 3/3: LivePortrait L23 + MusePose L24 + LatentSync lip-sync). Three-piece final gap closed.")

# 2. pre-stow successor wave (pre-stow law O-20261018-2236): closure evidence board job
assert "latentsync-qcboard" not in jobs, "qcboard job already exists"
bank["jobs"].append({
    "id": "latentsync-qcboard",
    "status": "pending",
    "priority": 13,
    "auth": "POOL-0016 night-1 closure evidence board (R-stack dossier human-eye face), C2082 pre-stow (pre-stow law O-20261018-2236)",
    "require": {
        "files_at_least": [
            ["media/latentsync-deploy/trial_c2079", "out.mp4", 1]
        ]
    },
    "cmd": [
        "D:\\ComfyUI\\python_embeded\\python.exe",
        "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\latentsync_qcboard_c2082.py"
    ],
    "log_out": "media/latentsync-deploy/log-qcboard.out.txt",
    "log_err": "media/latentsync-deploy/log-qcboard.err.txt",
    "note": "Mechanical PIL board: 6 input frames vs 6 output frames side-by-side from trial_c2079 (frames 4/16/28/40/52/70); output latentsync_trial_qcboard_c2082.jpg + qcboard_verdict.json + BOARD-END sentinel; feeds R-stack dossier (reference-library project-initiation evidence). Harvest next round.",
})

out = json.dumps(bank, ensure_ascii=True, indent=indent)
if eol == "\r\n":
    out = out.replace("\n", "\r\n")
if has_bom:
    out = "\ufeff" + out
with open(BANK, "w", encoding="utf-8-sig" if has_bom else "utf-8", newline="") as f:
    f.write(out)

rt = json.loads(open(BANK, "rb").read().decode("utf-8-sig"))
jobs2 = {x["id"]: x for x in rt["jobs"]}
assert jobs2["latentsync-trial"]["status"] == "done"
assert jobs2["latentsync-qcboard"]["status"] == "pending"
n_done = sum(1 for x in rt["jobs"] if x["status"] == "done")
n_pending = sum(1 for x in rt["jobs"] if x["status"] == "pending")
print("BANK-SURGERY2 OK trial=done PASS, qcboard=pending prestowed; done=%d pending=%d" % (n_done, n_pending))

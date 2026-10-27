"""C2140 step 4: harvest the KF-PACK-B probe (ok=6/6) and restow the bank.

Reads the runner receipt, closes the job, then pre-stows:
  - one runnable zero-GPU job (re-verify the v2 film after this push lands)
  - one blocked job (B-EX2 re-roll) so the pipeline intent is on the record
    without arming a command that cannot run yet.
"""
import io
import json

BANK = r"cph4/fleet/work-bank/bm-c-gpu-bank.json"
RECEIPT = r"cph4/fleet/mv-album-001-jay/xq-KFPB-RECEIPT-c2139-probe.json"
NOW = "2026-10-20T12:13:00"

rec = json.loads(io.open(RECEIPT, "rb").read().decode("utf-8-sig"))
frames = rec.get("frames") or rec.get("shots") or []

raw = io.open(BANK, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
data = json.loads(raw.decode("utf-8-sig"))

closed = False
for job in data["jobs"]:
    if job["id"] == "kf-packb-probe-c2138" and job["status"] != "done":
        job["status"] = "done"
        job["done_ts"] = NOW
        job["done_note"] = (
            "KFPB-PROBE-END ok=6/6 fails=none (261s burns). 6 PNGs 274-415KB in "
            "media/MV/mv0001/xingqing/xq-kf-packb-probe-c2139/, board "
            "xq-KFPB-BOARD-c2139-probe.jpg 168411B, receipt xq-KFPB-RECEIPT-c2139-probe.json. "
            "Native board read: 5 PASS / 1 MINOR (B-EX2 girl hand placement ambiguous + "
            "eyeline mismatch) / 0 FAIL."
        )
        closed = True

if not any(j["id"] == "packA-conform-v2-reverify-after-push" for j in data["jobs"]):
    data["jobs"].append(
        {
            "id": "packA-conform-v2-reverify-after-push",
            "status": "pending",
            "priority": 42,
            "auth": "C2140 re-verified v2 against origin/main 9ee0232a; this re-runs the same zero-GPU check after the C2140 push lands so the receipt in the repo cannot drift from the film.",
            "require": {"files_at_least": []},
            "cmd": [
                r"D:\ComfyUI\python_embeded\python.exe",
                r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq_packa_v2_origin_verify_c2135.py",
            ],
            "log_out": "media/mv-album-001-jay/log-packa-originverify-v2.out.txt",
            "log_err": "media/mv-album-001-jay/log-packa-originverify-v2.err.txt",
            "note": "Zero GPU, idempotent. PASS gate = ORIGIN-VERIFY-V2-END ok=1 mismatches=0.",
            "prestow_ts": NOW,
            "prestow_note": "C2140 pre-stow (bank law: never empty) after the probe closed.",
        }
    )

if not any(j["id"] == "kfpb-bex2-reroll-c2140" for j in data["jobs"]):
    data["jobs"].append(
        {
            "id": "kfpb-bex2-reroll-c2140",
            "status": "blocked",
            "priority": 40,
            "auth": "C2140 native board read: B-EX2 (dusk two-shot, hem hook) = MINOR - the girl's hand placement never resolves and the eyelines do not connect. Five other probe frames PASS.",
            "require": {"files_at_least": []},
            "cmd": [],
            "log_out": "media/MV/mv0001/logs/kfpb_bex2_reroll.out.log",
            "log_err": "media/MV/mv0001/logs/kfpb_bex2_reroll.err.log",
            "note": "BLOCKED: needs a single-frame variant of kfpb_probe_c2139.py (--only B-EX2, 3 candidate seeds, explicit hand/eyeline clause in the prompt). Author the variant first, then flip to pending. Do not fire while blocked.",
            "prestow_ts": NOW,
            "prestow_note": "C2140 pre-stow from the board read.",
        }
    )

body = json.dumps(data, ensure_ascii=False, indent=1).encode("utf-8")
io.open(BANK, "wb").write(b"\xef\xbb\xbf" + body if bom else body)

chk = json.loads(io.open(BANK, "rb").read().decode("utf-8-sig"))
print(
    "BANK-END closed=%s receipt_frames=%s"
    % (closed, len(frames) if isinstance(frames, list) else frames)
)
print("  open:", [j["id"] + ":" + j["status"] for j in chk["jobs"] if j["status"] != "done"])
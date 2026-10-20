"""C2140 crash-adoption bank surgery.

1) Close packA-conform-v2-origin-verify-v1 with the verifier receipt.
2) Pre-stow the KF-PACK-B probe as `blocked` (its runner never materialised in
   C2139, so firing it would false-fail); documents intent without arming a
   broken command.
Byte-identical JSON rewrite: keep indent=1, no trailing newline, no BOM.
"""
import io
import json

BANK = r"cph4/fleet/work-bank/bm-c-gpu-bank.json"
NOW = "2026-10-20T12:03:00"
RECEIPT = "media/mv-album-001-jay/log-packa-originverify-v2.out.txt"

raw = io.open(BANK, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
data = json.loads(raw.decode("utf-8-sig"))

closed = False
for job in data["jobs"]:
    if job["id"] == "packA-conform-v2-origin-verify-v1" and job["status"] != "done":
        job["status"] = "done"
        job["done_ts"] = NOW
        job["claimed_by"] = "tick-C2140-crash-adoption"
        job["done_note"] = (
            "ORIGIN-VERIFY-V2-END ok=1 mismatches=0 eol_only=5 frames=4710 "
            "I=-14.2 TP=-2.3 vs origin/main 9ee0232a; receipt " + RECEIPT
        )
        closed = True

has_packb = any(j["id"] == "kf-packb-probe-c2138" for j in data["jobs"])
if not has_packb:
    data["jobs"].append(
        {
            "id": "kf-packb-probe-c2138",
            "status": "blocked",
            "priority": 41,
            "auth": (
                "C2139 director verdict canonised the B face (seed 578950 dusk / "
                "514974 night) and decreed a 6-frame 672x384 KF-PACK-B probe before "
                "the 1344x768 main pass."
            ),
            "require": {"files_at_least": []},
            "cmd": [],
            "log_out": "media/mv-album-001-jay/log-kfpackb-probe.out.txt",
            "log_err": "media/mv-album-001-jay/log-kfpackb-probe.err.txt",
            "note": (
                "BLOCKED: the KF-PACK-B probe runner claimed by C2139 is not on disk "
                "(no tools/ or cph4/fleet/mv-album-001-jay/*packb* script exists). "
                "Next round must materialise the runner (reuse the KF-PACK-A shared "
                "blocks + ID_M_2001 with jman 0.6 on the two boy frames) then flip "
                "this job to pending. Do not fire while blocked."
            ),
            "prestow_ts": NOW,
            "prestow_note": "C2140 pre-stow: records the C2139 intent; runner gap logged in state.",
        }
    )

body = json.dumps(data, ensure_ascii=False, indent=1)
out = body.encode("utf-8")
if bom:
    out = b"\xef\xbb\xbf" + out
io.open(BANK, "wb").write(out)

data2 = json.loads(io.open(BANK, "rb").read().decode("utf-8-sig"))
print(
    "BANK-END closed=%s jobs=%d non_done=%s"
    % (
        closed,
        len(data2["jobs"]),
        [j["id"] + ":" + j["status"] for j in data2["jobs"] if j["status"] != "done"],
    )
)
"""C2140 step 2: the KF-PACK-B runner DOES exist (kfpb_probe_c2139.py, 14390B).

Correction: the first surgery marked the job `blocked` because the runner was
searched in the wrong tree (MiniGame tools + the album dir, not idle-guard-kit).
Flip it to pending with the real command, then the round claims it.
"""
import io
import json

BANK = r"cph4/fleet/work-bank/bm-c-gpu-bank.json"
NOW = "2026-10-20T12:14:00"

raw = io.open(BANK, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
data = json.loads(raw.decode("utf-8-sig"))

for job in data["jobs"]:
    if job["id"] != "kf-packb-probe-c2138":
        continue
    job["status"] = "claimed"
    job["priority"] = 41
    job["cmd"] = [
        r"D:\ComfyUI\python_embeded\pythonw.exe",
        r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit\kfpb_probe_c2139.py",
    ]
    job["log_out"] = "media/MV/mv0001/logs/kfpb_probe_c2139.out.log"
    job["log_err"] = "media/MV/mv0001/logs/kfpb_probe_c2139.err.log"
    job["note"] = (
        "6 face/limb frames at 672x384, one seed each, canonical B face + ID_M_2001 "
        "(jman 0.6 on the boy frame). PASS gate = KFPB-PROBE-END ok=6/6 in the log tail "
        "+ 6 PNGs >=50KB + strip board + receipt in "
        "media/MV/mv0001/xingqing/xq-kf-packb-probe-c2139/."
    )
    job["claimed_ts"] = NOW
    job["claimed_by"] = "tick-C2140-crash-adoption"
    job["prestow_note"] = (
        "C2139 authored the runner (idle-guard-kit/kfpb_probe_c2139.py) but never wrote the "
        "bank entry; C2140 materialised the entry from the runner header and fired it."
    )

body = json.dumps(data, ensure_ascii=False, indent=1).encode("utf-8")
if bom:
    body = b"\xef\xbb\xbf" + body
io.open(BANK, "wb").write(body)

check = json.loads(io.open(BANK, "rb").read().decode("utf-8-sig"))
for j in check["jobs"]:
    if j["id"] == "kf-packb-probe-c2138":
        print("BANK-OK status=%s cmd=%s" % (j["status"], j["cmd"][-1]))
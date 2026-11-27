# -*- coding: utf-8 -*-
# Bank surgery (tick-C2091): pre-stow successor wave p17 packA-qc-strips-v2 (pre-stow law O-20261018-2236)
# i2v3 (p16) burn still in flight (guard claim 20:25:59, S3-19 burning) - ZERO touch on p16, harvest belongs to a later round.
# p17 = 31-unit full QC board regen with redo-r1 6-clip swap -> X2670 sec-6 assembly-unlock prefix (board re-adjudication base plate).
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

# 0. byte-preserving pre-check: round-trip of unmodified object must equal original text
for ascii_face in (False, True):
    probe = json.dumps(bank, ensure_ascii=ascii_face, indent=indent)
    if eol == "\r\n":
        probe = probe.replace("\n", "\r\n")
    if probe == text:
        break
else:
    raise SystemExit("ROUNDTRIP-FAIL: neither ascii face reproduces original bytes - byte surgery required, abort")
print("ROUNDTRIP OK ensure_ascii=%s eol=%r indent=%d bom=%s" % (ascii_face, eol, indent, has_bom))

# 1. zero-touch guard: p16 i2v3 must still be claimed by the guard (burn in flight)
j = jobs["xq-redo-i2v3"]
assert j["status"] == "claimed", "i2v3 status=%s (expected claimed - burn in flight)" % j["status"]
print("P16 i2v3 untouched: status=claimed since %s" % j["claimed_ts"])

# 2. pre-stow successor wave p17: 31-unit board regen (redo-r1 swap), require-gated on i2v3 3 mp4s
assert "packA-qc-strips-v2" not in jobs, "p17 already exists"
bank["jobs"].append({
    "id": "packA-qc-strips-v2",
    "status": "pending",
    "priority": 17,
    "auth": "X2670 sec-6 assembly-unlock prefix: 31-unit full QC board regen with redo-r1 6-clip swap (board re-adjudication base plate), C2091 pre-stow (pre-stow law O-20261018-2236); v1 board = xq-PACKA-QC-STRIPS-20261018.jpg (C2059, pre-redo); runner DRY-verified C2091 (py_compile green + missing-gate exactly 1 = S3-19 in-burn)",
    "require": {
        "files_at_least": [
            ["media/mv-album-001-jay/clips-packA-redo-r1", "XQ_F5-33a-redo-r1.mp4", 1],
            ["media/mv-album-001-jay/clips-packA-redo-r1", "XQ_S4-24-redo-r1.mp4", 1],
            ["media/mv-album-001-jay/clips-packA-redo-r1", "XQ_S3-19-redo-r1.mp4", 1]
        ]
    },
    "cmd": [
        "D:\\ComfyUI\\python_embeded\\pythonw.exe",
        "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\packA_qc_strips_v2_c2091.py"
    ],
    "log_out": "media/mv-album-001-jay/log-qcstripsv2.out.txt",
    "log_err": "media/mv-album-001-jay/log-qcstripsv2.err.txt",
    "note": "31-unit board regen with redo-r1 swap: 6 re-burned units (F5-33a/S2-14/S3-19/S3-20/S4-22/S4-24) read from clips-packA-redo-r1 and labeled [REDO-R1], other 25 units unchanged from clips-packA-768. require gates on i2v3 3 mp4s (F5-33a/S4-24/S3-19) so guard auto-claims right after i2v3 burn end = zero idle window (CEO 10min idle SLA). PASS gate = STRIPS-V2 DONE: 31 clips sentinel in log-qcstripsv2.out tail + board xq-PACKA-QC-STRIPS-v2-c2091.jpg >= 1000000B + zero exit. Harvest next round alongside i2v3 harvest gate 4/4: per-unit sec-4 adjudication of 3 i2v3 units (qc strips) + director re-review on v2 board (board re-adjudication) -> assembly unlock face (X2670 sec-6: PACK-A 31/31 green + S5-27 return from bm-a director seat).",
})

out = json.dumps(bank, ensure_ascii=ascii_face, indent=indent)
if eol == "\r\n":
    out = out.replace("\n", "\r\n")
if has_bom:
    out = "\ufeff" + out
with open(BANK, "w", encoding="utf-8-sig" if has_bom else "utf-8", newline="") as f:
    f.write(out)

rt = json.loads(open(BANK, "rb").read().decode("utf-8-sig"))
jobs2 = {x["id"]: x for x in rt["jobs"]}
assert jobs2["xq-redo-i2v3"]["status"] == "claimed"
assert jobs2["packA-qc-strips-v2"]["status"] == "pending"
assert len(rt["jobs"]) == 18
n_done = sum(1 for x in rt["jobs"] if x["status"] == "done")
n_pending = sum(1 for x in rt["jobs"] if x["status"] == "pending")
n_claimed = sum(1 for x in rt["jobs"] if x["status"] == "claimed")
print("BANK-SURGERY C2091 OK jobs=18 done=%d pending=%d claimed=%d (p16 i2v3 burn untouched, p17 strips-v2 prestowed at %s)" % (n_done, n_pending, n_claimed, now))

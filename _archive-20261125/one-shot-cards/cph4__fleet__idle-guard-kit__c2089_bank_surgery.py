# Bank surgery (tick-C2089): harvest xq-redo-kf-reroll3 PASS (native adjudication 3/3 winners) + pre-stow i2v3 successor job p16
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

# 1. harvest kfreroll3: claimed (guard claim 19:40:59) -> done PASS (C2089 native adjudication)
j = jobs["xq-redo-kf-reroll3"]
assert j["status"] == "claimed", "kfreroll3 status=%s" % j["status"]
j["status"] = "done"
j["done_ts"] = now
j["done_note"] = ("HARVEST PASS by tick-C2089: PASS gate 4/4 (KF-REROLL-END ok=6/6 fails=none in log tail + 6 full PNGs "
                  "578082-1128878B all >=50KB in kfreroll-r1 + progress json + board xq-KFREROLL3-BOARD-c2088.jpg 211282B). "
                  "Native adjudication 3/3 winners: F5-33a=kf2 s897596 (5/5: blank age-worn label, zero text, zero mirrored "
                  "gibberish, zero orange-sticker elements = defect-signature class avoided, clear-shell consistent with passed "
                  "F5-33b); S4-24=kf1 s361394 (5/5: label blank soft, zero readable text, zero micro-print, zero pseudo logo, "
                  "fingers natural, geometry plausible); S3-19=kf2 s979448 (order sec-4 gate 3/3: dusk sky discernible + single "
                  "arm single pointing finger + zero smear/confetti/tiling; kf1 s602988 disqualified by second ambiguous limb "
                  "mass lower-left; honest note: star sits mid-frame, gate carries no star-position item, finger sightline leads "
                  "toward it). Retry budget 2/2 per unit consumed, all 3 units resolved within budget - no escalation to director "
                  "seat needed. Next slice = i2v leg prestowed p16 xq-redo-i2v3 (F5-33a zero-change 51w / S4-24 draft-A 58w / "
                  "S3-19 zero-change 72w FIX, first_frame = winners).")

# 2. pre-stow successor wave (pre-stow law O-20261018-2236): i2v leg for the 3 winners
assert "xq-redo-i2v3" not in jobs, "i2v3 job already exists"
bank["jobs"].append({
    "id": "xq-redo-i2v3",
    "status": "pending",
    "priority": 16,
    "auth": "X2670 redo order sec-2/sec-3.1 i2v leg (3 KF-reroll winners F5-33a/S4-24/S3-19), C2089 pre-stow (pre-stow law O-20261018-2236); winner evidence = C2089 native single-frame reads + board xq-KFREROLL3-BOARD-c2088.jpg",
    "require": {
        "files_at_least": [
            ["media/MV/mv0001/xingqing/kfreroll-r1", "F5-33a_s897596.png", 1],
            ["media/MV/mv0001/xingqing/kfreroll-r1", "S4-24_s361394.png", 1],
            ["media/MV/mv0001/xingqing/kfreroll-r1", "S3-19_s979448.png", 1]
        ]
    },
    "cmd": [
        "D:\\ComfyUI\\python_embeded\\python.exe",
        "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\mv-album-001-jay\\local-i2v\\h3_i2v_album.py",
        "--repo",
        "K:\\Fluxgroup\\FluxGroup",
        "--lane",
        "bmcpackAredo",
        "--manifest",
        "cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-redo-r1-i2v3.json",
        "--only",
        "XQ_F5-33a-redo-r1,XQ_S4-24-redo-r1,XQ_S3-19-redo-r1"
    ],
    "log_out": "media/mv-album-001-jay/log-redo-i2v3.out.txt",
    "log_err": "media/mv-album-001-jay/log-redo-i2v3.err.txt",
    "note": "Winners per C2089 native adjudication -> i2v leg: F5-33a zero-change 51w (original verbatim, clean of label mention) + S4-24 draft A 58w verbatim (strokes-clause hotbed removed) + S3-19 zero-change 72w FIX draft; first_frame = winning full KFs (F5-33a_s897596 / S4-24_s361394 / S3-19_s979448); lane bmcpackAredo out clips-packA-redo-r1; seed renewal = -redo-r1 id-MD5 family (distinct from orig units and kf1/kf2 families). PASS gate = ALBUM LANE DONE ok=3 fail=0 in log tail + 3 mp4 >=100KB in media/mv-album-001-jay/clips-packA-redo-r1/ + progress-bmcpackAredo.jsonl ok x3 + ffprobe -count_frames decode-clean (S3-19 mandatory per order sec-3.3, others recommended). Harvest next round: qc strips 3 units + X2670 sec-4 gates per unit (F5-33a zero-pseudo-text + self-stop held / S4-24 three-frame subject hold + zero readable label / S3-19 decode-integrity + sky + single arm) -> director re-review -> assembly unlock face (X2670 sec-6: PACK-A 31/31 green + S5-27 return).",
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
assert jobs2["xq-redo-kf-reroll3"]["status"] == "done"
assert jobs2["xq-redo-i2v3"]["status"] == "pending"
assert len(rt["jobs"]) == 17
n_done = sum(1 for x in rt["jobs"] if x["status"] == "done")
n_pending = sum(1 for x in rt["jobs"] if x["status"] == "pending")
print("BANK-SURGERY C2089 OK kfreroll3=done PASS winners adjudicated, i2v3=pending prestowed; jobs=17 done=%d pending=%d" % (n_done, n_pending))

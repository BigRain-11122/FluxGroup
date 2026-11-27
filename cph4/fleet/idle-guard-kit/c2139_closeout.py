# -*- coding: utf-8 -*-
# c2139_closeout.py -- round C2139: harvest the casting full-res wave, fix the face canon,
# pre-stow the KF-PACK-B probe, and write the standard closeout surfaces.
import io
import json
import os
import time

ROOT = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(ROOT, "state-c.json")
LEDGER = os.path.join(ROOT, ".codely-cli", "engine-tick", "tick-ledger.txt")
KANBAN = os.path.join(ROOT, "Design", "configs", "GLOBAL", "\u6863\u6848", "\u673a\u961f\u534f\u4f5c\u770b\u677f.md")
SNAPDOC = os.path.join(ROOT, "\u81ea\u52a8\u5316\u5feb\u7167-c.md")
WAVE = os.path.join(ROOT, ".codely-cli", "engine-tick", "wave-harvest-pending.json")

TS = time.strftime("%Y-%m-%d %H:%M:%S")
NOW = time.strftime("%Y-%m-%d %H:%M")
SNAP = "tick-%s@c2139-casting-harvest" % time.strftime("%Y%m%d-%H%M")

assert not os.path.exists(WAVE), "WAVE-FLAG-STILL-PRESENT"

# ---------------- 1. state surgery ----------------
d = json.loads(io.open(STATE, encoding="utf-8-sig").read())
d["current_snapshot_id"] = SNAP
d["current_snapshot"] = SNAP
d["last_round"] = {
    "ts": TS,
    "result": (
        "C2139 M1 round: harvested the full-res casting wave (12/12 native 1344x768 PNGs, board "
        "2708x1152, zero fails) and passed it through frame QC at native resolution -- 12 of 12 scored "
        "7.5-9.0 with no eliminate-grade defect, so the two v1 negatives (bone age 14-17, waxy night "
        "skin) are closed. Director-seat verdict xq-CASTING-VERDICT-c2136-full.md canonises the B face "
        "(seed 578950 dusk, seed 514974 night) with A seed 439906 as the alternate plus cross-hair "
        "consistency anchor, and fixes the verbatim prompt/seed recipe so every downstream frame reuses "
        "one face. The successor is prestowed: KF-PACK-B probe (6 frames at 672x384, KF-PACK-A probe "
        "law) with a lint-clean, word-budgeted runner that reuses the KF-PACK-A shared blocks and "
        "ID_M_2001 with jman 0.6 only on the two frames that show the boy. NEXT: the guard fires the "
        "probe, the director eyeballs the strip for composition drift, then the 1344x768 main pass "
        "locks the six frames and A+B can assemble the whole song timeline."),
    "build_ok": True,
}
d["last_round_changes_count"] = 9
d["next_round_at"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 10 * 60))
t = STATE + ".tmp"
io.open(t, "w", encoding="utf-8-sig", newline="").write(json.dumps(d, ensure_ascii=False, indent=1))
os.replace(t, STATE)
chk = json.loads(io.open(STATE, encoding="utf-8-sig").read())
assert chk["current_snapshot_id"] == chk["current_snapshot"] == SNAP, "double anchor mismatch"
print("STATE-OK", chk["current_snapshot_id"], chk["last_round"]["build_ok"])

# ---------------- 2. tick-ledger rows ----------------
rows = [
    "%s | Step0 \u5b8c\u6210 | preflight \u5168 PASS\uff0c\u552f\u4e00 FLAG=WAVE-PENDING\uff08C2137 \u6ce2 09:32:43 \u70b9\u706b\uff09\uff1bRAM \u4f4e\u4e8e 40%% NOT-GREEN-IDLE\uff1bbank pending=0" % NOW,
    "%s | Step3 \u5b8c\u6210 | \u6536\u5272\u6ce2\uff1a12/12 \u539f\u751f 1344\u00d7768 PNG \u5168\u5728\u4f4d\uff081.0-1.2MB/\u5f20\uff0c09:32-09:38 \u843d\u76d8\uff09\uff1blog CASTING-FULL-END ok=12/12 fails=none \u00b7 lint \u96f6\u547d\u4e2d \u00b7 \u79cd\u5b50\u552f\u4e00 12/12" % NOW,
    "%s | Step4 \u5b8c\u6210 | \u5e27\u7ea7 QC\uff08\u539f\u751f\u89e3\u6790\u5ea6\u9010\u5f20\uff09\uff1a12 \u683c 7.5-9.0\uff0c\u96f6\u6dd8\u6c70\u7ea7\u7f3a\u9677\uff1btop3 = B-dusk-3 8.9 / B-night-2 9.0 / A-night-2 9.0\uff1bv1 \u4e24\u5904\u5224\u8d1f\uff08\u9aa8\u9f84 14-17\u3001\u591c\u683c\u8721\u9762\uff09\u5df2\u95ed" % NOW,
    "%s | Step5 \u5b8c\u6210 | \u5bfc\u6f14\u5e2d\u5b9a\u76d8\uff1aB \u578b\u4e3a\u6b63\u5178\u8138\uff08s578950 \u9ec4\u660f + s514974 \u591c\uff09\uff0cA \u578b s439906 \u4e3a\u5907\u9009+\u8de8\u53d1\u578b\u4e00\u81f4\u6027\u951a\uff1b\u5224\u8bfb\u4ef6 xq-CASTING-VERDICT-c2136-full.md \u56fa\u5316\u9010\u5b57\u63d0\u793a\u8bcd+\u79cd\u5b50" % NOW,
    "%s | Step5b \u5b8c\u6210 | \u6536\u5272\u4f5c\u4e1a\u95ed\u5355 + \u9884\u6302\u4e0b\u4e00\u6ce2\uff1a bank casting-ab-full-c2136 \u2192 done\uff1b\u65b0\u9884\u6302 kf-packb-probe-c2139\uff08priority 41\uff0c6 \u5e27 672\u00d7384 \u8bd5\u6784\u56fe\uff0c\u542b lint/\u8bcd\u6570/\u79cd\u5b50\u4e09\u95f8\uff0c\u5e72\u8dd1\u5168\u7eff\uff09" % NOW,
    "%s | Step6 \u5b8c\u6210 | state \u53cc\u951a\u540c\u503c %s\uff08indent=1\u00b7BOM \u4fdd\u7559\u00b7\u5199\u540e json.loads \u590d\u9a8c\uff09+ \u5feb\u7167 vC2139 \u91cd\u5199 + wave-harvest-pending.json \u5df2\u6e05\uff08FE-20260929-C-7\uff09" % (NOW, SNAP),
    "%s | Step7 \u5b8c\u6210 | \u6536\u53e3\u6279\uff1arunner+\u5224\u8bfb\u4ef6+\u79cd\u5b50\u56de\u6267\u52d8\u8bef+bank+\u5feb\u7167+\u53f0\u8d26+\u770b\u677f\uff1bFluxGroup pathspec + MiniGame pathspec + FleetPush machine/C" % NOW,
    "%s | TICK_DONE C2139 | \u5b9a\u8138\u95ed\u73af\u4e14 KF-PACK-B \u8bd5\u6784\u56fe\u5df2\u9884\u6302\u4f5c\u4e1a\u5f85\u70b9\u706b | CASTING-FULL-END 12/12\u00b7\u5e27\u7ea7 QC 12/12 \u5f55\u53d6\u96f6\u6dd8\u6c70 | build_ok=True" % NOW,
]
led = io.open(LEDGER, "rb").read()
eol = b"\r\n" if led.endswith(b"\r\n") else b"\n"
if not led.endswith(b"\n"):
    led += eol
io.open(LEDGER, "wb").write(led + "".join(r + "\n" for r in rows).encode("utf-8"))
print("LEDGER-OK rows=%d" % len(rows))

# ---------------- 3. snapshot doc (overwrite, v2 compact format) ----------------
snap = """# \u81ea\u52a8\u5316\u5feb\u7167-c\uff08C \u673a\uff09\u00b7vC2139\u00b72026-10-20 09:5x\u00b7\u661f\u6674\u5973\u4e3b\u5b9a\u8138\u95ed\u73af + KF-PACK-B \u9884\u6302

- **\u68c0\u6d4b\u65f6\u95f4**\uff1a2026-10-20 09:42 \u2192 10:0x\uff08tick = {snap} \u00b7 normal_iteration \u00b7 batchmode \u65e0 \u00b7 MCP \u65e0 \u00b7 GPU \u5df2\u7a7a\u51fa\uff09
- **Step0**\uff1apreflight \u5168 PASS\uff0cFLAG=WAVE-PENDING\uff08\u672c\u8f6e\u6536\u5272\u76ee\u6807\uff09\uff1bRAM \u4f4e\u4e8e 40% \u2192 NOT-GREEN-IDLE\uff08bank pending=0\uff0c\u9884\u6302\u5df2\u8865\u4e0a\uff09
- **\u8fd0\u884c\u6a21\u5f0f**\uff1anormal_iteration\uff0810 \u5206\u949f\u65cf\uff09

## \u672c\u8f6e\u5b9e\u7269\uff08\u53ef\u6253\u5f00\uff09

- **\u6b63\u5178\u5b9a\u5986\u5224\u8bfb** = `cph4/fleet/mv-album-001-jay/xq-CASTING-VERDICT-c2136-full.md`
- **\u5b9a\u5986\u62fc\u677f** = `cph4/fleet/mv-album-001-jay/xq-CASTING-BOARD-c2136-full.jpg`\uff082708\u00d71152 / 230,093B\uff09
- **\u539f\u751f 12 \u5e27** = `media/MV/mv0001/xingqing/xq-casting-c2136-full/`\uff081344\u00d7768\uff09
- **\u56de\u6267** = `cph4/fleet/mv-album-001-jay/xq-CASTING-RECEIPT-c2136-full.json`
- **\u4e0b\u6ce2 runner** = `cph4/fleet/idle-guard-kit/kfpb_probe_c2139.py`\uff08\u5df2\u9884\u6302\uff0c\u5e72\u8dd1\u5168\u7eff\uff09

## \u8f66\u9053\u5757

| \u8f66\u9053 | \u72b6\u6001 |
|---|---|
| M1 dev-tick | \u672c\u73ed\uff08C2139\uff09 |
| M2 \u96f7\u8fbe | \u4e0a\u6b21 09:52\uff0810-20\uff09 |
| M4 \u653f\u7b56 | \u65e0\u65b0\u4ef6 |
| M5 \u5ba1\u8ba1 | \u4e0a\u6b21 10-20 \u65e9\u73ed |
| M6 \u7acb\u9879 | \u65e0\u65b0\u4ef6 |

## \u5f00\u53d1\u5757\uff08WIP\uff09

- \u4e3b\u7ebf = **\u661f\u6674 MV\uff08mv-album-001-jay\uff09**\uff1aA \u5305 33 \u5355\u5143\u5df2\u88c5\u914d + \u54cd\u5ea6\u6bcd\u7248 + origin \u590d\u6838\u95ed\u73af\uff1b**\u5973\u4e3b\u8138\u5df2\u5b9a\u76d8**\uff1bB \u5305 6 \u5e27\u5f85\u70b9\u706b\u8bd5\u6784\u56fe\u3002
- \u5176\u4f59\u6b3e\uff08G22/G25/G03/G06\u2026\uff09= \u89c2\u5bdf\u4f4d\uff0c\u672c\u8f6e\u96f6\u52a8\u4f5c\u3002

## \u8d44\u4ea7\u53f0\u8d26

| \u57df | \u6001 | \u8bf4\u660e |
|---|---|---|
| \u7b56\u5212 | A | \u661f\u6674 39 \u5e27\u4e2d A33 \u5168\u843d\u5730\uff0cB6 \u89c4\u683c\u5df2\u5b9a\u5e76\u5df2\u9884\u6302 runner |
| \u4ee3\u7801 | B | \u65e0 blocked\uff1bA \u5305\u88c5\u914d\u7d22\u5f15 v2 \u4e0e\u6837\u7247 v2 \u5747\u8fc7\u95f8 |
| QA | A | \u9009\u89d2\u4e09\u95e8\u7981\u5168\u8fc7\uff1b\u6b63\u6863\u5206\u8f6e CASTING-FULL-END 12/12 + \u5e27\u7ea7 QC 12/12 \u96f6\u6dd8\u6c70 |
| \u7f8e\u672f | B | \u6b63\u5178\u8138\u4e09\u5f20\u5c31\u4f4d\uff1bB \u5305 6 \u5e27\u672a\u4ea7 |
| \u97f3\u9891 | A | \u672c\u66f2 259.4s \u6bcd\u5e26\u5728\u76d8\uff1b\u6837\u7247\u5df2\u8fc7 loudnorm |

## \u8d28\u91cf\u5757

- \u95f8 = CASTING-FULL-END 12/12 \u00b7 lint \u96f6\u547d\u4e2d \u00b7 \u79cd\u5b50\u552f\u4e00 12/12 \u00b7 \u5e27\u7ea7 QC 12/12 \u65e0\u6dd8\u6c70\u7ea7\u7f3a\u9677
- \u4e0b\u6ce2 runner \u4e09\u95f8\u5e72\u8dd1\u5168\u7eff\uff1alint 6/6\u3001\u79cd\u5b50\u552f\u4e00 6/6\u3001\u8bcd\u6570 60-125\uff08<200\uff09
- \u9057\u7559\uff1a\u4e0a\u8f6e\u53f0\u8d26\u63a7\u5236\u53f0\u663e\u793a mojibake = \u663e\u793a\u9762\u975e\u5b57\u8282\u9762\uff08B1449 \u5224\u4f8b\uff09\uff0c\u672c\u8f6e\u4e0d\u4fee

## \u95ee\u9898\u6e05\u5355

- **(\u9ec4)** KF-PACK-B 6 \u5e27\u8bd5\u6784\u56fe\u5f85 IdleGuard \u70b9\u706b \u2192 \u5bfc\u6f14\u5e2d\u770b\u62fc\u677f\u622a\u7968\u79fb \u2192 \u5347 1344\u00d7768 \u6b63\u6863
- **(\u84dd)** \u673a\u5668\u95e8\uff1a\u65e0

## \u989d\u5ea6\u4e0e\u5de5\u5177

- GPU\uff1a\u6ce2\u5df2\u6536\u5b8c\u91ca\u653e\uff1bComfyUI 0.36.0 \u5728\u73ed\u5f85\u4e0b\u4e00\u6ce2
- \u4e91\u7aef token\uff1a\u672c\u8f6e\u96f6\u6d88\u8017\uff08\u5168\u672c\u5730\uff09
- \u5907\u8d27\u6c60\uff1abm-c-gpu-bank jobs=46 \u00b7 pending=1\uff08`kf-packb-probe-c2139`\uff09\u00b7 claimed=0

## \u4e0b\u8f6e\u9009\u7ebf

1. \u70b9\u706b `kf-packb-probe-c2139`\uff086 \u5e27 672\u00d7384\uff09\u2192 \u62fc\u677f\u4eba\u773c\u62bd\u68c0\u6784\u56fe\u6f02\u79fb
2. \u8fc7\u95f8 \u2192 1344\u00d7768 \u6b63\u6863\u4e0a\u9501\u516d\u5e27\uff08\u540c\u79cd\u5b50\u540c\u63d0\u793a\u8bcd\uff09
3. A+B \u5408\u88c5\u8986\u76d6\u5168\u66f2\uff08\u73b0 A \u5305 196.14s / \u8868 238s / \u66f2 259.4s\uff09
4. \u5386\u53f2\u5feb\u7167\uff08vC1998\u2013vC2137\uff09\u5728 git \u91cc\u53ef\u6eaf\uff0c\u672c\u6587\u4ef6\u81ea vC2139 \u8d77\u53ea\u7559\u5f53\u524d\u6001
""".format(snap=SNAP)
t = SNAPDOC + ".tmp"
io.open(t, "w", encoding="utf-8", newline="").write(snap)
os.replace(t, SNAPDOC)
print("SNAP-OK", SNAP)

# ---------------- 4. kanban row ----------------
k = io.open(KANBAN, encoding="utf-8").read()
kn = ("| C | 2026-10-20 | **C2139 \u661f\u6674\u5973\u4e3b\u5b9a\u8138\u95ed\u73af + KF-PACK-B \u9884\u6302**"
      "\uff0809:42-10:0x tick\u00b7\u53f7\u6c60 C2139\uff09\uff1a"
      "**\u6b63\u5728\u5e72**=`kf-packb-probe-c2139` \u5df2\u9884\u6302\u5f85\u70b9\u706b\uff086 \u5e27 672\u00d7384 \u8bd5\u6784\u56fe\uff09\uff1b"
      "**\u6700\u8fd1\u4ea4\u4ed8**=\u6b63\u6863 12/12 \u5168\u6536\u5272\uff08CASTING-FULL-END ok=12\uff0c\u5e27\u7ea7 QC 12/12 \u96f6\u6dd8\u6c70\uff09+\u5224\u8bfb\u4ef6 "
      "`xq-CASTING-VERDICT-c2136-full.md`\uff08B \u578b\u4e3a\u6b63\u5178 s578950/s514974\uff0cA \u578b s439906 \u5907\u9009\uff09\uff1b"
      "**\u4e0b\u4e00\u6b65**=\u70b9\u706b\u8bd5\u6784\u56fe\u2192\u62fc\u677f\u62bd\u68c0\u21921344\u00d7768 \u6b63\u6863\u4e0a\u9501\u516d\u5e27\u2192A+B \u5408\u88c5\uff1b"
      "**\u81ea\u6291**=\u672c\u73ed\u672a\u58f0\u79f0\u6210\u54c1\uff0cB \u5305\u516d\u5e27\u5c1a\u672a\u70b9\u706b |\n")
idx = k.find("| C | ")
if idx < 0:
    raise SystemExit("KANBAN-C-ROW-SEARCH-FAIL")
k2 = k[:idx] + kn + k[idx:]
tmpk = KANBAN + ".tmp"
io.open(tmpk, "w", encoding="utf-8", newline="").write(k2)
os.replace(tmpk, KANBAN)
print("KANBAN-OK delta=%d" % (len(k2) - len(k)))
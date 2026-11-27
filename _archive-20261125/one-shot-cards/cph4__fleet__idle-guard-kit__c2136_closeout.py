# -*- coding: utf-8 -*-
# c2136_closeout.py -- state surgery + tick-ledger rows + kanban row for round C2136.
import io
import json
import os
import time

ROOT = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(ROOT, "state-c.json")
LEDGER = os.path.join(ROOT, ".codely-cli", "engine-tick", "tick-ledger.txt")
KANBAN = os.path.join(ROOT, "Design", "configs", "GLOBAL", "\u6863\u6848", "\u673a\u961f\u534f\u4f5c\u770b\u677f.md")

SNAP = "tick-20261020-0852@c2136-casting-board"
TS = time.strftime("%Y-%m-%d %H:%M:%S")
NOW = time.strftime("%Y-%m-%d %H:%M")

# ---------------- state surgery (indent=1 family, BOM preserved) ----------------
raw = io.open(STATE, encoding="utf-8-sig").read()
d = json.loads(raw)
d["current_snapshot_id"] = SNAP
d["current_snapshot"] = SNAP
d["last_round"] = {
    "ts": TS,
    "result": (
        "C2136 M1 round: Xingqing female-lead casting candidate board (the blocker for KF-PACK-B, "
        "whose 6 face-dependent frames hold the whole second half of the film). (1) PRODUCT: "
        "media/MV/mv0001/xingqing/xq-casting-c2136/ - 16 composition frames (4 hair types x dusk/night "
        "x 2 seeds, 672x384, Krea2 turbo, male jman LoRA deliberately omitted for a female face). "
        "Contact board xq-CASTING-BOARD-c2136.jpg. (2) DEFECT CAUGHT AT THE BIRTH STATION: the v1 "
        "read scored bone age 14-17 (role is ~19) and waxy night skin, so a fix pass went out in the "
        "same round - age block raised to woman of 19-20 / first-year university student with a "
        "defined jawline, night light switched to practical lamp with grain in the shadows, plus a "
        "gravel-voiced 'soft rounded cheeks' typo fix on type A. v2 board: A 8.0 / B 8.0 / C 7.5 / "
        "D 6.5, four types still cleanly separable, no celebrity match on either pass (casting gate "
        "3 of 3 passed), era look passed. (3) BANK: closed the stuck 'claimed' v2 origin-verify job "
        "from its runner receipt (ORIGIN-VERIFY-V2-END ok=1) instead of re-running it, and pre-stowed "
        "casting-ab-full-c2136 (A/B at 1344x768, 3 seeds per light) so the bank is never empty."),
    "build_ok": True,
}
d["last_round_changes_count"] = 9
d["next_round_at"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 12 * 60))
tmp = STATE + ".tmp"
io.open(tmp, "w", encoding="utf-8-sig", newline="").write(json.dumps(d, ensure_ascii=False, indent=1))
os.replace(tmp, STATE)
chk = json.loads(io.open(STATE, encoding="utf-8-sig").read())
assert chk["current_snapshot_id"] == chk["current_snapshot"] == SNAP, "double anchor mismatch"
print("STATE-OK", chk["current_snapshot_id"], chk["last_round"]["build_ok"])

# ---------------- tick-ledger rows ----------------
rows = [
    "%s | Step0 \u5b8c\u6210 | preflight \u5168 PASS \u96f6 FLAG\uff1bLOCK 1m=\u672c\u73ed\u81ea\u6301\uff1bRAM 15.5%%<40%% NOT-GREEN-IDLE\uff1bGPU free 9.5G verdict=GPU_DRAFT_OK"
    % NOW,
    "%s | Step1-2 \u5b8c\u6210 | \u5728\u7ba1\u4e3b\u7ebf=\u661f\u6674 MV\uff1aA \u5305 33 \u5355\u5143\u88c5\u914d+\u54cd\u5ea6\u6bcd\u7248+origin \u590d\u6838\u5df2\u95ed\u73af\uff1bB \u5305 6 \u5e27\u5361\u5b9a\u8138=\u672c\u8f6e\u5934\u53f7\u524d\u7f6e\u4ef6"
    % NOW,
    "%s | Step5 \u5b8c\u6210 | \u5b9e\u4f53\u4ea7\u51fa\uff1a\u9009\u89d2\u5019\u9009\u5e27 16/16\uff08CASTING-END ok=16\uff09+ \u4fee\u6b63\u7248 8/8\uff08CASTING-V2-END ok=8\uff09\uff1b\u4e24\u5f20\u63a5\u89e6\u677f 326,558B / 148,025B"
    % NOW,
    "%s | Step5 \u5b8c\u6210 | \u81ea\u6293\u7f3a\u9677\uff1av1 \u9aa8\u76f8 14-17 \u5c81+\u591c\u573a\u8721\u611f \u2192 \u540c\u7ad9\u4fee\u6b63\uff08v2 \u5e74\u9f84 19-21\u3001\u9897\u7c92\u56de\u5f52\uff09\uff1bD \u578b\u4ecd\u504f\u5c0f\u3001B \u578b\u591c\u683c\u5218\u6d77\u4e22\u5931\u5df2\u5165\u4e0b\u4e00\u6b65\u6e05\u5355"
    % NOW,
    "%s | Step6 \u5b8c\u6210 | state \u53cc\u951a\u540c\u503c %s\uff08indent=1 \u8c31\u7cfb\u3001BOM \u4fdd\u7559\u3001\u5199\u540e json.loads \u590d\u9a8c\uff09+ \u5feb\u7167 vC2136 \u91cd\u5199\u81f3\u5f53\u524d\u6001"
    % (NOW, SNAP),
    "%s | Step7 \u5b8c\u6210 | \u4ea7\u54c1\u4ef6+\u56de\u6267+\u5224\u8bfb\u4ef6+bank \u624b\u672f+state+\u5feb\u7167+\u53f0\u8d26+\u770b\u677f \u540c\u6279\u6536\u53e3\uff1bFluxGroup pathspec + MiniGame pathspec + FleetPush machine/C"
    % NOW,
    "%s | TICK_DONE C2136 | \u661f\u6674\u5973\u4e3b\u9009\u89d2\u5019\u9009\u677f\uff0816+8 \u5e27\u4e24\u7248\uff09\u8fc7\u9009\u89d2\u4e09\u95e8\u7981 | \u95f8=CASTING ok=16/16 \u00b7 V2 ok=8/8 \u00b7 \u53cd\u5411\u6d4b\u8bd5\u96f6\u649e\u8138 | build_ok=True"
    % NOW,
]
led = io.open(LEDGER, "rb").read()
eol = b"\r\n" if led.endswith(b"\r\n") else b"\n"
if not led.endswith(b"\n"):
    led += eol
block = "".join(r + "\n" for r in rows).encode("utf-8")
io.open(LEDGER, "wb").write(led + block)
tail = io.open(LEDGER, encoding="utf-8", errors="replace").read().splitlines()[-1]
print("LEDGER-OK rows=%d tail_has_done=%s" % (len(rows), "TICK_DONE" in tail))

# ---------------- kanban row (prepend to the machine C block) ----------------
k = io.open(KANBAN, encoding="utf-8").read()
kn = ("| C | 2026-10-20 | **C2136 \u661f\u6674\u5973\u4e3b\u9009\u89d2\u5019\u9009\u677f\u00b7\u5b9a\u8138\u524d\u7f6e\u4ef6\u4ea4\u4ed8**"
      "\uff0808:31-08:52 \u4ea4\u4e92\u7a97 tick\u00b7\u53f7\u6c60 C2136@08:37:27\u00b7GPU 24 \u683c\u71c3\u70e7\u96f6\u5931\u8d25\uff09\uff1a"
      "**\u6b63\u5728\u5e72**=\u65e0\uff08\u672c\u8f6e\u5df2\u6536\u53e3\uff09\uff1b"
      "**\u6700\u8fd1\u4ea4\u4ed8**=`cph4/fleet/mv-album-001-jay/xq-CASTING-BOARD-c2136.jpg`\uff08v1 4\u00d74\uff09+ "
      "`xq-CASTING-BOARD-c2136-v2.jpg`\uff08\u4fee\u6b63\u7248 4\u00d72\uff09+ 24 \u5f20 672\u00d7384 \u539f\u56fe + "
      "\u4e24\u4efd\u53ef\u590d\u73b0\u56de\u6267 + \u5224\u8bfb\u4ef6 `xq-CASTING-READ-c2136.md`\uff1b\u95f8=CASTING-END ok=16/16\u00b7"
      "V2-END ok=8/8\u00b7\u53cd\u5411\u6d4b\u8bd5\u96f6\u649e\u8138\uff08\u9009\u89d2\u4e09\u95e8\u7981\u5168\u8fc7\uff09\uff1b"
      "**\u4e0b\u4e00\u6b65**=\u5bfc\u6f14\u5e2d\u4ece A(8.0)/B(8.0) \u53cc\u7ebf\u9009\u578b \u2192 \u9884\u6302\u4f5c\u4e1a "
      "`casting-ab-full-c2136`\uff081344\u00d7768\u00d73\u79cd\u5b50\uff09\u2192 \u9501 ID \u5757 \u2192 `KF-PACK-B` 6 \u5e27\uff1b"
      "**\u81ea\u6293\u7f3a\u9677**=v1 \u9aa8\u76f8 14-17 \u2192 \u540c\u7ad9\u4fee\u6b63\u4e3a 19-21\uff0c\u9057\u7559 D \u578b\u504f\u5c0f/B \u578b\u591c\u683c\u5218\u6d77\u4e22\u5931\u5df2\u5165\u4e0b\u4e00\u6b65\u6e05\u5355 |\n")
idx = k.find("| C | ")
if idx < 0:
    raise SystemExit("KANBAN-C-ROW-SEARCH-FAIL")
k2 = k[:idx] + kn + k[idx:]
tmpk = KANBAN + ".tmp"
io.open(tmpk, "w", encoding="utf-8", newline="").write(k2)
os.replace(tmpk, KANBAN)
print("KANBAN-OK inserted_at=%d delta=%d" % (idx, len(k2) - len(k)))
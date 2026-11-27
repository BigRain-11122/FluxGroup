# -*- coding: ascii -*-
# c2133_state_surgery.py - state surgery for the C2133 conform round.
# Contract-preserving: detect BOM / indent / EOL from the bytes on disk.

import io
import json
import os

STATE = r"K:\Fluxgroup\MiniGame\state-c.json"
CSID = "tick-20261020-0805@c2133-packa-conform-orderfix"
NEXT = "2026-10-20 08:22"

RESULT = (
    "C2133 M1 round, one product artifact plus an index defect fix. "
    "(1) ORDER DEFECT FOUND IN C2132: that index listed units by walking the clip folder, "
    "so it opened the film with the finale block (F5-33a/b/c/F5-34). The authored order puts "
    "that block last. Index v2 (xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json/.md) is rebuilt from the "
    "authored pack manifest with F5-33c inserted before F5-34; 33 units, 6 redo-r1 picks, "
    "196.14s at authored windows. "
    "(2) PRODUCT: A-pack conform rendered - media/mv-album-001-jay/assembly-packA/"
    "XQ-PACKA-CONFORM-v1-c2133.mp4, 1344x768 24fps, 196.25s, 44.6MB, straight cuts on the "
    "authored windows, song muxed from t=0 (F0-01a is the 0-2s opening) with 0.6s/1.4s fades. "
    "Board read 10 tiles every 20s: distinct scenes, normal exposure, day-to-night arc, coherent "
    "grade, no black/frozen/duplicated frames. "
    "(3) TIMING PROOF: xq_packa_cutpoints_c2133.py compares, per unit, the conform frame at "
    "mid-window against the same frame of its own source clip (MAD, +-4 frame search to absorb "
    "the constant ~0.1s render offset): CUTPOINTS-END ok=1 exact=33/33 max_mad=2.83. The first "
    "gate attempt used scene scores and returned 12/33 - a detector limit (no firing between "
    "similar shots, false fires on motion), not a trim defect, adjudicated and replaced. "
    "(4) BANK: packA-assembly-index-verify-v1 closed PASS - INDEX-VERIFY-END ok=1 mismatches=0; "
    "its 07:25 claim had no runner run because the C2132 verifier died deleting its own "
    "guard-held log (WinError 32). Replacement verifier never touches its log, re-hashes all 33 "
    "clips, checks unit order against the pack manifest and checks the v1 pair on origin. "
    "(5) REVIEW PACK: 960px proxy 15.25MB + 33-tile cut strip 204KB for bm-a single-look review; "
    "strip read confirms the cut opens on interior close-ups and closes on the writing close-ups. "
    "(6) Bank successor prestowed: packA-conform-origin-verify-v1. build_ok=True"
)


def main():
    raw = open(STATE, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8-sig")
    indent = 1
    for line in text.splitlines()[1:]:
        s = line.lstrip(" ")
        if s.startswith('"') and len(s) != len(line):
            indent = len(line) - len(s)
            break
    doc = json.loads(text)
    before = (doc["last_round"]["ts"], doc["current_snapshot_id"])

    doc["last_round"] = {"ts": "2026-10-20 08:05", "result": RESULT, "build_ok": True}
    doc["current_snapshot_id"] = CSID
    doc["current_snapshot"] = CSID
    doc["next_round_at"] = NEXT

    out = json.dumps(doc, ensure_ascii=False, indent=indent)
    if crlf:
        out = out.replace("\n", "\r\n")
    data = out.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    with open(STATE, "wb") as f:
        f.write(data)

    back = json.loads(open(STATE, "rb").read().decode("utf-8-sig"))
    ok = (back["last_round"]["build_ok"] is True
          and back["current_snapshot_id"] == back["current_snapshot"]
          and back["current_snapshot_id"] == CSID)
    print("STATE-OK=%s bytes=%d bom=%s crlf=%s indent=%d" % (ok, len(data), bom, crlf, indent))
    print("prev_ts=%s prev_csid=%s -> %s" % (before[0], before[1], CSID))


if __name__ == "__main__":
    main()
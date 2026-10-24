# -*- coding: utf-8 -*-
"""C2201 closeout: state-c.json surgery + snapshot-c CEO lines + tick ledger.

Pointers only (no schema churn). Snapshot is rewritten in place with the same
UTF-8 / LF shape the previous round wrote.
"""
import io
import json
import os
import datetime

STATE = r"K:\Fluxgroup\MiniGame\state-c.json"
SNAP = r"K:\Fluxgroup\MiniGame\自动化快照-c.md"
LEDGER = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\tick-ledger.txt"

TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
SNAP_ID = "tick-%s@C2201" % datetime.datetime.now().strftime("%Y%m%d-%H%M")

RESULT = (
    "C2201: the KN16 window is now clean at the source instead of patched, and the KN film is "
    "re-cut as v5. The round opened on an in-flight 768P re-burn (fired by the crashed 21:11 tick) "
    "whose prompt held the moon glow close to the disc; harvested at 21:48 (1851s, ok=1). Measured "
    "against the take v4 used, the concentric ring energy collapsed: radial bump mean 4.04 -> 0.98 "
    "(-76%), max 18.9 -> 4.15, halo saturation 0.405 -> 0.131, ring coverage 0.00-0.12 of the sky "
    "band. That re-burn paid with a new prior - thin near-vertical rain streaks over the whole sky - "
    "so a native-resolution pass (horizontal median baseline width 9 plus a 25-row vertical "
    "coherence mask) removes only pixels that are brighter than both horizontal neighbours and part "
    "of a sustained column: streak pixels 41,664 -> 2,426 (-94%) at t=9.0s, 21,695 -> 445 at t=2.0s, "
    "whole-frame luma 56.9 -> 55.4. Stars, cloud lobes, the moon disc and the grain survive; the "
    "first attempt ran the detector on a 4x downscale and missed exactly the thinnest lines, which "
    "is why the native pass exists. The KN02 caption strip the crashed round had already cropped is "
    "verified gone (bottom-band pixels above 205: 0, peak 192.8). Film re-encoded as v5 with the new "
    "KN16: 41 windows, 239.042s, 5737 frames, audio copied; kn_film_gate --tag v5-C2201 = PASS with "
    "0 duplicate pairs and luma floor 20.22. DIRECTOR-REVIEW-KN-FILM-v5-C2201.md is written as a "
    "production-side PASS recommendation, listing the two items left to the director seat (KN18/KN17 "
    "same-source proximity, faint green flare residue under the deck). Every previous take is "
    "archived, nothing deleted."
)

NEXT = (
    "Next batch (C2202): the KN film v5 sits with the director seat - if it signs PASS, publish the "
    "CEO review link; if REVISE, work only the named item. Two prepared options stay staged in the "
    "assembler: folding KN18's 9s into KN17/KN19, and a second green-flare pass. Standing law "
    "unchanged: no further starfield close-up burns at 768P. G25 SortIt's T001c wave is still staged "
    "but RAM-gated (machine free RAM sat at 1-4% all round because the BigMoney CPU lane is saturated)."
)


def append_ledger(lines):
    raw = io.open(LEDGER, "rb").read()
    eol = b"\r\n" if b"\r\n" in raw else b"\n"
    add = b"".join(l.encode("utf-8") + eol for l in lines)
    if not raw.endswith(b"\n"):
        add = eol + add
    with io.open(LEDGER, "ab") as fh:
        fh.write(add)


def write_snapshot():
    text = io.open(SNAP, encoding="utf-8").read()
    lines = text.splitlines()
    lines[0] = ("# Automated snapshot - machine C, vC2201 - %s - product round: KN16 fixed at the "
                "source (re-burn + native streak pass), film v5 encoded and gated PASS" % TS)
    out = []
    for ln in lines:
        if ln.startswith("- **本轮时间**"):
            ln = ("- **本轮时间**：%s（tick C2201 收口，快照 id %s，normal_iteration）" % (TS, SNAP_ID))
        elif ln.startswith("- **Step0**"):
            ln = ("- **Step0**：Step0Preflight 全 PASS（state 108.9KB / 无 lane-inbox / 无 CEO-DESK / "
                  "无 redline / 无 merge / 无 claims / push-lag 0）；INFO=NOT-GREEN-IDLE（RAM 1-4%，"
                  "BigMoney CPU 道满载）/ 外来 meta 14 / matrix_open 16 / 上一班 21:11 超时被判 NO_DONE")
        elif ln.startswith("- M1 态"):
            ln = ("- M1 态：本班 C2201 产品轮，KN 全片 v5 已出（239.042s / 5737 帧 / 门 PASS），"
                  "KN16 改为源头重烧 + 原生分辨率去雨丝，KN02 伪字幕条复核已净。")
        elif ln.startswith("- **Current**"):
            ln = ("- **Current**：KN16 两代先验（同心光环 + 雨丝）都清掉了，做法是重烧一次 + 两道结构修正，"
                  "没有第三次生成；全片 v5 门 PASS，待导演席签字。")
        elif ln.startswith("- **Latest artefact**"):
            ln = ("- **Latest artefact**："
                  "`K:\\Fluxgroup\\FluxGroup\\media\\mv-album-001-jay\\assembly-packA-KN\\KN-FULL-v1-C2201.mp4`"
                  "（239.042s，89.4MB，gate PASS）+ "
                  "`...\\qc-boards\\KN16-C2200-COMPARE.jpg`（旧 take vs 重烧 take 对照）+ "
                  "`...\\qc-boards\\KN16-STREAK-C2200B.jpg`（雨丝处理前后）+ "
                  "`...\\cph4\\fleet\\mv-album-001-jay\\DIRECTOR-REVIEW-KN-FILM-v5-C2201.md`")
        elif ln.startswith("- **Next milestone**"):
            ln = ("- **Next milestone**：导演席对 v5 签 PASS/REVISE -> 若 PASS 出 CEO 呈审地址"
                  "（窗 <= 24h）；未签则按批复改。")
        out.append(ln)
    with io.open(SNAP, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")


def main():
    with io.open(STATE, encoding="utf-8") as fh:
        st = json.load(fh)
    st["current_snapshot_id"] = SNAP_ID
    st["current_snapshot"] = {"id": SNAP_ID, "ts": TS, "batch": "C2201"}
    st["last_round"] = {"ts": TS, "result": RESULT, "build_ok": True}
    st["next_round"] = NEXT
    st["next_round_at"] = "2026-10-24 23:08"
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, ensure_ascii=False, indent=1)
    write_snapshot()
    append_ledger([
        "[%s] [Step0 done] C2201: inherited a live 768P re-burn from the 21:11 tick (which died at the "
        "25-minute silence guard). Preflight all PASS; INFO = NOT-GREEN-IDLE (RAM 1.3-4%%), foreign-guid "
        "metas 14, matrix_open 16, 21:11 round marked NO_DONE_SUSPECT_CRASH." % TS,
        "[%s] [Step1-5 done] C2201: harvested the KN16 re-burn (1851s, ok=1) and measured it against the "
        "take v4 used: radial bump 4.04 -> 0.98 (-76%%), max 18.9 -> 4.15, halo chroma 0.405 -> 0.131, ring "
        "coverage 0.00-0.12. The re-burn brought a rain-streak prior, so a native pass removes only thin "
        "vertically coherent lines (streak px 41,664 -> 2,426, luma 56.9 -> 55.4); the first detector ran on "
        "a 4x downscale and missed the thinnest lines, hence the native weights. KN02 caption strip verified "
        "gone (0 pixels above 205 in the bottom band). Film re-encoded v5: 41 windows, 239.042s, 5737 frames, "
        "audio copied; gate PASS (0 duplicate pairs, luma floor 20.22)." % TS,
        "[%s] [Step6-7 done] C2201: state last_round/next_round rewritten, snapshot-c CEO lines refreshed, "
        "director review v5 written, all previous takes archived, ledger written." % TS,
        "2026-10-24 22:58 TICK_DONE C2201 | product round | batch C2201 | film v5 at 239.042s passes the "
        "machine gate with the KN16 halo and rain streaks gone at the source; next = director signature on "
        "v5, then the CEO link; no further starfield close-up burns at 768P",
    ])
    print("closeout written")


if __name__ == "__main__":
    main()


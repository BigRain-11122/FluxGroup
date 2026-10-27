"""C2197 closeout: wave flag, state, snapshot and ledger for the keyframe-repair round.

The round did not just re-burn: it found the root of three RED takes in the
keyframe layer, rebuilt the keyframe deterministically as a crop of the proven
KN17 plate, measured it, and only then spent GPU time.
"""

import io
import json
import os
import sys
import time

MG = r"K:\Fluxgroup\MiniGame"
HQ = r"K:\Fluxgroup\FluxGroup"
MEDIA = os.path.join(HQ, "media", "mv-album-001-jay")
SNAP = os.path.join(MG, "\u81ea\u52a8\u5316\u5feb\u7167-c.md")
STATE = os.path.join(MG, "state-c.json")
LEDGER = os.path.join(MG, ".codely-cli", "engine-tick", "tick-ledger.txt")
FLAGS = [
    os.path.join(MG, ".codely-cli", "engine-tick", "wave-harvest-pending.json"),
    os.path.join(HQ, ".codely-cli", "engine-tick", "wave-harvest-pending.json"),
]

BATCH = "C2197"
PROMPT_ID = "6df0c06a-dac9-4909-b66e-276d45c04a61"
NOW = time.strftime("%Y-%m-%d %H:%M")

FLAG_PAYLOAD = {
    "batch": BATCH,
    "project": "mv-album-001-jay / KN18 iteration-7 768P from the KN17 crop plate",
    "fired_at": NOW,
    "what": ("Four RED takes traced back to the keyframe layer. The generated KN18 keyframes could not be aimed "
             "between nearly empty (p99 19-22) and milky bright (89, then 145), so KN18's keyframe is now a real "
             "crop into the proven KN17 star band (median 23, p99 38, irregular natural stars, checked by eye at "
             "1:1) and iteration-7 was fired from it at 768P as ComfyUI prompt " + PROMPT_ID + " (seed 336717)."),
    "verdict_paths": [
        "media/mv-album-001-jay/logs/kn18-prod-c2197.log",
        "media/mv-album-001-jay/logs/kn18-prod-c2197.json",
        "media/mv-album-001-jay/qc-boards/KN18-PROD-C2197.jpg",
        "media/mv-album-001-jay/logs/kn18-kf-crop-c2197.json",
        "media/mv-album-001-jay/clips-red/KN_G6-KN18-c2192-768p-red.mp4",
        "media/mv-album-001-jay/clips-red/KN_G6-KN18-c2194-768p-red.mp4",
        "media/mv-album-001-jay/clips-red/KN_G7-KN18-c2196-768p-red.mp4",
    ],
    "harvest_round_task": (
        "0) the three earlier RED takes are archived in clips-red/ - do not re-screen them. "
        "1) adopt the iteration-7 render (clips-local-768/KN_G8-KN18.mp4, or the watcher verdict "
        "logs/kn18-prod-c2197.json) and screen it: p99 <= 47 at t=1.5/5.0/9.0s plus a 1:1 native strip, and this "
        "time also check that the field stays irregular - no lattice rows, no vertical striations, no molten blobs. "
        "2) green -> promote to clips-local-768/KN_A-KN18.mp4, encode the film with kn_full_assembly_c2183.py "
        "--encode --batch C2198, then kn_film_gate.py --tag v3-C2198. 3) red -> stop burning: put all four takes "
        "in front of the director seat and pick between reusing the KN17 plate outright for this beat (accepting "
        "the near-repeat 9s earlier) and cutting the beat with a retime. 4) director pass on the whole film, "
        "including the multi-ring halo around the moon at 108.9-109.1s. 5) delete this file once harvested."),
    "prior": ("iteration-4 dense close-up RED 26/79/69; iteration-5 sparse close-up RED 27/80/74; iteration-6 "
              "dust-haze RED 126/143/155. KN17 wide GREEN 32/31/32. Keyframe audit: generated KN18 keyframes p99 "
              "19 / 22 / 89 / 145 against the KN17 plate's 37 - the keyframe was the variable all along."),
}

STATE_RESULT = (
    "C2197: all three KN18 attempts were screened and the failure was traced to the keyframe layer instead of the "
    "wording. iteration-5 (sparse starfield close-up) came back RED at p99 27/80/74, no better than the 26/79/69 "
    "of the dense wording, and iteration-6 (dust haze with no point lights) came back far worse at 126/143/155 - "
    "the board shows molten gold cells rather than dust. The measurements explain all three: the generated KN18 "
    "keyframes cannot be aimed between nearly empty (p99 19, then 22) and milky bright (89, then 145), while the "
    "sibling KN17 plate holds the right field at median 18 / p99 37 and cleared 768P at 32/31/32. Star density, "
    "the 'evenly' vocabulary and the dust wording were each ruled out in turn. So the keyframe was rebuilt "
    "deterministically rather than generated again: a real crop into the KN17 band, re-grained, measured at "
    "median 23 / p99 38 and checked by eye at 1:1 (irregular natural stars, faint milky band, no lattice), which "
    "also makes the two breathing shots continuous in the cut. iteration-7 was then fired at 768P from that plate "
    "as prompt 6df0c06a. All three red takes were archived to clips-red/, so the production dir holds no red clip."
)

STATE_NEXT = (
    "Harvest the iteration-7 KN18 render (ComfyUI prompt %s, fired 19:05, ~25min class) via "
    "c2197_kn18_watch_harvest.py: p99 <= 47 at 1.5/5.0/9.0s plus a 1:1 strip, and check the field stays irregular "
    "(no lattice rows, no vertical striations, no molten blobs). Green -> promote to clips-local-768/KN_A-KN18.mp4, "
    "encode the film with kn_full_assembly_c2183.py --encode --batch C2198, then kn_film_gate.py --tag v3-C2198. "
    "Red -> stop burning and escalate all four takes to the director seat: reuse the KN17 plate for this beat, or "
    "cut the beat with a retime. Director pass on the whole film once KN18 lands, with the multi-ring halo around "
    "the moon at 108.9-109.1s still on note." % PROMPT_ID
)

LEDGER_LINES = [
    "[%s] [Step0 done] C2197: continuation round off the C2196 product batch - the iteration-6 render landed RED "
    "at 18:48 (p99 126/143/155) and its board reads as molten gold cells, so the batch continued with the keyframe "
    "layer as the suspect." % NOW,
    "[%s] [Step1-5 done] C2197: root cause found and fixed at the right layer. Two generated keyframes were tried "
    "first: one with a denser dust style (p99 89, too milky) and one with a dark base under dense points (p99 145, "
    "worse) - the generator cannot be aimed between nearly empty and milky bright for this shot, while the KN17 "
    "plate sits at median 18 / p99 37 and cleared 768P. So the keyframe is now a deterministic crop into the KN17 "
    "band (c2197_kn18_kf_crop.py: median 23, p99 38, re-grained, verified by eye at 1:1 for irregular stars and no "
    "lattice), which also makes the two breathing shots continuous. iteration-7 fired at 768P from that plate "
    "(prompt 6df0c06a, seed 336717) with a watcher attached, and all three red takes moved to clips-red/." % NOW,
    "[%s] [Step6-7 done] C2197: product round closeout - wave flag retargeted at iteration-7 in both repos, state "
    "last_round/next_round rewritten with the keyframe finding, snapshot CEO lines refreshed, ledger written." % NOW,
    "%s TICK_DONE C2197 | product round | batch C2197 | next = harvest iteration-7 (p99<=47 + 1:1 irregularity) "
    "-> promote -> film via --batch C2198 -> kn_film_gate -> director pass; a fifth wording iteration is off the "
    "table, the fallback is a director decision on the four takes" % NOW,
]


def patch_state():
    with io.open(STATE, encoding="utf-8") as fh:
        st = json.load(fh)
    st["last_round"] = {"ts": NOW, "result": STATE_RESULT, "build_ok": True}
    st["next_round"] = STATE_NEXT
    st["current_snapshot_id"] = "tick-%s@%s" % (time.strftime("%Y%m%d-%H%M"), BATCH)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("state patched")


def patch_snapshot():
    with io.open(SNAP, encoding="utf-8", newline="") as fh:
        lines = fh.read().split("\n")
    header = ("# Automated snapshot - machine C, v%s - %s - product round: KN18 RED traced to the keyframe layer, "
              "keyframe rebuilt as a KN17 crop, iteration-7 burning" % (BATCH, NOW))
    step0 = ("- **Step0**: continuation of the C2196 round; the iteration-6 render had already landed RED "
             "(p99 126/143/155, molten gold cells) so the batch continued with the keyframe as the suspect. "
             "INFO=NOT-GREEN-IDLE / foreign meta 14 / matrix_open 16.")
    active = ("- **Current**: KN18 iteration-7 768P burn (prompt 6df0c06a, from the cropped KN17 plate, seed "
              "336717) rendering; watcher c2197_kn18_watch_harvest.py attached; three red takes archived.")
    latest = ("- **Latest artefact**: `K:\\Fluxgroup\\FluxGroup\\media\\mv-album-001-jay\\frames\\KN_KN18.png` "
              "(the rebuilt keyframe: median 23 / p99 38, irregular stars verified at 1:1) + "
              "`...\\logs\\kn18-kf-crop-c2197.json` + `...\\qc-boards\\KN18-PROD-C2196.jpg` (the molten-gold read) + "
              "`...\\clips-red\\` (three red takes, all out of the production dir).")
    nxt = ("- **Next milestone**: iteration-7 green -> KN_A-KN18 promoted -> film via `--batch C2198` -> "
           "kn_film_gate -> director pass -> CEO link (window <= 24h).")
    rules = [("- **Step0**", step0), ("- **Current**", active),
             ("- **Latest artefact**", latest), ("- **Next milestone**", nxt)]
    for pref, repl in rules:
        for i, ln in enumerate(lines):
            if ln.startswith(pref):
                lines[i] = repl
                break
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            lines[i] = header
            break
    with io.open(SNAP, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines))
    print("snapshot patched")


def append_ledger():
    with io.open(LEDGER, "rb") as fh:
        raw = fh.read()
    eol = b"\r\n" if raw.count(b"\r\n") > raw.count(b"\n") / 2 else b"\n"
    if not raw.endswith(b"\n"):
        raw += eol
    block = b"".join(line.encode("utf-8") + eol for line in LEDGER_LINES)
    with io.open(LEDGER, "wb") as fh:
        fh.write(raw + block)
    print("ledger appended", len(LEDGER_LINES))


def main():
    for f in FLAGS:
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with io.open(f, "w", encoding="ascii") as fh:
            json.dump(FLAG_PAYLOAD, fh, indent=1, ensure_ascii=True)
    print("flags written:", len(FLAGS))
    patch_state()
    patch_snapshot()
    append_ledger()
    return 0


if __name__ == "__main__":
    sys.exit(main())
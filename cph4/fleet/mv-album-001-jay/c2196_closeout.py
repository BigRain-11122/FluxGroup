"""C2196 closeout: archive the RED take, retarget the wave flag at iteration-6,
and record the product round in state, snapshot and tick ledger.

Why a file and not an inline -c: the payload is Chinese-heavy and PowerShell
quoting mangles it (B611). Every write is explicit and LF-preserving.
"""

import io
import json
import os
import shutil
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

BATCH = "C2196"
PROMPT_ID = "9241c92a-fd8f-4b35-a593-0203bc342c9d"
NOW = time.strftime("%Y-%m-%d %H:%M")
RED_SRC = os.path.join(MEDIA, "clips-local-768", "KN_G6-KN18.mp4")
RED_DST = os.path.join(MEDIA, "clips-red", "KN_G6-KN18-c2194-768p-red.mp4")

FLAG_PAYLOAD = {
    "batch": BATCH,
    "project": "mv-album-001-jay / KN18 iteration-6 768P burn (dust-haze close-up, no point lights)",
    "fired_at": NOW,
    "what": ("iteration-5 came back RED (p99 27/80/74 vs threshold 47, no better than the 26/79/69 of the dense "
             "wording), so the shot itself was re-specified rather than re-worded: a close-up of drifting warm dust "
             "with no point lights at all, same window and same role in the cut. Submitted as ComfyUI prompt "
             + PROMPT_ID + " at 18:25; the manifest id changed (KN_G6 -> KN_G7) so the derived seed moved to "
             "567074 - wording and seed both moved, but the two earlier burns already isolated the variable as "
             "the shot spec, not the vocabulary."),
    "verdict_paths": [
        "media/mv-album-001-jay/logs/kn18-prod-c2196.log",
        "media/mv-album-001-jay/logs/kn18-prod-c2196.json",
        "media/mv-album-001-jay/qc-boards/KN18-PROD-C2196.jpg",
        "media/mv-album-001-jay/logs/kn-keyframe-glow-c2195.json",
        "media/mv-album-001-jay/clips-red/KN_G6-KN18-c2194-768p-red.mp4",
    ],
    "harvest_round_task": (
        "0) the two earlier RED takes are already archived to clips-red/ - do not re-screen them. "
        "1) adopt the iteration-6 render by disk (clips-local-768/KN_G7-KN18.mp4) or via the watcher's verdict "
        "logs/kn18-prod-c2196.json, and screen it: p99 <= 47 at t=1.5/5.0/9.0s plus a 1:1 native strip, no lattice "
        "of glowing points, no vertical striations. 2) green -> promote to clips-local-768/KN_A-KN18.mp4, encode "
        "the film with kn_full_assembly_c2183.py --encode --batch C2197, run kn_film_gate.py --tag v4-C2197. "
        "3) red -> the starfield close-up is structurally dead on this model; escalate to the director seat with "
        "the three takes and choose: keep the wide KN17 recipe for both galaxy beats, or cut the beat and retime. "
        "4) director pass on the whole film, incl. the multi-ring halo around the moon at 108.9-109.1s. "
        "5) delete this file once harvested."),
    "prior": ("iteration-4 dense close-up RED 26/79/69; iteration-5 sparse close-up RED 27/80/74; sibling KN17 wide "
              "GREEN 32/31/32 on the same workflow. Keyframe audit: KN_KN18.png p99 19 / med 16 (nearly empty) vs "
              "KN_KN17.png p99 37 / med 18."),
}

STATE_RESULT = (
    "C2196: the iteration-5 KN18 render was harvested and screened RED - p99 27/80/74 against a threshold of 47, "
    "no better than the 26/79/69 of the previous dense wording - and the harvest was taken by the "
    "session-independent watcher instead of a CLI child, so it survived the round ending. The decisive work was "
    "measurement rather than another guess: the sibling KN17 is green at 32/31/32 as an extreme wide on the same "
    "workflow, and a keyframe glow audit showed KN_KN18.png is nearly empty (p99 19 / median 16) where "
    "KN_KN17.png already holds its field (p99 37 / median 18). Combined with the RED board reading as a regular "
    "lattice of glowing amber lamps with vertical streaks, that says an empty sky plus point-light vocabulary "
    "makes the model tile the frame - star density and the 'evenly' vocabulary were both ruled out. So iteration-6 "
    "re-specifies the shot instead of the sentence: a close-up of drifting warm dust with no point lights, same "
    "window and same job in the cut, burned at 768P with prompt 9241c92a. The RED take was archived out of the "
    "production dir to clips-red/KN_G6-KN18-c2194-768p-red.mp4 and the empty production slot left clear."
)

STATE_NEXT = (
    "Harvest the iteration-6 KN18 render (ComfyUI prompt %s, submitted 18:25, ~25min class under GPU contention) "
    "with c2196_kn18_watch_harvest.py, which screens p99 <= 47 at 1.5/5.0/9.0s plus a 1:1 native strip. Green -> "
    "promote to clips-local-768/KN_A-KN18.mp4, encode film v3/v4 with kn_full_assembly_c2183.py --encode --batch "
    "C2197, then kn_film_gate.py before any director pass. Red -> stop iterating wording: the starfield close-up is "
    "structurally dead on this model at 768P, so the director seat picks between the wide KN17 recipe for both "
    "galaxy beats and cutting the beat with a retime. Director pass on the whole film once KN18 lands, with the "
    "multi-ring halo around the moon at 108.9-109.1s still on note." % PROMPT_ID
)

LEDGER_LINES = [
    "[%s] [Step0 done] C2196: Step0Preflight one FLAG=WAVE-PENDING (C2194 KN18 iteration-5); state parses, no "
    "redline, no claims, no encoding bad rows, no lane inbox." % NOW,
    "[%s] [Step1-5 done] C2196: harvest landed mid-round - the iteration-5 render finished at 18:18:00 (1938862 "
    "bytes, 1455s against a 780s class under a GPU pinned at 100%%) and screened RED at p99 27/80/74 (threshold "
    "47), i.e. the sparse wording did not move the failure at all. Instead of a third blind re-word, measured the "
    "keyframes: KN_KN18.png is p99 19 / median 16 (nearly empty) against KN_KN17.png p99 37 / median 18, and KN17 "
    "is green at 32/31/32 as an extreme wide on the same workflow - so the variable is a point-light close-up over "
    "an empty keyframe, which the model tiles into a lattice of glowing lamps with vertical streaks. Re-specified "
    "the shot as drifting warm dust with no point lights (same window, same job in the cut) and fired 768P "
    "iteration-6 as prompt 9241c92a, then attached a cloned watcher for it. Archived the RED take out of the "
    "production dir to clips-red/KN_G6-KN18-c2194-768p-red.mp4." % NOW,
    "[%s] [Step6-7 done] C2196: product round closeout - wave flag retargeted at iteration-6 in both repos, state "
    "last_round/next_round rewritten with the measurement, snapshot three CEO lines refreshed, ledger written." % NOW,
    "%s TICK_DONE C2196 | product round | batch C2196 | next = harvest iteration-6 (p99<=47 + 1:1 strip) -> "
    "promote -> film via --batch C2197 -> kn_film_gate -> director pass; a third wording iteration is now "
    "explicitly off the table" % NOW,
]


def read_text(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def archive_red():
    if not os.path.isfile(RED_SRC):
        print("red take already gone from the production dir")
        return
    first, second = os.path.getsize(RED_SRC), None
    os.makedirs(os.path.dirname(RED_DST), exist_ok=True)
    shutil.move(RED_SRC, RED_DST)
    print("archived red take -> %s (%d bytes)" % (os.path.basename(RED_DST), first))


def write_flags():
    for f in FLAGS:
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with io.open(f, "w", encoding="ascii") as fh:
            json.dump(FLAG_PAYLOAD, fh, indent=1, ensure_ascii=True)
    print("flags written:", len(FLAGS))


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
    lines = read_text(SNAP).split("\n")
    header = ("# Automated snapshot - machine C, v%s - %s - product round: KN18 iteration-5 RED, keyframes "
              "measured, shot re-specified as dust-haze close-up (iteration-6 burning)" % (BATCH, NOW))
    step0 = ("- **Step0**: preflight one FLAG=WAVE-PENDING (iteration-5 KN18 burn in flight); NOTE the burn was "
             "still rendering at 1395s with GPU at 100%%, so the harvest watcher was attached instead of waiting. "
             "INFO=NOT-GREEN-IDLE / foreign meta 14 / matrix_open 16.")
    active = ("- **当前活**: KN18 iteration-6 768P burn (prompt 9241c92a, dust-haze close-up, no point lights) "
              "rendering, watcher c2196_kn18_watch_harvest.py attached.")
    recent = ("- **最近实物**: `K:\\Fluxgroup\\FluxGroup\\media\\mv-album-001-jay\\qc-boards\\KN18-PROD-C2194.jpg` "
              "(the RED lattice read) + `...\\logs\\kn-keyframe-glow-c2195.json` (keyframe audit: KN18 p99 19 vs "
              "KN17 37) + `...\\clips-red\\KN_G6-KN18-c2194-768p-red.mp4` + `cph4\\fleet\\mv-album-001-jay\\"
              "c2195_kn_keyframe_glow.py` / `c2196_kn18_iter6.py`.")
    milestone = ("- **下个里程碑**: iteration-6 green -> KN_A-KN18 promoted -> film via `--batch C2197` -> "
                 "kn_film_gate -> director pass -> CEO link (window <= 24h).")
    out = []
    done = {"header": False, "step0": False, "active": False, "recent": False, "milestone": False}
    for ln in lines:
        if ln.startswith("# ") and not done["header"]:
            out.append(header); done["header"] = True
        elif ln.startswith("- **Step0**") and not done["step0"]:
            out.append(step0); done["step0"] = True
        elif ln.startswith("- **\u5f53\u524d\u6d3b**") and not done["active"]:
            out.append(active); done["active"] = True
        elif ln.startswith("- **\u6700\u8fd1\u5b9e\u7269**") and not done["recent"]:
            out.append(recent); done["recent"] = True
        elif ln.startswith("- **\u4e0b\u4e2a\u91cc\u7a0b\u7891**") and not done["milestone"]:
            out.append(milestone); done["milestone"] = True
        else:
            out.append(ln)
    write_text(SNAP, "\n".join(out))
    print("snapshot replaced", [k for k, v in done.items() if v],
          "missing", [k for k, v in done.items() if not v])


def append_ledger():
    with io.open(LEDGER, "rb") as fh:
        raw = fh.read()
    eol = b"\r\n" if raw.count(b"\r\n") > raw.count(b"\n") / 2 else b"\n"
    if not raw.endswith(b"\n"):
        raw += eol
    block = b"".join(line.encode("utf-8") + eol for line in LEDGER_LINES)
    with io.open(LEDGER, "wb") as fh:
        fh.write(raw + block)
    print("ledger appended", len(LEDGER_LINES), "lines, eol=%r" % eol)


def main():
    archive_red()
    write_flags()
    patch_state()
    patch_snapshot()
    append_ledger()
    return 0


if __name__ == "__main__":
    sys.exit(main())
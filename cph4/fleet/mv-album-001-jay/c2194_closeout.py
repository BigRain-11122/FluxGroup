"""C2194 closeout: wave flag (both copies) + state + snapshot + tick ledger.

Kept as a file rather than an inline -c because the payload is Chinese-heavy and
PowerShell quoting mangles it (B611). All writes are explicit, LF-preserving.
"""

import io
import json
import os
import subprocess
import sys
import time

MG = r"K:\Fluxgroup\MiniGame"
HQ = r"K:\Fluxgroup\FluxGroup"
SNAP = os.path.join(MG, "\u81ea\u52a8\u5316\u5feb\u7167-c.md")
STATE = os.path.join(MG, "state-c.json")
LEDGER = os.path.join(MG, ".codely-cli", "engine-tick", "tick-ledger.txt")
FLAGS = [
    os.path.join(MG, ".codely-cli", "engine-tick", "wave-harvest-pending.json"),
    os.path.join(HQ, ".codely-cli", "engine-tick", "wave-harvest-pending.json"),
]
BATCH = "C2194"
PROMPT_ID = "d0fcc4ca-fb80-4f68-97fa-f829b950585c"
NOW = time.strftime("%Y-%m-%d %H:%M")
STAMP = time.strftime("%Y-%m-%d %H:%M:%S")

FLAG_PAYLOAD = {
    "batch": BATCH,
    "project": "mv-album-001-jay / KN18 iteration-5 768P burn (sparse-field close-up)",
    "fired_at": NOW,
    "what": ("KN18 768P re-burn with prompt v5.0-C2194-sparse-closeup, submitted as ComfyUI "
             "prompt " + PROMPT_ID + " (seed 102675 carried over, so the wording is the only variable). "
             "It sits behind one queued 480P animatic job, then renders ~20min."),
    "verdict_paths": [
        "media/mv-album-001-jay/logs/kn18-prod-c2194.log",
        "media/mv-album-001-jay/logs/kn18-prod-c2194.json",
        "media/mv-album-001-jay/qc-boards/KN18-PROD-C2194.jpg",
        "media/mv-album-001-jay/clips-red/KN_G6-KN18-c2192-768p-red.mp4",
    ],
    "harvest_round_task": (
        "0) the C2192 take is already screened RED and archived to clips-red/ - do not re-screen it. "
        "1) fetch the ComfyUI history for prompt " + PROMPT_ID + " (or adopt by disk once clips-local-768/KN_G6-KN18.mp4 "
        "appears) and screen it: p99 <= 47 at t=1.5/5.0/9.0 plus a 1:1 native sky strip, no ballooned disks, "
        "no vertical striations. 2) green -> copy to clips-local-768/KN_A-KN18.mp4 and run "
        "`python kn_full_assembly_c2183.py --encode --batch C2195`, then `python kn_film_gate.py --film <film> "
        "--index <index> --tag v3-C2195`. 3) red -> iterate the wording again (density down, gaps wider). "
        "4) director pass on the whole film, incl. the multi-ring halo around the moon at 108.9-109.1s. "
        "5) delete this file once harvested."),
    "prior": ("C2192 768P burn = RED, p99 26/79/69 against threshold 47, ballooned disks plus vertical "
              "striations at 1:1, even though the same prompt cleared the 480P probe at 22/25/28. "
              "Sibling KN17 768P is GREEN at 32/31/32. Film v2 passes kn_film_gate (5737 frames, 0 duplicate pairs)."),
}

LEDGER_LINES = [
    "[%s] [Step0 done] %s C2194: preflight one FLAG=WAVE-PENDING (C2192 KN18 768P burn). Found the C2192 driver "
    "process dead with its CLI session while the render had actually finished server-side at 17:50:43 - the "
    "adopt-by-disk path, not the driver, is the truth source." % (STAMP, NOW),
    "[%s] [Step1-5 done] %s C2194 product batch: harvested the C2192 KN18 768P render and screened it RED "
    "(p99 26/79/69 vs threshold 47; ballooned glowing disks plus vertical light striations on the native 1:1 "
    "strip) - a 480P pass does not carry to 768P on a close-up because the same star density subtends far larger. "
    "Archived the red take to clips-red/KN_G6-KN18-c2192-768p-red.mp4 (never leave a red clip in the production "
    "dir) and submitted iteration-5 with prompt v5.0-C2194-sparse-closeup (few hundred well-separated points, "
    "plain flat darkness between them, seed 102675 unchanged so the wording is the only variable). "
    "Built two reusable gates: kn_film_gate.py (exhaustive framemd5 duplicate pairs + per-second luma floor + "
    "window coverage; run on film v2 = PASS, 5737 frames, 0 identical pairs, 41 windows) and "
    "c2194_kn18_watch_harvest.py (session-independent adopt-by-disk harvest). kn_full_assembly_c2183.py gained "
    "--batch so earlier cuts are never overwritten." % (STAMP, NOW),
    "[%s] [Step6-7 done] %s C2194 closeout: wave flag re-pointed at prompt %s (both repo copies), state last_round/"
    "next_round updated, snapshot three CEO lines refreshed, ledger written. Product files in the HQ repo." % (
        STAMP, NOW, PROMPT_ID),
    "%s TICK_DONE %s | product batch | next = harvest the iteration-5 KN18 render (p99 <= 47 + 1:1 strip) -> "
    "promote KN_A-KN18 -> film v3 (--batch C2195) -> kn_film_gate -> director pass" % (NOW, BATCH),
]


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def append_ledger():
    raw = read_text(LEDGER)
    if raw and not raw.endswith("\n"):
        raw += "\n"
    raw += "\n".join(LEDGER_LINES) + "\n"
    write_text(LEDGER, raw)


def patch_state():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        st = json.load(fh)
    st["last_round"] = {
        "ts": NOW,
        "result": (
            "C2194: the C2192 KN18 768P render was harvested and screened RED - p99 26/79/69 against threshold 47, "
            "ballooned glowing disks and vertical light striations on the native 1:1 strip - even though the same "
            "prompt cleared the 480P probe at 22/25/28. That closes the open question: a 480P pass does not carry "
            "to 768P when the shot is a close-up, because the same star density subtends far larger on screen. "
            "The red take was archived to clips-red/KN_G6-KN18-c2192-768p-red.mp4 instead of being left in the "
            "production dir, and iteration-5 was submitted with prompt v5.0-C2194-sparse-closeup (a few hundred "
            "well-separated points with plain flat darkness between them; seed 102675 unchanged so the wording is "
            "the only variable). Two reusable gates were built and one was validated: kn_film_gate.py runs an "
            "exhaustive framemd5 duplicate-pair audit plus a per-second luma floor plus window coverage, and it "
            "returns PASS on film v2 (5737 frames, 0 identical pairs, 41 contiguous windows, luma min 20.2); "
            "c2194_kn18_watch_harvest.py makes the harvest session-independent by adopting the render from disk. "
            "kn_full_assembly_c2183.py gained --batch so earlier cuts stay intact. Also learned: the C2192 burn "
            "driver died with its CLI session while the render survived inside ComfyUI, so process liveness is not "
            "evidence of a failed burn - disk is."),
        "build_ok": True,
    }
    st["next_round"] = (
        "Harvest the iteration-5 KN18 768P render (ComfyUI prompt %s, submitted 17:53, behind one queued 480P "
        "animatic, so expect it ~18:30). Screen p99 <= 47 at 1.5/5.0/9.0 plus a 1:1 native sky strip with no "
        "ballooned disks and no vertical striations. Green -> promote to clips-local-768/KN_A-KN18.mp4, re-encode "
        "the film with kn_full_assembly_c2183.py --encode --batch C2195, then run kn_film_gate.py against the new "
        "cut before any director pass. Red -> iterate the wording again (density down, gaps wider) rather than "
        "re-probing at 480P, which is now known to be a non-predictive gate for this shot. Director re-pass on the "
        "whole film once KN18 lands, with the multi-ring halo around the moon at 108.9-109.1s still on note." % PROMPT_ID
    )
    st["current_snapshot_id"] = "tick-%s@%s" % (time.strftime("%Y%m%d-%H%M"), BATCH)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def patch_snapshot():
    lines = read_text(SNAP).split("\n")
    header = ("# Automated snapshot - machine C, v%s - %s - product round: KN18 768P screened RED and archived, "
              "iteration-5 sparse-field re-burn submitted, film gate built and validated on film v2"
              % (BATCH, NOW))
    step0 = ("- **Step0**: preflight one FLAG=WAVE-PENDING (C2192 KN18 burn); the burn driver died with its CLI "
             "session, the render itself finished server-side at 17:50:43 -> adopt by disk, not by process liveness. "
             "INFO=NOT-GREEN-IDLE / foreign meta 14 / matrix_open 16.")
    active = ("- **Current**: KN18 iteration-5 768P burn rendering (prompt d0fcc4ca, prompt v5.0-C2194 sparse "
              "close-up, seed 102675); the C2192 take is RED and archived out of the production dir.")
    recent = ("- **Latest artefact**: `K:\\Fluxgroup\\FluxGroup\\media\\mv-album-001-jay\\qc-boards\\KN18-PROD-C2194.jpg` "
              "(the RED read: ballooned disks + vertical striations) + `...\\clips-red\\KN_G6-KN18-c2192-768p-red.mp4`; "
              "gate evidence `...\\logs\\kn-film-gate-v2-C2183.json` (film v2 PASS: 5737 frames, 0 duplicate pairs, "
              "41 windows, luma min 20.2); reusable gates `cph4\\fleet\\mv-album-001-jay\\kn_film_gate.py` + "
              "`c2194_kn18_watch_harvest.py`.")
    milestone = ("- **Next milestone**: KN18 green -> KN_A-KN18 promoted -> film v3 (`--batch C2195`) -> kn_film_gate "
                 "-> director pass -> CEO link (window <= 24h).")
    out = []
    done = {"header": False, "step0": False, "active": False, "recent": False, "milestone": False}
    for ln in lines:
        if ln.startswith("# ") and not done["header"]:
            out.append(header)
            done["header"] = True
        elif ln.startswith("- **Step0**") and not done["step0"]:
            out.append(step0)
            done["step0"] = True
        elif ln.startswith("- **\u5f53\u524d\u6d3b**") and not done["active"]:
            out.append(active)
            done["active"] = True
        elif ln.startswith("- **\u6700\u8fd1\u5b9e\u7269**") and not done["recent"]:
            out.append(recent)
            done["recent"] = True
        elif ln.startswith("- **\u4e0b\u4e2a\u91cc\u7a0b\u7891**") and not done["milestone"]:
            out.append(milestone)
            done["milestone"] = True
        else:
            out.append(ln)
    missing = [k for k, v in done.items() if not v]
    write_text(SNAP, "\n".join(out))
    print("snapshot: replaced", [k for k, v in done.items() if v], "missing", missing)


def main():
    for f in FLAGS:
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with io.open(f, "w", encoding="ascii") as fh:
            json.dump(FLAG_PAYLOAD, fh, indent=1, ensure_ascii=True)
    print("flags written:", len(FLAGS))
    patch_state()
    print("state patched")
    patch_snapshot()
    append_ledger()
    print("ledger appended:", len(LEDGER_LINES), "lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
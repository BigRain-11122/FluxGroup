"""C2198 closeout: the KN18 beat is resolved, the film is re-encoded and gated, so
the wave flag is emptied (harvest complete) rather than re-pointed.
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

BATCH = "C2198"
NOW = time.strftime("%Y-%m-%d %H:%M")

RESULT = (
    "C2198: the KN18 beat is resolved without a sixth burn. The fifth attempt (iteration-7, from the rebuilt KN17 "
    "crop plate) was also RED - p99 93/106/134 - and its board showed uniform, growing bokeh disks, which closes "
    "the diagnosis: a dense star field cannot survive a 768P close-up on this model, and the plate was never the "
    "remaining variable. Instead of another generation the beat is now film language: a 1.45x tight reframe of the "
    "green KN17 768P take with a slow lateral drift and re-seeded grain (c2198_kn18_punchin.py), which measured "
    "p99 34/35/39 against KN17's 30.3 YAVG and passed the 1:1 check as irregular points rather than disks. The "
    "film was re-encoded as v3 in 41 windows (239.042s / 5737 frames / audio 239.03s) and kn_film_gate returns "
    "PASS: 0 duplicate pairs, luma floor 20.22, full window coverage. A junction board was cut at 117.00 -> 117.60s "
    "and the wide-to-tight cut holds brightness and tone, so the beat now reads as one continuous sky instead of "
    "a repeat. The director review for v3 is written and it is REVISE on exactly one item: KN16's moon at "
    "108.9-109.1s still carries a full rainbow multi-ring halo that reads as a lens-flare effect rather than a "
    "2000s film halo. All five red takes and both keyframe trials are archived, so no red clip remains in the "
    "production dir."
)

NEXT = (
    "Next batch (C2199): fix KN16's moon halo - regenerate that plate so the halo is a single soft warm-white "
    "bloom with two or three fading rings and no rainbow separation (or push the moon smaller and let the cloud "
    "deck carry the beat), re-burn its 768P take, re-encode the film via kn_full_assembly_c2183.py --batch C2199, "
    "re-run kn_film_gate, then ask the director seat to sign v4. The KN18 finding is settled and must not be "
    "re-litigated: no further starfield close-up burns at 768P."
)

LEDGER_LINES = [
    "[%s] [Step0 done] C2198: continuation of the KN18 batch after the iteration-7 render landed RED at 19:29 "
    "(p99 93/106/134, uniform growing bokeh disks)." % NOW,
    "[%s] [Step1-5 done] C2198: closed the KN18 question by changing medium instead of wording - a 1.45x tight "
    "reframe of the green KN17 768P take with a slow lateral drift and re-seeded grain (p99 34/35/39, YAVG 33.3 "
    "vs KN17 30.3, 1:1 check clean), then re-encoded the film as v3 (41 windows, 239.042s, 5737 frames) and ran "
    "kn_film_gate -> PASS (0 duplicate pairs, luma floor 20.22). Cut a junction board 117.00 -> 117.60s: the "
    "wide-to-tight cut holds brightness and tone. Wrote DIRECTOR-REVIEW-KN-FILM-v3-C2198.md = REVISE on one item "
    "(KN16 moon rainbow halo at 108.9-109.1s)." % NOW,
    "[%s] [Step6-7 done] C2198: harvest complete, so the wave flag is emptied in both repos instead of re-pointed; "
    "state last_round/next_round rewritten, snapshot CEO lines refreshed, ledger written." % NOW,
    "%s TICK_DONE C2198 | product round | batch C2198 | film v3 exists and passes the machine gate; next = KN16 "
    "moon halo fix in C2199 then director signature on v4" % NOW,
]


def drop_flags():
    n = 0
    for f in FLAGS:
        if os.path.isfile(f):
            os.remove(f)
            n += 1
    print("flags removed:", n)


def patch_state():
    with io.open(STATE, encoding="utf-8") as fh:
        st = json.load(fh)
    st["last_round"] = {"ts": NOW, "result": RESULT, "build_ok": True}
    st["next_round"] = NEXT
    st["current_snapshot_id"] = "tick-%s@%s" % (time.strftime("%Y%m%d-%H%M"), BATCH)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("state patched")


def patch_snapshot():
    with io.open(SNAP, encoding="utf-8", newline="") as fh:
        lines = fh.read().split("\n")
    header = ("# Automated snapshot - machine C, v%s - %s - product round: KN18 resolved by reframing the KN17 "
              "take, film v3 encoded and gated PASS, director review = REVISE on the KN16 moon halo"
              % (BATCH, NOW))
    step0 = ("- **Step0**: continuation after the iteration-7 KN18 render landed RED at 19:29 (uniform bokeh "
             "disks). INFO=NOT-GREEN-IDLE / foreign meta 14 / matrix_open 16.")
    active = ("- **Current**: KN18 beat closed (no further burns); film v3 encoded and gated PASS; the only open "
              "defect is KN16's rainbow moon halo, queued for C2199.")
    latest = ("- **Latest artefact**: `K:\\Fluxgroup\\FluxGroup\\media\\mv-album-001-jay\\assembly-packA-KN\\"
              "KN-FULL-v1-C2198.mp4` (film v3, 239.042s, PASS) + `...\\qc-boards\\KN-FILM-v3-C2198-JUNCTION.jpg` "
              "(the 117s wide-to-tight cut) + `...\\cph4\\fleet\\mv-album-001-jay\\DIRECTOR-REVIEW-KN-FILM-v3-C2198.md` "
              "(REVISE, one item).")
    nxt = ("- **Next milestone**: KN16 halo fix -> re-burn that unit -> film v4 -> gate -> director signature -> "
           "CEO link (window <= 24h).")
    for pref, repl in [("- **Step0**", step0), ("- **Current**", active),
                       ("- **Latest artefact**", latest), ("- **Next milestone**", nxt)]:
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
    drop_flags()
    patch_state()
    patch_snapshot()
    append_ledger()
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""Per-cycle pseudo-text guard for the KN 768P wave (batch C2170, zero GPU).

Runs as a work-bank job between burns.  Every cycle it scans every landed
KN_A-*.mp4 for the subtitle-band pseudo-text class found on KN02 (a generated
caption strip that the eye-based sample gate missed), so a defective unit is
flagged the moment it lands instead of after all 30 have burned.

Writes media/mv-album-001-jay/evidence-c2170/pseudotext-guard.json and appends
one summary line to that directory's guard log.  Never kills a burn: the halt
decision stays with the round that reads the verdict.

Halt guidance encoded in the output:
  landed >= 5 and suspects >= 2  -> HALT-RECOMMENDED (>=40% defect rate)
  landed >= 9 and suspects >= 3  -> HALT-RECOMMENDED (>=33% defect rate)
"""
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ALBUM = os.path.join(os.path.dirname(HERE), "mv-album-001-jay")
if ALBUM not in sys.path:
    sys.path.insert(0, ALBUM)
import kn_pseudotext_probe as PTP

REPO = r"K:\Fluxgroup\FluxGroup"
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768")
EVID = os.path.join(REPO, "media", "mv-album-001-jay", "evidence-c2170")
OUT = os.path.join(EVID, "pseudotext-guard.json")
LOGF = os.path.join(EVID, "pseudotext-guard.log")


def main():
    os.makedirs(EVID, exist_ok=True)
    clips = sorted(glob.glob(os.path.join(CLIPS, "KN_A-*.mp4")))
    rows = []
    for c in clips:
        try:
            rows.append(PTP.scan(c, step=6))
        except Exception as exc:                       # never break the cycle
            rows.append({"clip": os.path.basename(c), "verdict": "ERROR",
                         "error": repr(exc)[:200]})
    landed = len(rows)
    suspects = [r for r in rows if r["verdict"] == "SUSPECT"]
    n = len(suspects)
    halt = (landed >= 5 and n >= 2) or (landed >= 9 and n >= 3)
    payload = {
        "batch": "C2170",
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "landed": landed,
        "suspect": n,
        "halt_recommended": halt,
        "halting_units": [r["clip"] for r in suspects],
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    line = ("[%s] landed=%d suspect=%d halt=%s %s\n"
            % (payload["ts"], landed, n, "YES" if halt else "no",
               ",".join(payload["halting_units"]) or "-"))
    with open(LOGF, "a", encoding="utf-8") as f:
        f.write(line)
    print("PSEUDO-GUARD-END landed=%d suspect=%d halt=%s -> %s"
          % (landed, n, "YES" if halt else "no", OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
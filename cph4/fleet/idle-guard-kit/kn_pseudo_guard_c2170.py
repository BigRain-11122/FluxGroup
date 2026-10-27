"""Per-cycle birth gate for the KN 768P wave (C2170 pseudo-text + C2171 framing drift).

Runs as a work-bank job between burns, zero GPU.  Every cycle it scans every landed
KN_A-*.mp4 for two defect classes that the eye-based sample gate missed:

  1. pseudo-text  (C2170): a generated caption strip in the bottom band.  KN02.
  2. framing drift (C2171): the rendered camera move contradicts the authored one.
     KN02 was authored as a locked-off tripod frame but pushed in to 1.8x by 5.0 s,
     so it cannot cut with the rooftop block.  The probe reads the declared move out
     of the i2v prompt and judges the rendered zoom against it:
       locked -> zoom must stay <= 1.15x
       push   -> zoom must reach >= 1.10x
       mobile / pull -> not judged (translation and widening are not measurable by a
                        centre-crop search; 12 of 30 units are locked, so the class
                        that matters is covered)

Writes evidence-c2170/pseudotext-guard.json (both faces, one row per landed unit) and
appends one summary line to the guard log.  Never kills a burn: the halt decision
stays with the round that reads the verdict.

Halt guidance encoded in the output (any face counts as a defect):
  landed >= 5 and defects >= 2  -> HALT-RECOMMENDED (>=40% defect rate)
  landed >= 9 and defects >= 3  -> HALT-RECOMMENDED (>=33% defect rate)
"""
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ALBUM = os.path.join(os.path.dirname(HERE), "mv-album-001-jay")
LOCAL_I2V = os.path.join(ALBUM, "local-i2v")
for p in (ALBUM, LOCAL_I2V):
    if p not in sys.path:
        sys.path.insert(0, p)
import kn_pseudotext_probe as PTP
import kn_framing_drift_probe as FDP

REPO = r"K:\Fluxgroup\FluxGroup"
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768")
EVID = os.path.join(REPO, "media", "mv-album-001-jay", "evidence-c2170")
OUT = os.path.join(EVID, "pseudotext-guard.json")
LOGF = os.path.join(EVID, "pseudotext-guard.log")
MANIFEST = os.path.join(LOCAL_I2V, "run-bmc-kn-i2v.json")


def load_intents():
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            man = json.load(fh)
        return {u["shot"]: FDP.camera_intent(u.get("i2v_prompt", ""))
                for u in man.get("units", [])}
    except Exception:
        return {}


def main():
    os.makedirs(EVID, exist_ok=True)
    intents = load_intents()
    clips = sorted(glob.glob(os.path.join(CLIPS, "KN_A-*.mp4")))
    rows = []
    for c in clips:
        shot = os.path.basename(c).split("-")[-1].replace(".mp4", "")
        intent = intents.get(shot, "unclassified")
        try:
            row = PTP.scan(c, step=6)
        except Exception as exc:                       # never break the cycle
            row = {"clip": os.path.basename(c), "verdict": "ERROR", "error": repr(exc)[:200]}
        row["intent"] = intent
        row["framing"] = "-"
        try:
            fr = FDP.probe(c, intent)
            row["framing"] = fr.get("verdict", "-")
            row["max_zoom"] = fr.get("max_zoom")
            row["max_zoom_at_sec"] = fr.get("max_zoom_at_sec")
        except Exception as exc:
            row["framing"] = "ERROR"
            row["framing_error"] = repr(exc)[:160]
        rows.append(row)
    landed = len(rows)
    suspect = [r for r in rows if r.get("verdict") == "SUSPECT"]
    drift = [r for r in rows if r.get("framing") in ("DRIFT", "FLAT")]
    flagged = sorted({r["clip"] for r in suspect} | {r["clip"] for r in drift})
    n = len(flagged)
    halt = (landed >= 5 and n >= 2) or (landed >= 9 and n >= 3)
    payload = {
        "batch": "C2171",
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "faces": ["pseudotext", "framing-drift"],
        "landed": landed,
        "suspect": len(suspect),
        "framing_drift": len(drift),
        "defects": n,
        "halt_recommended": halt,
        "halting_units": flagged,
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    line = ("[%s] landed=%d pseudo=%d framing=%d defects=%d halt=%s %s\n"
            % (payload["ts"], landed, len(suspect), len(drift), n,
               "YES" if halt else "no", ",".join(flagged) or "-"))
    with open(LOGF, "a", encoding="utf-8") as f:
        f.write(line)
    print("BIRTH-GATE-END landed=%d pseudo=%d framing=%d defects=%d halt=%s -> %s"
          % (landed, len(suspect), len(drift), n, "YES" if halt else "no", OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
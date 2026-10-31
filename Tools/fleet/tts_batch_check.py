# -*- coding: utf-8 -*-
"""tts_batch_check.py - prove a TTS batch actually produced audio, from any box.

Why: on 2026-10-31 a claim (Q-TTS-1202R) sat in RUNNING for two hours with no lane
report and no receipt, and nobody could tell "still encoding" apart from "the claim
died on pickup". The card's deliverable is a directory on another machine, so the
master cannot check it. This probe runs on the owning box and turns the directory
into evidence: file count, bytes, newest mtime, and a verdict.

Usage:
  python Tools/fleet/tts_batch_check.py --dir C:/.../r1202_ep001_060 \
      --out cph4/fleet/queue-receipts/Q-TTS-1202R-bm-b-verify.md [--expect 57]

Exit code 0 = evidence written; 1 = directory missing (nothing to judge).
"""
import argparse
import json
import os
import time
from datetime import datetime

AUDIO_EXT = (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus")
WRITE_SETTLE_S = 300  # a batch that wrote nothing for 5 min is not encoding


def scan(directory):
    files, total, newest = [], 0, 0.0
    for root, _dirs, names in os.walk(directory):
        for n in names:
            if not n.lower().endswith(AUDIO_EXT):
                continue
            p = os.path.join(root, n)
            try:
                st = os.stat(p)
            except OSError:
                continue
            files.append(os.path.relpath(p, directory))
            total += st.st_size
            newest = max(newest, st.st_mtime)
    return files, total, newest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect", type=int, default=0)
    a = ap.parse_args()

    d = a.dir
    if not os.path.isdir(d):
        print("[tts-check] MISSING %s" % d)
        return 1

    files, total, newest = scan(d)
    age_min = round((time.time() - newest) / 60.0, 1) if newest else None
    dir_mtime = os.path.getmtime(d)
    dir_age_min = round((time.time() - dir_mtime) / 60.0, 1)

    if not files:
        verdict = "EMPTY - no audio produced"
    elif a.expect and len(files) < a.expect:
        verdict = "PARTIAL %d/%d" % (len(files), a.expect)
    elif age_min is not None and age_min <= WRITE_SETTLE_S / 60.0:
        verdict = "BURNING - newest file written %.1f min ago" % age_min
    else:
        verdict = "COMPLETE-STOPPED - newest file is %.1f min old" % (age_min or -1)

    rows = [
        "# TTS batch evidence - %s" % d,
        "",
        "checked_at = %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "host = %s" % os.environ.get("COMPUTERNAME", "?"),
        "audio_files = %d%s" % (len(files), (" (expected %d)" % a.expect) if a.expect else ""),
        "bytes = %d (%.1f MB)" % (total, total / 1e6),
        "newest_write_age_min = %s" % age_min,
        "dir_write_age_min = %s" % dir_age_min,
        "verdict = %s" % verdict,
        "",
        "## first 10 files",
    ]
    rows += ["- " + f for f in sorted(files)[:10]]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")

    print(json.dumps({"dir": d, "files": len(files), "bytes": total,
                      "newest_age_min": age_min, "verdict": verdict,
                      "out": a.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
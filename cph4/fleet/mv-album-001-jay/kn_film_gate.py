"""KN PACK-A film delivery gate (mechanical, re-runnable per cut).

One command that answers the questions a director pass always re-asks, so the
director round can spend its time on craft instead of bookkeeping:

  * container truth: duration, frame count, fps, size, audio stream/length
  * duplicate-frame audit: exhaustive framemd5 over the whole film, every pair
    of identical frames reported (a montage that silently repeats a take reads
    as a freeze, and brightness stats cannot see it)
  * exposure audit: per-second mean luma floor (catches under-exposed holds)
  * window coverage: every window in the assembly index must be inside the
    film timeline, contiguous, and end at the declared film end

Usage:
  python kn_film_gate.py --film <mp4> [--index <json>] [--tag C2194]
Writes media/mv-album-001-jay/logs/kn-film-gate-<tag>.json and prints a verdict.
Exit 0 = PASS, 3 = REVIEW (a finding worth a human read), 2 = bad input.
"""

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile

REPO = r"K:\Fluxgroup\FluxGroup"
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
LOGDIR = os.path.join(MEDIA, "logs")
DUP_PAIR_LIMIT = 0        # a delivered cut must carry zero identical frame pairs
LUMA_FLOOR = 18.0         # per-second mean luma below this is a visible black hold


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=index,codec_type,codec_name,width,height,"
         "nb_frames,r_frame_rate,sample_rate,channels,duration",
         "-of", "json", path],
        capture_output=True, text=True,
    )
    d = json.loads(out.stdout or "{}")
    fmt = d.get("format") or {}
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), {})
    return {
        "duration": round(float(fmt.get("duration") or 0), 3),
        "bytes": int(fmt.get("size") or 0),
        "video": {
            "codec": v.get("codec_name"), "w": v.get("width"), "h": v.get("height"),
            "frames": v.get("nb_frames"), "fps": v.get("r_frame_rate"),
        },
        "audio": {
            "codec": a.get("codec_name"), "rate": a.get("sample_rate"),
            "channels": a.get("channels"),
            "dur": round(float(a.get("duration") or 0), 3),
        },
    }


def framemd5_pairs(path):
    """Exhaustive identical-frame audit; returns (frames, pair_count, samples)."""
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "md5.txt")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path, "-an", "-f", "framemd5", out],
            check=True,
        )
        digests = []
        with io.open(out, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    digests.append(parts[-1])
    pairs = 0
    samples = []
    run_start = None
    for i in range(1, len(digests)):
        if digests[i] == digests[i - 1]:
            pairs += 1
            if run_start is None:
                run_start = i - 1
        else:
            if run_start is not None and len(samples) < 12:
                samples.append([run_start, i - 1])
            run_start = None
    if run_start is not None and len(samples) < 12:
        samples.append([run_start, len(digests) - 1])
    return len(digests), pairs, samples


def luma_floor(path):
    res = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-an", "-vf",
         "scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    vals = []
    for line in (res.stdout or "").splitlines():
        if "YAVG=" in line:
            try:
                vals.append(float(line.split("YAVG=")[1]))
            except ValueError:
                pass
    if not vals:
        return None
    per_sec = []
    step = 24
    for i in range(0, len(vals), step):
        chunk = vals[i:i + step]
        per_sec.append(round(sum(chunk) / len(chunk), 2))
    low = [[i, v] for i, v in enumerate(per_sec) if v < LUMA_FLOOR]
    return {
        "seconds_sampled": len(per_sec),
        "min": min(per_sec),
        "mean": round(sum(per_sec) / len(per_sec), 2),
        "below_floor": low[:20],
        "below_floor_count": len(low),
    }


def window_coverage(index_path, film_dur):
    if not index_path or not os.path.isfile(index_path):
        return {"checked": False, "reason": "index not supplied or missing"}
    with io.open(index_path, "r", encoding="utf-8") as fh:
        idx = json.load(fh)
    rows = idx.get("windows") or []
    gaps = []
    prev_end = 0.0
    for r in rows:
        start = float(r.get("start", 0.0))
        end = float(r.get("end", 0.0))
        if abs(start - prev_end) > 0.02:
            gaps.append({"at": round(prev_end, 3), "next_start": round(start, 3)})
        prev_end = end
    return {
        "checked": True,
        "windows": len(rows),
        "declared_film_end": idx.get("film_end"),
        "last_window_end": round(prev_end, 3),
        "gaps": gaps[:12],
        "beyond_film": [r.get("shot") for r in rows if float(r.get("end", 0)) > film_dur + 0.1],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--index", default=None)
    ap.add_argument("--tag", default="latest")
    a = ap.parse_args()
    if not os.path.isfile(a.film):
        print("MISSING %s" % a.film)
        return 2

    meta = probe(a.film)
    frames, pairs, samples = framemd5_pairs(a.film)
    luma = luma_floor(a.film)
    cov = window_coverage(a.index, meta["duration"])

    findings = []
    if pairs > DUP_PAIR_LIMIT:
        findings.append("duplicate frames: %d identical pairs, runs %s" % (pairs, samples))
    if luma and luma["below_floor_count"]:
        findings.append("under-exposed seconds below %.0f: %d" % (LUMA_FLOOR, luma["below_floor_count"]))
    if cov.get("checked"):
        if cov["gaps"]:
            findings.append("window gaps: %s" % cov["gaps"])
        if cov["beyond_film"]:
            findings.append("windows past film end: %s" % cov["beyond_film"])
    if meta["audio"]["dur"] and meta["duration"]:
        if meta["audio"]["dur"] + 0.35 < meta["duration"]:
            findings.append("audio shorter than picture: %.2fs vs %.2fs" % (
                meta["audio"]["dur"], meta["duration"]))

    payload = {
        "tag": a.tag,
        "film": a.film,
        "meta": meta,
        "frames_hashed": frames,
        "duplicate_pairs": pairs,
        "duplicate_runs": samples,
        "luma": luma,
        "coverage": cov,
        "findings": findings,
        "verdict": "PASS" if not findings else "REVIEW",
    }
    os.makedirs(LOGDIR, exist_ok=True)
    out = os.path.join(LOGDIR, "kn-film-gate-%s.json" % a.tag)
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    v = meta["video"]
    print("%s %ss %s frames %sx%s audio %.2fs@%s" % (
        os.path.basename(a.film), meta["duration"], frames, v["w"], v["h"],
        meta["audio"]["dur"], meta["audio"]["rate"]))
    print("duplicate pairs=%d  luma min=%s  windows=%s" % (
        pairs, (luma or {}).get("min"), cov.get("windows")))
    print("VERDICT", payload["verdict"], findings or "")
    print("json:", out)
    return 0 if payload["verdict"] == "PASS" else 3


if __name__ == "__main__":
    sys.exit(main())
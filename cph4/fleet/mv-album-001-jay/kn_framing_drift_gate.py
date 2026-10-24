"""Camera-intent vs rendered-zoom gate for i2v clips (zero GPU).

Why this file exists
--------------------
C2171 wrote the rule and produced verdicts for KN01-KN17; C2176 laid those
verdicts next to the landed frames.  The producer itself was never committed, so
the gate could not be re-run on the units landing afterwards, and a gate without
a producer silently stops being applied exactly when the wave grows.

This script ports the rule into a tracked, re-runnable file, and it changes the
measurement, because the C2171 method does not survive a re-run: a centre-crop
match against frame 0 only fits when the content stands still.  These shots move,
so every sample matches best at 1.00x and the one non-trivial reading (KN17 at
2.30x) comes from the empty-sky tail, i.e. it measures noise, not camera travel.

Measurement used here
---------------------
Fourier-Mellin / log-polar phase correlation between frame 0 and each sampled
frame.  The magnitude spectrum is invariant to translation, so subject movement
does not enter; a zoom shows up as a shift along the log-radius axis:

    frame -> grey -> centre square -> windowed FFT magnitude
          -> log-polar sample -> phase correlation vs frame 0 -> log scale

Per-sample peaks are kept for audit.  Isolated spikes (estimator failure on a
low-texture frame) are removed with a median-of-5 over time, and a gross outlier
outside +-0.25 marks the clip "unstable" rather than quietly flattening it.

Verdicts (thresholds unchanged from C2171)
------------------------------------------
    locked  <=1.15x  -> PASS      >1.15x -> FLAT (camera drifted off its lock)
    push    >=1.10x  -> PASS      decisive flat -> FLAT (declared move not rendered)
    push    in between, or unstable series -> UNDECIDED (goes to the eye board)
    pull / mobile    -> NOT-JUDGED (a pull is the same number read backwards,
                                    lateral travel is not a zoom)

UNDECIDED is deliberate: the estimator's noise floor is a few percent on
content-heavy shots, so calling those FLAT would manufacture false positives at
the same rate the old gate missed real ones.

Usage
-----
    python kn_framing_drift_gate.py --clip <path.mp4>
    python kn_framing_drift_gate.py --scan-dir <dir> --manifest <manifest.json>
    python kn_framing_drift_gate.py --scan-dir <dir> --manifest <m.json> \
        --regress <prior-evidence.json> --out <out.json>

Exit code 0 = no FLAT and (with --regress) no verdict mismatch, 1 otherwise.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

import numpy as np

SAMPLE_FPS = 2.0
SQ = 512                    # centre square used for the spectrum
NR = 160                    # log-radius bins
NT = 180                    # angular bins
RMIN, RMAX = 8.0, SQ * 0.45
PEAK_MIN = 0.02             # below this the correlation is meaningless
OUTLIER = 0.25              # deviation from 1.0 that means the estimator failed
MED_WIDTH = 5               # median filter over time, kills isolated spikes
LOCKED_TOL = 1.15
PUSH_MIN = 1.10
PUSH_FLAT_MAX = 1.03        # a decisive "did not move" for a declared push
MIN_FRAMES = 4

INTENT_PATTERNS = (
    ("locked", ("locked-off tripod", "holds a locked")),
    ("pull", ("eases back",)),
    ("push", ("eases in",)),
    ("mobile", ("travels alongside", "slides laterally", "pans ", "tilts up",
                "cranes down", "rises with it")),
)


def intent_of_prompt(prompt):
    """Declared intent, read from the camera sentence of the shot's own prompt."""
    m = re.search(r"(camera[^.]*\.)", prompt or "")
    sentence = (m.group(1) if m else prompt or "").lower()
    for name, keys in INTENT_PATTERNS:
        if any(k in sentence for k in keys):
            return name
    return "unknown"


def probe_meta(clip):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration", "-of", "json", clip],
        capture_output=True, text=True)
    d = json.loads(out.stdout)
    st = d["streams"][0]
    return int(st["width"]), int(st["height"]), float(d["format"]["duration"])


def sample_frames(clip, w, h):
    cmd = ["ffmpeg", "-v", "error", "-i", clip, "-vf", "fps=%g,format=gray" % SAMPLE_FPS,
           "-vsync", "0", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = w * h
    frames = []
    try:
        while True:
            buf = proc.stdout.read(size)
            if not buf or len(buf) < size:
                break
            frames.append(np.frombuffer(buf, dtype=np.uint8).reshape(h, w))
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()
    return frames


_WIN = np.outer(np.hanning(SQ), np.hanning(SQ)).astype(np.float32)
_LOGR = np.linspace(np.log(RMIN), np.log(RMAX), NR)
_TH = np.linspace(0, np.pi, NT, endpoint=False)
_R, _T = np.meshgrid(_LOGR, _TH, indexing="ij")
_YS = np.clip((SQ // 2 + np.exp(_R) * np.sin(_T)).astype(int), 0, SQ - 1)
_XS = np.clip((SQ // 2 + np.exp(_R) * np.cos(_T)).astype(int), 0, SQ - 1)


def logpolar(img):
    """Translation-invariant spectrum fingerprint of one frame."""
    h, w = img.shape
    y0, x0 = (h - SQ) // 2, (w - SQ) // 2
    a = img[y0:y0 + SQ, x0:x0 + SQ].astype(np.float32)
    mag = np.abs(np.fft.fftshift(np.fft.fft2(a * _WIN)))
    v = np.log1p(mag[_YS, _XS])
    return v - v.mean()


def scale_vs(ref, cur):
    """(scale, peak) of cur relative to ref from the log-radius shift."""
    a = np.fft.fft2(ref)
    b = np.fft.fft2(cur)
    r = a * np.conj(b)
    r /= (np.abs(r) + 1e-9)
    corr = np.fft.ifft2(r).real
    iy, ix = np.unravel_index(np.argmax(corr), corr.shape)
    peak = float(corr[iy, ix])
    # parabolic interpolation along the log-radius axis for sub-bin accuracy
    up = corr[(iy - 1) % NR, ix]
    dn = corr[(iy + 1) % NR, ix]
    denom = (up - 2 * corr[iy, ix] + dn)
    sub = 0.0 if abs(denom) < 1e-12 else 0.5 * (up - dn) / denom
    shift = iy + max(-0.5, min(0.5, sub))
    if shift > NR / 2.0:
        shift -= NR
    step = _LOGR[1] - _LOGR[0]
    return float(np.exp(shift * step)), peak


def median_filter(vals, width):
    n = len(vals)
    out = []
    for i in range(n):
        a, b = max(0, i - width // 2), min(n, i + width // 2 + 1)
        out.append(float(np.median(vals[a:b])))
    return out


def scan(clip, intent=None, prompt=None):
    if intent in (None, "", "auto"):
        intent = intent_of_prompt(prompt)
    w, h, dur = probe_meta(clip)
    frames = sample_frames(clip, w, h)
    base = {"clip": os.path.basename(clip), "path": clip, "intent": intent,
            "intent_source": "prompt" if prompt else "argument"}
    if len(frames) < MIN_FRAMES:
        base.update({"frames_sampled": len(frames), "verdict": "SKIP",
                     "reason": "too few frames"})
        return base

    ref = logpolar(frames[0])
    raw = [scale_vs(ref, logpolar(f)) for f in frames[1:]]
    series = [max(1.0, z) for z, _ in raw]
    stable = [z if p >= PEAK_MIN and abs(z - 1.0) <= OUTLIER else 1.0
              for z, p in raw]
    filtered = median_filter(stable, MED_WIDTH)
    unstable = any(abs(z - 1.0) > OUTLIER and p >= PEAK_MIN for z, p in raw)
    max_zoom = max(filtered) if filtered else 1.0
    peak_at = (filtered.index(max_zoom) + 1) / SAMPLE_FPS

    verdict, why = "NOT-JUDGED", "intent is not a zoom"
    if intent == "locked":
        if max_zoom > LOCKED_TOL:
            verdict, why = "FLAT", "locked frame moved %.2fx" % max_zoom
        else:
            verdict, why = "PASS", "held within %.2fx" % LOCKED_TOL
    elif intent == "push":
        if max_zoom >= PUSH_MIN:
            verdict, why = "PASS", "rendered push %.2fx" % max_zoom
        elif unstable:
            verdict, why = "UNDECIDED", "estimator unstable, needs an eye pass"
        elif max_zoom <= PUSH_FLAT_MAX:
            verdict, why = "FLAT", "declared push rendered %.2fx" % max_zoom
        else:
            verdict, why = "UNDECIDED", "%.2fx is inside the noise floor" % max_zoom

    base.update({
        "frames_sampled": len(frames) + 1,
        "duration": round(dur, 3),
        "max_zoom": round(max_zoom, 3),
        "max_zoom_at_sec": round(peak_at, 2),
        "raw_max_zoom": round(max(series), 3),
        "min_zoom": round(min(filtered), 3),
        "unstable": unstable,
        "peak_min": round(min(p for _, p in raw), 4),
        "peak_max": round(max(p for _, p in raw), 4),
        "series": [round(z, 2) for z in filtered],
        "verdict": verdict,
        "reason": why,
    })
    return base


def load_manifest(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return {u["id"]: u for u in d.get("units", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip")
    ap.add_argument("--intent", default="auto")
    ap.add_argument("--scan-dir")
    ap.add_argument("--glob", default="KN_A-KN*.mp4")
    ap.add_argument("--manifest", help="KN i2v manifest, source of declared intent")
    ap.add_argument("--regress", help="prior gate evidence to compare against")
    ap.add_argument("--out")
    ap.add_argument("--batch", default="")
    a = ap.parse_args()

    units = load_manifest(a.manifest) if a.manifest else {}
    if a.clip:
        clips = [a.clip]
    elif a.scan_dir:
        clips = sorted(glob.glob(os.path.join(a.scan_dir, a.glob)))
    else:
        ap.error("need --clip or --scan-dir")
    if not clips:
        print("NO_CLIPS")
        return 0

    rows = []
    for c in clips:
        stem = os.path.splitext(os.path.basename(c))[0]
        u = units.get(stem, {})
        rows.append(scan(c, a.intent, u.get("i2v_prompt")))

    diffs = []
    if a.regress:
        with open(a.regress, encoding="utf-8") as fh:
            prior = {r["clip"]: r for r in json.load(fh).get("rows", [])}
        for r in rows:
            p = prior.get(r["clip"])
            if not p:
                continue
            r["c2171_verdict"] = p.get("verdict")
            r["c2171_max_zoom"] = p.get("max_zoom")
            if p.get("verdict") != r["verdict"]:
                diffs.append({"clip": r["clip"], "was": p.get("verdict"),
                              "now": r["verdict"], "now_zoom": r["max_zoom"]})

    for r in rows:
        print("%-16s intent=%-7s zoom=%.2fx@%.1f  %-10s %-38s (C2171 %s)" % (
            r["clip"], r["intent"], r.get("max_zoom") or 0,
            float(r.get("max_zoom_at_sec") or 0), r["verdict"],
            r.get("reason", "-"), r.get("c2171_verdict", "-")))

    flat = [r["clip"] for r in rows if r["verdict"] == "FLAT"]
    undecided = [r["clip"] for r in rows if r["verdict"] == "UNDECIDED"]
    if a.out:
        doc = {
            "batch": a.batch,
            "rule": ("declared camera intent vs rendered zoom: Fourier-Mellin "
                     "log-polar phase correlation vs frame 0 at %g fps, median-of-%d "
                     "over time; locked FLAT if >%.2fx, push PASS if >=%.2fx, push FLAT "
                     "if <=%.2fx and stable, otherwise UNDECIDED; pull/mobile not judged"
                     % (SAMPLE_FPS, MED_WIDTH, LOCKED_TOL, PUSH_MIN, PUSH_FLAT_MAX)),
            "scanned": len(rows),
            "flagged": len(flat),
            "flagged_units": flat,
            "undecided": undecided,
            "regress_diffs": diffs,
            "rows": rows,
        }
        d = os.path.dirname(os.path.abspath(a.out))
        os.makedirs(d, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        print("VERDICT ->", a.out)
    print("FRAMING-END scanned=%d flat=%d undecided=%d regress_diff=%d"
          % (len(rows), len(flat), len(undecided), len(diffs)))
    return 1 if (flat or diffs) else 0


if __name__ == "__main__":
    sys.exit(main())
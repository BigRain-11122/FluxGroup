# C2171: shot-scale drift probe for the KN 768P i2v wave (birth-station gate).
# Why: KN_A-KN02 was authored as a locked-off rooftop WIDE but rendered as a medium
# close-up by frame 66, so it cannot cut with the rest of the rooftop block. The
# pseudo-text probe (C2170) only catches the caption strip, not the scale change.
# Method: geometric, deterministic, no model, no GPU, no color heuristics.
#   If the model pushed in, a later frame is ~ a centre crop of frame 0 magnified.
#   So for each later frame, search scale s in SCALES, crop the centre of f0 to
#   (W/s, H/s), resample back to the grid, and keep the s with the smallest mean
#   absolute difference. Verdict DRIFT when best s >= 1.4 AND that s beats s=1.0
#   by >= 20% of the residual (otherwise camera motion explains the mismatch).
# Superseded first attempt: skin-share ratio, rejected same round because the warm
# dusk sky read as skin (f0 share 0.19 on a wide shot) -- a self-constructed probe.
# ASCII only (B2046). Writes nothing outside the evidence dir.
import json
import os
import subprocess
import sys

SCALES = (1.0, 1.15, 1.3, 1.45, 1.6, 1.8, 2.0, 2.3)
GRID_W = 84
LOCKED_TOLERANCE = 1.15   # a locked-off frame must not change shot size at all
PUSH_MIN_SCALE = 1.10     # a declared push must actually move


def camera_intent(prompt):
    """Read the declared camera move out of the authored i2v sentence.

    locked = tripod / still / handheld hold -> shot size must not change
    push   = eases in / dolly in         -> shot size must grow
    pull   = eases back / pulls back     -> widens; the crop search cannot see it
    mobile = slides / travels / pans / tilts / cranes / rises -> not measurable here
    Order matters: translation is checked before the static phrases, because several
    rows mix a travel verb with a static clause ("settles when the subject stills").
    """
    p = prompt.lower()
    if "eases back" in p or "pulls back" in p or "pull back" in p:
        return "pull"
    if any(k in p for k in ("slides laterally", "travels alongside", "tracks",
                            "pans ", "tilts up", "tilts down", "cranes ",
                            "rises with", "crane ")):
        return "mobile"
    if any(k in p for k in ("locked-off", "locked off", "tripod", "handheld hold")):
        return "locked"
    if any(k in p for k in ("eases in", "dolly", "pushes in", "push in")):
        return "push"
    return "unclassified"


def sample_frames(clip, width=336, fps=2.0):
    cmd = [
        "ffmpeg", "-v", "error", "-i", clip,
        "-vf", "fps=%s,scale=%d:-1" % (fps, width),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    pr = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if pr.returncode != 0:
        raise RuntimeError("ffmpeg failed: %s" % pr.stderr.decode("utf-8", "replace")[:300])
    geo = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", clip],
        stdout=subprocess.PIPE).stdout.decode().strip().split(",")
    w, h = int(geo[0]), int(geo[1])
    sw = width
    sh = int(round(h * float(width) / float(w)))
    size = sw * sh * 3
    data = pr.stdout
    frames = [data[i:i + size] for i in range(0, len(data) - size + 1, size)]
    return frames, sw, sh, fps


def to_grid(buf, sw, sh, gw=GRID_W):
    """Block-average a raw frame to a gw x (gw*sh/sw) grayscale grid."""
    gh = max(8, int(round(gw * float(sh) / float(sw))))
    bx = sw / float(gw)
    by = sh / float(gh)
    out = []
    for gy in range(gh):
        y0 = int(gy * by)
        y1 = max(y0 + 1, int((gy + 1) * by))
        for gx in range(gw):
            x0 = int(gx * bx)
            x1 = max(x0 + 1, int((gx + 1) * bx))
            acc = 0
            n = 0
            for y in range(y0, y1):
                base = y * sw * 3
                for x in range(x0, x1):
                    p = base + x * 3
                    acc += buf[p] + buf[p + 1] + buf[p + 2]
                    n += 1
            out.append(acc / float(n * 3))
    return out, gw, gh


def centre_crop(grid, gw, gh, scale):
    """Centre-crop the grid to 1/scale and resample back to gw x gh."""
    cw = max(4, int(round(gw / scale)))
    ch = max(4, int(round(gh / scale)))
    ox = (gw - cw) // 2
    oy = (gh - ch) // 2
    out = []
    for gy in range(gh):
        sy = oy + min(ch - 1, int(gy * ch / float(gh)))
        row = sy * gw
        for gx in range(gw):
            sx = ox + min(cw - 1, int(gx * cw / float(gw)))
            out.append(grid[row + sx])
    return out


def mean_abs_diff(a, b):
    n = len(a)
    return sum(abs(a[i] - b[i]) for i in range(n)) / float(n)


def probe(clip, intent):
    frames, sw, sh, fps = sample_frames(clip)
    if len(frames) < 2:
        return {"clip": os.path.basename(clip), "intent": intent, "verdict": "NO-FRAMES"}
    f0, gw, gh = to_grid(frames[0], sw, sh)
    crops = {s: centre_crop(f0, gw, gh, s) for s in SCALES}
    worst = None
    for idx in range(1, len(frames)):
        g, _, _ = to_grid(frames[idx], sw, sh)
        diffs = {s: mean_abs_diff(crops[s], g) for s in SCALES}
        best = min(diffs, key=diffs.get)
        if worst is None or best > worst["scale"]:
            worst = {"idx": idx, "sec": round(idx / fps, 2), "scale": best,
                     "diff_at_best": round(diffs[best], 2), "diff_at_1.0": round(diffs[1.0], 2)}
    if intent in ("mobile", "pull"):
        v = "NOT-JUDGED"          # camera translates / widens; shot size not measurable here
    elif intent == "locked":
        v = "DRIFT" if worst["scale"] > LOCKED_TOLERANCE else "PASS"
    elif intent == "push":
        v = "FLAT" if worst["scale"] < PUSH_MIN_SCALE else "PASS"
    else:
        v = "UNCLASSIFIED"
    return {
        "clip": os.path.basename(clip),
        "intent": intent,
        "frames_sampled": len(frames),
        "grid": "%dx%d" % (gw, gh),
        "max_zoom": worst["scale"],
        "max_zoom_at_sec": worst["sec"],
        "resid_at_best": worst["diff_at_best"],
        "resid_at_scale1": worst["diff_at_1.0"],
        "verdict": v,
    }


def main():
    args = sys.argv[1:]
    out_json = ""
    manifest = ""
    if "--json" in args:
        i = args.index("--json")
        out_json = args[i + 1]
        args = args[:i] + args[i + 2:]
    if "--manifest" in args:
        i = args.index("--manifest")
        manifest = args[i + 1]
        args = args[:i] + args[i + 2:]
    intents = {}
    if manifest:
        with open(manifest, encoding="utf-8") as fh:
            man = json.load(fh)
        for u in man.get("units", []):
            intents[u["shot"]] = camera_intent(u.get("i2v_prompt", ""))
    rows = []
    for clip in args:
        shot = os.path.basename(clip).split("-")[-1].replace(".mp4", "")
        intent = intents.get(shot, "unclassified")
        try:
            rows.append(probe(clip, intent))
        except Exception as e:
            rows.append({"clip": os.path.basename(clip), "intent": intent,
                         "verdict": "ERROR", "error": str(e)[:200]})
    bad = [r["clip"] for r in rows if r.get("verdict") in ("DRIFT", "FLAT")]
    doc = {
        "batch": "C2171",
        "rule": "declared camera intent vs rendered zoom (centre-crop search on f0): "
                "locked<=%.2fx, push>=%.2fx, mobile=not judged"
                % (LOCKED_TOLERANCE, PUSH_MIN_SCALE),
        "scanned": len(rows),
        "flagged": len(bad),
        "flagged_units": bad,
        "rows": rows,
    }
    print(json.dumps(doc, indent=1))
    if out_json:
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
        print("WROTE %s" % out_json)


if __name__ == "__main__":
    main()
# -*- coding: ascii -*-
# kn_full_assembly_c2183.py - KN (Ke Ai Nv Ren) full-film assembly station, v1.
#
# Why this exists: C2182 proved all 30 rendered units sit on disk and that the
# 30 new shots concat into a 196.35s rough cut. But the song is 239.03s, and the
# remaining 42.68s is the replay band (11 windows in the shots script that re-use
# the same rendered units at different speeds and trims). Nobody could watch the
# real picture until the station could build the replay band and lay the song
# under it. That is what this pass does - the first watchable cut of the film.
#
# Single source of truth:
#   * shot order, windows and speeds come from the shots script (NEW + REUSE);
#   * per-unit source clip and grade anchor come from the i2v manifest;
#   * grade rows come from the Grade case (Ke Ai Nv Ren GRADE v1).
# Nothing is hand-typed twice: the script imports the shots module rather than
# copying its numbers.
#
# Deliberate v1 scope (documented, not accidental):
#   * every boundary is a hard cut. The song's own design law puts all
#     transitions in the material (cloud swallowing the plane, star dust opening,
#     window light answering), and allows exactly one dissolve inside KN20 -
#     which is rendered into that unit, not an edit-layer effect;
#   * grade is applied per light anchor as the Grade case prescribes
#     (contrast / lifted blacks / warm-cool balance / vignette / grain).
#     Halation and per-anchor frame measurement belong to the v2 grade pass;
#   * titles and the AIGC label are burned in this pass, verified by frame
#     readback afterwards;
#   * audio is the master track trimmed to the song length, loudnorm to
#     -14 LUFS, with a short head fade and a 2.4s tail fade.
#
# Usage:
#   python kn_full_assembly_c2183.py --dry-run     # index + asserts only
#   python kn_full_assembly_c2183.py --encode      # write the cut mp4
import argparse
import json
import os
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
MV = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
SHOTS = os.path.join(MV, "\u53ef\u7231\u5973\u4eba-shots-v2.py")
MANIFEST = os.path.join(MV, "local-i2v", "run-bmc-kn-i2v.json")
CLIPDIR = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768")
AUDIO = os.path.join(MV, "audio", "\u5468\u6770\u4f26 - \u53ef\u7231\u5973\u4eba.mp3")
OUTDIR = os.path.join(REPO, "media", "mv-album-001-jay", "assembly-packA-KN")
FONT = "C:/Windows/Fonts/simhei.ttf"
W, H, FPS = 1344, 768, 24
FILM_END = 239.03
MIN_SPEED = 0.85
BATCH = "C2183"

# Grade rows per light anchor (Grade case v1 section three).
GRADE = {
    "roof_dusk": "eq=contrast=1.06:saturation=0.98,curves=all='0/0.010 1/1'",
    "roof_night": "eq=contrast=1.07:saturation=0.99,curves=all='0/0.012 1/1'",
    "city_bowl": "eq=contrast=1.10:saturation=1.02,colorbalance=rs=0.02:bs=-0.02",
    "city_moon": "eq=contrast=1.06:saturation=0.98,colorbalance=bs=0.03,curves=all='0/0.014 1/1'",
    "cloud_moon": "eq=contrast=1.05:saturation=0.98,curves=all='0/0.020 0.5/0.52 1/1'",
    "warm_window": "eq=contrast=1.05:saturation=1.02,curves=all='0/0.012 1/1',vignette=angle=0.30",
    "streak": "eq=contrast=1.05:saturation=1.02,curves=all='0/0.012 1/1',vignette=angle=0.30",
    "galaxy_gold": "eq=contrast=1.08:saturation=1.03,noise=alls=5:allf=t+u",
}


def _esc(path):
    """Filter-graph path form: forward slashes, quoted, colon escaped.

    ffmpeg's filter parser treats ':' as an option separator, so a Windows drive
    letter has to be escaped inside quotes; the unquoted form fails to parse.
    """
    return "'" + path.replace("\\", "/").replace(":", "\\:") + "'"


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def load_windows():
    """Windows straight from the shots script (NEW then REUSE), sorted by start."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kn_shots", SHOTS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = []
    for src, kind in ((mod.NEW, "new"), (mod.REUSE, "replay")):
        for r in src:
            rows.append({"shot": r[0], "t0": float(r[1]), "t1": float(r[2]),
                         "speed": float(r[3]), "kind": kind, "note": r[4]})
    rows.sort(key=lambda x: x["t0"])
    return rows, float(mod.FILM_END)


def build_index(rows, film_end):
    units = {u["shot"]: u for u in json.load(open(MANIFEST, encoding="utf-8"))["units"]}
    cache = {}
    for r in rows:
        u = units[r["shot"]]
        u = dict(u)
        r["id"] = u["id"]
        r["light"] = u["light"]
        r["win_s"] = round(r["t1"] - r["t0"], 3)
        clip = os.path.join(CLIPDIR, u["id"] + ".mp4")
        r["clip"] = clip
        r["present"] = os.path.isfile(clip) and os.path.getsize(clip) > 100 * 1024
        if clip not in cache:
            cache[clip] = probe_duration(clip) if r["present"] else 0.0
        src = cache[clip]
        r["src_s"] = round(src, 3)
        if not r["present"]:
            r["eff_speed"], r["fit"], r["pad_s"] = r["speed"], "MISSING", 0.0
            continue
        need = src / r["win_s"] if r["win_s"] else r["speed"]
        if need >= r["speed"]:
            eff, fit = r["speed"], "trim"
        elif need >= MIN_SPEED:
            eff, fit = need, "slowed"
        else:
            eff, fit = MIN_SPEED, "padded"
        achieved = min(src / eff, r["win_s"])
        r["eff_speed"] = round(eff, 4)
        r["fit"] = fit
        r["pad_s"] = round(max(0.0, r["win_s"] - achieved), 3)
    _assert_timeline(rows, film_end)
    return rows


def _assert_timeline(rows, film_end):
    bad = []
    if abs(rows[0]["t0"]) > 0.001:
        bad.append("head starts at %.3f" % rows[0]["t0"])
    if abs(rows[-1]["t1"] - film_end) > 0.05:
        bad.append("tail ends at %.3f (expect %.2f)" % (rows[-1]["t1"], film_end))
    for a, b in zip(rows, rows[1:]):
        d = round(b["t0"] - a["t1"], 3)
        if d > 0.001:
            bad.append("gap %.3f between %s and %s" % (d, a["shot"], b["shot"]))
        if d < -0.001:
            bad.append("overlap %.3f between %s and %s" % (-d, a["shot"], b["shot"]))
    missing = [r["shot"] for r in rows if not r["present"]]
    if missing:
        bad.append("missing units: %s" % ",".join(missing))
    assert not bad, "TIMELINE ASSERT FAILED: " + " | ".join(bad)


def write_text_files():
    paths = {}
    for key, text in (
        ("title", "\u53ef\u7231\u5973\u4eba"),
        ("end", "\u8bcd\u66f2\u8457\u4f5c\u6743 / \u5f55\u97f3\u5236\u4f5c\u8005\u6743 \u6388\u6743\u4e2d"),
        ("aigc", "AI \u751f\u6210"),
    ):
        p = os.path.join(OUTDIR, "text-%s-%s.txt" % (key, BATCH))
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        paths[key] = p
    return paths


def encode(rows, texts):
    os.makedirs(OUTDIR, exist_ok=True)
    def leg(r, dur, punch):
        chain = ("trim=0:{src:.3f},setpts=(PTS-STARTPTS)/{sp},"
                 "trim=duration={dur:.3f},setpts=PTS-STARTPTS,fps={fps},"
                 "scale={w}:{h}:force_original_aspect_ratio=increase").format(
                     src=r["src_s"], sp=r["eff_speed"], dur=dur, fps=FPS, w=W, h=H)
        if punch:
            chain += (",crop=iw*0.86:ih*0.86,scale={w}:{h},setsar=1,"
                      "eq=brightness=0.015:saturation=1.02".format(w=W, h=H))
        else:
            chain += ",crop={w}:{h},setsar=1".format(w=W, h=H)
        return chain + "," + GRADE[r["light"]]

    inputs, chains, labels = [], [], []
    for i, r in enumerate(rows):
        inputs += ["-i", r["clip"]]
        if r["pad_s"] > 0.12:
            # The window wants more than the render can give at the slow floor.
            # A multi-second freeze reads as a stuck frame, so the tail is filled
            # by a second pass of the same take punched in slightly (the method
            # the Xing Qing v10 cut proved): different framing, same material.
            rem = r["pad_s"]
            first_len = round(r["win_s"] - rem, 3)
            chains.append(
                "[{i}:v]split=2[ia{i}][ib{i}];"
                "[ia{i}]{a},format=yuv420p[g1_{i}];"
                "[ib{i}]{b},format=yuv420p[g2_{i}];"
                "[g1_{i}][g2_{i}]concat=n=2:v=1:a=0[v{i}]".format(
                    i=i, a=leg(r, first_len, False), b=leg(r, rem, True)))
        else:
            chain = "[%d:v]" % i + leg(r, r["win_s"], False)
            if r["pad_s"] > 0.001:
                chain += ",tpad=stop_mode=clone:stop_duration=%.3f" % r["pad_s"]
            chains.append(chain + ",format=yuv420p[v%d]" % i)
        labels.append("[v%d]" % i)

    font = _esc(FONT)
    title = ("drawtext=fontfile={f}:textfile={t}:fontsize=64:fontcolor=white:"
             "shadowcolor=black@0.65:shadowx=2:shadowy=2:x=(w-text_w)/2:y=(h-text_h)/2-40:"
             "enable='between(t,0.6,3.4)'").format(f=font, t=_esc(texts["title"]))
    end = ("drawtext=fontfile={f}:textfile={t}:fontsize=26:fontcolor=white@0.86:"
           "shadowcolor=black@0.7:shadowx=1:shadowy=1:x=(w-text_w)/2:y=h-140:"
           "enable='between(t,235.03,239.03)'").format(f=font, t=_esc(texts["end"]))
    aigc = ("drawtext=fontfile={f}:textfile={t}:fontsize=22:fontcolor=white@0.72:"
            "shadowcolor=black@0.7:shadowx=1:shadowy=1:x=w-text_w-36:y=h-text_h-28").format(
                f=font, t=_esc(texts["aigc"]))

    tail = (";{labels}concat=n={n}:v=1:a=0[cc];"
            "[cc]{title},{end},{aigc}[out]").format(
                labels="".join(labels), n=len(rows), title=title, end=end, aigc=aigc)
    graph = ";".join(chains) + tail

    mp4 = os.path.join(OUTDIR, "KN-FULL-v1-%s.mp4" % BATCH)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs + [
        "-i", AUDIO,
        "-filter_complex", graph,
        "-map", "[out]", "-map", "%d:a" % len(rows),
        "-af", "atrim=0:%.2f,asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-2:LRA=11,"
               "afade=t=in:st=0:d=0.30,afade=t=out:st=%.2f:d=2.40" % (FILM_END, FILM_END - 2.43),
        "-c:v", "libx264", "-preset", "faster", "-crf", "19",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", "%.2f" % FILM_END,
        "-movflags", "+faststart", mp4,
    ]
    print("ENCODING %d windows -> %s" % (len(rows), os.path.basename(mp4)))
    sys.stdout.flush()
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFMPEG FAILED rc=%d" % res.returncode)
        print((res.stderr or "")[-3000:])
        raise SystemExit(1)
    return mp4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--encode", action="store_true")
    ap.add_argument("--batch", default=None,
                    help="override the output batch tag (keeps earlier cuts intact)")
    a = ap.parse_args()
    if a.batch:
        global BATCH
        BATCH = a.batch
    os.makedirs(OUTDIR, exist_ok=True)
    rows, film_end = load_windows()
    build_index(rows, film_end)
    prints = " ".join("%s:%s" % (r["shot"], r["fit"]) for r in rows if r["fit"] != "trim")
    print("WINDOWS %d | total %.2fs | non-trim fits: %s" % (len(rows), film_end, prints or "none"))
    print("GRADE anchors: %s" % ",".join(sorted(set(r["light"] for r in rows))))
    idx = os.path.join(OUTDIR, "KN-FULL-INDEX-%s.json" % BATCH)
    with open(idx, "w", encoding="utf-8") as f:
        json.dump({"batch": BATCH, "film_end": film_end, "windows": rows}, f, indent=1)
    print("index:", idx)
    if not a.encode:
        print("DRY-RUN OK (no encode)")
        return
    texts = write_text_files()
    mp4 = encode(rows, texts)
    print("WROTE", mp4, os.path.getsize(mp4))


if __name__ == "__main__":
    main()
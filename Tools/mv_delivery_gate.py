# -*- coding: utf-8 -*-
"""mv_delivery_gate.py - one gate for every defect class the director keeps catching.

CEO 2026-10-24: "之前的MV剪辑和转场一直出问题，还有镜头运镜，AI视频的瑕疵和重复的
重大问题，所以务必去规避和检查" -> every one of those becomes a counted check here,
not a note in a review document.

Checks (all mechanical, no eyes required):
  D1 repetition   - exact duplicate frames (ffmpeg framemd5) + a shot appearance reused
                    at a different time in the film (per-shot dHash collision)
  D2 stillness    - runs of near-identical frames (dead hold) and per-shot mean motion,
                    which is what "AI 视频不动 / 运镜没有" actually looks like
  D3 warp/jump    - intra-shot whole-frame displacement that returns to the same framing
                    (delegated to mv_stability_gate.py, which already corroborates on a
                    static patch so flames and moving actors do not false-positive)
  D4 flicker      - luminance steps inside a shot (AI exposure pumping) with no cut there
  D5 edits        - cut/transition inventory must show >=4 languages and <=70% hard cuts
                    (CHK-E1), read from the assembly index when one is supplied

Exit 0 = PASS. Exit 1 = violation(s). --json writes a machine receipt.

Usage:
  python Tools/mv_delivery_gate.py <video> [--index <assembly index json>]
                                  [--expect-frames N] [--json out.json]
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
def _ffmpeg():
    """Resolve ffmpeg at run time. The old hardcoded C:\\Program Files path went dead
    after the 2026-10 winget migration, so this gate crashed instead of checking
    (found 2026-10-28 before it was burned as a queue job)."""
    import shutil
    for cand in (shutil.which("ffmpeg"),
                 r"C:\Users\sjs20\AppData\Local\Microsoft\WinGet\Packages"
                 r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                 r"\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe",
                 r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"):
        if cand and os.path.exists(cand):
            return cand
    return "ffmpeg"


FFMPEG = _ffmpeg()

W, H = 336, 188
SCALE = 1344.0 / W

FREEZE_MAD = 0.20          # same floor mv_stability_gate uses
FREEZE_RUN = 3
CUT_MAD = 12.0             # a hard cut looks like a big mean-abs-difference
SHOT_MOTION_MIN = 0.55     # mean MAD inside a shot
SHOT_SHIFT_MIN = 0.35      # mean global displacement px/frame - a slow crane still moves
STILL_MAD = 0.45           # a shot is "still" only when BOTH are low: MAD alone
                           # punishes slow cinematography and rewards grain
FLICKER_IRE = 9.0          # luminance step inside a shot
REPEAT_HAMMING = 4         # 8x8 dHash distance that counts as "the same picture again"
CUT_HASH_SAME = 6          # still the same picture across a big MAD step -> not a cut
CUT_CORNER_STEP = 4.5      # corner-floor step (IRE) below which a luma jump is local light

CH, CW = 24, 42            # corner patches on the 336x188 scan scale


def min_corner_luma(g):
    """Darkest corner = the stable black floor.

    A diegetic light event (flame flare, sparks, a lamp catching) moves the lit area
    while the shadow-side corner stays put; an exposure pump raises every corner.
    """
    cs = (g[0:CH, 0:CW], g[0:CH, -CW:], g[-CH:, 0:CW], g[-CH:, -CW:])
    return float(min(c.mean() for c in cs))


def is_structural_cut(prev_g, g, mad_i):
    """A cut has to change the picture, and only a local light source keeps the floor.

    Judged on MAD alone, mv0001's 102.2s fire flare-up (30 IRE in four frames) was cut
    into a 9-frame shot plus its own continuation; the two halves then hashed the same
    and D1 reported a phantom "reused shot" in twelve consecutive deliveries
    (2026-11-02 .. 2026-11-14) - a red everyone learned to wave through.

    Structure alone is not enough either: D07->D08 at 167.22s splices two takes of the
    same hazy corridor and the dHash distance is still 4/64. What separates them is the
    black floor - a flame or lamp leaves the darkest corner alone (102.2s: d=1.3),
    while a veil/exposure lift moves every corner (167.2s: d=5.7).
    """
    if mad_i < CUT_MAD:
        return False
    if hamming(dhash(prev_g), dhash(g)) > CUT_HASH_SAME:
        return True
    return abs(min_corner_luma(prev_g) - min_corner_luma(g)) >= CUT_CORNER_STEP


def dhash(gray):
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = small[:, 1:] > small[:, :-1]
    return bits.flatten()


def hamming(a, b):
    return int(np.count_nonzero(a != b))


def framemd5_dupes(path):
    tmp = os.path.join(os.environ.get("TEMP", "."), "mvdg_%d.framemd5" % os.getpid())
    subprocess.check_call([FFMPEG, "-v", "error", "-i", path, "-map", "0:v:0",
                           "-f", "framemd5", tmp])
    hashes = []
    with open(tmp, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            hashes.append(s.split(",")[-1].strip())
    os.remove(tmp)
    seen, dup_at = {}, []
    for i, h in enumerate(hashes):
        if h in seen:
            dup_at.append((seen[h], i))
        else:
            seen[h] = i
    return len(hashes), dup_at


def stability(path, expect):
    tmp = os.path.join(os.environ.get("TEMP", "."), "mvdg_stab_%d.json" % os.getpid())
    args = [sys.executable, os.path.join(HERE, "mv_stability_gate.py"), path, "--json", tmp]
    if expect:
        args += ["--expect-frames", str(expect)]
    subprocess.run(args, capture_output=True)
    try:
        d = json.load(open(tmp, encoding="utf-8"))
    except Exception:
        d = {"seams": [], "freezes": [], "frames": 0, "pass": False}
    finally:
        if os.path.isfile(tmp):
            os.remove(tmp)
    return d


def scan(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    grays, mad, yavg, shift = [], [], [], []
    prev = None
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY)
        grays.append(g)
        yavg.append(float(g.mean()))
        gf = g.astype(np.float32)
        mad.append(0.0 if prev is None else float(np.mean(np.abs(gf - prev))))
        if prev is None:
            shift.append(0.0)
        else:
            (dx, dy), _ = cv2.phaseCorrelate(prev, gf)
            shift.append(float((dx * dx + dy * dy) ** 0.5) * SCALE)
        prev = gf
    cap.release()
    return fps, grays, np.asarray(mad), np.asarray(yavg), np.asarray(shift)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?")
    ap.add_argument("--self-test", action="store_true",
                    help="run the cut/luma and repeat-hash controls, no video needed")
    ap.add_argument("--index", default="")
    ap.add_argument("--expect-frames", type=int, default=0)
    ap.add_argument("--card", action="append", default=[],
                    help="intentional still window start:end in seconds (title/credit cards); "
                         "repeatable. Exempt from D2/D3 only - D1/D4 still apply.")
    ap.add_argument("--whitelist", default="",
                    help="reprise whitelist JSON (same schema as mv_full_audit.py); pairs "
                         "listed there are designed reprises, not D1 defects")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.video:
        ap.error("video is required unless --self-test")

    cards = []
    for spec in a.card:
        try:
            s0, s1 = spec.split(":")
            cards.append((float(s0), float(s1)))
        except Exception:
            sys.exit("bad --card spec: %r (want start:end)" % spec)

    fails = []
    n_dup, dup_at = framemd5_dupes(a.video)
    st = stability(a.video, a.expect_frames)
    fps, grays, mad, yavg, shift = scan(a.video)
    n = len(grays)

    # D1 repetition ------------------------------------------------------
    if dup_at:
        fails.append("D1 exact duplicate frames: %d pair(s), first at frame %d (%.2fs)" %
                     (len(dup_at), dup_at[0][1], dup_at[0][1] / fps))

    is_cut = np.zeros(n, dtype=bool)
    luma_events = []
    for i in range(1, n):
        if is_structural_cut(grays[i - 1], grays[i], mad[i]):
            is_cut[i] = True
        elif mad[i] >= CUT_MAD:
            luma_events.append(i)
    if luma_events:
        print("note: %d in-shot luma event(s) treated as light, not cut (first %.2fs)" %
              (len(luma_events), luma_events[0] / fps))
    cuts = [i for i in range(1, n) if is_cut[i]]
    bounds = [0] + cuts + [n]
    shots = [(bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1) if bounds[k + 1] - bounds[k] >= 6]

    hashes = []
    for s0, s1 in shots:
        mid = (s0 + s1) // 2
        hashes.append((s0, s1, dhash(grays[mid])))
    seen_pairs = []
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            if hamming(hashes[i][2], hashes[j][2]) <= REPEAT_HAMMING:
                seen_pairs.append((hashes[i][0], hashes[j][0]))

    # intentional reprises are design; the canon whitelist names them (same schema as
    # mv_full_audit.py). Without this the gate always FAILs on mv0001's designed repeats,
    # which is why the whole check was unreadable as a pass/fail signal (2026-10-28).
    n_wl = 0
    if a.whitelist and os.path.exists(a.whitelist) and seen_pairs:
        try:
            with open(a.whitelist, encoding="utf-8-sig") as fh:
                wl = json.load(fh)
            tol = float(wl.get("tolerance_sec", 5.0))
            pairs = wl.get("pairs", [])
            keep = []
            for f0, f1 in seen_pairs:
                t0, t1 = f0 / fps, f1 / fps
                hit = any(abs(t0 - p["a"]) <= tol and abs(t1 - p["b"]) <= tol or
                          abs(t0 - p["b"]) <= tol and abs(t1 - p["a"]) <= tol for p in pairs)
                if hit:
                    n_wl += 1
                else:
                    keep.append((f0, f1))
            seen_pairs = keep
        except Exception as e:
            print("note: whitelist unreadable (%s)" % e)

    if n_wl:
        print("note: %d reprise pair(s) matched the whitelist (design, not counted)" % n_wl)
    if seen_pairs:
        for f0, f1 in seen_pairs:
            print("D1-PAIR unlisted: %.2fs vs %.2fs" % (f0 / fps, f1 / fps))
        fails.append("D1 shot reused on screen: %d pair(s), first %.2fs vs %.2fs" %
                     (len(seen_pairs), seen_pairs[0][0] / fps, seen_pairs[0][1] / fps))

    # D2 stillness -------------------------------------------------------
    # Per-frame motion is inversely proportional to fps: after minterpolate the same
    # 24fps move arrives as ~40% of the MAD at 60fps. The thresholds below are stated
    # at 24fps and scaled, otherwise every 60fps delivery reports 20+ "static" shots
    # (v727 60fps receipt, 2026-11-11) and the D2 line becomes noise.
    motion_ref = (24.0 / fps) if fps else 1.0
    still_mad, shift_min = motion_thresholds(fps)
    if abs(motion_ref - 1.0) > 0.01:
        print("note: fps=%.2f -> still_mad=%.2f shift_min=%.2f (24fps equivalents %.2f/%.2f)"
              % (fps, still_mad, shift_min, STILL_MAD, SHOT_SHIFT_MIN))

    def in_card(t0, t1):
        """True when the window STARTS inside a declared card window.

        Start-based, not containment: a card sits on a held frame, so the shot that
        carries it runs a little past the card's own end and must still be exempt.
        """
        return any(c0 - 0.05 <= t0 <= c1 for c0, c1 in cards)

    still_shots = []
    for s0, s1 in shots:
        seg = mad[s0 + 1:s1] if s1 - s0 > 1 else np.array([0.0])
        seg_s = shift[s0 + 1:s1] if s1 - s0 > 1 else np.array([0.0])
        avg = float(seg.mean()) if seg.size else 0.0
        avg_s = float(seg_s.mean()) if seg_s.size else 0.0
        # still means the picture barely changes AND the frame does not travel:
        # a slow crane has low MAD but real displacement and must not be failed.
        if avg < still_mad and avg_s < shift_min and not in_card(s0 / fps, s1 / fps):
            still_shots.append((s0, s1, round(avg, 2), round(avg_s, 2)))
    if still_shots:
        fails.append("D2 near-static shots: %d (first %.2f-%.2fs mean_mad=%.2f)" %
                     (len(still_shots), still_shots[0][0] / fps, still_shots[0][1] / fps,
                      still_shots[0][2]))

    # D3 seams / dead holds (stability gate) -----------------------------
    if st.get("seams"):
        fails.append("D3 intra-shot frame jumps: %d (first %.2fs shift=%.1fpx)" %
                     (len(st["seams"]), st["seams"][0]["t"], st["seams"][0]["shift_px"]))
    if st.get("freezes"):
        live = [f for f in st["freezes"] if not in_card(f["t"], f["t"] + f["run"] / fps)]
        long_holds = [f for f in live if f["run"] >= 6]
        if long_holds:
            fails.append("D3 dead holds >=0.25s: %d of %d freeze runs (worst run=%d frames at %.2fs)" %
                         (len(long_holds), len(live),
                          max(f["run"] for f in long_holds), min(f["t"] for f in long_holds)))
        elif live:
            print("note: %d sub-0.25s freeze run(s) left (worst %d frames)" %
                  (len(live), max(f["run"] for f in live)))

    # D4 flicker ---------------------------------------------------------
    # 2026-10-31 director-adjudication upgrade (v717/v718 review): a luma step driven by
    # diegetic light (fire flare-up, sparks) moves the lit area while the frame corners
    # stay put; an exposure pump moves the whole raster. The four mv0001 fire events
    # (102.2s + the 211.2-211.3s flame ramp, deltas 10.7/9.0/9.4 monotonic) are design,
    # not defects - so the gate now tests locality before flagging.
    flick = []
    for s0, s1 in shots:
        for i in range(s0 + 2, s1):
            d = abs(yavg[i] - yavg[i - 1])
            # not is_cut[], not mad < CUT_MAD: a 30 IRE exposure pop is a real defect
            # even though it used to look "cut-like" and slip past both detectors.
            if d >= FLICKER_IRE and not is_cut[i]:
                cstep = abs(min_corner_luma(grays[i]) - min_corner_luma(grays[i - 1]))
                if cstep < CUT_CORNER_STEP:
                    continue  # darkest corner stable: diegetic local light
                flick.append((i, round(d, 1)))
    if flick:
        fails.append("D4 exposure flicker inside shots: %d (first %.2fs delta=%.1f)" %
                     (len(flick), flick[0][0] / fps, flick[0][1]))

    # D5 edit grammar ----------------------------------------------------
    grammar = None
    if a.index and os.path.isfile(a.index):
        try:
            g = json.load(open(a.index, encoding="utf-8"))
            counts = g.get("edit_grammar") or g.get("counts")
            grammar = counts
            classes = sum(1 for k in ("cut", "motion", "dissolve", "blur") if (counts or {}).get(k, 0) > 0)
            tot = sum((counts or {}).values())
            hard = 100.0 * (counts or {}).get("cut", 0) / tot if tot else 100.0
            if classes < 4 or hard > 70.0:
                fails.append("D5 edit grammar: classes=%d hard_cuts=%.1f%% (need >=4, <=70%%)" %
                             (classes, hard))
        except Exception as e:
            fails.append("D5 index unreadable: %s" % e)

    # report -------------------------------------------------------------
    print("file    :", a.video)
    print("frames  : %d @ %.3ffps  shots=%d  dup_pairs=%d  static_shots=%d" %
          (n, fps, len(shots), len(dup_at), len(still_shots)))
    print("stability: seams=%d freezes=%d" % (len(st.get("seams", [])), len(st.get("freezes", []))))
    if grammar:
        print("grammar :", json.dumps(grammar, ensure_ascii=False))
    for f in fails:
        print("FAIL", f)
    verdict = "PASS" if not fails else "FAIL"
    print("VERDICT:", verdict)

    if a.json:
        json.dump({"file": a.video, "frames": n, "fps": fps, "shots": len(shots),
                   "dup_pairs": len(dup_at), "static_shots": still_shots,
                   "reprise_whitelisted": n_wl, "reprise_unlisted": len(seen_pairs),
                   "reprise_unlisted_pairs": [[round(f0 / fps, 2), round(f1 / fps, 2)]
                                              for f0, f1 in seen_pairs],
                   "luma_events": len(luma_events),
                   "stability": {"seams": st.get("seams", []), "freezes": st.get("freezes", [])},
                   "flicker": flick[:50], "grammar": grammar,
                   "fails": fails, "verdict": verdict},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if verdict == "PASS" else 1


def _synth_frame(seed):
    """A banded frame: enough structure for dHash to be meaningful, no ffmpeg needed."""
    rng = np.random.default_rng(seed)
    g = np.zeros((H, W), np.float32)
    x = 0
    while x < W:
        w = int(12 + rng.integers(0, 20))
        g[:, x:x + w] = 40 + 120 * rng.random()
        x += w
    g += rng.normal(0, 4, (H, W))
    return np.clip(cv2.GaussianBlur(g, (7, 7), 0), 0, 255).astype(np.uint8)


def _add_pool(g, cx, cy, r, gain):
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    m = np.clip(1.0 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r, 0, 1) ** 2
    return np.clip(g.astype(np.float32) + m * gain, 0, 255).astype(np.uint8)


def motion_thresholds(fps):
    """(still_mad, shot_shift_min) at the observed fps, stated in 24fps equivalents.

    Per-frame motion is inversely proportional to fps: after minterpolate the same
    24fps move arrives as ~40% of the MAD at 60fps. Un-scaled, every 60fps delivery
    reported 20+ "static" shots (v727 60fps receipt, 2026-11-11) and D2 became noise.
    """
    ref = (24.0 / fps) if fps else 1.0
    return STILL_MAD * ref, SHOT_SHIFT_MIN * ref


def self_test():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("PASS  " if cond else "FAIL  ") + name)

    a, b = _synth_frame(1), _synth_frame(2)
    pooled = _add_pool(a, W // 2, H // 2, 45, 60)
    pumped = np.clip(a.astype(np.float32) * 1.45 + 12, 0, 255).astype(np.uint8)

    # (1) positive control: two different pictures are a cut
    check("real cut is a cut", is_structural_cut(a, b, 20.0))
    # (2) negative: a diegetic pool flare inside one shot is not a cut
    #     (this is the 102.2s fire flare that produced the phantom D1 pair)
    check("local pool flare is not a cut", not is_structural_cut(a, pooled, 20.0))
    # (3) positive: a look-alike splice that lifts the whole raster IS a cut
    #     (this is D07->D08 at 167.22s in mv0001: dHash 4/64 but the floor lifts 5.7)
    check("look-alike splice with lifted floor is a cut", is_structural_cut(a, pumped, 30.0))
    # (4) negative: under CUT_MAD nothing is a cut, however different the frames
    check("sub-threshold step is never a cut", not is_structural_cut(a, b, 3.0))
    # (5) the D1 repeat rule still separates two shots and still matches one picture
    check("distinct shots do not collide", hamming(dhash(a), dhash(b)) > REPEAT_HAMMING)
    check("same picture still matches", hamming(dhash(a), dhash(a.copy())) <= REPEAT_HAMMING)
    # (6) the D4 locality test: local light keeps the dark corner, a pump moves it
    check("pool keeps the dark corner",
          abs(min_corner_luma(a) - min_corner_luma(pooled)) < CUT_CORNER_STEP)
    check("pump moves the dark corner",
          abs(min_corner_luma(a) - min_corner_luma(pumped)) >= CUT_CORNER_STEP)

    # (7) fps scaling: the v727 60fps receipt's 21 "static" shots were a threshold bug.
    #     One real slow move (MAD 0.20, shift 0.12 px/frame) must read still at 24fps
    #     and moving at 60fps.
    m24, s24 = motion_thresholds(24.0)
    m60, s60 = motion_thresholds(60.0)
    check("24fps thresholds match the stated constants",
          abs(m24 - STILL_MAD) < 1e-9 and abs(s24 - SHOT_SHIFT_MIN) < 1e-9)
    check("60fps threshold scales to 40%", abs(m60 - STILL_MAD * 0.4) < 1e-9)
    check("slow move reads still at 24fps", 0.20 < m24 and 0.12 < s24)
    check("the same move is not still at 60fps", not (0.20 < m60 and 0.12 < s60))

    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
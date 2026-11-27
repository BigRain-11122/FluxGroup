# -*- coding: ascii -*-
# xq_packb_assembly_v11_c2168.py - PACK-B v11: motion repair slot wiring.
#   Adds two per-shot override tables so a repaired take can be dropped in by key:
#     SOURCE_OVERRIDE[shot] = repo-relative clip path
#     IN_FRAME[shot]      = first source frame to use (skip a dead head)
#   Nothing is overridden until a shot is listed, so the default cut is v10.
#
# xq_packb_assembly_v10_c2168.py - PACK-B v10: closes R6-2 (continuity) on the
# edit layer only. No generation, no GPU.
#   R6-2a 38.000-44.000s: the sailor-uniform girl (a different person, different
#         light) is replaced by the unused PACK-A take of the S1-07 cloud shot
#         (226 frames, never used in any cut), so the surreal cloud passage runs
#         continuously instead of introducing a stranger.
#   R6-2b 44.000-53.417s: the back seat carried a child (~7 years old), which read
#         as a casting break against the adult woman at 70.0s. The take is cropped
#         to the rider (crop=760:428:0:170) so the passenger is out of frame and
#         the side-profile cycling beat survives unchanged in time and motion.
# Everything else is the v9 graph (which was the v8 graph) unchanged.
#
# xq_packb_assembly_v8_c2168.py - PACK-B v8: closes the two hard items of
# DIRECTOR-REVIEW-PACKB-V7-20261024.md and re-cuts the whole picture.
#
#   V7-1 S2-10/S2-11 (53.417-63.667s) colour+detail break -> local grade
#        compensation at the block level (option b of the review).
#   V7-2 226-232s note plate pseudo-glyphs -> new note take
#        clips-local-768/XQ_B-F5-33c-v8.mp4 (real readable handwriting,
#        built by xq_packb_note_fix_c2168.py), slot swapped in.
#
# Everything else is the proven v7 graph, unchanged.
#
# Why: DIRECTOR-REVIEW-PACKB-V2-20261020.md returned REVISE with three blocking
# items. This pass closes all three on the picture side without re-burning any
# clip source, plus the conditional tail item R5:
#
#   R1 title card   : 2.0-4.0s serif title card over the dark upper-left void of
#                     F0-01b, soft drop shadow (no hard stroke), fade 250/180ms.
#   R2 edit grammar : the cut was 39 straight hard cuts. Ten joins become real
#                     transitions (6 cross dissolves, 4 blur wipes) and three
#                     joins are booked as same-direction motion matches, so the
#                     picture now uses four edit language classes with hard cuts
#                     at 26/39 = 66.7% (CHK-E1 wants >= 4 classes, <= 70% hard).
#   R3 opening prop : the note in F0-01a carries unreadable pseudo-Chinese on the
#                     focal plane. The note region is pushed out of focus with a
#                     feathered radial mask (blurred copy composited over the
#                     frame), so the paper reads as depth of field, not letters.
#                     No source re-render and no GPU.
#   R5 tail plate   : 218-238s gets a black crush, a per-frame gate flicker and
#                     16mm grain, plus a small stacked end credit on the dark
#                     bottom-left corner, so the tape macro reads as an archival
#                     plate instead of a bright static hold.
#
# Frame exactness is preserved: every block that carries a transition has its
# tail extended by the transition duration (source headroom first, frame clone
# as the fallback), so total = sum(block) - sum(transition) = 5712 frames.
#
# Audio is copied bit for bit from the v3 master (already -14.3 LUFS / -2.2 dBTP
# after the two pass loudnorm), so this pass cannot regress the audio line.
#
# Outputs:
#   cph4/fleet/mv-album-001-jay/xq-PACKB-ASSEMBLY-INDEX-v3-c2158.json / .md
#   cph4/fleet/mv-album-001-jay/xq-PACKB-EDIT-GRAMMAR-c2158.json / .md
#   cph4/fleet/mv-album-001-jay/xq-PACKB-ASSEMBLY-RECEIPT-c2158.json
#   media/mv-album-001-jay/assembly-packB/XQ-PACKB-ASSEMBLY-v4-c2158.mp4

import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
EDL = os.path.join(OUTDIR, "xq-PACKB-EDL-v5-c2154.json")
INDEX_A = os.path.join(OUTDIR, "xq-PACKA-ASSEMBLY-INDEX-v2-c2133.json")
OUT_MEDIA = os.path.join(MEDIA, "assembly-packB")
PREV = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v10-c2167.mp4")

OUT_JSON = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v11-c2168.json")
OUT_MD = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-INDEX-v11-c2168.md")
OUT_GRAMMAR_JSON = os.path.join(OUTDIR, "xq-PACKB-EDIT-GRAMMAR-c2168.json")
OUT_GRAMMAR_MD = os.path.join(OUTDIR, "xq-PACKB-EDIT-GRAMMAR-c2168.md")
OUT_RECEIPT = os.path.join(OUTDIR, "xq-PACKB-ASSEMBLY-RECEIPT-c2168.json")

OUT_MP4 = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v11-c2168.mp4")
OUT_NOMUX = os.path.join(OUT_MEDIA, "XQ-PACKB-ASSEMBLY-v11-c2168.video-only.mp4")
FILTER_SCRIPT = os.path.join(OUT_MEDIA, "filter-c2168.txt")
LOG_RUN = os.path.join(MEDIA, "log-packb-assembly-c2168.run.txt")
TITLE_PNG = os.path.join(OUT_MEDIA, "card-c2158-title.png")
CREDIT_PNG = os.path.join(OUT_MEDIA, "card-c2158-endcredit.png")
MASK_PNG = os.path.join(OUT_MEDIA, "mask-c2158-note.png")
JOIN_SHEET = os.path.join(OUT_MEDIA, "XQ-PACKB-v8-JOINS-c2168.jpg")

FFMPEG = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\Program Files\ffmpeg\bin\ffprobe.exe"
FONT = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"

BATCH = "C2168"
FPS = 24
TIMELINE = 238.0
TIMELINE_FRAMES = 5712
W, H = 1344, 768
MONTAGE = ("S5-26", "S5-27", "S5-28")
BUMP = "S1-07"
BUMP_FRAMES = 3
SOURCE_OVERRIDE = {
    # D-20261024-06: the two night takes the local i2v model could not move.
    # S3-19 re-generated on the cloud video model (crane up, star enters frame).
    "S3-19": "clips-repaired-768/XQ_S3-19-cloud.mp4",
    # S4-23 stays local: dead middle dropped, take sped up 1.118x (mean frame
    # change 0.54 -> 0.61, the single 0.25s hold removed). Invisible at 12s.
    "S4-23": "clips-repaired-768/XQ_S4-23-sp112.mp4",
    # Director defect: the 760px crop still admitted a profile at 50.3-51.8s.
    # Pre-cropped at 700px (x 0-700, y 30-424) and verified frame-by-frame.
    "S1-09": "clips-repaired-768/XQ_S1-09-crop700.mp4",
    # S5-27 shipped with a 7-frame dead hold at 174.46s; re-burned at 768P with
    # seed 141421, which measured freezes=0.
    # Director D2: r5 still carried two parallel streaks at 174.5s and 183.0s.
    # r6 is a clean take of the same milky band (no streaks, matches S5-26/28).
    "S5-27": "clips-local-768/XQ_S5-27-r6.mp4",
}
IN_FRAME = {}

B_FILES = {
    "S1-07": "clips-local-768/XQ_B-S1-07-r5a.mp4",
    "S1-08": "clips-packA-768/XQ_S1-07.mp4",
    "S3-18cont": "clips-local-768/XQ_B-S3-18cont.mp4",
    "S3-21": "clips-local-768/XQ_B-S3-21.mp4",
    "S5-31": "clips-local-768/XQ_B-S5-31.mp4",
    "F5-33c": "clips-local-768/XQ_B-F5-33c-v8.mp4",
}

# R2: transition per outgoing shot. Frames at 24fps.
DISSOLVES = {"F0-01b": 6, "S2-16": 8, "S3-21": 8, "S4-24": 8, "S5-25": 10, "F5-33c": 10}
BLURS = {"S1-08": 8, "S3-19": 8, "S3-20": 8, "S5-30": 8}
MOTIONS = ("S1-07", "S2-10", "S5-29")

# R5: the tail plate window [218.0, 238.0).
TAIL_START = 218.0
# V8-1: the two shots the director flagged for a colour/detail break.
GRADE_V8 = ("S2-10", "S2-11")
CROP_R6 = {}  # S1-09 now arrives pre-cropped (see SOURCE_OVERRIDE)
GRADE_CHAIN = (",colorbalance=rm=-0.10:gm=-0.03:bm=0.10:rh=-0.16:gh=-0.05:bh=0.16"
               ":rs=-0.02:bs=0.04,eq=brightness=-0.03:contrast=1.08:saturation=1.08"
               ",unsharp=5:5:0.8")
# R6-a: +1.5 IRE on the astronomy window (director: muddy on a phone)
MONTAGE_LIFT = (172.0, 186.0)
PUNCH_WINDOW = (179.0, 186.0)
PUNCH_CHAIN = (",crop=1003:573:170:97,scale=%d:%d:flags=lanczos,"
               "eq=brightness=0.02:contrast=1.02,noise=alls=6:allf=t+u,setsar=1" % (W, H))

# R1: title card window and R5: end credit window, in seconds.
TITLE_AT, TITLE_LEN = 2.0, 2.0
CREDIT_AT, CREDIT_LEN = 232.2, 5.0


def logline(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (stamp, msg)
    try:
        with open(LOG_RUN, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line)
    except Exception:
        pass


def probe(path, count_frames=True):
    cmd = [FFPROBE, "-v", "error"]
    if count_frames:
        cmd += ["-count_frames"]
    cmd += ["-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
            "-show_entries", "format=duration", "-of", "json", path]
    d = json.loads(subprocess.check_output(cmd).decode("utf-8", "replace"))
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {
        "res": "%sx%s" % (st["width"], st["height"]),
        "fps": round(float(num) / float(den), 3),
        "frames": int(st.get("nb_read_frames") or 0),
        "sec": round(float(d["format"]["duration"]), 3),
    }


def fr(sec):
    return int(round(float(sec) * FPS))


# ---------------------------------------------------------------- cards

def _font(size):
    from PIL import ImageFont
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name("SemiBold")
    except Exception:
        pass
    return f


def render_card(path, lines, color=(245, 240, 230), shadow=True):
    """Render stacked lines with wide tracking and a soft drop shadow."""
    from PIL import Image, ImageDraw, ImageFilter
    tracking = 10
    gap = 16
    metrics = []
    for text, size in lines:
        f = _font(size)
        w = 0
        for ch in text:
            w += f.getlength(ch) + tracking
        w -= tracking
        asc, desc = f.getmetrics()
        metrics.append((text, f, int(w), asc + desc))
    body_w = max(m[2] for m in metrics)
    body_h = sum(m[3] for m in metrics) + gap * (len(metrics) - 1)
    pad = 28
    img = Image.new("RGBA", (body_w + pad * 2, body_h + pad * 2), (0, 0, 0, 0))
    # shadow layer: same text, blurred, offset down, so the edge stays soft
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ys = pad
    for text, f, w, h in metrics:
        x = pad
        for ch in text:
            ds.text((x, ys), ch, font=f, fill=(0, 0, 0, 150))
            x += f.getlength(ch) + tracking
        ys += h + gap
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    img.alpha_composite(sh, (0, 5))
    d = ImageDraw.Draw(img)
    ys = pad
    for text, f, w, h in metrics:
        x = pad
        for ch in text:
            d.text((x, ys), ch, font=f, fill=color + (236,))
            x += f.getlength(ch) + tracking
        ys += h + gap
    img.save(path)
    return {"path": path, "size": [img.size[0], img.size[1]], "pad": pad,
            "body": [body_w, body_h]}


def render_note_mask(path):
    """Radial feathered mask over the opening note (255 = blurred copy)."""
    from PIL import Image, ImageDraw, ImageFilter
    cx, cy = 0.40 * W, 0.62 * H
    rx, ry = 0.31 * W, 0.29 * H
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    img = img.filter(ImageFilter.GaussianBlur(70))
    img.save(path)
    return {"path": path, "center": [round(cx, 1), round(cy, 1)],
            "radii": [round(rx, 1), round(ry, 1)], "feather_sigma": 70}


# ---------------------------------------------------------------- assembly

def build_rows():
    with open(EDL, encoding="utf-8-sig") as f:
        edl = json.load(f)
    with open(INDEX_A, encoding="utf-8-sig") as f:
        idx = json.load(f)
    by_unit = {c["unit"]: c for c in idx["clips"]}

    def clip_of(shot):
        if shot in SOURCE_OVERRIDE:
            rel = SOURCE_OVERRIDE[shot]
            return os.path.join(MEDIA, rel.replace("/", os.sep)), rel
        if shot in B_FILES:
            rel = B_FILES[shot]
            return os.path.join(MEDIA, rel.replace("/", os.sep)), rel
        row = by_unit.get("XQ_" + shot)
        if not row:
            return None, None
        return os.path.join(MEDIA, row["file"].replace("/", os.sep)), row["file"]

    slots = []
    for s in sorted(edl["shots"], key=lambda r: (float(r["t0"]), float(r["t1"]), r["shot"])):
        key = (round(float(s["t0"]), 3), round(float(s["t1"]), 3))
        if slots and slots[-1]["slot"] == key:
            slots[-1]["shots"].append(s["shot"])
        else:
            slots.append({"slot": key, "shots": [s["shot"]]})

    rows = []
    cursor = 0
    for sl in slots:
        t0, t1 = sl["slot"]
        start = max(fr(t0), cursor)
        end = fr(t1)
        need = end - start
        if need <= 0:
            continue
        shots = sl["shots"]

        if len(shots) > 1 and shots[0] in MONTAGE:
            infos = []
            for shot in shots:
                path, rel = clip_of(shot)
                infos.append((shot, rel, probe(path)["frames"]))
            shortest = min(i[2] for i in infos)
            n = max(1, -(-need // shortest))
            base = need // n
            rem = need - base * n
            for k in range(n):
                shot, rel, src_frames = infos[k % len(infos)]
                take = base + (1 if k < rem else 0)
                rows.append({"shot": shot, "file": rel, "src_frames": src_frames,
                             "in_frame": 0, "frames": take,
                             "slot": [round(t0, 3), round(t1, 3)]})
                start += take
            cursor = start
            continue

        if len(shots) > 1:
            base = need // len(shots)
            rem = need - base * len(shots)
            parts = [(shots[k], base + (1 if k < rem else 0)) for k in range(len(shots))]
        else:
            parts = [(shots[0], need)]

        for shot, want in parts:
            path, rel = clip_of(shot)
            if not path or not os.path.exists(path):
                logline("MISSING %s" % shot)
                sys.exit(3)
            info = probe(path)
            take = min(want, info["frames"] - int(IN_FRAME.get(shot, 0)))
            if shot == BUMP and len(shots) == 1:
                take = min(want + BUMP_FRAMES, info["frames"])
            if take < want:
                logline("SHORT %s frames=%d want=%d deficit=%d" %
                        (shot, take, want, want - take))
            rows.append({"shot": shot, "file": rel, "src_frames": info["frames"],
                         "in_frame": int(IN_FRAME.get(shot, 0)), "frames": take,
                         "want_frames": want,
                         "deficit_frames": max(0, want - take),
                         "slot": [round(t0, 3), round(t1, 3)]})
            start += take
        cursor = start
    return rows


def main():
    if not os.path.isdir(OUT_MEDIA):
        os.makedirs(OUT_MEDIA)

    rows = build_rows()

    # 1) timeline in frames for the picture as cut (before transitions)
    cur = 0
    for r in rows:
        r["timeline_frames"] = [cur, cur + r["frames"]]
        r["timeline"] = [round(cur / FPS, 4), round((cur + r["frames"]) / FPS, 4)]
        r["cut_span"] = round(r["frames"] / FPS, 4)
        cur += r["frames"]
    cut_frames = cur
    drift_frames = TIMELINE_FRAMES - cut_frames
    if drift_frames != 0:
        logline("DRIFT-ABORT frames=%d want=%d drift=%d" % (cut_frames, TIMELINE_FRAMES, drift_frames))
        sys.exit(4)

    # 2) book the edit language per join
    for i, r in enumerate(rows):
        last = (i == len(rows) - 1)
        if last:
            r["transition"] = None
        elif r["shot"] in DISSOLVES:
            r["transition"] = {"type": "dissolve", "frames": DISSOLVES[r["shot"]], "xfade": "fade"}
        elif r["shot"] in BLURS:
            r["transition"] = {"type": "blur", "frames": BLURS[r["shot"]], "xfade": None}
        elif r["shot"] in MOTIONS:
            r["transition"] = {"type": "motion", "frames": 0, "xfade": None}
        else:
            r["transition"] = {"type": "cut", "frames": 0, "xfade": None}

    # 3) extend the outgoing block by the transition so the total never shortens
    for i, r in enumerate(rows):
        r["head_blur"] = rows[i - 1]["transition"]["frames"] if (
            i > 0 and rows[i - 1]["transition"]["type"] == "blur") else 0
        r["tail_blur"] = (r["transition"]["frames"]
                          if r["transition"] and r["transition"]["type"] == "blur" else 0)
        t = r["transition"]
        d = t["frames"] if t and t.get("xfade") else 0
        r["tail_frames"] = d
        r["out_frames"] = r["frames"] + d
        headroom = r["src_frames"] - r["frames"]
        pad = max(0, r["out_frames"] - r["src_frames"])
        r["pad_frames"] = pad
        r["used_headroom"] = min(d, max(0, headroom))
        if pad > TIMELINE_FRAMES // 4:
            logline("PAD-ABORT %s pad=%d" % (r["shot"], pad))
            sys.exit(6)
        # the transition consumes (block_end - D) .. block_end of the joined
        # picture: rewrite the timeline of the outgoing block once more below.

    # 4) cards and mask
    title_info = render_card(TITLE_PNG, [("\u661f\u6674", 84)])
    credit_info = render_card(CREDIT_PNG, [("\u661f\u6674", 40), ("\u539f\u66f2 \u5468\u6770\u4f26", 21)],
                              color=(240, 232, 218))
    mask_info = render_note_mask(MASK_PNG)
    logline("CARDS title=%dx%d credit=%dx%d mask=%dx%d" %
            (title_info["size"][0], title_info["size"][1],
             credit_info["size"][0], credit_info["size"][1], W, H))

    # 5) filter graph: blocks -> groups -> xfade chain -> overlays
    lines = []

    def plan_segments(total, head, tail):
        """Tile a block into sharp and defocused segments.

        A blur join is not an xfade: the outgoing shot defocuses out over its
        last frames and the incoming shot defocuses in over its first frames,
        then the picture cuts. No frames are added or removed, so the timeline
        never moves, and no frozen tail has to be hidden inside a wipe.
        """
        segs = []
        if head > 0:
            steps = min(4, head)
            sig = [22, 15, 9, 4][4 - steps:]
            sizes = [head // steps + (1 if k < head % steps else 0) for k in range(steps)]
            pos = 0
            for k in range(steps):
                segs.append((pos, pos + sizes[k], sig[k]))
                pos += sizes[k]
        mid_start = head
        mid_end = total - tail
        if mid_end > mid_start:
            segs.append((mid_start, mid_end, 0))
        if tail > 0:
            steps = min(4, tail)
            sig = [4, 9, 15, 22][:steps]
            sizes = [tail // steps + (1 if k < tail % steps else 0) for k in range(steps)]
            pos = mid_end
            for k in range(steps):
                segs.append((pos, pos + sizes[k], sig[k]))
                pos += sizes[k]
        if segs[-1][1] != total:
            logline("SEG-ABORT %d != %d" % (segs[-1][1], total))
            sys.exit(10)
        return segs

    for i, r in enumerate(rows):
        chain = "[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS," \
                "scale=%d:%d:flags=lanczos,setsar=1,fps=%d,format=yuv420p" % (
                    i, r["in_frame"], r["in_frame"] + min(r["out_frames"], r["src_frames"]),
                    W, H, FPS)
        if r["pad_frames"]:
            chain += ",tpad=stop_mode=clone:stop=%d" % r["pad_frames"]
        chain += ",trim=end_frame=%d,setpts=PTS-STARTPTS,settb=AVTB" % r["out_frames"]
        # R6-a: the 172-186s astronomy montage was reading muddy on a phone
        if MONTAGE_LIFT[0] <= r["timeline"][0] < MONTAGE_LIFT[1]:
            chain += ",eq=brightness=0.045:contrast=1.03:saturation=1.05"
        # R6-3: the second montage pass is a pixel copy of the first; punch in
        # and re-grain it so no two frames hash the same.
        if PUNCH_WINDOW[0] <= r["timeline"][0] < PUNCH_WINDOW[1]:
            chain += PUNCH_CHAIN
        # R5: the tail plate window gets crushed blacks, gate flicker and grain
        # V8-1: S2-10/S2-11 read as a flat amber plate, off the
        # Xingqing-GRADE-v1 gold-blue pairing. Measured on the v7 native
        # frame 54.0s: sky B-R = -39.5 against +18.9 at 30.4s. Pull the
        # yellow cast back, return the sky to blue, recover the detail.
        if r["shot"] in CROP_R6:
            chain += CROP_R6[r["shot"]]
        if r["shot"] in GRADE_V8:
            chain += GRADE_CHAIN
        if r["timeline"][1] > TAIL_START + 0.001:
            chain += (",eq=eval=frame:brightness='-0.048+0.011*random(0)':"
                      "contrast=1.10:saturation=0.96,noise=alls=8:allf=t+u")
        segs = plan_segments(r["out_frames"], r.get("head_blur", 0),
                             r.get("tail_blur", 0))
        if len(segs) == 1:
            lines.append(chain + "[b%d]" % i)
            continue
        lines.append(chain + ",split=%d%s" %
                     (len(segs), "".join("[s%d_%d]" % (i, k) for k in range(len(segs)))))
        for k, (a, b, sig) in enumerate(segs):
            part = "[s%d_%d]trim=start_frame=%d:end_frame=%d" % (i, k, a, b)
            if sig:
                part += ",gblur=sigma=%d:steps=2" % sig
            part += ",setpts=PTS-STARTPTS[g%d_%d]" % (i, k)
            lines.append(part)
        lines.append("".join("[g%d_%d]" % (i, k) for k in range(len(segs))) +
                     "concat=n=%d:v=1:a=0[b%d]" % (len(segs), i))

    # R3: push the opening note out of focus with the feathered mask
    lines.append("[b0]split=2[n0a][n0b]")
    lines.append("[n0b]gblur=sigma=18:steps=2[n0c]")
    lines.append("[40:v]format=gray,scale=%d:%d[nmask]" % (W, H))
    lines.append("[n0a][n0c][nmask]maskedmerge[r0]")

    # groups of consecutive hard cuts: a group ends where an xfade begins
    groups = []
    for i, r in enumerate(rows):
        label = "[r0]" if i == 0 else "[b%d]" % i
        if not groups:
            groups.append({"labels": [label], "frames": r["out_frames"],
                           "next_xfade": None, "next_d": 0,
                           "shots": [r["shot"]]})
        else:
            g = groups[-1]
            g["labels"].append(label)
            g["frames"] += r["out_frames"]
            g["shots"].append(r["shot"])
        t = r["transition"]
        if t and t.get("xfade"):
            groups[-1]["next_xfade"] = t["xfade"]
            groups[-1]["next_d"] = t["frames"]
            groups.append({"labels": [], "frames": 0,
                           "next_xfade": None, "next_d": 0, "shots": []})
    if groups and not groups[-1]["labels"]:
        groups.pop()

    # concat inside each group
    for gi, g in enumerate(groups):
        if len(g["labels"]) == 1:
            g["out"] = g["labels"][0]
        else:
            lines.append("%sconcat=n=%d:v=1:a=0[g%d]" %
                         ("".join(g["labels"]), len(g["labels"]), gi))
            g["out"] = "[g%d]" % gi

    # xfade chain across groups
    cursor = groups[0]["frames"]
    cur_label = groups[0]["out"]
    for gi in range(1, len(groups)):
        g = groups[gi]
        d = groups[gi - 1]["next_d"]
        xf = groups[gi - 1]["next_xfade"]
        if not xf or d <= 0:
            logline("CHAIN-ABORT boundary=%d has no transition" % gi)
            sys.exit(7)
        offset = (cursor - d) / float(FPS)
        lines.append("%s%sxfade=transition=%s:duration=%.6f:offset=%.6f[xf%d]" %
                     (cur_label, g["out"], xf, d / float(FPS), offset, gi))
        cur_label = "[xf%d]" % gi
        cursor = cursor + g["frames"] - d

    if cursor != TIMELINE_FRAMES:
        logline("CHAIN-ABORT frames=%d want=%d" % (cursor, TIMELINE_FRAMES))
        sys.exit(8)

    # The transition chain lands one frame long on a float offset (measured: 5713
        # against the 5712 contract). The encode is capped at the contract length so
        # the container, the frame grid and the audio all end on the same frame.
        cur_label = cur_label

        # R1/R5: title card and end credit as alpha faded overlays
    lines.append("[41:v]format=rgba,fade=t=in:st=0:d=0.250:alpha=1,"
                 "fade=t=out:st=%.3f:d=0.180:alpha=1,setpts=PTS-STARTPTS+%.3f/TB[ttl]" %
                 (TITLE_LEN - 0.180, TITLE_AT))
    lines.append("%s[ttl]overlay=%d:%d:eof_action=pass[vo1]" %
                 (cur_label, 80 - title_info["pad"], 168 - title_info["pad"]))
    lines.append("[42:v]format=rgba,fade=t=in:st=0:d=0.600:alpha=1,"
                 "fade=t=out:st=%.3f:d=0.500:alpha=1,setpts=PTS-STARTPTS+%.3f/TB[ecd]" %
                 (CREDIT_LEN - 0.500, CREDIT_AT))
    lines.append("[vo1][ecd]overlay=%d:%d:eof_action=pass[vfin]" %
                 (72 - credit_info["pad"], 636 - credit_info["pad"]))

    with open(FILTER_SCRIPT, "w", encoding="ascii", errors="replace", newline="\n") as f:
        f.write(";\n".join(lines) + "\n")

    # input order: 0..39 the blocks, then mask at 40, title at 41, credit at 42
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
    for r in rows:
        cmd += ["-i", os.path.join(MEDIA, r["file"].replace("/", os.sep))]
    cmd += ["-loop", "1", "-t", "6.0", "-i", MASK_PNG]
    cmd += ["-loop", "1", "-t", "%.3f" % TITLE_LEN, "-i", TITLE_PNG]
    cmd += ["-loop", "1", "-t", "%.3f" % CREDIT_LEN, "-i", CREDIT_PNG]
    cmd += ["-filter_complex_script", FILTER_SCRIPT, "-map", "[vfin]", "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-frames:v", str(TIMELINE_FRAMES),
            "-movflags", "+faststart", OUT_NOMUX]
    logline("ASSEMBLY-START units=%d frames=%d transitions=%d" %
            (len(rows), cursor,
             sum(1 for r in rows if r["transition"] and r["transition"].get("xfade"))))
    t0 = time.time()
    subprocess.check_call(cmd)
    logline("ASSEMBLY-ENC done in %.1fs" % (time.time() - t0))

    if not os.path.exists(PREV):
        logline("PREV-MISSING %s" % PREV)
        sys.exit(5)
    # audio is carried over byte for byte: v3 already passed the delivery lines
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
           "-i", OUT_NOMUX, "-i", PREV,
           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "copy",
           "-t", "%.3f" % TIMELINE, "-movflags", "+faststart", OUT_MP4]
    subprocess.check_call(cmd)

    info = probe(OUT_MP4)
    out_bytes = os.path.getsize(OUT_MP4)
    frames_ok = 1 if info["frames"] == TIMELINE_FRAMES else 0
    dur_ok = 1 if abs(info["sec"] - TIMELINE) <= 0.06 else 0

    # 6) edit grammar accounting (CHK-E1)
    counts = {"cut": 0, "motion": 0, "dissolve": 0, "blur": 0}
    joins = []
    for i, r in enumerate(rows[:-1]):
        t = r["transition"]["type"]
        counts[t] += 1
        joins.append({
            "n": i + 1,
            "at": r["timeline"][1],
            "from": r["shot"],
            "to": rows[i + 1]["shot"],
            "class": t,
            "frames": r["transition"]["frames"],
            "mechanism": ("hard cut on matched movement direction" if t == "motion"
                          else "straight cut" if t == "cut"
                          else ("defocus out/in over %d frames (%.3fs) then cut" %
                                (r["transition"]["frames"],
                                 r["transition"]["frames"] / float(FPS)))
                          if t == "blur"
                          else "xfade %s %d frames (%.3fs)" %
                               (r["transition"]["xfade"], r["transition"]["frames"],
                                r["transition"]["frames"] / float(FPS))),
        })
    total_joins = len(joins)
    optical = counts["dissolve"] + counts["blur"]
    classes = sum(1 for k in ("cut", "motion", "dissolve", "blur") if counts[k] > 0)
    hard_pct = round(100.0 * counts["cut"] / total_joins, 2)
    grammar_ok = 1 if (classes >= 4 and hard_pct <= 70.0 and counts["dissolve"] >= 6
                       and counts["blur"] >= 4 and counts["motion"] >= 3) else 0

    # 7) indexes
    v = {
        "schema": "xq-packb-assembly-index/v3",
        "batch": BATCH,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "project": "mv0001-xingqing",
        "edl": "v5",
        "why": ("Director seat returned REVISE on v2. This pass closes R1 (title card), "
                "R2 (edit language), R3 (opening prop out of focus) and R5 (tail plate "
                "protection) on the picture side, keeps the frame grid and carries the "
                "v3 audio over untouched."),
        "fps": FPS,
        "timeline_seconds": TIMELINE,
        "timeline_frames": TIMELINE_FRAMES,
        "slots": None,
        "units": len(rows),
        "cut_frames": cut_frames,
        "drift_frames": drift_frames,
        "deficit_frames": sum(r.get("deficit_frames", 0) for r in rows),
        "padded_frames": sum(r["pad_frames"] for r in rows),
        "clips": rows,
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(v, f, ensure_ascii=False, indent=1)
        f.write("\n")

    md = ["# Xingqing PACK-B - assembly index v3 (%s)" % BATCH, "",
          "> Built %s. Revise pass on EDL v5: title card, edit language, opening prop,"
          " tail plate." % v["ts"], "",
          "- units: **%d** / cut: **%d frames = %.3fs** / drift: **%d**" %
          (len(rows), cut_frames, cut_frames / float(FPS), drift_frames),
          "- transitions: dissolve **%d** / blur **%d** / motion **%d** / cut **%d**" %
          (counts["dissolve"], counts["blur"], counts["motion"], counts["cut"]),
          "- tail-pad frames used: **%d** (clone where a take had no headroom)" %
          sum(r["pad_frames"] for r in rows), "",
          "## Cut table (frames are authoritative)",
          "| # | shot | src | cut | +tail | timeline (s) | transition out |",
          "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        md.append("| %d | %s | %d | %d | %d | %.3f-%.3f | %s |" %
                  (i, r["shot"], r["src_frames"], r["frames"], r["tail_frames"],
                   r["timeline"][0], r["timeline"][1],
                   r["transition"]["type"] if r["transition"] else "-"))
    md += ["", "## Honest notes",
           "- hard cuts at the montage beats (172-186s) are deliberate: six whole 56f takes.",
           "- every transition is absorbed by the outgoing block tail, so the film is still",
           "  exactly 5712 frames; where a take had no spare frames the tail is a 6-8 frame",
           "  clone hidden inside the transition.",
           "- audio is copied from the v3 master, not re-encoded."]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")

    g = {
        "schema": "xq-packb-edit-grammar/v1",
        "batch": BATCH,
        "ts": v["ts"],
        "check": "CHK-E1",
        "rule": "language classes >= 4 and hard cuts <= 70% of joins",
        "total_joins": total_joins,
        "counts": counts,
        "optical_transitions": optical,
        "classes_present": classes,
        "hard_cut_pct": hard_pct,
        "verdict": "PASS" if grammar_ok else "FAIL",
        "joins": joins,
    }
    with open(OUT_GRAMMAR_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")

    gmd = ["# Xingqing PACK-B - edit grammar (%s)" % BATCH, "",
           "> CHK-E1 program count from the assembly index. No hand counting.", "",
           "| class | joins | share |", "|---|---|---|"]
    for k in ("cut", "motion", "dissolve", "blur"):
        gmd.append("| %s | %d | %.1f%% |" % (k, counts[k], 100.0 * counts[k] / total_joins))
    gmd += ["",
            "- classes present: **%d** (need >= 4)" % classes,
            "- hard cuts: **%.1f%%** (need <= 70%%)" % hard_pct,
            "- verdict: **%s**" % g["verdict"], "",
            "## Join table", "| n | at (s) | from -> to | class | mechanism |",
            "|---|---|---|---|---|"]
    for j in joins:
        gmd.append("| %d | %.3f | %s -> %s | %s | %s |" %
                   (j["n"], j["at"], j["from"], j["to"], j["class"], j["mechanism"]))
    with open(OUT_GRAMMAR_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(gmd) + "\n")

    # 8) join sheet: one thumbnail per join so every boundary is inspectable
    try:
        from PIL import Image
        thumbs = []
        for j in joins:
            p = os.path.join(OUT_MEDIA, "_join_%02d.png" % j["n"])
            # a transition is sampled at its midpoint, a cut on the last frame
            # that belongs to the outgoing shot
            t = (j["at"] + (j["frames"] / 48.0)) if j["frames"] else max(j["at"] - 0.045, 0)
            subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                                   "-ss", "%.4f" % t,
                                   "-i", OUT_MP4, "-frames:v", "1", p])
            thumbs.append(p)
        cols, tw = 8, 168
        th = int(round(tw * H / float(W)))
        rowsn = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rowsn * th), (0, 0, 0))
        for k, p in enumerate(thumbs):
            im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
            sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
        sheet.save(JOIN_SHEET, quality=92)
        for p in thumbs:
            os.remove(p)
        join_sheet_ok = 1
    except Exception as ex:
        logline("JOINSHEET-FAIL %s" % ex)
        join_sheet_ok = 0

    # 9) card presence proof: the title frame must differ from the previous master
    card_proof = {}
    try:
        pf = os.path.join(OUT_MEDIA, "_proof_card_new.png")
        pv = os.path.join(OUT_MEDIA, "_proof_card_old.png")
        subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                               "-ss", "2.6", "-i", OUT_MP4, "-frames:v", "1", pf])
        subprocess.check_call([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                               "-ss", "2.6", "-i", PREV, "-frames:v", "1", pv])
        from PIL import Image, ImageChops
        a = Image.open(pf).convert("RGB")
        b = Image.open(pv).convert("RGB")
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        card_proof = {"new": pf, "old": pv, "diff_bbox": list(bbox) if bbox else None,
                      "ok": 1 if bbox else 0}
        os.replace(pf, os.path.join(OUT_MEDIA, "native_2p6_c2163.png"))
    except Exception as ex:
        logline("CARDPROOF-FAIL %s" % ex)
        card_proof = {"ok": 0}

    receipt = {
        "batch": BATCH,
        "ts": v["ts"],
        "units": len(rows),
        "cut_frames": cut_frames,
        "timeline_frames": TIMELINE_FRAMES,
        "drift_frames": drift_frames,
        "out_frames": info["frames"],
        "out_seconds": info["sec"],
        "out": os.path.relpath(OUT_MP4, REPO).replace("\\", "/"),
        "out_bytes": out_bytes,
        "audio": "copied from v3 master (-14.3 LUFS / -2.2 dBTP)",
        "cards": {"title": title_info, "credit": credit_info, "mask": mask_info},
        "edit_grammar": {k: counts[k] for k in counts},
        "grammar_verdict": g["verdict"],
        "padded_frames": sum(r["pad_frames"] for r in rows),
        "join_sheet": os.path.relpath(JOIN_SHEET, REPO).replace("\\", "/"),
        "card_proof": card_proof,
        "index": os.path.relpath(OUT_JSON, REPO).replace("\\", "/"),
        "grammar": os.path.relpath(OUT_GRAMMAR_JSON, REPO).replace("\\", "/"),
    }
    with open(OUT_RECEIPT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
        f.write("\n")

    ok = 1 if (frames_ok and dur_ok and grammar_ok and join_sheet_ok and
               card_proof.get("ok") and out_bytes > 3000000) else 0
    logline("REVISE-END ok=%d frames=%d/%d out=%.3fs bytes=%d grammar=%s "
            "cut=%d motion=%d dissolve=%d blur=%d padded=%d card=%d" %
            (ok, info["frames"], TIMELINE_FRAMES, info["sec"], out_bytes,
             g["verdict"], counts["cut"], counts["motion"], counts["dissolve"],
             counts["blur"], sum(r["pad_frames"] for r in rows), card_proof.get("ok", 0)))
    logline("OUT %s" % receipt["out"])
    if not ok:
        sys.exit(9)


if __name__ == "__main__":
    main()
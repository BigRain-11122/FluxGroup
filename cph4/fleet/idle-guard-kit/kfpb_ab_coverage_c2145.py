# -*- coding: utf-8 -*-
"""kfpb_ab_coverage_c2145.py -- Xingqing A+B keyframe coverage board.

Authorization: bank job kfpb-ab-coverage-c2145; xq-CASTING-VERDICT-c2136-full.md sec-4 item 3
(the A+B coverage board is the gate before any i2v wave).

What it does (zero GPU, read-only over the frame dirs):
  1. parse Xingqing-SHOTLIST-v3.md for every shot row that belongs to pack A or B, with its
     time window;
  2. scan the known xingqing frame directories and map each PNG filename to a shot id;
  3. emit a JSON coverage map (per shot: window, pack, dirs that hold frames, frame count) and a
     timeline board PNG where covered seconds are green, uncovered seconds are red, and pack B
     shots are ticked underneath.

It does NOT judge frame quality - that is the verdict jobs' job. A shot counts as covered when at
least one PNG for its id exists on disk.
"""
import io, json, os, re, sys

ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay")
SHOTLIST = os.path.join(ALBUM, "\u661f\u6674-SHOTLIST-v3.md")
XQ = os.path.join(ROOT, "media", "MV", "mv0001", "xingqing")
OUT_PNG = os.path.join(ALBUM, "xq-KF-COVERAGE-c2145.png")
OUT_JSON = os.path.join(ALBUM, "xq-KF-COVERAGE-c2145.json")

# Frame directories that hold KF renders for this video. Directories that only hold casting
# plates or probe boards are excluded on purpose.
FRAME_DIRS = [
    "abatch", "abatch_s7r", "t1", "t1r1", "t1r1hd", "delivery",
    "s7r-4k", "kfreroll-r1", "s527reshake", "f533c-reroll2",
    "xq-kf-packb-mainpass-c2144", "xq-kf-s317-feet-c2145",
]

SHOT_RE = re.compile(r"^(?:KFPB_MP_)?([A-Z]\d+-\d+[a-c]?)")
WIN_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[-\u2013]\s*(\d+(?:\.\d+)?)")
ID_RE = re.compile(r"^([A-Z]\d+-)(\d+(?:/\d+)*)([a-c]?)$")


def expand_id(raw):
    """S2-11/12/13 -> [S2-11, S2-12, S2-13]."""
    m = ID_RE.match(raw)
    if not m:
        return [raw]
    prefix, nums, suffix = m.group(1), m.group(2), m.group(3)
    return [prefix + n + suffix for n in nums.split("/")]


def parse_shotlist():
    rows = []
    for line in io.open(SHOTLIST, encoding="utf-8").read().split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 9 or cells[0] in ("\u955c\u4f4d", "") or set(cells[0]) <= set("-: "):
            continue
        pack = cells[7].strip()
        if pack not in ("A", "B"):
            continue
        m = WIN_RE.search(cells[3])
        if not m:
            continue
        t0, t1 = float(m.group(1)), float(m.group(2))
        for sid in expand_id(cells[0]):
            rows.append({"shot": sid, "pack": pack, "t0": t0, "t1": t1,
                         "type": cells[1], "window_raw": cells[3]})
    return rows


def scan_frames():
    """shot id -> {dir: [filenames]}"""
    found = {}
    for d in FRAME_DIRS:
        p = os.path.join(XQ, d)
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            if not fn.lower().endswith(".png"):
                continue
            m = SHOT_RE.match(fn)
            if not m:
                continue
            found.setdefault(m.group(1), {}).setdefault(d, []).append(fn)
    return found


def build():
    shots = parse_shotlist()
    frames = scan_frames()
    covered, gaps = [], []
    for s in shots:
        hit = frames.get(s["shot"], {})
        s["dirs"] = sorted(hit)
        s["n_frames"] = sum(len(v) for v in hit.values())
        (covered if s["n_frames"] else gaps).append(s)

    total = max([s["t1"] for s in shots] + [0.0])

    # True timeline coverage = union of the shot windows, so holes between shots are reported
    # instead of being hidden behind the per-shot "missing" count.
    spans = sorted((s["t0"], s["t1"]) for s in shots)
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 1e-9:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    holes, cursor = [], 0.0
    for a, b in merged:
        if a - cursor > 1e-9:
            holes.append([round(cursor, 2), round(a, 2)])
        cursor = max(cursor, b)
    if total - cursor > 1e-9:
        holes.append([round(cursor, 2), round(total, 2)])
    union_s = round(sum(b - a for a, b in merged), 1)
    hole_s = round(sum(b - a for a, b in holes), 1)

    payload = {
        "wave": "xq-kf-coverage-c2145",
        "runner": "bm-c C2145",
        "auth": "bank job kfpb-ab-coverage-c2145; casting verdict c2136 sec-4 item 3",
        "shotlist": os.path.relpath(SHOTLIST, ROOT).replace("\\", "/"),
        "frame_dirs": FRAME_DIRS,
        "timeline_seconds": total,
        "shots_total": len(shots),
        "shots_covered": len(covered),
        "shots_missing": len(gaps),
        "uncovered_seconds": hole_s,
        "covered_seconds": union_s,
        "timeline_holes": holes,
        "shots": shots,
        "gaps": [g["shot"] for g in gaps],
        "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
    }
    io.open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n")

    from PIL import Image, ImageDraw, ImageFont
    F = lambda n, b=False: ImageFont.truetype(
        os.path.join(r"C:\Windows\Fonts", "arialbd.ttf" if b else "arial.ttf"), n)
    W, H = 1500, 150 + 62 * max(1, (len(shots) + 1) // 2)
    img = Image.new("RGB", (W, H), (16, 16, 16))
    d = ImageDraw.Draw(img)
    d.text((24, 18), "XINGQING  A+B KEYFRAME COVERAGE  c2145", font=F(26, True), fill=(235, 235, 235))
    d.text((24, 54), "shots %d  |  covered %d  |  missing %d  |  covered %.1fs  |  uncovered %.1fs  of %.1fs"
           % (len(shots), len(covered), len(gaps), payload["covered_seconds"],
              payload["uncovered_seconds"], total), font=F(16), fill=(170, 170, 170))

    # timeline bar
    x0, x1, y0, y1 = 24, W - 24, 96, 132
    d.rectangle([x0, y0, x1, y1], fill=(40, 26, 26))
    span = max(total, 1.0)
    for s in shots:
        a = x0 + (s["t1"] - s["t0"] > 0 and (s["t0"] / span) * (x1 - x0))
        b = x0 + (s["t1"] / span) * (x1 - x0)
        col = (66, 150, 96) if s["n_frames"] else (168, 58, 58)
        h = y1 if s["pack"] == "A" else y1 - 12
        d.rectangle([a, y0 + (0 if s["pack"] == "A" else 12), b, h], fill=col)
    d.text((x0, y1 + 4), "0s", font=F(13), fill=(140, 140, 140))
    d.text((x1 - 44, y1 + 4), "%.0fs" % total, font=F(13), fill=(140, 140, 140))

    # per-shot columns
    y = 158
    for i, s in enumerate(shots):
        col_x = 24 if i % 2 == 0 else W // 2 + 8
        if i % 2 == 0 and i:
            y += 62
        ok = s["n_frames"] > 0
        d.text((col_x, y), "%s  [%s]  %s  %s"
               % (s["shot"], s["pack"], s["window_raw"], "OK" if ok else "MISSING"),
               font=F(15, True), fill=(120, 200, 150) if ok else (225, 110, 110))
        detail = ("%d frames in %s" % (s["n_frames"], ",".join(s["dirs"])[:70])) if ok else "no PNG on disk"
        d.text((col_x, y + 20), detail, font=F(13), fill=(160, 160, 160))

    img.save(OUT_PNG)
    print("COVERAGE shots=%d covered=%d missing=%d timeline_holes=%.1fs"
          % (len(shots), len(covered), len(gaps), hole_s))
    print("COVERAGE holes=%s" % (",".join("%.2f-%.2fs" % (a, b) for a, b in holes) or "none"))
    print("COVERAGE gaps=%s" % (",".join(payload["gaps"]) or "none"))
    print("COVERAGE board %s %dB" % (OUT_PNG, os.path.getsize(OUT_PNG)))
    print("COVERAGE json  %s %dB" % (OUT_JSON, os.path.getsize(OUT_JSON)))
    return 0


if __name__ == "__main__":
    sys.exit(build())
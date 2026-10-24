# kn_768p_sampled_board_c2172.py - mid-wave sampled board for the KN 768P wave (C2172).
# The wave is still burning (10/30 landed). This builds human-reviewable contact
# boards of native frames so the wave can be judged while it is in flight instead of
# only after it drains, and records the per-unit declarative facts (window vs decoded
# duration, authored camera intent, birth-gate verdict) next to the pictures.
import glob
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

REPO = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2172")
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MANIFEST = os.path.join(OUTDIR, "local-i2v", "run-bmc-kn-i2v.json")
GUARD = os.path.join(ALBUM, "evidence-c2170", "pseudotext-guard.json")
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
PER_BOARD = 5
COLS = 3
CELL_W = 448
PAD = 8
HEAD = 40


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def grab(path, sec, dest):
    # -ss after -i keeps the seek exact enough for a contact sheet
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", path, "-ss", "%.3f" % sec,
         "-frames:v", "1", dest],
        check=True)
    return Image.open(dest).convert("RGB")


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def main():
    os.makedirs(EVID, exist_ok=True)
    with open(MANIFEST, encoding="utf-8") as fh:
        units = {u["id"]: u for u in json.load(fh).get("units", [])}
    guard = {}
    if os.path.exists(GUARD):
        with open(GUARD, encoding="utf-8") as fh:
            guard = {r["clip"]: r for r in json.load(fh).get("rows", [])}

    clips = sorted(glob.glob(os.path.join(CLIPS, "KN_A-KN*.mp4")))
    rows = []
    tiles = []
    for clip in clips:
        name = os.path.splitext(os.path.basename(clip))[0]
        dur = probe_duration(clip)
        if dur <= 0:
            continue
        stamps = (0.4, max(0.5, dur / 2.0), max(0.6, dur - 0.35))
        frames = []
        for i, ts in enumerate(stamps):
            dst = os.path.join(EVID, "%s-t%02d.png" % (name, i))
            frames.append((ts, grab(clip, ts, dst)))
        g = guard.get(os.path.basename(clip), {})
        u = units.get(name, {})
        rows.append({
            "unit": name,
            "clip": os.path.relpath(clip, REPO).replace("\\", "/"),
            "win_s": u.get("win_s"),
            "src_s": u.get("src_s"),
            "decoded_s": round(dur, 3),
            "intent": g.get("intent", "-"),
            "pseudo": g.get("verdict", "-"),
            "framing": g.get("framing", "-"),
            "max_zoom": g.get("max_zoom"),
            "max_zoom_at_sec": g.get("max_zoom_at_sec"),
            "bytes": os.path.getsize(clip),
        })
        tiles.append((name, g, frames))

    boards = []
    for b in range(0, len(tiles), PER_BOARD):
        chunk = tiles[b:b + PER_BOARD]
        cell_h = int(CELL_W * chunk[0][2][0][1].size[1] / chunk[0][2][0][1].size[0])
        rowsn = len(chunk)
        board = Image.new("RGB", (COLS * CELL_W + PAD * (COLS + 1),
                                  HEAD + rowsn * (cell_h + PAD) + PAD), (18, 18, 18))
        d = ImageDraw.Draw(board)
        f_big = font(24)
        f_sm = font(18)
        first = chunk[0][0]
        last = chunk[-1][0]
        d.text((PAD, 8), "KN 768P wave sampled board (batch C2172) - %s..%s - native 1344x768"
               % (first, last), fill=(240, 240, 240), font=f_big)
        for r, (name, g, frames) in enumerate(chunk):
            y = HEAD + r * (cell_h + PAD)
            intent = g.get("intent", "-")
            tag = "pseudo=%s framing=%s" % (g.get("verdict", "-"), g.get("framing", "-"))
            if g.get("max_zoom"):
                tag += " zoom=%.2fx@%.1fs" % (g["max_zoom"], float(g.get("max_zoom_at_sec") or 0))
            for c, (ts, im) in enumerate(frames):
                x = PAD + c * (CELL_W + PAD)
                im = im.resize((CELL_W, cell_h), Image.LANCZOS)
                board.paste(im, (x, y))
                d.text((x + 8, y + 6), "%.2fs" % ts, fill=(255, 235, 120), font=f_sm)
            d.text((PAD, y + cell_h - 24), "%s [%s] %s" % (name, intent, tag),
                   fill=(160, 255, 160), font=f_sm)
        out = os.path.join(OUTDIR, "KN-768P-BOARD-%d-c2172.jpg" % (b // PER_BOARD + 1))
        board.save(out, quality=88)
        boards.append(out)
        print("BOARD %s %dB" % (out, os.path.getsize(out)))

    verdict = {
        "batch": "C2172",
        "wave_manifest": os.path.relpath(MANIFEST, REPO).replace("\\", "/"),
        "landed": len(rows),
        "planned": len(units),
        "boards": [os.path.relpath(p, REPO).replace("\\", "/") for p in boards],
        "rows": rows,
        "note": ("Mid-wave sample, not a landing verdict. Duration is decoded from the "
                 "delivered mp4 and compared with the authored src_s window; intent and "
                 "birth-gate columns come from evidence-c2170/pseudotext-guard.json so the "
                 "board and the gate cannot drift apart."),
    }
    vp = os.path.join(EVID, "sampled-board.json")
    with open(vp, "w", encoding="utf-8") as fh:
        json.dump(verdict, fh, ensure_ascii=False, indent=1)
    print("VERDICT %s landed=%d/%d boards=%d" % (vp, len(rows), len(units), len(boards)))


if __name__ == "__main__":
    main()
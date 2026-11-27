# C2177: gate board for the KN units that landed after the C2176 pass (KN18-KN20),
# plus the two reference rows the new verdicts are read against: KN11 (declared
# push rendered flat) and KN17 (declared push actually rendered). Same shape as
# kn_pa768_gate_board_c2176.py: this script does not judge anything, it only lays
# native frames next to the verdict JSONs that already exist on disk, so board and
# gates cannot drift apart.
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

REPO = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2177")
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
FRAMING = os.path.join(EVID, "framing-drift-c2177.json")
PSEUDO = os.path.join(EVID, "pseudotext-c2177.json")
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
COLS = 3
CELL_W = 448
PAD = 8
HEAD = 40
UNITS = ["KN_A-KN11", "KN_A-KN17", "KN_A-KN18", "KN_A-KN19", "KN_A-KN20"]


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


def load_rows(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return {r["clip"]: r for r in json.load(fh).get("rows", [])}


def main():
    os.makedirs(EVID, exist_ok=True)
    framing = load_rows(FRAMING)
    pseudo = load_rows(PSEUDO)
    tiles, rows = [], []
    for name in UNITS:
        clip = os.path.join(CLIPS, name + ".mp4")
        if not os.path.exists(clip):
            continue
        dur = probe_duration(clip)
        if dur <= 0:
            continue
        stamps = (0.4, max(0.5, dur / 2.0), max(0.6, dur - 0.35))
        frames = []
        for i, ts in enumerate(stamps):
            frames.append((ts, grab(clip, ts, os.path.join(EVID, "%s-t%02d.png" % (name, i)))))
        f = framing.get(name + ".mp4", {})
        p = pseudo.get(name + ".mp4", {})
        rows.append({
            "unit": name,
            "intent": f.get("intent"),
            "zoom": f.get("max_zoom"),
            "framing": f.get("verdict", "NOT-RUN"),
            "reason": f.get("reason"),
            "series": f.get("series"),
            "pseudo": p.get("verdict", "not-scanned-this-round"),
        })
        tiles.append((name, f, p, frames))

    if not tiles:
        print("NO_TILES")
        return 1

    cell_h = int(CELL_W * tiles[0][3][0][1].size[1] / tiles[0][3][0][1].size[0])
    board = Image.new("RGB", (COLS * CELL_W + PAD * (COLS + 1),
                              HEAD + len(tiles) * (cell_h + PAD) + PAD), (18, 18, 18))
    d = ImageDraw.Draw(board)
    f_big, f_sm = font(24), font(18)
    d.text((PAD, 8), "KN 768P birth-gate board (batch C2177) - native 1344x768",
           fill=(240, 240, 240), font=f_big)
    for r, (name, f, p, frames) in enumerate(tiles):
        y = HEAD + r * (cell_h + PAD)
        for c, (ts, im) in enumerate(frames):
            x = PAD + c * (CELL_W + PAD)
            board.paste(im.resize((CELL_W, cell_h), Image.LANCZOS), (x, y))
            d.text((x + 8, y + 6), "%.2fs" % ts, fill=(255, 235, 120), font=f_sm)
        colour = (160, 255, 160)
        if f.get("verdict") == "FLAT":
            colour = (255, 120, 120)
        elif f.get("verdict") == "UNDECIDED":
            colour = (255, 200, 110)
        d.text((PAD, y + cell_h - 24),
               "%s intent=%s zoom=%.2fx %s | pseudo=%s"
               % (name, f.get("intent"), float(f.get("max_zoom") or 0),
                  f.get("verdict", "NOT-RUN"), p.get("verdict", "-")),
               fill=colour, font=f_sm)
    out = os.path.join(OUTDIR, "KN-768P-GATE-BOARD-1-c2177.jpg")
    board.save(out, quality=88)
    print("BOARD %s %dB" % (out, os.path.getsize(out)))

    doc = {"batch": "C2177", "scope": "KN units landed after the C2176 pass, plus the two reference rows",
           "boards": [os.path.relpath(out, REPO).replace("\\", "/")],
           "gates": {"framing": os.path.relpath(FRAMING, REPO).replace("\\", "/"),
                     "pseudo": os.path.relpath(PSEUDO, REPO).replace("\\", "/")},
           "rows": rows}
    vp = os.path.join(EVID, "gate-board.json")
    with open(vp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("VERDICT %s rows=%d" % (vp, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
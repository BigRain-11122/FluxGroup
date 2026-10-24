# C2178: eye station for the KN15 class. This script judges nothing - it lays
# native frames next to the verdicts that already exist on disk (framing gate,
# pseudo-text, prompt hygiene), plus the eye verdict recorded in the notes file,
# so the board and the gates cannot drift apart.
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

REPO = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2178")
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
NOTES = os.path.join(EVID, "unit-notes-c2178.json")
FRAMING = os.path.join(ALBUM, "evidence-c2177", "framing-drift-c2177.json")
HYGIENE = os.path.join(EVID, "hygiene-manifest-legacy-c2178.json")
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
COLS = 3
CELL_W = 448
PAD = 8
HEAD = 44


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def grab(path, sec, dest):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ss", "%.3f" % sec,
                    "-frames:v", "1", dest], check=True)
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
    with open(NOTES, encoding="utf-8") as fh:
        notes = json.load(fh)
    framing = load_rows(FRAMING)
    hygiene = {r["unit"]: r for r in json.load(open(HYGIENE, encoding="utf-8"))["rows"]}

    tiles, rows = [], []
    for item in notes["units"]:
        name = item["unit"]
        clip = os.path.join(CLIPS, name + ".mp4")
        if not os.path.exists(clip):
            continue
        dur = probe_duration(clip)
        if dur <= 0:
            continue
        stamps = (0.4, max(0.5, dur / 2.0), max(0.6, dur - 0.35))
        frames = [(ts, grab(clip, ts, os.path.join(EVID, "%s-t%02d.png" % (name, i))))
                  for i, ts in enumerate(stamps)]
        f = framing.get(name + ".mp4", {})
        h = hygiene.get(name, {})
        rows.append({"unit": name, "eye": item["eye"], "note": item["note"],
                     "framing": f.get("verdict", "NOT-RUN"), "zoom": f.get("max_zoom"),
                     "hygiene": h.get("verdict", "n/a"),
                     "hygiene_terms": h.get("fail", []) + h.get("warn", [])})
        tiles.append(frames)

    if not tiles:
        print("NO_TILES")
        return 1

    cell_h = int(CELL_W * tiles[0][0][1].size[1] / tiles[0][0][1].size[0])
    board = Image.new("RGB", (COLS * CELL_W + PAD * (COLS + 1),
                              HEAD + len(tiles) * (cell_h + PAD) + PAD), (18, 18, 18))
    d = ImageDraw.Draw(board)
    f_big, f_sm = font(22), font(17)
    d.text((PAD, 8), "KN 768P eye station (C2178) - native 1344x768, 3 frames per unit",
           fill=(240, 240, 240), font=f_big)
    for r, frames in enumerate(tiles):
        row = rows[r]
        y = HEAD + r * (cell_h + PAD)
        for c, (ts, im) in enumerate(frames):
            x = PAD + c * (CELL_W + PAD)
            board.paste(im.resize((CELL_W, cell_h), Image.LANCZOS), (x, y))
            d.text((x + 8, y + 6), "%.2fs" % ts, fill=(255, 235, 120), font=f_sm)
        colour = (160, 255, 160) if row["eye"] == "OK" else (
            (255, 200, 110) if row["eye"] == "THIN" else (255, 120, 120))
        d.text((PAD, y + cell_h - 24),
               "%s  eye=%s  framing=%s(%.2fx)  hygiene=%s"
               % (row["unit"], row["eye"], row["framing"], float(row["zoom"] or 0),
                  row["hygiene"]),
               fill=colour, font=f_sm)
        d.text((PAD, y + cell_h - 44), row["note"].encode("ascii", "replace").decode(),
               fill=(210, 210, 210), font=f_sm)

    out = os.path.join(OUTDIR, "KN-768P-EYE-BOARD-1-c2178.jpg")
    board.save(out, quality=88)
    print("BOARD %s %dB" % (out, os.path.getsize(out)))
    doc = {"batch": "C2178",
           "scope": "KN15 plate/set drift against clean controls and the empty-sky unit",
           "board": os.path.relpath(out, REPO).replace("\\", "/"),
           "notes": os.path.relpath(NOTES, REPO).replace("\\", "/"),
           "rows": rows}
    with open(os.path.join(EVID, "eye-board.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("VERDICT rows=%d" % len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
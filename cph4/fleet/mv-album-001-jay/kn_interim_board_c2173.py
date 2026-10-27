# kn_interim_board_c2173.py - one frame per landed KN unit, in cut order, on a single board.
# Purpose: the interim cut can be watched, but counting a repeating MOTIF across the cut
# needs all 13 setups side by side. Purely a reading aid: no verdicts, no scores.
import glob
import io
import json
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

ALBUM = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2173")
OUTDIR = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay"
CELL_W, PAD, HEAD, COLS = 336, 6, 26, 4
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"


def font(sz):
    try:
        return ImageFont.truetype(FONT_PATH, sz)
    except Exception:
        return ImageFont.load_default()


def main():
    tl = io.open(glob.glob(os.path.join(OUTDIR, "*shots-v2.py"))[0], encoding="utf-8").read()
    first = {}
    for shot, s, e, sp in re.findall(r'\("(KN\d+[a-z]?)",\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)', tl):
        first.setdefault(shot, (float(s), float(e)))
    items = []
    for clip in sorted(glob.glob(os.path.join(CLIPS, "KN_A-KN*.mp4")),
                       key=lambda p: int(re.search(r"KN(\d+)", os.path.basename(p)).group(1))):
        shot = re.search(r"(KN\d+)", os.path.basename(clip)).group(1)
        items.append((shot, clip))
    cell_h = int(CELL_W * 768 / 1344)
    rows = (len(items) + COLS - 1) // COLS
    W = COLS * (CELL_W + PAD) + PAD
    H = HEAD + rows * (cell_h + PAD + 16) + PAD
    board = Image.new("RGB", (W, H), (16, 16, 16))
    d = ImageDraw.Draw(board)
    d.text((PAD, 5), "KN 768P landed units in cut order (C2173)", font=font(16), fill=(220, 220, 220))
    for i, (shot, clip) in enumerate(items):
        tmp = os.path.join(EVID, "_b%s.png" % shot)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "default=nw=1:nk=1", clip],
                                   capture_output=True, text=True).stdout.strip() or 0)
        subprocess.run([r"C:\Program Files\ffmpeg\bin\ffmpeg.exe", "-v", "error", "-y",
                        "-ss", "%.3f" % (dur * 0.45), "-i", clip, "-frames:v", "1",
                        "-vf", "scale=%d:-1" % CELL_W, tmp], check=True)
        im = Image.open(tmp).convert("RGB")
        x = PAD + (i % COLS) * (CELL_W + PAD)
        y = HEAD + (i // COLS) * (cell_h + PAD + 16)
        board.paste(im, (x, y))
        t0 = first.get(shot, (0, 0))[0]
        d.text((x, y + im.height + 2), "%s  t=%.2fs  %ds" % (shot, t0, round(dur)),
               font=font(13), fill=(190, 190, 190))
    out = os.path.join(EVID, "KN-INTERIM-BOARD-c2173.jpg")
    board.save(out, quality=88)
    print(out, board.size)


if __name__ == "__main__":
    main()
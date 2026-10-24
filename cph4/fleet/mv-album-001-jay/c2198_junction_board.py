"""C2198: director-pass board for the KN film v3 - the KN17 -> KN18 junction and the moon halo.

Two things need eyes on them: whether the wide-to-tight reframe across the cut reads
as one continuous sky rather than a repeat, and the multi-ring halo around the moon
that earlier reviews flagged at 108.9-109.1s.
"""

import os
import subprocess

from PIL import Image

MEDIA = r"K:\Fluxgroup\FluxGroup\media\mv-album-001-jay"
FILM = os.path.join(MEDIA, "assembly-packA-KN", "KN-FULL-v1-C2198.mp4")
OUT = os.path.join(MEDIA, "qc-boards", "KN-FILM-v3-C2198-JUNCTION.jpg")
TIMES = [108.95, 109.10, 115.00, 117.00, 117.60, 118.40, 121.00, 125.50]


def main():
    cw = 448
    tiles = []
    tmp_dir = os.path.join(MEDIA, "qc-frames-c2198", "junction")
    os.makedirs(tmp_dir, exist_ok=True)
    for t in TIMES:
        p = os.path.join(tmp_dir, "j_%05.2f.png" % t)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", FILM,
                        "-frames:v", "1", p], check=True)
        im = Image.open(p)
        r = cw / float(im.size[0])
        tiles.append(im.resize((cw, max(1, int(im.size[1] * r)))))
    rh = max(t.size[1] for t in tiles)
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, rh * rows), (12, 12, 14))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * cw, (i // cols) * rh))
    sheet.save(OUT, quality=92)
    print("board=%s tiles=%d" % (OUT, len(tiles)))


if __name__ == "__main__":
    main()
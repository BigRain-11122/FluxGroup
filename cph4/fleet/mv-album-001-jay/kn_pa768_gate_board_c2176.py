# C2176: birth-station gate board for the KN 768P units that landed after C2172.
# Why: the two mechanical gates (caption pseudo-text C2170, shot-scale drift C2171)
# were last run on KN01-KN10. The wave has since delivered KN11-KN17, and every one
# of them was about to reach assembly ungated. This script does not re-judge: it
# only lays the landed native frames next to the two gate verdicts that already
# exist on disk, so the board and the gates cannot drift apart (same structure as
# kn_768p_sampled_board_c2172.py).
import glob
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

REPO = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(ALBUM, "clips-local-768")
EVID = os.path.join(ALBUM, "evidence-c2176")
OUTDIR = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MANIFEST = os.path.join(OUTDIR, "local-i2v", "run-bmc-kn-i2v.json")
PSEUDO = os.path.join(EVID, "pseudotext-c2176.json")
FRAMING = os.path.join(EVID, "framing-drift-c2176.json")
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
PER_BOARD = 5
COLS = 3
CELL_W = 448
PAD = 8
HEAD = 40
UNITS = ["KN_A-KN%02d" % i for i in range(11, 18)]


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
    with open(path, encoding="utf-8") as fh:
        return {r["clip"]: r for r in json.load(fh).get("rows", [])}


def main():
    os.makedirs(EVID, exist_ok=True)
    with open(MANIFEST, encoding="utf-8") as fh:
        units = {u["id"]: u for u in json.load(fh).get("units", [])}
    pseudo = load_rows(PSEUDO)
    framing = load_rows(FRAMING)

    rows = []
    tiles = []
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
            dst = os.path.join(EVID, "%s-t%02d.png" % (name, i))
            frames.append((ts, grab(clip, ts, dst)))
        p = pseudo.get(name + ".mp4", {})
        f = framing.get(name + ".mp4", {})
        u = units.get(name, {})
        rows.append({
            "unit": name,
            "clip": os.path.relpath(clip, REPO).replace("\\", "/"),
            "win_s": u.get("win_s"),
            "src_s": u.get("src_s"),
            "decoded_s": round(dur, 3),
            "pseudo": p.get("verdict", "NOT-RUN"),
            "pseudo_coverage": p.get("coverage"),
            "intent": f.get("intent", "-"),
            "framing": f.get("verdict", "NOT-RUN"),
            "max_zoom": f.get("max_zoom"),
            "max_zoom_at_sec": f.get("max_zoom_at_sec"),
            "bytes": os.path.getsize(clip),
        })
        tiles.append((name, p, f, frames))

    boards = []
    for b in range(0, len(tiles), PER_BOARD):
        chunk = tiles[b:b + PER_BOARD]
        cell_h = int(CELL_W * chunk[0][3][0][1].size[1] / chunk[0][3][0][1].size[0])
        rowsn = len(chunk)
        board = Image.new("RGB", (COLS * CELL_W + PAD * (COLS + 1),
                                  HEAD + rowsn * (cell_h + PAD) + PAD), (18, 18, 18))
        d = ImageDraw.Draw(board)
        f_big = font(24)
        f_sm = font(18)
        d.text((PAD, 8), "KN 768P birth-gate board (batch C2176) - %s..%s - native 1344x768"
               % (chunk[0][0], chunk[-1][0]), fill=(240, 240, 240), font=f_big)
        for r, (name, p, fr, frames) in enumerate(chunk):
            y = HEAD + r * (cell_h + PAD)
            tag = "pseudo=%s framing=%s(%s)" % (
                p.get("verdict", "NOT-RUN"), fr.get("verdict", "NOT-RUN"),
                fr.get("intent", "-"))
            if fr.get("max_zoom"):
                tag += " zoom=%.2fx@%.1fs" % (fr["max_zoom"], float(fr.get("max_zoom_at_sec") or 0))
            for c, (ts, im) in enumerate(frames):
                x = PAD + c * (CELL_W + PAD)
                im = im.resize((CELL_W, cell_h), Image.LANCZOS)
                board.paste(im, (x, y))
                d.text((x + 8, y + 6), "%.2fs" % ts, fill=(255, 235, 120), font=f_sm)
            colour = (160, 255, 160)
            if p.get("verdict") == "SUSPECT" or fr.get("verdict") in ("DRIFT", "FLAT"):
                colour = (255, 170, 110)
            d.text((PAD, y + cell_h - 24), "%s %s" % (name, tag), fill=colour, font=f_sm)
        out = os.path.join(OUTDIR, "KN-768P-GATE-BOARD-%d-c2176.jpg" % (b // PER_BOARD + 1))
        board.save(out, quality=88)
        boards.append(out)
        print("BOARD %s %dB" % (out, os.path.getsize(out)))

    flagged = [r for r in rows if r["pseudo"] == "SUSPECT"
               or r["framing"] in ("DRIFT", "FLAT")]
    doc = {
        "batch": "C2176",
        "scope": "KN 768P units landed after the C2172 sample (KN11-KN17)",
        "manifests": {"wave": os.path.relpath(MANIFEST, REPO).replace("\\", "/")},
        "gates": {
            "pseudo": os.path.relpath(PSEUDO, REPO).replace("\\", "/"),
            "framing": os.path.relpath(FRAMING, REPO).replace("\\", "/"),
        },
        "boards": [os.path.relpath(p, REPO).replace("\\", "/") for p in boards],
        "scanned": len(rows),
        "flagged": [r["unit"] for r in flagged],
        "rows": rows,
        "note": ("Birth-station sample of the wave still in flight (KN18 burning at "
                 "round time). Columns are the C2170/C2171 gate verdicts read back from "
                 "disk, not a second opinion; an eye pass on the boards decides whether a "
                 "flagged unit is worth a re-burn."),
    }
    vp = os.path.join(EVID, "gate-board.json")
    with open(vp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("VERDICT %s scanned=%d flagged=%s" % (vp, len(rows), doc["flagged"]))
    for r in rows:
        print("%-12s %-7s cov=%s | %-10s %-10s zoom=%s"
              % (r["unit"], r["pseudo"], r["pseudo_coverage"], r["intent"],
                 r["framing"], r["max_zoom"]))


if __name__ == "__main__":
    main()
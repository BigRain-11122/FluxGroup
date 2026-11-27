"""C2190 harvest: KN17 768P production burn (iteration-4 no-band prompt).

Same evidence pipeline as c2189_kn_harvest.py, retargeted at the 768P lane:
three native frames at 1.5/5.0/9.0s, blurred-sky p99 screening, plus a 1:1
native sky strip for the geometry read (vertical shard striations, hard torn
edge). Threshold raised to 47 because this is the 768P family - the 480P
calibration (82) does not carry over.

Glow numbers remain a screening aid. Calibration anchors:
  KN17 768P v3.4 = 43/44/47 (brightness pass, geometry fail)
  KN17 480P r4   = 36/37/38 (green, no striations)

The director eye pass stays the verdict.
"""

import io
import json
import os
import subprocess
import sys
import time

REPO = r"K:\Fluxgroup\FluxGroup"
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(MEDIA, "clips-local-768")
QCDIR = os.path.join(MEDIA, "qc-frames-c2190")
BOARD = os.path.join(MEDIA, "qc-boards", "KN-GALAXY-PROD-c2190.jpg")
OUT_JSON = os.path.join(MEDIA, "logs", "kn-harvest-c2190.json")
BATCH = "C2190"
TIMES = (1.5, 5.0, 9.0)
GLOW_SCREEN = 47.0
CLIP_NAME = "KN_G5-KN17.mp4"


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_frames,r_frame_rate:format=duration",
         "-of", "json", path],
        capture_output=True, text=True,
    )
    d = json.loads(out.stdout)
    st = (d.get("streams") or [{}])[0]
    return {
        "w": st.get("width"), "h": st.get("height"),
        "frames": st.get("nb_frames"), "fps": st.get("r_frame_rate"),
        "dur": round(float(d["format"]["duration"]), 3),
        "bytes": os.path.getsize(path),
    }


def grab(clip, t, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", clip,
                    "-frames:v", "1", dst], check=True)
    return dst


def glow(path):
    from PIL import Image, ImageFilter
    import numpy as np
    im = Image.open(path).convert("L")
    w, h = im.size
    sky = im.crop((0, 0, w, int(h * 0.55)))
    bl = sky.filter(ImageFilter.GaussianBlur(radius=max(6, w // 40)))
    a = np.asarray(bl).astype("float32")
    return {
        "med": round(float(np.median(a)), 1),
        "p95": round(float(np.percentile(a, 95)), 1),
        "p99": round(float(np.percentile(a, 99)), 1),
    }


def crop_sky(src, dst, frac_top=0.10, frac_h=0.42):
    from PIL import Image
    im = Image.open(src)
    w, h = im.size
    im.crop((0, int(h * frac_top), w, int(h * (frac_top + frac_h)))).save(dst)
    return dst


def main():
    clip = os.path.join(CLIPS, CLIP_NAME)
    if not os.path.isfile(clip):
        print("MISSING %s" % clip)
        return 2
    os.makedirs(QCDIR, exist_ok=True)
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)

    meta = probe(clip)
    frames = []
    thumbs = []
    for t in TIMES:
        dst = os.path.join(QCDIR, "KN17_768p_t%s.png" % t)
        grab(clip, t, dst)
        g = glow(dst)
        g["t"] = t
        g["file"] = os.path.basename(dst)
        frames.append(g)
        thumbs.append(dst)

    crop_src = os.path.join(QCDIR, "KN17_768p_t5.0.png")
    crop_dst = os.path.join(QCDIR, "KN17_768p_t5.0_sky1to1.png")
    crop_sky(crop_src, crop_dst)
    thumbs.append(crop_dst)

    worst = max(f["p99"] for f in frames)
    verdict = "STARFIELD-LIKE" if worst <= GLOW_SCREEN else "BRIGHT-BAND"

    try:
        from PIL import Image
        ims = [Image.open(p) for p in thumbs]
        cw = 448
        sized = []
        for im in ims:
            r = cw / float(im.size[0])
            sized.append(im.resize((cw, int(im.size[1] * r))))
        cols = 4
        rowsn = (len(sized) + cols - 1) // cols
        rh = max(i.size[1] for i in sized)
        sheet = Image.new("RGB", (cols * cw, rowsn * rh), (12, 12, 14))
        for i, im in enumerate(sized):
            sheet.paste(im, ((i % cols) * cw, (i // cols) * rh))
        sheet.save(BOARD, quality=92)
    except Exception as exc:
        print("board failed:", exc)

    payload = {
        "batch": BATCH,
        "clip": CLIP_NAME,
        "meta": meta,
        "frames": frames,
        "p99_max": worst,
        "screen": verdict,
        "threshold": GLOW_SCREEN,
        "sky_crop": os.path.basename(crop_dst),
        "harvested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "board": BOARD,
    }
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    print("%s %dx%d %s frames p99=%s max=%.1f -> %s" % (
        CLIP_NAME, meta["w"], meta["h"], meta["frames"],
        "/".join(str(f["p99"]) for f in frames), worst, verdict))
    print("board:", BOARD)
    return 0 if verdict == "STARFIELD-LIKE" else 3


if __name__ == "__main__":
    sys.exit(main())
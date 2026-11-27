"""C2189 harvest: KN galaxy 480P probe iteration 4 (band noun dropped).

Reads the two iteration-4 480P probe clips, pulls three native frames each, and
screens the sky light field the same way the C2187/C2188 harvests did. Adds a 1:1
native crop of the upper sky for the geometry check the C2189 verdict called out
(vertical shard striations, hard torn edges) - the low-res board alone cannot
show that.

Glow numbers are a screening aid. Calibration carried forward from C2186/C2187:
known-good KN17 at 63/66/76 (768P) and 43/44/47 (480P-family), known-bad KN18
(iteration 3) at 89/110/114.

The director eye pass stays the verdict; this script only produces evidence.
"""

import io
import json
import os
import subprocess
import sys

REPO = r"K:\Fluxgroup\FluxGroup"
PKG = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(REPO, "media", "mv-album-001-jay")
CLIPS = os.path.join(MEDIA, "clips-verify-480")
QCDIR = os.path.join(MEDIA, "qc-frames-c2189-r4")
BOARD = os.path.join(MEDIA, "qc-boards", "KN-GALAXY-R4-c2189.jpg")
OUT_JSON = os.path.join(MEDIA, "logs", "kn-harvest-c2189.json")
BATCH = "C2189"
TIMES = (1.5, 5.0, 9.0)
GLOW_SCREEN = 82.0
PAIRS = [("KN17", "KN_G4-KN17.mp4"), ("KN18", "KN_G4-KN18.mp4")]


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
    box = (0, int(h * frac_top), w, int(h * (frac_top + frac_h)))
    im.crop(box).save(dst)
    return dst


def main():
    os.makedirs(QCDIR, exist_ok=True)
    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    rows = []
    thumbs = []
    for shot, name in PAIRS:
        clip = os.path.join(CLIPS, name)
        if not os.path.isfile(clip):
            rows.append({"shot": shot, "clip": name, "missing": True})
            continue
        meta = probe(clip)
        frames = []
        for t in TIMES:
            dst = os.path.join(QCDIR, "%s_480p_t%s.png" % (shot, t))
            grab(clip, t, dst)
            g = glow(dst)
            g["t"] = t
            g["file"] = os.path.basename(dst)
            frames.append(g)
            thumbs.append(dst)
        # 1:1 native sky strip for the geometry read (striations / torn edges)
        crop_src = os.path.join(QCDIR, "%s_480p_t5.0.png" % shot)
        crop_dst = os.path.join(QCDIR, "%s_480p_t5.0_sky1to1.png" % shot)
        crop_sky(crop_src, crop_dst)
        thumbs.append(crop_dst)
        worst = max(f["p99"] for f in frames)
        rows.append({
            "shot": shot, "clip": name, "meta": meta, "frames": frames,
            "p99_max": worst,
            "screen": "STARFIELD-LIKE" if worst <= GLOW_SCREEN else "BRIGHT-BAND",
            "sky_crop": os.path.basename(crop_dst),
        })

    # contact sheet, 3 frames per clip + the 1:1 sky strip
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
    except Exception as exc:  # board is evidence convenience, not the verdict
        print("board failed:", exc)

    payload = {"batch": BATCH, "clips": rows,
               "threshold": GLOW_SCREEN,
               "harvested_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
               "board": BOARD}
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
    for r in rows:
        if r.get("missing"):
            print("%s MISSING" % r["shot"])
            continue
        print("%s %s p99=%s max=%.1f -> %s" % (
            r["shot"], r["clip"],
            "/".join(str(f["p99"]) for f in r["frames"]),
            r["p99_max"], r["screen"]))
    print("board:", BOARD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
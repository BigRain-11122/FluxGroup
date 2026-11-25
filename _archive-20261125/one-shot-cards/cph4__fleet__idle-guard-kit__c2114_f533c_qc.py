# -*- coding: utf-8 -*-
# c2114_f533c_qc.py -- XQ_F5-33c 3-frame strip QC (native frames + board + receipt)
import os, json, subprocess, sys
from PIL import Image, ImageDraw

REPO = r"K:\Fluxgroup\FluxGroup"
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay", "clips-packA-768")
CLIP = os.path.join(CLIPS, "XQ_F5-33c.mp4")
OUTDIR = os.path.join(REPO, "media", "mv-album-001-jay", "qc-f533c-c2114")
BOARD = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay", "xq-F533C-QC-STRIP-c2114.jpg")
RECEIPT = os.path.join(OUTDIR, "receipt.json")
NO_WINDOW = 0x08000000
os.makedirs(OUTDIR, exist_ok=True)

if not os.path.isfile(CLIP):
    print("MISSING CLIP: %s" % CLIP)
    sys.exit(1)

size = os.path.getsize(CLIP)
p = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
                    "-show_entries", "format=duration", "-of", "json", CLIP],
                   capture_output=True, text=True, creationflags=NO_WINDOW, timeout=180)
if p.returncode != 0:
    print("FFPROBE FAIL: " + p.stderr[:400])
    sys.exit(1)
meta = json.loads(p.stdout)
st = meta["streams"][0]
dur = float(meta["format"]["duration"])
w, h = int(st["width"]), int(st["height"])
nf = int(st.get("nb_read_frames", 0))

ts = [0.4, dur / 2.0, max(0.2, dur - 0.4)]
frames = []
for i, t in enumerate(ts):
    fp = os.path.join(OUTDIR, "f5-33c_t%d_native.png" % i)
    r = subprocess.run(["ffmpeg", "-y", "-ss", "%.3f" % t, "-i", CLIP, "-frames:v", "1", fp],
                       capture_output=True, creationflags=NO_WINDOW, timeout=120)
    if r.returncode != 0 or not os.path.isfile(fp):
        print("FRAME FAIL at t=%.2f" % t)
        sys.exit(1)
    frames.append(fp)

W, H, GAP, LBL = 672, 384, 8, 20
board = Image.new("RGB", (len(frames) * (W + GAP) + GAP, H + LBL + GAP * 2), (24, 22, 20))
dr = ImageDraw.Draw(board)
for i, fp in enumerate(frames):
    im = Image.open(fp).convert("RGB").resize((W, H), Image.LANCZOS)
    x = GAP + i * (W + GAP)
    board.paste(im, (x, GAP))
    dr.text((x, GAP + H + 4), "t=%.2fs" % ts[i], fill=(214, 194, 152))
board.save(BOARD, quality=90)

receipt = {
    "unit": "XQ_F5-33c",
    "clip": CLIP,
    "clip_bytes": size,
    "width": w, "height": h, "fps": st.get("r_frame_rate"), "frames": nf,
    "duration_s": round(dur, 3),
    "gate_bytes_ok": size >= 100 * 1024,
    "gate_decode_ok": nf > 0 and w == 1344 and h == 768,
    "sample_ts": [round(t, 3) for t in ts],
    "native_frames": frames,
    "board": BOARD,
    "board_bytes": os.path.getsize(BOARD),
}
with open(RECEIPT, "w", encoding="utf-8") as f:
    json.dump(receipt, f, ensure_ascii=False, indent=1)
print("F533C-QC-DONE bytes=%d %dx%d %df %.2fs board=%dB" % (size, w, h, nf, dur, receipt["board_bytes"]))
print("GATES bytes_ok=%s decode_ok=%s" % (receipt["gate_bytes_ok"], receipt["gate_decode_ok"]))
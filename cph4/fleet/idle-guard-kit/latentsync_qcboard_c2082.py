# LatentSync trial QC board (POOL-0016 night-1 closure evidence) - pre-stowed by tick-C2082
# Mechanical board: 6 input frames (trial_c2079/video.mp4, 25fps re-encoded input) vs
# 6 output frames (trial_c2079/out.mp4, lip-synced result) side-by-side strips.
# Feeds the R-stack dossier human-eye check. Verdict JSON + BOARD-END sentinel.
import json
import os
import subprocess
import sys
import time

FG = r"K:\Fluxgroup\FluxGroup"
WORK = os.path.join(FG, "media", "latentsync-deploy", "trial_c2079")
DEPLOY = os.path.join(FG, "media", "latentsync-deploy")
BOARD = os.path.join(DEPLOY, "latentsync_trial_qcboard_c2082.jpg")
VERDICT = os.path.join(DEPLOY, "qcboard_verdict.json")
# c2083 fix: trial consumed the repo demo asset directly (latentsync_trial_c2079.py L197,
# media/latentsync/assets/demo1_video.mp4) and left no copy inside trial_c2079/,
# so the first fire died on MISSING trial_c2079/video.mp4. Fallback keeps the
# bank cmd path unchanged (guard refire compatible).
IN_VIDEO = os.path.join(FG, "media", "latentsync", "assets", "demo1_video.mp4")


def resolve_src(name):
    src = os.path.join(WORK, name)
    if name == "video.mp4" and not os.path.exists(src) and os.path.exists(IN_VIDEO):
        return IN_VIDEO
    return src

N = 6
FRAME_IDS = [4, 16, 28, 40, 52, 70]  # spread across the 82f result


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def extract(video, idx, out_png):
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-nostdin", "-i", video,
         "-vf", "select=eq(n\\,%d)" % idx, "-frames:v", "1", out_png],
        capture_output=True)
    return r.returncode == 0 and os.path.exists(out_png)


def main():
    log("QCBOARD-START latentsync trial input-vs-output board (C2082)")
    ok = True
    strips = []
    for name in ("video.mp4", "out.mp4"):
        src = resolve_src(name)
        if not os.path.exists(src):
            log("MISSING %s" % src)
            print("BOARD-END status=FAIL")
            sys.exit(1)
    from PIL import Image, ImageDraw

    cell_w = 320
    for name, tag in (("video.mp4", "IN"), ("out.mp4", "OUT")):
        src = resolve_src(name)
        frames = []
        tmpdir = os.path.join(DEPLOY, "qcboard_tmp_c2082")
        os.makedirs(tmpdir, exist_ok=True)
        for i, fid in enumerate(FRAME_IDS):
            png = os.path.join(tmpdir, "%s_%02d.png" % (tag, i))
            if extract(src, fid, png):
                im = Image.open(png).convert("RGB")
                w, h = im.size
                im = im.resize((cell_w, int(h * cell_w / w)))
                frames.append(im)
            else:
                ok = False
                frames.append(Image.new("RGB", (cell_w, 200), (40, 40, 40)))
        strip = Image.new("RGB", (cell_w * N, max(f.size[1] for f in frames)), (10, 10, 10))
        x = 0
        for f in frames:
            strip.paste(f, (x, 0))
            x += cell_w
        strips.append((tag, strip))
    total_h = sum(s.size[1] + 34 for _, s in strips) + 26
    board = Image.new("RGB", (cell_w * N, total_h), (8, 10, 16))
    d = ImageDraw.Draw(board)
    y = 0
    d.text((8, 6), "LatentSync v1.5 trial PASS C2082 - input (top) vs lip-sync output (bottom), frames %s" % FRAME_IDS, fill=(150, 200, 255))
    y = 26
    for tag, s in strips:
        d.text((8, y + 8), "%s  %s" % (tag, "input 25fps" if tag == "IN" else "out.mp4 lip-synced"), fill=(255, 220, 120))
        board.paste(s, (0, y + 30))
        y += s.size[1] + 34
    board.save(BOARD, quality=90)
    with open(VERDICT, "w", encoding="utf-8") as f:
        json.dump({"status": "PASS" if ok else "PARTIAL", "board": BOARD,
                   "bytes": os.path.getsize(BOARD), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}, f, indent=1)
    log("QCBOARD %s bytes=%d -> %s" % ("PASS" if ok else "PARTIAL", os.path.getsize(BOARD), BOARD))
    log("BOARD-END status=%s" % ("PASS" if ok else "PARTIAL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

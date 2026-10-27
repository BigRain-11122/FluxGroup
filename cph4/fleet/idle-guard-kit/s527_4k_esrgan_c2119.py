"""C2119: S5-26/27/28 six-grid 4K line (r1017 sec-8 item-1 / sec-5 row-1).

Pipeline per grid: ComfyUI LoadImage -> UpscaleModelLoader(RealESRGAN_x4plus)
-> ImageUpscaleWithModel -> SaveImage; then PIL LANCZOS to 3840 wide and
+0.07 film grain (sec-5 pre-condition 2). Original files are never touched;
all output lands in media/MV/mv0001/xingqing/s7r-4k/.

Outputs: 6 PNG + compare board + receipt JSON.
"""
import json
import os
import random
import sys
import time
import urllib.request

from PIL import Image, ImageDraw

COMFY = "http://127.0.0.1:8188"
REPO = r"K:\Fluxgroup\FluxGroup"
SRC_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "abatch_s7r")
OUT_DIR = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "s7r-4k")
BOARD = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-BOARD-c2119.jpg")
RECEIPT = os.path.join(REPO, "media", "MV", "mv0001", "xingqing", "xq-S527-4K-RECEIPT-c2119.json")

GRIDS = [
    ("S5-26", "S5-26_s20185_s7rC.png"),
    ("S5-26", "S5-26_s20191_s7rC.png"),
    ("S5-27", "S5-27_s20192_s7rC.png"),
    ("S5-27", "S5-27_s20193_s7rC.png"),
    ("S5-28", "S5-28_s20202_s7rC.png"),
    ("S5-28", "S5-28_s20205_s7rC.png"),
]

TARGET_W = 3840
GRAIN = 0.07


def log(msg):
    print(msg, flush=True)


def post_json(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(COMFY + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def upload(local_path, name):
    boundary = "----c2119boundary"
    with open(local_path, "rb") as f:
        blob = f.read()
    body = b""
    body += ("--" + boundary + "\r\n").encode()
    body += ('Content-Disposition: form-data; name="image"; filename="%s"\r\n' % name).encode()
    body += b"Content-Type: image/png\r\n\r\n" + blob + b"\r\n"
    body += ("--" + boundary + "\r\n").encode()
    body += b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
    body += ("--" + boundary + "--\r\n").encode()
    req = urllib.request.Request(
        COMFY + "/upload/image", data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def workflow(img_name, prefix):
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": img_name}},
        "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "RealESRGAN_x4plus.pth"}},
        "3": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 0], "filename_prefix": prefix}},
    }


def run_one(shot, fname):
    src = os.path.join(SRC_DIR, fname)
    if not os.path.exists(src):
        raise SystemExit("MISSING %s" % src)
    up_name = "c2119_" + os.path.basename(src)
    upload(src, up_name)
    prefix = "c2119_4k_" + os.path.basename(src).replace(".png", "")
    pid = post_json("/prompt", {"prompt": workflow(up_name, prefix),
                                "client_id": "c2119"})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(2)
        hist = get_json("/history/" + pid)
        if pid in hist:
            entry = hist[pid]
            state = entry.get("status", {}).get("status_str", "")
            if state == "success":
                files = []
                for node in entry.get("outputs", {}).values():
                    files.extend(node.get("images", []))
                return files, time.time() - t0
            if state == "error":
                raise SystemExit("COMFY_ERROR %s" % json.dumps(entry)[:400])
    raise SystemExit("TIMEOUT waiting %s" % pid)


def fetch_out(files):
    """SaveImage writes into ComfyUI output/; read via /view."""
    f = files[0]
    q = "?filename=%s&subfolder=%s&type=output" % (urllib.request.quote(f["filename"]),
                                                    urllib.request.quote(f.get("subfolder", "")))
    with urllib.request.urlopen(COMFY + "/view" + q, timeout=180) as r:
        blob = r.read()
    tmp = os.path.join(OUT_DIR, "_tmp_" + f["filename"])
    with open(tmp, "wb") as fh:
        fh.write(blob)
    return tmp


def finish_frame(tmp, shot, fname):
    im = Image.open(tmp).convert("RGB")
    w, h = im.size
    if w > TARGET_W:
        nh = int(round(h * TARGET_W / float(w)))
        im = im.resize((TARGET_W, nh), Image.LANCZOS)
    # light grain to neutralise plastic feel (r1017 sec-5 pre-condition 2)
    import numpy as np
    arr = np.asarray(im).astype(np.int16)
    rng = np.random.default_rng(20210228)
    amp = 255 * GRAIN / 3.0
    noise = rng.normal(0.0, amp, size=(arr.shape[0], arr.shape[1], 1))
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    out = os.path.join(OUT_DIR, "%s_%s_4k.png" % (shot, os.path.basename(fname).replace(".png", "")))
    im.save(out, "PNG", optimize=True)
    os.remove(tmp)
    return out, im


def star_metric(im, box):
    """Bright-pixel retention in the upper band (proxy for faint star retention)."""
    crop = im.crop(box).convert("L")
    hist = crop.histogram()
    bright = sum(hist[200:])
    total = crop.size[0] * crop.size[1]
    return bright / float(total)


def corner_dark(im, box):
    crop = im.crop(box).convert("L")
    hist = crop.histogram()
    total = crop.size[0] * crop.size[1]
    dark = sum(hist[:36])
    return dark / float(total)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    frames = []
    for shot, fname in GRIDS:
        log("BURN %s %s" % (shot, fname))
        files, secs = run_one(shot, fname)
        tmp = fetch_out(files)
        out, im = finish_frame(tmp, shot, fname)
        src = Image.open(os.path.join(SRC_DIR, fname)).convert("RGB")
        w, h = im.size
        band = (int(w * 0.15), int(h * 0.03), int(w * 0.85), int(h * 0.42))
        row = {
            "shot": shot, "src": fname, "out": os.path.basename(out),
            "src_size": list(src.size), "out_size": [w, h],
            "bytes": os.path.getsize(out), "burn_secs": round(secs, 1),
            "star_ratio_upper_band": round(star_metric(im, band), 5),
            "star_ratio_src": round(star_metric(src, (int(src.size[0] * 0.15), int(src.size[1] * 0.03),
                                                     int(src.size[0] * 0.85), int(src.size[1] * 0.42))), 5),
            "corner_dark_ratio": round(corner_dark(im, (0, 0, int(w * 0.12), int(h * 0.18))), 4),
        }
        rows.append(row)
        frames.append((shot, src, im, row))
        log("DONE %s %s %dx%d %dB %.1fs" % (shot, os.path.basename(out), w, h, row["bytes"], secs))

    # compare board: per grid a native 1:1 crop of the 4K frame (768x432) above
    # the same region of the source, 2 rows x 3 columns
    cw, ch = 768, 432
    pad = 12
    bw = 3 * cw + 4 * pad
    bh = 2 * (ch + 26) + (ch + 26) + 3 * pad
    board = Image.new("RGB", (bw, bh), (14, 14, 16))
    d = ImageDraw.Draw(board)
    for i, (shot, src, im, row) in enumerate(frames):
        col = i % 3
        blk = i // 3
        x = pad + col * (cw + pad)
        y_4k = pad + blk * (2 * (ch + 26) + pad)
        y_src = y_4k + ch + 26
        w, h = im.size
        crop4 = im.crop((int(w * 0.5 - cw / 2), int(h * 0.42 - ch / 2),
                         int(w * 0.5 + cw / 2), int(h * 0.42 + ch / 2)))
        board.paste(crop4, (x, y_4k))
        sw, sh = src.size
        crop_s = src.crop((int(sw * 0.5 - cw / 2), int(sh * 0.42 - ch / 2),
                           int(sw * 0.5 + cw / 2), int(sh * 0.42 + ch / 2))).resize((cw, ch), Image.LANCZOS)
        board.paste(crop_s, (x, y_src))
        d.text((x + 4, y_4k + 4), "%s 4K %dx%d" % (shot, w, h), fill=(255, 232, 170))
        d.text((x + 4, y_src + 4), "%s SRC %dx%d" % (shot, sw, sh), fill=(190, 190, 190))
    board.save(BOARD, "JPEG", quality=90)

    receipt = {
        "batch": "c2119-s527-4k-esrgan",
        "spec": "r1017 sec-8 item-1 / sec-5 row-1 (six grids ESRGAN x4 + LANCZOS)",
        "model": "RealESRGAN_x4plus.pth",
        "target_width": TARGET_W,
        "grain": GRAIN,
        "pre_repair_note": "sec-5 pre-condition 1 (local line-hallucination / dot-matrix cleanup) NOT applied in this leg; leg-1 = upscale + grain only, 4K monitor recheck decides.",
        "frames": rows,
        "board": os.path.basename(BOARD),
        "board_bytes": os.path.getsize(BOARD),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(RECEIPT, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
    log("S527-4K-END ok=%d board=%s bytes=%d" % (len(rows), os.path.basename(BOARD), receipt["board_bytes"]))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # fail loud into the log tail
        log("S527-4K-END ok=0 error=%r" % (exc,))
        raise
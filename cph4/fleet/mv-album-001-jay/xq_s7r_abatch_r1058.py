# -*- coding: ascii -*-
# xq_s7r_abatch_r1058.py - S7 remediation pass on xingqing A-batch flagged
# frames (bm-c r1058, CEO idle-fill order 2026-10-17 13:0x).
# Scope routed by xq-AB-ZOOMQC-r1057 sec.3 (system faces -> POOL-0017 chain):
#   S5-26/27/28 sky banding / S5-30 over-smoothed skin / S0-series oily
#   specular highlights.
# Variants per frame (ADDITIVE ONLY - originals untouched, no gate needed:
# this is post-processing on already-signed grids, evidence for bm-a re-review):
#   A = original + 16mm monochrome grain (perceptual dither: masks banding,
#       adds skin/sky texture; zero structural change)
#   B = original + gentle highlight shoulder (softens oily speculars) + grain
#   C = (sky frames only: S5-26/27/28, no faces -> identity-safe)
#       RealESRGAN_x4plus via ComfyUI 8188 then LANCZOS back to 1344x768
# Outputs -> media/MV/mv0001/xingqing/abatch_s7r/ (variants, 2 boards,
# receipt json). ASCII prints only (PS5.1 GBK law). Run with python_embeded.

import io
import json
import os
import random
import subprocess
import time
import urllib.parse
import urllib.request
import uuid
import zlib

COMFY = "http://127.0.0.1:8188"
SRC = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch"
OUT = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\xingqing\abatch_s7r"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
MODEL = "RealESRGAN_x4plus.pth"

# (position, seed, want_esrgan_C)
FRAMES = [
    ("S5-26", "s20185", True), ("S5-26", "s20191", True),
    ("S5-27", "s20192", True), ("S5-27", "s20193", True),
    ("S5-28", "s20202", True), ("S5-28", "s20205", True),
    ("S5-30", "s20222", False), ("S5-30", "s20223", False),
    ("S0-02", "s20016", False), ("S0-02", "s20020", False),
    ("S0-03", "s20027", False), ("S0-03", "s20031", False),
    ("S0-04", "s20033", False), ("S0-04", "s20039", False),
    ("S0-05", "s20043", False), ("S0-05", "s20044", False),
    ("S0-06", "s20048", False), ("S0-06", "s20053", False),
]
W, H = 1344, 768


class Log:
    def __init__(self, path):
        self.f = open(path, "a", encoding="ascii", errors="replace")

    def __call__(self, msg):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
        try:
            print(line)
        except Exception:
            pass
        self.f.write(line + "\n")
        self.f.flush()


def http_json(path, obj=None, method=None, timeout=30):
    url = COMFY + path
    data = None
    headers = {}
    if obj is not None:
        data = json.dumps(obj).encode("ascii")
        headers["Content-Type"] = "application/json"
    if method:
        headers["X-HTTP-Method-Override"] = method
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        raise RuntimeError("HTTP %s %s %s: %s" % (e.code, method or "GET", path, detail))


def http_get_bytes(path):
    with urllib.request.urlopen(COMFY + path, timeout=90) as r:
        return r.read()


def vram_used_mb():
    try:
        q = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL).decode("ascii").strip().splitlines()
        return int(q[0].strip())
    except Exception:
        return -1


def upload_image(path, name):
    boundary = "----bmcS7rB" + uuid.uuid4().hex
    with open(path, "rb") as f:
        blob = f.read()
    body = io.BytesIO()
    body.write(("--%s\r\nContent-Disposition: form-data; name=\"image\"; "
                "filename=\"%s\"\r\nContent-Type: image/png\r\n\r\n"
                % (boundary, name)).encode("ascii"))
    body.write(blob)
    body.write(("\r\n--%s--\r\n" % boundary).encode("ascii"))
    req = urllib.request.Request(
        COMFY + "/upload/image", data=body.getvalue(),
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def build_prompt(image_name, prefix):
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": MODEL}},
        "3": {"class_type": "ImageUpscaleWithModel",
              "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 0],
                                                    "filename_prefix": prefix}},
    }


def run_upscale(image_name, prefix, log):
    prompt_id = http_json("/prompt", {"prompt": build_prompt(image_name, prefix),
                                      "client_id": "bmc-s7r-r1058"})["prompt_id"]
    t0 = time.perf_counter()
    peak = vram_used_mb()
    while True:
        time.sleep(0.5)
        cur = vram_used_mb()
        if cur > peak:
            peak = cur
        h = http_json("/history/" + prompt_id, timeout=15)
        if prompt_id in h:
            entry = h[prompt_id]
            st = entry.get("status", {})
            if st.get("completed"):
                if st.get("status_str") != "success":
                    raise RuntimeError("prompt failed: " + json.dumps(st)[:300])
                outs = []
                for node in entry.get("outputs", {}).values():
                    for im in node.get("images", []):
                        outs.append(im)
                return time.perf_counter() - t0, peak, outs
        if time.perf_counter() - t0 > 600:
            raise RuntimeError("timeout waiting prompt " + prompt_id)


def fetch_output(im):
    q = urllib.parse.urlencode({"filename": im["filename"],
                                "subfolder": im.get("subfolder", ""),
                                "type": im.get("type", "output")})
    return http_get_bytes("/view?" + q)


def shoulder_lut():
    lut = []
    knee = 209  # 0.82*255
    for v in range(256):
        if v <= knee:
            y = v
        else:
            y = knee + (v - knee) * 0.62
        lut.append(max(0, min(255, int(y + 0.5))))
    return lut * 3  # same curve for R/G/B (grade-neutral de-oil)


def add_grain(img, strength, seed):
    from PIL import Image, ImageChops
    w, h = img.size
    rnd = random.Random(seed)
    nb = bytes([rnd.getrandbits(8) for _ in range(w * h)])
    noise_rgb = Image.frombytes("L", (w, h), nb).convert("RGB")
    return Image.blend(img, ImageChops.soft_light(img, noise_rgb), strength)


def labeled_cell(img, text, tw=448, th=256):
    from PIL import Image, ImageDraw
    cell = img.resize((tw, th), Image.LANCZOS).convert("RGB")
    d = ImageDraw.Draw(cell)
    d.rectangle((0, 0, tw, 16), fill=(0, 0, 0))
    d.text((4, 3), text, fill=(255, 255, 255))
    return cell


def build_board(rows, path):
    # rows: list of list of (label, PIL image)
    from PIL import Image
    tw, th = 448, 256
    bw = tw * 4
    bh = th * len(rows)
    board = Image.new("RGB", (bw, bh), (24, 24, 24))
    for ri, row in enumerate(rows):
        for ci, (label, img) in enumerate(row):
            if img is None:
                continue
            board.paste(labeled_cell(img, label, tw, th), (ci * tw, ri * th))
    board.save(path, quality=88)
    return os.path.getsize(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(LOGDIR, exist_ok=True)
    log = Log(os.path.join(LOGDIR, "s7r_r1058.log"))
    log("S7R-START frames=%d comfy=%s" % (len(FRAMES), COMFY))
    http_json("/system_stats", timeout=15)
    log("S7R-HEALTH comfy alive")
    from PIL import Image
    lut = shoulder_lut()
    rows = []
    esr_done = 0
    for pos, seed, want_c in FRAMES:
        name = "%s_%s" % (pos, seed)
        src_path = os.path.join(SRC, name + ".png")
        if not os.path.exists(src_path):
            log("MISS " + name + " - skipped")
            continue
        orig = Image.open(src_path).convert("RGB")
        if orig.size != (W, H):
            log("WARN %s size=%s expected=%s" % (name, orig.size, (W, H)))
        # A: grain only (stable per-frame seed: crc32, reproducible evidence)
        frame_seed = zlib.crc32(name.encode("ascii"))
        a = add_grain(orig, 0.14, frame_seed)
        a_path = os.path.join(OUT, name + "_s7rA.png")
        a.save(a_path)
        # B: shoulder + grain
        b = add_grain(orig.point(lut), 0.14, frame_seed ^ 0x5A5A)
        b_path = os.path.join(OUT, name + "_s7rB.jpg")
        b.save(b_path, quality=92)
        variants = ["A grain", "B shoulder+grain"]
        c_img = None
        row = {"frame": name, "variants": ["s7rA.png", "s7rB.jpg"], "c": False}
        if want_c:
            try:
                up = upload_image(src_path, name + ".png")
                elapsed, peak, outs = run_upscale(up["name"], "s7r1058/" + name, log)
                raw = fetch_output(outs[0])
                c_img = Image.open(io.BytesIO(raw)).convert("RGB")
                if c_img.size != (W * 4, H * 4):
                    log("WARN %s upscaled=%s" % (name, c_img.size))
                c_img = c_img.resize((W, H), Image.LANCZOS)
                c_path = os.path.join(OUT, name + "_s7rC.png")
                c_img.save(c_path)
                variants.append("C esrgan+down")
                row["c"] = True
                row["esrgan_sec"] = round(elapsed, 2)
                row["vram_peak_mb"] = peak
                esr_done += 1
                log("OK %s C %.2fs peak=%dMB" % (name, elapsed, peak))
            except Exception as e:
                log("C-FAIL %s: %s" % (name, str(e)[:160]))
        rows.append(row)
        build_rows = [("orig " + name, orig), ("A grain", a),
                      ("B shoulder+grain", b)]
        if c_img is not None:
            build_rows.append(("C esrgan+down", c_img))
        main_rows.append((name, build_rows))
        log("OK %s A/B%s" % (name, "+C" if row["c"] else ""))
    # boards: split into two boards of <=9 rows
    board_paths = []
    chunks = [main_rows[0:9], main_rows[9:18]]
    for bi, chunk in enumerate(chunks, 1):
        if not chunk:
            continue
        bpath = os.path.join(OUT, "xq-AB-S7R-BOARD-%d-r1058.jpg" % bi)
        size = build_board([row_data for (_n, row_data) in chunk], bpath)
        board_paths.append(os.path.basename(bpath))
        log("BOARD %s %dB" % (os.path.basename(bpath), size))
    receipt = {
        "batch": "xingqing A-batch S7 remediation (ZOOMQC r1057 sec.3 routed)",
        "runner": "bm-c r1058",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "originals": "untouched (additive evidence for bm-a director re-review)",
        "frames": rows,
        "boards": board_paths,
        "esrgan_frames": esr_done,
        "grain_strength": 0.14,
        "shoulder": "knee 209 slope 0.62 (highlight de-oil, grade-neutral)",
        "ceo_order": "2026-10-17 13:0x idle-fill order",
    }
    rpath = os.path.join(OUT, "xq_s7r_abatch_receipt_r1058.json")
    with open(rpath, "w") as f:
        json.dump(receipt, f, indent=1)
    log("S7R-DONE frames=%d esrgan=%d receipt=%s" % (len(rows), esr_done, rpath))


main_rows = []

if __name__ == "__main__":
    main()

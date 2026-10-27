# -*- coding: ascii -*-
# xq_s7_halfroute_r1057.py - S7 half-route trial (POOL-0017, bm-c r1057)
# Card acceptance: three-version compare set (bare x4 / x4+LUT / x4+LUT+grain)
# + tier table. Chain: ffmpeg frame extract -> ComfyUI RealESRGAN_x4plus x4
# upscale (timed, VRAM-peak sampled) -> in-code filmic LUT -> 16mm grain.
# Missing/pending tiers recorded honestly (not faked): GFPGAN face restore,
# RIFE frame interpolation (stock = 4x-UltraSharp.pth + RealESRGAN_x4plus.pth
# only); seven-genre LUT bank (R-20261015-mv-genre-matrix color columns) and
# full-clip batch mode belong to the full S7 chain, not this trial.
# ASCII-only prints (PS5.1 encoding law). Stdlib + PIL only.

import io
import json
import os
import random
import subprocess
import time
import urllib.parse
import urllib.request
import uuid

COMFY = "http://127.0.0.1:8188"
BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
SRC = BASE + r"\bmc\i2v\v5redo"
OUT = BASE + r"\bmc\s7_trial_r1057"
CLIPS = ["C01_carver_face_v5.mp4", "SIL4_crowd_edge_v5.mp4"]
MODEL = "RealESRGAN_x4plus.pth"
FRAME_AT = 1.0  # seconds into clip


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
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        raise RuntimeError("HTTP %s %s %s: %s" % (e.code, method or "GET", path, detail))


def http_get_bytes(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
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
    boundary = "----bmcS7Boundary" + uuid.uuid4().hex
    with open(path, "rb") as f:
        blob = f.read()
    body = io.BytesIO()
    body.write(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                "Content-Type: image/png\r\n\r\n" % (boundary, name)).encode("ascii"))
    body.write(blob)
    body.write(("\r\n--%s--\r\n" % boundary).encode("ascii"))
    req = urllib.request.Request(
        COMFY + "/upload/image",
        data=body.getvalue(),
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=60) as r:
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


def run_upscale(image_name, prefix):
    prompt_id = http_json("/prompt", {"prompt": build_prompt(image_name, prefix),
                                      "client_id": "bmc-s7-r1057"})["prompt_id"]
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
                    raise RuntimeError("prompt failed: " + json.dumps(st)[:400])
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


def s7_lut(img):
    # Mechanical filmic half-route LUT: gentle S-curve + teal-shadow /
    # warm-highlight split tone. The seven-genre LUT bank is a full-chain
    # deliverable (genre-matrix color columns), not part of this trial.
    from PIL import Image, ImageChops
    w, h = img.size
    lut = []
    for c in range(3):
        ch = []
        for v in range(256):
            x = v / 255.0
            x = pow(x, 0.92)                 # lift shadows mildly
            x = x / (x + 0.55) * 1.55        # soft shoulder
            ch.append(max(0, min(255, int(x * 255 + 0.5))))
        lut.extend(ch)
    img = img.point(lut)
    shadow = Image.new("RGB", (w, h), (96, 122, 128))
    high = Image.new("RGB", (w, h), (255, 229, 200))
    mask = img.convert("L")
    teal = ImageChops.multiply(img, shadow)
    warm = ImageChops.multiply(img, high)
    return Image.composite(warm, teal, mask)


def s7_grain(img, strength=0.16):
    # 16mm-ish monochrome grain, soft-light blended.
    from PIL import Image, ImageChops
    w, h = img.size
    rnd = random.Random(20261017)
    nb = bytes([rnd.getrandbits(8) for _ in range(w * h)])
    noise_rgb = Image.frombytes("L", (w, h), nb).convert("RGB")
    return Image.blend(img, ImageChops.soft_light(img, noise_rgb), strength)


def main():
    os.makedirs(OUT, exist_ok=True)
    try:
        oi = http_json("/object_info/UpscaleModelLoader", timeout=15)
        stock = oi["UpscaleModelLoader"]["input"]["required"]["model_name"][1]
    except Exception:
        stock = []
    rows = []
    for clip in CLIPS:
        tag = clip.replace("_v5.mp4", "")
        frame_png = os.path.join(OUT, tag + "_src.png")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(FRAME_AT),
                               "-i", os.path.join(SRC, clip), "-frames:v", "1", frame_png])
        up = upload_image(frame_png, tag + "_src.png")
        elapsed, peak, outs = run_upscale(up["name"], "s7r1057/" + tag)
        if not outs:
            raise RuntimeError("no outputs for " + tag)
        raw = fetch_output(outs[0])
        up_path = os.path.join(OUT, tag + "_x4.png")
        with open(up_path, "wb") as f:
            f.write(raw)
        made = [os.path.basename(up_path)]
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            lut_img = s7_lut(img)
            lut_path = os.path.join(OUT, tag + "_lut.jpg")
            lut_img.save(lut_path, quality=92)
            made.append(os.path.basename(lut_path))
            full_path = os.path.join(OUT, tag + "_s7.jpg")
            s7_grain(lut_img).save(full_path, quality=92)
            made.append(os.path.basename(full_path))
        except Exception as e:
            print("WARN grade skipped (%s): %s" % (tag, str(e)[:120]))
        rows.append({"clip": clip, "frame_at_s": FRAME_AT, "model": MODEL,
                     "upscale_sec": round(elapsed, 2), "vram_peak_mb": peak,
                     "versions": made,
                     "out_file_kb": round(len(raw) / 1024.0, 1)})
        print("OK %s: upscale %.2fs vram_peak=%dMB -> %s" % (tag, elapsed, peak, " ".join(made)))
    table = {"trial": "POOL-0017 S7 half-route", "runner": "bm-c r1057",
             "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "comfy_url": COMFY, "model": MODEL,
             "upscale_models_stock": stock,
             "missing_tiers": ["GFPGAN (face restore)", "RIFE (frame interpolation)"],
             "pending_full_chain": ["seven-genre LUT bank (R-20261015-mv-genre-matrix)",
                                    "full-clip batch mode (per-frame video pass)"],
             "frames": rows}
    with open(os.path.join(OUT, "s7_tier_table_r1057.json"), "w") as f:
        json.dump(table, f, indent=1)
    print("TABLE %s" % os.path.join(OUT, "s7_tier_table_r1057.json"))
    print("STOCK %s" % json.dumps(stock))


if __name__ == "__main__":
    main()

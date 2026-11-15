# -*- coding: utf-8 -*-
"""kf_male_edit.py - male KFs via the Qwen-Image-Edit model (keep the face, change the scene).

Why: measured on this box, anchor img2img cannot satisfy both axes at once.
  denoise 0.62-0.70 -> face 0.64-0.68 but scene unchanged (bg difference ~5-12)
  denoise 0.90      -> scene really changes (mad 28) but face drops to 0.42
The edit model is the tool designed for "this person, a different scene", so it takes
over here. Graph parameters are taken from the shipped blueprint
`ComfyUI/blueprints/Image Edit (Qwen 2511).json`:
  UNET qwen_image_edit_2511_int8 · CLIP qwen_2.5_vl_7b_fp8 (type qwen_image) ·
  ModelSamplingAuraFlow shift 3.1 · CFGNorm 1 · KSampler 40 steps / cfg 4 / euler / simple.

Gate (both required): SFace cosine to the anchor >= --min-sim AND a BACKGROUND-ONLY
difference >= --min-bg. Background is measured outside the central subject box, because
a torch or a hand can lift a whole-frame MAD from 5 to 17 without changing the scene.

Usage:
  py Tools/kf_male_edit.py --scenes C01_carver_face [--seeds 2]
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request
import uuid

import cv2
import numpy as np

SERVER = "http://127.0.0.1:8188"
COMFY_INPUT = r"C:\Users\sjs20\comfyui-krea\ComfyUI_Windows_portable\ComfyUI\input"
DEFAULT_ANCHOR = (r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\canon"
                  r"\kf-v730\D03b_v2_s9151.png")
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\canon\kf-v731-edit"
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
MODEL_SFACE = os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx")

W, H = 1344, 768
STEPS, CFG, SHIFT = 40, 4.0, 3.1
UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"

KEEP = ("Keep the SAME man, the same face, the same hair, the same skin tone as the "
        "reference photo - do not change his identity. Change only the surroundings, "
        "the wardrobe and the camera position: ")

SCENES = {
    "C01_carver_face": ("Now he is inside a dark Babylonian carving workshop at night, "
                        "wearing a coarse undyed linen work-cloth, holding a bronze chisel; "
                        "seen from a low three-quarter angle, a single clay oil lamp burning "
                        "on the right, carved cuneiform stone behind him, deep shadows."),
    "D01_carver_words": ("Now he leans over a large dark stone tablet with a reed stylus, "
                         "seen from behind his shoulder at a steep overhead angle, one warm "
                         "lamp raking across the carved wedge signs, the room falling to black."),
    "B01_weary": ("Now he sits on a low stool beside a dying hearth in an empty mud-brick "
                  "room, shoulders sunk, one hand on his forehead, wide angle from the side, "
                  "the embers the only light, a half-carved slab leaning against the wall."),
    "E01c_first_line": ("Now he is in a modern 2001 Taipei room at night, leaning over a "
                        "paper page writing its first line, seen from a high side angle, a "
                        "warm tungsten desk lamp lighting only the page, the rest in deep shadow."),
}


def graph(prompt, seed, anchor_name):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "qwen_image"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "69": {"class_type": "LoadImage", "inputs": {"image": anchor_name}},
        "52": {"class_type": "TextEncodeQwenImageEditPlus",
               "inputs": {"clip": ["11", 0], "vae": ["12", 0], "image1": ["69", 0],
                          "prompt": prompt}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["52", 0]}},
        "64": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["10", 0], "shift": SHIFT}},
        "65": {"class_type": "CFGNorm", "inputs": {"model": ["64", 0], "strength": 1.0}},
        "61": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "58": {"class_type": "KSampler",
               "inputs": {"model": ["65", 0], "positive": ["52", 0], "negative": ["13", 0],
                          "latent_image": ["61", 0], "seed": seed, "steps": STEPS, "cfg": CFG,
                          "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "62": {"class_type": "VAEDecode", "inputs": {"samples": ["58", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["62", 0],
                                                    "filename_prefix": "kf_male_edit"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def gen(prompt, seed, anchor_name, dst, budget=1800):
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt, seed, anchor_name),
                                    "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < budget:
        try:
            h = json.loads(urllib.request.urlopen(SERVER + "/history/" + pid, timeout=45).read())
            if pid in h:
                for _n, o in h[pid]["outputs"].items():
                    for img in o.get("images", []):
                        url = ("%s/view?filename=%s&subfolder=%s&type=%s"
                               % (SERVER, urllib.parse.quote(img["filename"]),
                                  urllib.parse.quote(img["subfolder"]), img["type"]))
                        open(dst, "wb").write(urllib.request.urlopen(url, timeout=180).read())
                        return True
        except Exception as e:
            print("    poll retry (%s)" % type(e).__name__, flush=True)
        time.sleep(4.0)
    return False


def embed(path, rec):
    img = cv2.imread(path)
    if img is None:
        return None
    det = cv2.FaceDetectorYN.create(MODEL, "", (img.shape[1], img.shape[0]), 0.6, 0.3, 5000)
    _, faces = det.detect(img)
    if faces is None or not len(faces):
        return None
    f = max(faces, key=lambda r: r[2] * r[3])
    v = rec.feature(rec.alignCrop(img, f.reshape(1, -1))).flatten().astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def bg_mad(a_path, b_path, size=(336, 192)):
    """Difference outside the central subject box - the actual 'different scene' test."""
    a, b = cv2.imread(a_path), cv2.imread(b_path)
    if a is None or b is None:
        return -1.0
    ga = cv2.cvtColor(cv2.resize(a, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(cv2.resize(b, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = ga.shape
    m = np.ones_like(ga, dtype=bool)
    m[int(h * 0.18):int(h * 0.95), int(w * 0.22):int(w * 0.78)] = False  # exclude subject
    return float(np.mean(np.abs(ga - gb)[m]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", default=DEFAULT_ANCHOR)
    ap.add_argument("--scenes", default=",".join(SCENES))
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--min-sim", type=float, default=0.55)
    ap.add_argument("--min-bg", type=float, default=12.0)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(COMFY_INPUT, exist_ok=True)
    anchor_name = "anchor_male_edit.png"
    shutil.copyfile(a.anchor, os.path.join(COMFY_INPUT, anchor_name))
    rec = cv2.FaceRecognizerSF.create(MODEL_SFACE, "")
    base = embed(a.anchor, rec)
    if base is None:
        sys.exit("anchor face not detectable")
    print("anchor=%s steps=%d cfg=%.1f shift=%.1f min_sim=%.2f min_bg=%.1f"
          % (os.path.basename(a.anchor), STEPS, CFG, SHIFT, a.min_sim, a.min_bg), flush=True)

    report = {}
    for key in a.scenes.split(","):
        key = key.strip()
        if key not in SCENES:
            print("skip %s" % key); continue
        prompt = KEEP + SCENES[key]
        best = (None, -1.0, -1.0, None)
        for s in range(a.seeds):
            seed = 9300 + s * 11
            dst = os.path.join(OUT, "E_%s_s%d.png" % (key, seed))
            if not gen(prompt, seed, anchor_name, dst):
                print("  [%s] seed %d TIMEOUT" % (key, seed), flush=True); continue
            v = embed(dst, rec)
            sim = -1.0 if v is None else float(np.dot(base, v))
            bg = bg_mad(a.anchor, dst)
            print("  [%s] seed %d sim=%.3f bg=%.1f" % (key, seed, sim, bg), flush=True)
            if sim >= a.min_sim and bg >= a.min_bg and sim > best[1]:
                best = (dst, sim, bg, seed)
        report[key] = {"best": os.path.basename(best[0]) if best[0] else None,
                       "sim": round(best[1], 3), "bg": round(best[2], 1),
                       "seed": best[3], "pass": bool(best[0])}
        print("  -> %s %s sim=%.3f bg=%.1f"
              % (key, "PASS" if report[key]["pass"] else "FAIL", best[1], best[2]), flush=True)

    rp = os.path.join(OUT, "kf-male-edit-report.json")
    json.dump({"anchor": os.path.basename(a.anchor), "min_sim": a.min_sim,
               "min_bg": a.min_bg, "scenes": report},
              open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for r in report.values() if r["pass"])
    print("EDIT-KF %d/%d pass -> %s" % (ok, len(report), rp), flush=True)
    return 0 if ok == len(report) else 1


if __name__ == "__main__":
    sys.exit(main())

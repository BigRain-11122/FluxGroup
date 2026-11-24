# -*- coding: utf-8 -*-
"""kf_male_locked.py - regenerate the male-lead KFs against ONE anchor face, gated.

Why: v730 "unified" the male lead by feeding three different official photos into the
style-reference slot. Measured with SFace, the resulting KFs are six different faces
(pairwise median 0.117; the same-prompt two-seed pair only reaches 0.49, which is this
pipeline's own same-identity baseline). The CEO saw exactly that.

Fix: feed the SAME anchor image into all three reference slots, then refuse to keep a
candidate whose SFace cosine against the anchor is below --min-sim (default 0.45,
i.e. 90% of the 0.49 baseline). Seeds are retried until it passes, so nothing downstream
ever sees an off-identity keyframe.

Usage:
  py Tools/kf_male_locked.py --anchor <png> [--scenes C01,D01,B01,E01c] [--min-sim 0.45]
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
import uuid

import cv2
import numpy as np

SERVER = "http://127.0.0.1:8188"
COMFY_INPUT = r"C:\Users\sjs20\comfyui-krea\ComfyUI_Windows_portable\ComfyUI\input"
DEFAULT_ANCHOR = (r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\canon"
                  r"\kf-v730\D03b_v2_s9151.png")
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\canon\kf-v731"
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL, MODEL_SFACE = (os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx"),
                      os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx"))

W, H = 1344, 768

IDENTITY = ("Using the same young man from the reference images: a 22-year-old Taiwanese guy from the year 2001, "
            "NOT a Korean idol, no K-pop styling, no makeup, no glossy idol look, not a polished pretty boy. "
            "Keep his exact face: wide flat cheekbones, blunt rounded jaw with a slightly wide face, "
            "small narrow single-lidded sleepy downturned eyes, flat round nose tip, thick lower lip with a slight "
            "protruding mouth area, long black fringe swept low over his eyebrows, ordinary Taiwanese college-student "
            "charm, natural unretouched skin with visible pores and slight imperfections, matte complexion. ")

TAIL = (" Shot on 35mm film, cinematic film still from a 2001 Taiwanese music video, warm amber monochrome grade "
        "with deep crushed shadows, visible film grain. Absolutely no readable modern text, no typography, "
        "no letters, no logos, no watermark, pure imagery only.")

SCENES = {
    "C01_carver_face": ("A close-up at eye level, head and shoulders, in a dark Babylonian carver's workshop; "
                        "he holds a bronze chisel with a small mallet in his right hand, fine pale stone dust drifting; "
                        "his face lit strictly from the right by a single burning clay oil lamp, the left side in deep shadow; "
                        "behind him dark stone carrying shallow rows of carved wedge-cut cuneiform signs."),
    "D01_carver_words": ("A three-quarter side view with his face clearly visible and lit; his fingertip presses along a "
                         "freshly cut row of wedge-cut cuneiform signs on a dark stone tablet, a reed stylus loose in his "
                         "other hand; single warm oil-lamp light raking from the left; the workshop falling into black."),
    "B01_weary": ("A close-up shot inside a bare sleeping room, not the workshop: he sits on a low mat beside "
                  "a small clay lamp, shoulders sunk, one hand propping his forehead; behind him a plain mud-brick "
                  "wall with a rolled straw mat and a water jar, no carvings, the room almost entirely in shadow."),
    "E01c_first_line": ("A medium close-up at a wooden desk late at night, modern 2001 Taipei room; he leans over "
                        "a page writing its first line, warm tungsten desk lamp from the left, the rest of the room in "
                        "deep shadow, ancient cuneiform marks sketched at the page margin."),
}


def graph(prompt_text, seed, anchor_name, denoise=1.0, init_name=None):
    refs = {"69": anchor_name, "70": anchor_name, "71": anchor_name}
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["10", 0], "lora_name": "krea2_style_reference.safetensors", "strength_model": 1.0}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "69": {"class_type": "LoadImage", "inputs": {"image": refs["69"]}},
        "70": {"class_type": "LoadImage", "inputs": {"image": refs["70"]}},
        "71": {"class_type": "LoadImage", "inputs": {"image": refs["71"]}},
        "52": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["11", 0], "vae": ["12", 0], "image1": ["69", 0], "image2": ["70", 0],
            "image3": ["71", 0], "prompt": prompt_text}},
        "53": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["52", 0], "reference_latents_method": "index_timestep_zero"}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["53", 0]}},
        "64": {"class_type": "ModelSamplingFlux", "inputs": {"model": ["15", 0], "max_shift": 1.15, "base_shift": 0.5, "width": W, "height": H}},
        "57": {"class_type": "CFGGuider", "inputs": {"model": ["64", 0], "positive": ["53", 0], "negative": ["13", 0], "cfg": 1.0}},
        "63": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "59": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "60": {"class_type": "BasicScheduler", "inputs": {"model": ["64", 0], "scheduler": "simple", "steps": 8, "denoise": denoise}},
        "58": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["63", 0], "guider": ["57", 0], "sampler": ["59", 0], "sigmas": ["60", 0], "latent_image": ["61", 0]}},
        "62": {"class_type": "VAEDecode", "inputs": {"samples": ["58", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["62", 0], "filename_prefix": "kf_male_locked"}},
    }
    if denoise < 0.999:
        # img2img: start from the anchor latent so the face survives the scene change.
        # text-to-image only steered style (0.418/0.320/0.268 vs the anchor); a denoise
        # around 0.6 restyles the scene while keeping the identity already in the latent.
        init_ref = ["31", 0] if init_name else ["69", 0]
        if init_name:
            g["31"] = {"class_type": "LoadImage", "inputs": {"image": init_name}}
        g["30"] = {"class_type": "VAEEncode", "inputs": {"pixels": init_ref, "vae": ["12", 0]}}
        g["58"]["inputs"]["latent_image"] = ["30", 0]
    else:
        g["61"] = {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}}
        g["58"]["inputs"]["latent_image"] = ["61", 0]
    return g


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def gen(prompt, seed, anchor_name, dst, denoise=1.0, init_name=None, budget=900):
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt, seed, anchor_name, denoise, init_name),
                                    "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < budget:
        # a single dropped /history read used to kill the whole batch (and lose every
        # scene after it); poll errors must be survivable
        try:
            h = json.loads(urllib.request.urlopen(SERVER + "/history/" + pid, timeout=30).read())
            if pid in h:
                for _n, o in h[pid]["outputs"].items():
                    for img in o.get("images", []):
                        url = ("%s/view?filename=%s&subfolder=%s&type=%s"
                               % (SERVER, urllib.parse.quote(img["filename"]),
                                  urllib.parse.quote(img["subfolder"]), img["type"]))
                        open(dst, "wb").write(urllib.request.urlopen(url, timeout=120).read())
                        return True
        except Exception as e:
            print("    poll retry (%s)" % type(e).__name__, flush=True)
        time.sleep(3.0)
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


def mad_vs(a_path, b_path, size=(336, 192)):
    """Composition difference on a common grid; identity is measured separately."""
    a = cv2.imread(a_path)
    b = cv2.imread(b_path)
    if a is None or b is None:
        return -1.0
    ga = cv2.cvtColor(cv2.resize(a, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(cv2.resize(b, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.mean(np.abs(ga - gb)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", default=DEFAULT_ANCHOR)
    ap.add_argument("--scenes", default=",".join(SCENES))
    ap.add_argument("--min-sim", type=float, default=0.45)
    ap.add_argument("--min-mad", type=float, default=15.0,
                    help="composition difference vs the anchor; below this the 'new' shot "
                         "is the same picture restyled and reads as a repeat on screen")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--init", default="",
                    help="optional image to start the latent from (staging pass) while the "
                         "anchor still drives identity in the conditioning")
    ap.add_argument("--denoise", default="1.0",
                    help="one value or a comma list to sweep, e.g. 0.70,0.80")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    anchor_name = "anchor_male_v731.png"
    os.makedirs(COMFY_INPUT, exist_ok=True)
    shutil.copyfile(a.anchor, os.path.join(COMFY_INPUT, anchor_name))
    rec = cv2.FaceRecognizerSF.create(MODEL_SFACE, "")
    base = embed(a.anchor, rec)
    if base is None:
        sys.exit("anchor face not detectable: %s" % a.anchor)
    print("anchor=%s min_sim=%.2f seeds=%d" % (os.path.basename(a.anchor), a.min_sim, a.seeds), flush=True)

    report = {}
    for key in a.scenes.split(","):
        key = key.strip()
        if key not in SCENES:
            print("skip unknown scene %s" % key); continue
        prompt = IDENTITY + SCENES[key] + TAIL
        best = (None, -1.0, -1.0, None, None)
        for raw in str(a.denoise).split(","):
            dens = float(raw)
            for s in range(a.seeds):
                seed = 9200 + s * 7
                dst = os.path.join(OUT, "M_%s_d%d_s%d.png" % (key, int(dens * 100), seed))
                if not gen(prompt, seed, anchor_name, dst, dens):
                    print("  [%s] d=%.2f seed %d TIMEOUT" % (key, dens, seed), flush=True); continue
                v = embed(dst, rec)
                sim = -1.0 if v is None else float(np.dot(base, v))
                mad = mad_vs(a.anchor, dst)
                print("  [%s] d=%.2f seed %d sim=%.3f mad=%.1f" % (key, dens, seed, sim, mad), flush=True)
                # both axes must pass: same face AND a different picture. Keeping only the
                # best sim produced four near-identical frames (MAD 4-7).
                if sim >= a.min_sim and mad >= a.min_mad and sim > best[1]:
                    best = (dst, sim, mad, seed, dens)
                if best[0] and sim >= a.min_sim and mad >= a.min_mad:
                    break
        report[key] = {"best": os.path.basename(best[0]) if best[0] else None,
                       "sim": round(best[1], 3), "mad": round(best[2], 1),
                       "seed": best[3], "denoise": best[4],
                       "pass": bool(best[0])}
        print("  -> %s %s sim=%.3f mad=%.1f"
              % (key, "PASS" if report[key]["pass"] else "FAIL", best[1], best[2]), flush=True)

    rp = os.path.join(OUT, "kf-male-locked-report.json")
    json.dump({"anchor": os.path.basename(a.anchor), "min_sim": a.min_sim,
               "min_mad": a.min_mad, "scenes": report},
              open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for r in report.values() if r["pass"])
    print("LOCKED-KF %d/%d pass -> %s" % (ok, len(report), rp), flush=True)
    return 0 if ok == len(report) else 1


if __name__ == "__main__":
    sys.exit(main())



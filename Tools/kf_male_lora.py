# -*- coding: utf-8 -*-
"""kf_male_lora.py - keyframe generation where the IDENTITY LoRA carries the face, not image conditioning.

Why this exists (2026-11-16):
  kf_male_locked.py drives identity through the reference-image slot (TextEncodeQwenImageEditPlus
  with 1-3 anchor images) on top of krea2_style_reference. Measured with SFace, that route is capped:
  the 0.875 img2img sweep reached only 0.408 set-median (needs 0.55), and pure txt2img through the
  same conditioning reached 0.418/0.320/0.268 per scene.

  What has NOT been tested is letting the trained identity LoRA (jman_v1_rank32) do the work with
  NO reference images at all. If the LoRA actually learned the face, plain txt2img should produce the
  same person in four different rooms - which is exactly the "same man, different scene" the set gate
  demands. If it fails too, the LoRA itself is too weak and the honest next step is retraining, not
  more parameter sweeping.

Usage:
  py Tools/kf_male_lora.py --lora jman_v1_rank32.safetensors --strength 1.0 --seeds 3
  py Tools/kf_male_lora.py --lora jman_v1_rank32.safetensors --scenes C01,D01
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid

import cv2
import numpy as np

SERVER = "http://127.0.0.1:8188"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\canon\kf-v733"
MODEL, MODEL_SFACE = (os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx"),
                      os.path.join(HERE, "models", "face_recognition_sface_2021dec.onnx"))

W, H = 1344, 768

IDENTITY = ("A 22-year-old Taiwanese man from the year 2001, "
            "NOT a Korean idol, no K-pop styling, no makeup, no glossy idol look, not a polished pretty boy. "
            "His face: wide flat cheekbones, blunt rounded jaw with a slightly wide face, "
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


def graph(prompt_text, seed, lora, strength):
    """Plain text-to-image: identity must come from the LoRA weights alone."""
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["10", 0], "lora_name": lora, "strength_model": strength}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "52": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["11", 0], "vae": ["12", 0], "prompt": prompt_text}},
        "53": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["52", 0], "reference_latents_method": "index_timestep_zero"}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["53", 0]}},
        "64": {"class_type": "ModelSamplingFlux", "inputs": {"model": ["15", 0], "max_shift": 1.15, "base_shift": 0.5, "width": W, "height": H}},
        "57": {"class_type": "CFGGuider", "inputs": {"model": ["64", 0], "positive": ["53", 0], "negative": ["13", 0], "cfg": 1.0}},
        "63": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "59": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "60": {"class_type": "BasicScheduler", "inputs": {"model": ["64", 0], "scheduler": "simple", "steps": 8, "denoise": 1.0}},
        "61": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "58": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["63", 0], "guider": ["57", 0], "sampler": ["59", 0], "sigmas": ["60", 0], "latent_image": ["61", 0]}},
        "62": {"class_type": "VAEDecode", "inputs": {"samples": ["58", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["62", 0], "filename_prefix": "kf_male_lora"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def gen(prompt, seed, lora, strength, dst, budget=600):
    try:
        pid = post(SERVER + "/prompt", {"prompt": graph(prompt, seed, lora, strength),
                                       "client_id": str(uuid.uuid4())})["prompt_id"]
    except Exception as e:
        print("    submit failed: %s" % e, flush=True)
        return False
    t0 = time.time()
    while time.time() - t0 < budget:
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
        except Exception:
            pass
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


def bg_mad(a_path, b_path):
    """Background-only MAD: exclude the subject box so props/pose cannot fake a scene change."""
    a, b = cv2.imread(a_path), cv2.imread(b_path)
    if a is None or b is None:
        return -1.0
    size = (336, 192)
    ga = cv2.cvtColor(cv2.resize(a, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(cv2.resize(b, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    diff = np.abs(ga - gb)
    return float(diff.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", default="jman_v1_rank32.safetensors")
    ap.add_argument("--strength", default="1.0", help="one value or comma list to sweep")
    ap.add_argument("--scenes", default=",".join(SCENES))
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--min-sim", type=float, default=0.55)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    rec = cv2.FaceRecognizerSF.create(MODEL_SFACE, "")
    print("lora=%s strength=%s scenes=%d" % (a.lora, a.strength, len(a.scenes.split(","))), flush=True)

    made = []
    for key in a.scenes.split(","):
        key = key.strip()
        if key not in SCENES:
            print("skip unknown scene %s" % key); continue
        prompt = IDENTITY + SCENES[key] + TAIL
        for raw in str(a.strength).split(","):
            st = float(raw)
            for s in range(a.seeds):
                seed = 9300 + s * 11
                dst = os.path.join(OUT, "L_%s_st%d_s%d.png" % (key, int(st * 100), seed))
                if os.path.exists(dst):
                    print("  [%s] st=%.2f seed %d cached" % (key, st, seed), flush=True)
                elif not gen(prompt, seed, a.lora, st, dst):
                    print("  [%s] st=%.2f seed %d TIMEOUT" % (key, st, seed), flush=True); continue
                made.append((key, dst, st, seed))
                print("  [%s] st=%.2f seed %d -> %s" % (key, st, seed, os.path.basename(dst)), flush=True)

    # mutual identity inside the produced set (this is the test that matters)
    by_key = {}
    for key, dst, st, seed in made:
        v = embed(dst, rec)
        by_key.setdefault(key, []).append((dst, v, st, seed))

    pick = {}
    for key, cands in by_key.items():
        valid = [(d, v, st, sd) for d, v, st, sd in cands if v is not None]
        if valid:
            pick[key] = valid[0][0]
    print("\nscenes produced: %d, with detectable face: %d" % (len(by_key), len(pick)), flush=True)
    keys = list(pick)
    if len(keys) >= 2:
        sims = []
        for i, j in ((x, y) for x in range(len(keys)) for y in range(x + 1, len(keys))):
            va = embed(pick[keys[i]], rec); vb = embed(pick[keys[j]], rec)
            if va is None or vb is None:
                continue
            s = float(np.dot(va, vb)); sims.append(s)
            print("  pair %-18s %-18s sim=%.3f bg=%.1f"
                  % (keys[i], keys[j], s, bg_mad(pick[keys[i]], pick[keys[j]])), flush=True)
        if sims:
            print("\nidentity median=%.3f min=%.3f  (need >= %.2f)" % (float(np.median(sims)), min(sims), a.min_sim), flush=True)
            print("VERDICT: %s" % ("PASS" if float(np.median(sims)) >= a.min_sim else "FAIL"), flush=True)

    rp = os.path.join(OUT, "kf-male-lora-report.json")
    json.dump({"lora": a.lora, "strength": a.strength,
               "picks": {k: os.path.basename(v) for k, v in pick.items()}},
              open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("report -> %s" % rp, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

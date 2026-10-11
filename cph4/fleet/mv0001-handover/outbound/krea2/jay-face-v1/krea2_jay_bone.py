# -*- coding: utf-8 -*-
# krea2_jay_bone.py - bone-structure anchor iteration on MR2's seed family
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\jayrefid"
PHOTOS = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\jayphotos"
W, H = 1344, 768

NO_TEXT = "Absolutely no readable modern text, no typography, no letters, no logos, no watermark, pure imagery only."
PROMPT = ("Using the same young man from the reference images: a 22-year-old Taiwanese guy from the year 2001, "
          "NOT a Korean idol, no K-pop styling, no makeup, no glossy idol look, not a polished pretty boy. "
          "Keep his exact face: wide flat cheekbones, blunt rounded jaw with a slightly wide face, "
          "small narrow single-lidded sleepy downturned eyes, flat round nose tip, thick lower lip with a slight "
          "protruding mouth area, long black fringe swept low over his eyebrows, awkward campus charm of an ordinary "
          "Taiwanese college student, natural unretouched skin with visible pores and slight imperfections, matte complexion. "
          "Recreate him as a frontal portrait, head and shoulders, wearing a plain dark shirt, "
          "his face lit strictly from the left by a single clay oil lamp with open flame, the right side falling into soft shadow, "
          "subtle 35mm film grain. "
          "Cinematic film still from a 2001 music video, warm amber monochrome, deep shadows. " + NO_TEXT)

def graph(prompt_text, seed, r1, r2, r3):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["10", 0], "lora_name": "krea2_style_reference.safetensors", "strength_model": 1.0}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "69": {"class_type": "LoadImage", "inputs": {"image": r1}},
        "70": {"class_type": "LoadImage", "inputs": {"image": r2}},
        "71": {"class_type": "LoadImage", "inputs": {"image": r3}},
        "52": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["11", 0], "vae": ["12", 0], "image1": ["69", 0], "image2": ["70", 0], "image3": ["71", 0], "prompt": prompt_text}},
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["62", 0], "filename_prefix": "krea2_jaybone"}},
    }

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())

def run_one(name, seed, r1, r2, r3):
    pid = post(SERVER + "/prompt", {"prompt": graph(PROMPT, seed, r1, r2, r3), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 1500:
        time.sleep(4)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR:", json.dumps(h[pid]["status"].get("messages", []))[:400]); return
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=90).read()
                    open(os.path.join(OUT, name + ".png"), "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0)); return
    print("TIMEOUT " + name)

def main():
    # same three uploaded refs (server retains them)
    for i, s in enumerate([9043, 9045, 9046, 9047, 9048]):
        run_one("BN%d_seed%d" % (i, s), s, "ref_main_9.jpg", "ref_close_1.jpg", "ref_mv_91.jpg")
    print("BONE BATCH DONE")

main()

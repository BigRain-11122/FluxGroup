# -*- coding: utf-8 -*-
# kf_d03b_v2.py - D03b re-gen v2 (panel 11-14 VFX seat: the v1 KF's torch flame
# was cropped by the top edge and read as a thin white streak). Same jman
# identity lock; torch moved lower into frame with headroom above the flame.
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\canon\kf-v730"
W, H = 1344, 768

IDENTITY = ("Using the same young man from the reference images: a 22-year-old Taiwanese guy from the year 2001, "
            "NOT a Korean idol, no K-pop styling, no makeup, no glossy idol look, not a polished pretty boy. "
            "Keep his exact face: wide flat cheekbones, blunt rounded jaw with a slightly wide face, "
            "small narrow single-lidded sleepy downturned eyes, flat round nose tip, thick lower lip with a slight "
            "protruding mouth area, long black fringe swept low over his eyebrows, ordinary Taiwanese college-student "
            "charm, natural unretouched skin with visible pores and slight imperfections, matte complexion. ")

SCENE = ("Recreate him as a frontal portrait at eye level, head and shoulders, in a dark Babylonian carver's workshop, "
         "wearing a plain undyed coarse linen robe knotted at one shoulder, a smear of fine stone dust on one cheekbone. "
         "At the right side of the frame a burning reed-bundle torch is held LOW in a bronze sconce bowl at chest height, "
         "its whole flame fully inside the frame with clear empty headroom above the tip, the flame a broad amber-gold "
         "fan with smoky yellow tips, individual charred reed stems readable. His face is lit strictly from the right by "
         "this torch, the left half of his face falling into deep soft shadow. Behind him a dark stone wall carrying "
         "shallow rows of carved wedge-cut cuneiform signs. Subtle 35mm film grain, warm amber monochrome grade with "
         "deep crushed shadows. ")

TAIL = ("Cinematic film still from a 2001 Taiwanese music video. Absolutely no readable modern text, no typography, "
        "no letters, no logos, no watermark, pure imagery only.")


def graph(prompt_text, seed):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["10", 0], "lora_name": "krea2_style_reference.safetensors", "strength_model": 1.0}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "69": {"class_type": "LoadImage", "inputs": {"image": "ref_main_9.jpg"}},
        "70": {"class_type": "LoadImage", "inputs": {"image": "ref_close_1.jpg"}},
        "71": {"class_type": "LoadImage", "inputs": {"image": "ref_mv_91.jpg"}},
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["62", 0], "filename_prefix": "kf_d03b_v2"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())


def run_one(name, seed):
    pid = post(SERVER + "/prompt", {"prompt": graph(IDENTITY + SCENE + TAIL, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 1500:
        time.sleep(4)
        try:
            h = get(SERVER + "/history/" + pid)
        except Exception:
            continue
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR", name, json.dumps(h[pid]["status"].get("messages", []))[:300], flush=True); return
            for _n, o in h[pid]["outputs"].items():
                for img in o.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                                                  "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=90).read()
                    open(os.path.join(OUT, name + ".png"), "wb").write(data)
                    print("SAVED", name, "(%.0fs)" % (time.time() - t0), flush=True); return
    print("TIMEOUT", name, flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, s in enumerate([9150, 9151]):
        run_one("D03b_v2_s%d" % s, s)
    print("D03B V2 DONE", flush=True)


main()

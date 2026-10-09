# -*- coding: utf-8 -*-
# krea2_campus.py - male lead candidates: 90s/2000-era Taiwan MV + campus style
# v2 (O-20261009-1815/1830): all prompts assembled via prompt_lexicon mechanism.
#   Zero negative anchors, zero vague words, era-correct film stock (Vision 5279/5246), telecine grade.
import json, time, os, urllib.request, uuid, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_lexicon import ID_M_2001, FACE_M_2001, build_shot

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\campus"
os.makedirs(OUT, exist_ok=True)

def S(shot, pose, scene, lens, light, grade, texture, angle="eye", extra=""):
    return build_shot(shot=shot, id_block=ID_M_2001, wardrobe="uniform", face=FACE_M_2001,
                      pose=pose, scene=scene, lens=lens, light=light,
                      grade=grade, texture=texture, angle=angle, extra=extra)

JOBS = [
    ("C1_classroom", S("mw", "stand_classroom", "classroom", "35", "window", "nost", "film_day"), 8201),
    ("C2_library",   S("med", "read", "library", "50", "tung_left", "nost", "film_day"), 8202),
    ("C3_corridor",  S("hs", "window_lean", "corridor", "85", "window", "nost", "film_day"), 8203),
    ("C4_bicycle",   S("mw", "bike", "a campus road lined with tall camphor trees", "35", "golden", "nost", "film_day"), 8204),
    ("C5_rooftop",   S("med", "roofsit", "rooftop", "35", "dusk", "tw2001", "film_night"), 8205),
    ("C6_portrait",  S("hs", "facing the camera with a quiet downcast gaze", "classroom", "85", "tung_left", "tw2001", "film_night"), 8206),
    ("C7_ballcourt", S("med", "stand_court", "court", "35", "golden", "nost", "film_day"), 8207),
    ("C8_rainwalk",  S("wide", "walk_rain", "street", "35", "dusk", "tw2001", "film_night"), 8208),
]

W, H = 1344, 768

def graph(prompt_text, seed):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "simple", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0],
                "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "krea2_campus"}},
    }

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())

def run_one(name, prompt_text, seed):
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 1200:
        time.sleep(3)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR %s" % name, flush=True); return
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=60).read()
                    fn = os.path.join(OUT, name + ".png")
                    open(fn, "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0), flush=True)
                    return
    print("TIMEOUT " + name, flush=True)

def main():
    for name, p, s in JOBS:
        run_one(name, p, s)
    print("CAMPUS DONE %d" % len(JOBS), flush=True)

if __name__ == "__main__":
    main()

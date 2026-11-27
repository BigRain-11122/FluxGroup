# -*- coding: utf-8 -*-
# krea2_designs3.py - female lead candidate expansion per CEO order:
#   era rumored-girlfriend types (Vivian Hsu / Jolin Tsai / Patty Hou / Landy Wen).
# v2 (O-20261009-1815/1830): prompts assembled via prompt_lexicon mechanism (zero negatives,
#   era-correct stock 5279, ID blocks as verbatim constants, wispy fringe -> solid blunt fringe fix).
import json, time, os, urllib.request, uuid, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_lexicon import (ID_F_VVR, ID_F_JOLIN, ID_F_HOU, ID_F_LANDY,
                            FACE_F_2001, build_shot)

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\designs3"
os.makedirs(OUT, exist_ok=True)

def SF(shot, id_block, pose, scene, lens, light, wardrobe="gown", grade="mono", texture="film_night", extra=""):
    return build_shot(shot=shot, id_block=id_block, wardrobe=wardrobe, face=FACE_F_2001,
                      pose=pose, scene=scene, lens=lens, light=light,
                      grade=grade, texture=texture, extra=extra)

JOBS = [
    ("V1_vvr_smile",   SF("hs", ID_F_VVR, "portrait_front", "hall", "85", "flame"), 9201),
    ("V2_vvr_casual",  SF("med", ID_F_VVR, "standing relaxed by a sunny campus wall with long shadows", "a 2001 Taipei campus wall", "35", "golden", wardrobe="campus", grade="nost", texture="film_day"), 9202),
    ("V3_vvr_goddess", SF("med", ID_F_VVR, "goddess_materialize", "hall", "35", "flame", grade="bluefire"), 9203),
    ("J1_jolin_portrait", SF("hs", ID_F_JOLIN, "facing the camera with a shy sweet smile", "hall", "85", "flame", wardrobe="campus"), 9301),
    ("J2_jolin_modern",   SF("med", ID_F_JOLIN, "museum_look", "museum", "50", "tung_left", wardrobe="campus", grade="tw2001"), 9302),
    ("J3_jolin_lively",   SF("med", ID_F_JOLIN, "laugh_hand", "desk", "50", "lamp_desk", wardrobe="campus", grade="tw2001"), 9303),
    ("P1_patty_portrait", SF("hs", ID_F_HOU, "facing the camera with a graceful composed smile", "hall", "85", "flame"), 9401),
    ("P2_patty_modern",   SF("med", ID_F_HOU, "holding an old file folder in the dim aisle, composed and curious", "museum", "50", "tung_left", wardrobe="campus", grade="tw2001"), 9402),
    ("P3_patty_goddess",  SF("med", ID_F_HOU, "goddess_materialize", "hall", "35", "flame", grade="bluefire"), 9403),
    ("L1_landys_portrait", SF("hs", ID_F_LANDY, "facing the camera with a smoky half-lidded gaze", "hall", "85", "split"), 9501),
    ("L2_landy_stage",     SF("med", ID_F_LANDY, "profile_rim", "temple_corridor", "85", "halo"), 9502),
    ("L3_landy_modern",    SF("med", ID_F_LANDY, "leaning against a stone wall with a cool confident gaze toward the light", "museum", "50", "tung_left", wardrobe="campus", grade="tw2001"), 9503),
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "krea2_designs3"}},
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
    print("DESIGNS3 DONE %d" % len(JOBS), flush=True)

if __name__ == "__main__":
    main()

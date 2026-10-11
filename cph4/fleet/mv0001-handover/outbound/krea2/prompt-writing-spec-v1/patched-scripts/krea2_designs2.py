# -*- coding: utf-8 -*-
# krea2_designs2.py - design batch v2 per CEO 2026-10-09 orders:
#   female lead = Vivian Hsu type; male lead hair = early-2000s Taiwan album cover hairstyle.
# v2 (O-20261009-1815/1830): prompts assembled via prompt_lexicon mechanism (zero negatives,
#   era-correct stock 5279, telecine/mono grades, ID blocks as verbatim constants).
import json, time, os, urllib.request, uuid, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_lexicon import (ID_F_VVR, ID_M_2001_BONE, FACE_F_2001, FACE_M_2001, build_shot)

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\designs2"
os.makedirs(OUT, exist_ok=True)

def SF(shot, pose, scene, lens, light, grade="mono", texture="film_night", wardrobe="gown", extra=""):
    return build_shot(shot=shot, id_block=ID_F_VVR, wardrobe=wardrobe, face=FACE_F_2001,
                      pose=pose, scene=scene, lens=lens, light=light,
                      grade=grade, texture=texture, extra=extra)

def SM(shot, pose, scene, lens, light, hair, wardrobe, grade="mono", texture="film_night", extra=""):
    # hair described positively in extra (bottom/hair separation law: face base + era hairstyle variant)
    return build_shot(shot=shot, id_block=ID_M_2001_BONE, wardrobe=wardrobe, face=FACE_M_2001,
                      pose=pose, scene=scene, lens=lens, light=light,
                      grade=grade, texture=texture,
                      extra=(hair + ". " + extra).strip() if extra else hair)

JOBS = [
    ("F1_vvr_portrait", SF("hs", "portrait_front", "hall", "85", "flame", wardrobe="gown"), 9001),
    ("F2_vvr_goddess",  SF("med", "goddess_materialize", "hall", "35", "godray", grade="bluefire"), 9002),
    ("F3_vvr_modern2001", SF("med", "museum_look", "museum", "50", "tung_left", grade="tw2001", wardrobe="campus"), 9003),
    ("F4_vvr_eyes",     SF("cu", "her eyes lifted toward a warm light source", "hall", "85", "flame"), 9004),
    ("F5_vvr_profile",  SF("med", "profile_rim", "temple_corridor", "85", "halo"), 9005),
    ("F6_vvr_fullbody", SF("wide", "walk_corridor", "temple_corridor", "35", "godray", grade="bluefire"), 9006),
    ("M1_era_portrait", SM("hs", "facing the camera with a quiet downcast gaze", "hall", "85", "onelamp",
                           hair="His hair is a thick messy black medium-length cut with a long heavy fringe over his eyebrows, naturally covering the upper ears, plainly kept",
                           wardrobe="scribe"), 9101),
    ("M2_era_hairfocus", SM("hs", "facing the camera, hair clearly the subject", "a neutral dark studio corner", "85", "lamp_desk",
                            hair="His hair is a thick messy black medium-length cut, the long fringe lying over his eyebrows, plainly kept and slightly unkempt",
                            wardrobe="home", extra="his face visible under the fringe"), 9102),
    ("M3_era_scribe",   SM("med", "scribe", "tablet", "35", "flame",
                           hair="a plain wrapped headcloth pushed back to show his fringe",
                           wardrobe="scribe", extra="two clay oil lamps on the desk"), 9103),
    ("M4_era_modern2001", SM("med", "standing in the museum aisle at night, watching from a distance with longing", "museum", "50", "tung_left",
                             hair="His hair is a thick messy black medium-length cut with a long heavy fringe over his eyebrows",
                             wardrobe="home", grade="tw2001"), 9104),
    ("M5_era_hair2002", SM("hs", "facing the camera with a quiet downcast gaze", "hall", "85", "onelamp",
                           hair="His hair is the 2002 album-era layered black shag, the long fringe swept diagonally across his forehead with brows partly visible, jaw-length sides",
                           wardrobe="scribe"), 9105),
    ("M6_era_closeup",  SM("cu", "half-open sleepy eyes turned toward the lamp", "hall", "85", "flame",
                           hair="his thick black fringe lying over his eyebrows",
                           wardrobe="scribe", extra="the flat round nose tip and thick lower lip clearly visible"), 9106),
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "krea2_designs2"}},
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
    print("DESIGNS2 DONE %d" % len(JOBS), flush=True)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
# krea2_prompt_ab_test2.py - attribution groups B' and C (designed by prompt-engineering expert review)
# B' = Group A verbatim minus ONLY the negative wall + NO_TEXT (clean single-variable test for lesion 1)
# C  = lexicon v1.2 build_shot() actual output (official order + zero negatives + era-corrected params)
import json, time, os, urllib.request, uuid, sys

sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma")
from prompt_lexicon import (ID_M_2001, FACE_M_2001, build_shot, lint, SHOT_SIZE)

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\prompt-ab"
os.makedirs(OUT, exist_ok=True)

# ---- B': Group A verbatim, negatives surgically removed, everything else identical ----
ERA_B = ("A cinematic film still from a Taiwanese music video shot around the year 2000 on 35mm film: "
         "warm tungsten light and hazy window daylight, soft slightly unfocused lens, gentle halation, "
         "natural skin with visible film grain, muted nostalgic palette of old Taiwan campus dramas, "
         "plain honest textures. ")  # "no modern polish" removed
ID_M_B = ("The same young man in every image: a 20-year-old Taiwanese student from around the year 2000, "
          "ordinary campus charm rather than idol looks, sleepy narrow single-lidded eyes with heavy relaxed "
          "lids, thick lower lip, wide flat face with softly rounded cheeks, thick black chunky-strand fringe "
          "falling over his eyebrows, slightly messy natural hair with no styling product, lean frame, quiet "
          "introverted presence with an awkward gentle stubbornness. ")  # NOT/no-K-pop/no-makeup sentence removed
# NOTE: "with no styling product" kept? NO - it is a negative inside ID. Surgical rule:
# B' removes the STANDALONE negative wall sentences; the internal "no styling product" phrase is
# replaced by its positive twin "unstyled" (single-token surgical swap, documented here).
ID_M_B = ID_M_B.replace("slightly messy natural hair with no styling product",
                        "slightly messy unstyled natural hair")
BP_C6 = (ID_M_B + "Frontal portrait, head and shoulders, in the loose white school-uniform shirt, "
         "warm tungsten light sculpting his face, quiet downcast gaze, 85mm. " + ERA_B)  # NO_TEXT removed

# ---- C: lexicon v1.2 mechanism output (era-corrected: 50mm f/2.8, Vision 5279, telecine grade) ----
C_C6 = build_shot(
    shot="hs", id_block=ID_M_2001, wardrobe="uniform", face=FACE_M_2001,
    pose="sit_desk", scene="desk", lens="85", light="tung_left",
    grade="tw2001", texture="film_night", angle="eye",
    style_lead="as a film still from a Taiwanese campus music video filmed in 2001",
)
print("C prompt lint:", lint(C_C6), flush=True)
print("B' prompt lint:", lint(BP_C6), flush=True)  # B' intentionally keeps other flaws (no styling removed only)

JOBS = []
for tag, p in [("Bp_negfree", BP_C6), ("C_mech", C_C6)]:
    for i, sd in enumerate([8206, 9001, 9002, 9003]):
        JOBS.append(("%s_%d_seed%d" % (tag, i, sd), p, sd))

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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "prompt_ab"}},
    }

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url), timeout=60).read())

def run_one(name, prompt_text, seed):
    print("START %s" % name, flush=True)
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 1800:
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
    print("AB2 DONE %d" % len(JOBS), flush=True)

main()

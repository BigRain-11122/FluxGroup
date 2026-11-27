# -*- coding: utf-8 -*-
# krea2_prompt_ab_test.py - A/B proof: old negative-wall prompt vs new positive-narrative prompt
# Same scene, same seeds, Krea 2 turbo t2i. Group A = old style (negative anchors).
# Group B = new style (positive narration, no negative tokens anywhere).
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\prompt-ab"
os.makedirs(OUT, exist_ok=True)

# ---- Group A: OLD style, copied verbatim from krea2_campus.py C6_portrait ----
ERA_OLD = ("A cinematic film still from a Taiwanese music video shot around the year 2000 on 35mm film: "
           "warm tungsten light and hazy window daylight, soft slightly unfocused lens, gentle halation, "
           "natural skin with visible film grain, muted nostalgic palette of old Taiwan campus dramas, "
           "plain honest textures, no modern polish. ")
ID_M_OLD = ("The same young man in every image: a 20-year-old Taiwanese student from around the year 2000, "
            "ordinary campus charm rather than idol looks, sleepy narrow single-lidded eyes with heavy relaxed "
            "lids, thick lower lip, wide flat face with softly rounded cheeks, thick black chunky-strand fringe "
            "falling over his eyebrows, slightly messy natural hair with no styling product, lean frame, quiet "
            "introverted presence with an awkward gentle stubbornness. NOT a Korean idol, no K-pop styling, no "
            "makeup, no glossy grooming, no slim trendy fashion. ")
NO_TEXT_OLD = "Absolutely no readable modern text, no typography, no letters, no logos, no watermark, pure imagery only."
A_C6 = (ID_M_OLD + "Frontal portrait, head and shoulders, in the loose white school-uniform shirt, "
        "warm tungsten light sculpting his face, quiet downcast gaze, 85mm. " + ERA_OLD + NO_TEXT_OLD)

# ---- Group B: NEW style - one central narrative sentence, positive equivalents only ----
# Korean/K-pop/idol/makeup/watermark tokens: ABSENT. Same face identity words, same scene, same light.
B_C6 = ("A quiet film still from a Taiwanese campus music video filmed in 2001 on 35mm film: "
        "a frontal head-and-shoulders portrait of a 20-year-old Taiwanese student with sleepy narrow "
        "single-lidded eyes, heavy relaxed eyelids, a thick lower lip, softly rounded cheeks and a thick "
        "black chunky-strand fringe falling over his eyebrows. He wears a loose plain white school-uniform "
        "shirt with a dark collar, his bare face plain and natural, hair unstyled and slightly messy. "
        "A warm tungsten lamp sculpts his face from the side as he gazes quietly downward. "
        "Muted nostalgic color palette, gentle halation, visible film grain, honest plain 2001-era textures.")

JOBS = []
for tag, p in [("A_old", A_C6), ("B_new", B_C6)]:
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
    return json.loads(urllib.request.urlopen(req := urllib.request.Request(url), timeout=60).read())

def run_one(name, prompt_text, seed):
    print("START %s" % name, flush=True)
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
    print("AB TEST DONE %d" % len(JOBS), flush=True)

main()

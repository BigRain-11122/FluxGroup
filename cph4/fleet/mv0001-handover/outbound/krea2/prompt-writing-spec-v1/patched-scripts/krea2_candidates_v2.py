# -*- coding: utf-8 -*-
# krea2_candidates_v2.py - Route-A character candidates: Taiwan 80s/90s campus style + MV looks
# CEO rulings 2026-10-09: route A approved, 80s/90s campus style, female younger (18-20)
# v2 (O-20261009-1815/1830): negative wall + NO_TEXT removed per prompt-spec v1.1;
#   ID wording kept verbatim where CEO already saw/approved MC candidates; era (80s/90s) semantics kept.
import json, time, os, urllib.request, uuid, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_lexicon import lint

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\candv2"
os.makedirs(OUT, exist_ok=True)

FILM = ("cinematic film still, subtle 35mm film grain, natural unretouched skin with visible pores, "
        "a slightly faded film photo color palette of the late 1980s-90s Taiwan. ")

MALE_ID = ("a 22-year-old Taiwanese college student with quiet introverted awkward charm: small narrow "
           "single-lidded sleepy downturned eyes, thick lower lip, soft rounded wide face with flat "
           "cheekbones, blunt short chin, flat round nose tip, thick messy black hair with a long fringe "
           "falling over his eyebrows, plainly kept hair. ")
MALE_CAMPUS = ("He wears a loose plain white short-sleeve crew-neck shirt, simple straight-leg jeans, "
               "worn canvas shoes, carrying a plain backpack, riding an old bicycle through a quiet "
               "Taiwanese campus lane in the late 1980s: banyan trees, low concrete school buildings, "
               "morning haze, dappled sunlight. Medium-wide shot, he glances sideways with a shy "
               "half-smile. ")
MALE_CAMPUS2 = ("He sits alone at an old wooden desk in an empty classroom with a green chalkboard and "
                "green-painted window frames, wearing a loose plain gray crew-neck shirt, writing in a "
                "notebook, afternoon sun through dusty windows. Medium shot, quiet mood. ")
MALE_MV = ("He wears a plain loose dark shirt, standing in an ancient Babylonian temple corridor lit by "
           "a single clay oil lamp, holding a wet clay tablet with cuneiform, warm amber monochrome "
           "color grade with deep shadows, head-and-shoulders shot lit strictly from the left. ")

FEMALE_ID = ("an 18-year-old Taiwanese college girl with a fresh natural face: clear round "
             "bright eyes, smooth young skin, soft natural black eyebrows, small nose, gentle closed "
             "mouth with a light smile, long straight black hair with natural thin bangs, a plain "
             "bare-face youthful look. ")
FEMALE_CAMPUS = ("She wears a plain white short-sleeve school blouse and a simple dark pleated skirt, "
                 "canvas shoes, standing in a sunlit classroom corridor with green paint window frames, "
                 "holding textbooks against her chest, looking at the camera with a shy smile, late "
                 "1980s Taiwan campus, dappled afternoon light. ")
FEMALE_CAMPUS2 = ("She rides an old bicycle along a tree-lined campus lane in the late 1980s, wearing a "
                  "plain light blouse and long skirt, straw shoulder bag, glancing back at the camera "
                  "mid-ride, warm afternoon haze. ")
FEMALE_MV = ("A young woman in a flowing plain white gown fading into existence within dying torchlight "
             "inside an ancient Babylonian temple corridor, her backlit silhouette half-materialized like "
             "light made flesh, soft halation bloom, embers drifting, volumetric incense smoke, symmetrical "
             "columns receding into darkness, a fresh young face, 85mm full shot, soft focus. ")

BASE_STYLE = ("cinematic film still from a 2001 music video, warm amber monochrome color grading with "
              "deep shadows, subtle 35mm film grain, ancient Mesopotamian world. ")

PROMPTS = [
    ("MC1_campus_bike", MALE_ID + MALE_CAMPUS + FILM, 8091),
    ("MC2_campus_class", MALE_ID + MALE_CAMPUS2 + FILM, 8092),
    ("MC3_scribe", MALE_ID + MALE_MV + BASE_STYLE, 8093),
    ("FC1_corridor", FEMALE_ID + FEMALE_CAMPUS + FILM, 8094),
    ("FC2_bike", FEMALE_ID + FEMALE_CAMPUS2 + FILM, 8095),
    ("FC3_goddess", FEMALE_ID + FEMALE_MV + BASE_STYLE, 8096),
    ("CP1_pair", MALE_ID + FEMALE_ID +
     "The two stand together in a quiet late-1980s Taiwanese campus lane, he in loose white shirt and "
     "jeans with a plain backpack, she in a white school blouse and dark pleated skirt, both looking "
     "toward the camera with shy awkward expressions, two meters apart, dappled banyan shade. "
     + FILM, 8097),
]

for _nm, _pr, _sd in PROMPTS:
    _hits = lint(_pr)
    if _hits:
        print("LINT WARN %s: %s" % (_nm, _hits), flush=True)

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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "krea2_candv2"}},
    }

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())

def run_one(name, prompt_text, seed):
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(4)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR %s" % name, flush=True); return
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=90).read()
                    open(os.path.join(OUT, name + ".png"), "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0), flush=True)
                    return
    print("TIMEOUT %s" % name, flush=True)

def main():
    for nm, pr, sd in PROMPTS:
        print("START %s ..." % nm, flush=True)
        run_one(nm, pr, sd)
    print("CANDV2 DONE", flush=True)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
# krea2_chars.py - lead character design sheet: F-lead x6 looks + M-lead x6 looks (identity consistency test)
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\chars"
os.makedirs(OUT, exist_ok=True)

NO_TEXT = "Absolutely no readable modern text, no typography, no letters, no logos, no watermark, pure imagery only."
B = ("cinematic film still from a 2001 music video, warm amber monochrome color grading with deep shadows, "
     "single motivated torch light, subtle 35mm film grain, solemn and mysterious mood. " + NO_TEXT)

ID_F = ("The same young woman in every image: around 25 with classical European features, fair skin, dark chestnut hair "
        "falling loosely to her shoulders, calm gentle dark eyes with soft depth, understated natural beauty, "
        "quiet melancholic grace, no heavy makeup, no jewelry. ")
ID_M = ("The same young man in every image: an East Asian man around 22, black hair with a slightly long fringe swept "
        "low over his brows, lean frame, quiet introverted presence with gentle stubbornness, clean plain styling. ")

JOBS = [
    # F-lead: 6 looks (face visible per CEO order)
    ("F1_portrait",   ID_F + "Frontal portrait, head and shoulders, dying torchlight from the left sculpting her face, 85mm, shallow depth of field. " + B, 8001),
    ("F2_profile",    ID_F + "Side profile standing in an ancient Babylonian temple corridor, columns behind, torch rim light tracing her profile. " + B, 8002),
    ("F3_goddess",    ID_F + "In a flowing white gown fading into existence within dying torchlight, half-materialized, her face softly visible in the afterglow, symmetrical columns behind. " + B, 8003),
    ("F4_modern2001", ID_F + "In simple dark knit sweater and straight hair, standing at a museum archive aisle at night, looking at a glowing glass display case, 2001 casual styling. " + B, 8004),
    ("F5_eyes",       ID_F + "Close-up of her face, eyes lifted toward a warm light source, torchlight catching her skin texture, 100mm macro feel. " + B, 8005),
    ("F6_fullbody",   ID_F + "Full body in the flowing white gown, walking away down a torch-lit temple corridor, her figure small against the pillars, wide shot. " + B, 8006),
    # M-lead: 6 looks (2001-vibe young Asian man)
    ("M1_portrait",   ID_M + "Frontal portrait, head and shoulders, single clay oil lamp lighting his face from below-left, quiet gaze, 85mm. " + B, 8101),
    ("M2_scribe",     ID_M + "In plain linen scribe robes and wrapped headcloth, hunched writing on a wet clay tablet at a wooden desk with two clay oil lamps, concentration on his face. " + B, 8102),
    ("M3_modern2001", ID_M + "In a plain dark jacket, standing in a museum archive aisle at night, watching from a distance with longing, 2001 street styling. " + B, 8103),
    ("M4_overshoulder", ID_M + "Seen from behind over his shoulder, watching a girl at a glass display case, his profile in shadow, museum at night. " + B, 8104),
    ("M5_silhouette", ID_M + "Full-body silhouette holding a raised torch in a dark stone corridor, volumetric dust in the beam, rim light. " + B, 8105),
    ("M6_hands_writing", ID_M + "Medium shot pressing a reed stylus into a wet clay tablet, lamp glow on his face in profile, rows of finished tablets beside him. " + B, 8106),
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "krea2_chars"}},
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
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=60).read()
                    fn = os.path.join(OUT, name + ".png")
                    open(fn, "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0))
                    return
    print("TIMEOUT " + name)

def main():
    for name, p, s in JOBS:
        run_one(name, p, s)
    print("CHARS DONE %d" % len(JOBS))

main()

# -*- coding: utf-8 -*-
# SUPERSEDED 2026-10-10 — v1-era face-lock lane: locks a male frontal face into scenes,
# violating the 30s back/side-profile iron law. DO NOT RUN. History only.
# (Legal seat review 2026-10-10; see EXPERT-PANEL-PROTOCOL.md)
raise SystemExit("SUPERSEDED 2026-10-10: do not run reel_face_lock.py - violates 30s iron law. History only.")
# reel_face_lock.py - CEO consistency order for the 30s reel: lock canon faces into the 4 cast shots.
# Route: SWAP-style low-denoise (scene frame = image1 keeps composition; canon face = image2).
# Judge rules: dn0.55-0.6 = pixel-level face lock (8.5-9/10 pass in QEDIT 判例); Lightning 4-step for speed.
import json, time, os, urllib.request, uuid, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_lexicon import lint

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\quick-reel"
FASTFACE = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\fastface"
D3 = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\designs3"

UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
LIGHTNING = "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"

# canon references (CEO rulings: male canon = F5_seed7306_dn80; female keep-list = V3_vvr_goddess)
MALE_CANON = os.path.join(FASTFACE, "F5_seed7306_dn80.png")
FEMALE_CANON = os.path.join(D3, "V3_vvr_goddess.png")

KEEP_M = ("Keep the scene frame's pose, costume, lighting, composition and background completely "
          "unchanged; show the exact face of the man in the second image: the same oval face with soft "
          "full cheeks, the same small dark monolid eyes with a low sleepy detached gaze, the same heavy "
          "straight blunt-cut black fringe covering the eyebrows, the same soft rounded nose tip and full "
          "relaxed lips, with natural matte skin and 2001 film grain.")
KEEP_F = ("Keep the scene frame's pose, gown, lighting, composition and background completely "
          "unchanged; show the exact face of the woman in the second image: the same softly sweet oval "
          "face with full rounded cheeks, the same large bright dark double-lidded eyes, the same small "
          "straight nose and soft medium-full rosy lips, the same long straight black hair with a solid "
          "blunt full fringe, with natural matte skin and 2001 film grain.")

JOBS = [
    # (out_name, scene_frame, ref_face, prompt, seed)
    ("QR_S2_scribe_locked.png", "QR_S2_scribe.png", MALE_CANON, KEEP_M, 7811),
    ("QR_S6_bike_locked.png",   "QR_S6_bike.png",   MALE_CANON, KEEP_M, 7812),
    ("QR_S3_goddess_locked.png","QR_S3_goddess.png", FEMALE_CANON, KEEP_F, 7813),
    ("QR_S5_museum_locked.png", "QR_S5_museum.png",  FEMALE_CANON, KEEP_F, 7814),
]

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url), timeout=60).read())

def upload_image(path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----lock" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)

def graph(prompt_text, seed, img1, img2, denoise=0.58):
    g = {
        "161": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "145": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["161", 0], "shift": 3.1}},
        "152": {"class_type": "CFGNorm", "inputs": {"model": ["145", 0], "strength": 1.0, "pre_cfg": False}},
        "153": {"class_type": "LoraLoaderModelOnly",
                "inputs": {"model": ["152", 0], "lora_name": LIGHTNING, "strength_model": 1.0}},
        "162": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "qwen_image", "device": "default"}},
        "146": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "164": {"class_type": "LoadImage", "inputs": {"image": img1}},
        "160": {"class_type": "FluxKontextImageScale", "inputs": {"image": ["164", 0]}},
        "156": {"class_type": "VAEEncode", "inputs": {"pixels": ["160", 0], "vae": ["146", 0]}},
        "151": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["162", 0], "vae": ["146", 0], "image1": ["160", 0], "image2": ["165", 0], "prompt": prompt_text}},
        "149": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["162", 0], "vae": ["146", 0], "image1": ["160", 0], "image2": ["165", 0], "prompt": ""}},
        "148": {"class_type": "FluxKontextMultiReferenceLatentMethod",
                "inputs": {"conditioning": ["151", 0], "reference_latents_method": "index_timestep_zero"}},
        "147": {"class_type": "FluxKontextMultiReferenceLatentMethod",
                "inputs": {"conditioning": ["149", 0], "reference_latents_method": "index_timestep_zero"}},
        "169": {"class_type": "KSampler", "inputs": {
            "model": ["153", 0], "positive": ["148", 0], "negative": ["147", 0],
            "latent_image": ["156", 0], "seed": seed, "steps": 4, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple", "denoise": denoise}},
        "158": {"class_type": "VAEDecode", "inputs": {"samples": ["169", 0], "vae": ["146", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["158", 0], "filename_prefix": "reellock"}},
    }
    g["165"] = {"class_type": "LoadImage", "inputs": {"image": img2}}
    return g

def run_one(name, scene, ref, prompt, seed):
    i1 = upload_image(os.path.join(OUT, scene))
    i2 = upload_image(ref)
    hits = lint(prompt, mode="edit")
    print("[lock %s] lint=%s" % (name, hits or "GREEN"), flush=True)
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt, seed, i1, i2),
                                    "client_id": "bma-30s-reel-lock"})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 1200:
        time.sleep(5)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("[lock %s] ERROR" % name, flush=True)
                return
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=120).read()
                    open(os.path.join(OUT, name), "wb").write(data)
                    print("[lock %s] SAVED (%.0fs)" % (name, time.time() - t0), flush=True)
                    return
    print("[lock %s] TIMEOUT" % name, flush=True)

def main():
    for name, scene, ref, prompt, seed in JOBS:
        run_one(name, scene, ref, prompt, seed)
    print("FACE LOCK DONE 4", flush=True)

if __name__ == "__main__":
    main()

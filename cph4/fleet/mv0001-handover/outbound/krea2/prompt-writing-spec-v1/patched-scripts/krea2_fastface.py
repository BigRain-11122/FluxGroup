# -*- coding: utf-8 -*-
# krea2_fastface.py - FAST face-design variation batch (Lightning 4-step, CEO pick-ready)
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\fastface"
os.makedirs(OUT, exist_ok=True)
SRC = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\jayphotos\era\ceo_ref_poster_crop.png"

UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
LIGHTNING = "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
# v2 (O-20261009-1815/1830): result-state edit instruction (official style),
# keep-dominant, zero negatives, official 4K suffix slot kept.
PROMPT = ("Edit only the background: replace the background with a plain dark studio wall, and keep this "
          "young man completely unchanged - identical oval face with soft full cheeks, identical small "
          "dark monolid eyes with the same low sleepy detached gaze, identical straight dark eyebrows "
          "hidden under the same heavy straight blunt-cut black fringe covering the eyebrows, identical "
          "soft rounded nose tip, identical full relaxed lips, identical natural matte skin with warm "
          "2001 film grain, wearing the same red hoodie. Warm orange-red 2001 telecine grade.")

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=60).read())

def upload_image(path, name=None):
    fn = name or os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----fastface" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return r.get("name", fn)

def graph(prompt_text, seed, img1, denoise=0.8):
    return {
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
            "clip": ["162", 0], "vae": ["146", 0], "image1": ["160", 0], "prompt": prompt_text}},
        "149": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["162", 0], "vae": ["146", 0], "image1": ["160", 0], "prompt": ""}},
        "148": {"class_type": "FluxKontextMultiReferenceLatentMethod",
                "inputs": {"conditioning": ["151", 0], "reference_latents_method": "index_timestep_zero"}},
        "147": {"class_type": "FluxKontextMultiReferenceLatentMethod",
                "inputs": {"conditioning": ["149", 0], "reference_latents_method": "index_timestep_zero"}},
        "169": {"class_type": "KSampler", "inputs": {
            "model": ["153", 0], "positive": ["148", 0], "negative": ["147", 0],
            "latent_image": ["156", 0], "seed": seed, "steps": 4, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple", "denoise": denoise}},
        "158": {"class_type": "VAEDecode", "inputs": {"samples": ["169", 0], "vae": ["146", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["158", 0], "filename_prefix": "fastface"}},
    }

def run_one(name, seed, img1, denoise):
    print("START %s ..." % name, flush=True)
    pid = post(SERVER + "/prompt", {"prompt": graph(PROMPT, seed, img1, denoise),
                                    "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(3)
        h = get(SERVER + "/history/" + pid)
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR %s:" % name, json.dumps(h[pid]["status"].get("messages", []))[:600], flush=True)
                return None
            for node_id, node_out in h[pid]["outputs"].items():
                for img in node_out.get("images", []):
                    data = urllib.request.urlopen(SERVER + "/view?filename=" + img["filename"] +
                        "&subfolder=" + img["subfolder"] + "&type=" + img["type"], timeout=180).read()
                    fp = os.path.join(OUT, name + ".png")
                    open(fp, "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0), flush=True)
                    return fp
    print("TIMEOUT %s" % name, flush=True)
    return None

def main():
    src = upload_image(SRC)
    print("uploaded:", src, flush=True)
    for i, sd in enumerate([7301, 7302, 7303, 7304, 7305, 7306, 7307, 7308]):
        run_one("F%d_seed%d_dn80" % (i, sd), sd, src, 0.8)
    for j, sd in enumerate([7311, 7312]):
        run_one("F%d_seed%d_dn70" % (8 + j, sd), sd, src, 0.7)
    print("FASTFACE DONE", flush=True)

if __name__ == "__main__":
    main()
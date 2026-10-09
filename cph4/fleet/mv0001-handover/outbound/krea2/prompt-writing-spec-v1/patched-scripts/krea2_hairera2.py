# -*- coding: utf-8 -*-
# krea2_hairera2.py - text-only era-hairstyle hard restyle on approved face (no celebrity photo refs in pipeline)
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\hairera"
os.makedirs(OUT, exist_ok=True)
BASE = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\designs2\M6_era_closeup.png"

UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
# v2 (O-20261009-1815/1830): geometry-first era fringe kept (CEO-approved slab tokens),
# negative wall removed; hair described as one dense mass with matte finish.
H2001_HARD = ("Change only his hairstyle into an authentic year-2001 Taiwanese college-student haircut: "
              "a blunt, straight-cut, full black fringe like a solid slab falling flat over the eyebrows, "
              "covering the forehead completely, dead-straight matte texture as one dense unlayered mass "
              "with a hard straight edge, squared side masses covering half the ears, flat heavy natural "
              "look, plainly grown and unstyled like ordinary early-2000s Asian college students, matte "
              "finish. Keep his face completely unchanged - identical face shape, head angle, eyes, gaze, "
              "nose, mouth, lips and skin. Keep the lighting, background, color grade and clothing "
              "unchanged. Only the hairstyle changes.")

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=60).read())

def upload_image(path, name=None):
    fn = name or os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----hairera2" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return r.get("name", fn)

def graph(prompt_text, seed, img1, steps=40, cfg=4.0, denoise=0.72):
    return {
        "161": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "145": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["161", 0], "shift": 3.1}},
        "152": {"class_type": "CFGNorm", "inputs": {"model": ["145", 0], "strength": 1.0, "pre_cfg": False}},
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
            "model": ["152", 0], "positive": ["148", 0], "negative": ["147", 0],
            "latent_image": ["156", 0], "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "simple", "denoise": denoise}},
        "158": {"class_type": "VAEDecode", "inputs": {"samples": ["169", 0], "vae": ["146", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["158", 0], "filename_prefix": "hairera"}},
    }

def run_one(name, prompt_text, seed, img1, steps=40, cfg=4.0, denoise=0.72):
    print("START %s ..." % name, flush=True)
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed, img1, steps, cfg, denoise),
                                    "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 2400:
        time.sleep(5)
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
                    print("SAVED %s (%.0fs) -> %s" % (name, time.time() - t0, fp), flush=True)
                    return fp
    print("TIMEOUT %s" % name, flush=True)
    return None

def main():
    b = upload_image(BASE, "m6_era_closeup.png")
    print("uploaded base:", b, flush=True)
    run_one("H1b_2001_dn72", H2001_HARD, 7111, b, denoise=0.72)
    run_one("H1c_2001_dn78", H2001_HARD, 7112, b, denoise=0.78)
    print("HAIRERA2 DONE", flush=True)

if __name__ == "__main__":
    main()
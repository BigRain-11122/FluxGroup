# -*- coding: utf-8 -*-
# krea2_hairera.py - hairstyle-era swap on the CEO-approved face M6_era_closeup
# standalone (avoids concurrent edits to krea2_qwen2511_edit.py from other windows)
# v2 (O-20261009-1815/1830): negative hair wall removed per prompt-spec v1.1 -
#   hair geometry described positively (era hair tokens instead of "no see-through / no salon" wall).
import json, time, os, sys, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\hairera"
os.makedirs(OUT, exist_ok=True)

BASE = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\designs2\M6_era_closeup.png"
WEB = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\jayphotos"
ERA = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\jayphotos\era"

UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"

KEEP_HAIR = ("Keep his face completely unchanged - identical face shape, head angle, eyes, gaze, nose, "
             "mouth, lips and skin with natural film grain and pores. Keep the lighting, background, "
             "color grade and clothing unchanged. Only the hairstyle changes.")

H2001 = ("Change only his hairstyle: give him the hairstyle of the man in the second image - a heavy "
         "natural black shag from the year 2001, long thick messy fringe falling flat over the eyebrows "
         "and nearly covering them, a solid dense fringe and flat heavy hair lying naturally, plainly "
         "kept early-2000s Taiwanese college-student hair. " + KEEP_HAIR)
H2002 = ("Change only his hairstyle: give him the hairstyle of the man in the second image - a layered "
         "black shag from the year 2002 with the long fringe swept diagonally across the forehead, brows "
         "partly visible, jaw-length sides, a heavy natural matte finish. " + KEEP_HAIR)
H2003 = ("Change only his hairstyle: give him the hairstyle of the man in the second image - black layered "
         "hair from the year 2003 with a heavier straight fringe hanging down over the eyebrows, flat and "
         "heavy, a plain natural 2003 look. " + KEEP_HAIR)

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=60).read())

def upload_image(path, name=None):
    fn = name or os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----hairera" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return r.get("name", fn)

def graph(prompt_text, seed, img1, img2, steps=40, cfg=4.0, denoise=0.62):
    return {
        "161": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "145": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["161", 0], "shift": 3.1}},
        "152": {"class_type": "CFGNorm", "inputs": {"model": ["145", 0], "strength": 1.0, "pre_cfg": False}},
        "162": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "qwen_image", "device": "default"}},
        "146": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "164": {"class_type": "LoadImage", "inputs": {"image": img1}},
        "160": {"class_type": "FluxKontextImageScale", "inputs": {"image": ["164", 0]}},
        "156": {"class_type": "VAEEncode", "inputs": {"pixels": ["160", 0], "vae": ["146", 0]}},
        "165": {"class_type": "LoadImage", "inputs": {"image": img2}},
        "151": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["162", 0], "vae": ["146", 0], "image1": ["160", 0], "image2": ["165", 0], "prompt": prompt_text}},
        "149": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["162", 0], "vae": ["146", 0], "image1": ["160", 0], "image2": ["165", 0], "prompt": ""}},
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

def run_one(name, prompt_text, seed, img1, img2, steps=40, cfg=4.0, denoise=0.62):
    print("START %s ..." % name, flush=True)
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed, img1, img2, steps, cfg, denoise),
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
    dn = float(os.environ.get("HAIRERA_DN", "0.62"))
    b = upload_image(BASE, "m6_era_closeup.png")
    print("uploaded base:", b, flush=True)
    ref01 = upload_image(os.path.join(WEB, "web_5.jpg"))
    ref02 = upload_image(os.path.join(ERA, "bd_1.jpg"))
    ref03 = upload_image(os.path.join(ERA, "yhm_3.jpg"))
    run_one("H1_2001fantasy", H2001, 7101, b, ref01, denoise=dn)
    run_one("H2_2002eightdim", H2002, 7102, b, ref02, denoise=dn)
    run_one("H3_2003yehuimei", H2003, 7103, b, ref03, denoise=dn)
    print("HAIRERA DONE", flush=True)

if __name__ == "__main__":
    main()
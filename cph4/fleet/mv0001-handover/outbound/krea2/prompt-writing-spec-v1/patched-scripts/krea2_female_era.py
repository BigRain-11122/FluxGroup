# -*- coding: utf-8 -*-
# krea2_female_era.py - apply early-2000s Taiwanese female-idol facial DNA (from AI-generated J1) to female lead frames
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\femaleera"
os.makedirs(OUT, exist_ok=True)
D3 = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\designs3"

UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
# v2 (O-20261009-1815/1830): era-DNA migration prompts, zero negatives;
# era-girl anchors (blunt full fringe / structural apple cheeks) stated positively.
KEEP_W = ("Keep the first image's white dress, pose, lighting, background and composition completely "
          "unchanged.")
FE1 = ("Change only the woman's face and hairstyle to match the woman in the second image: the same softly "
       "round face with full apple cheeks as natural structure, the same big dark double-lidded "
       "rounded-almond eyes with a clear eyelid fold, the same small nose with a soft rounded tip, the "
       "same medium-full rosy lips, the same soft natural brows, the same sweet gentle expression, and "
       "the same hairstyle - long straight black hair with a solid blunt full fringe lying flat on the "
       "eyebrows. " + KEEP_W)
FE2 = ("Change only the woman's facial features to match the woman in the second image: the same softly "
       "round face with full apple cheeks as natural structure, the same big dark double-lidded "
       "rounded-almond eyes, the same small nose with a soft rounded tip, the same medium-full rosy "
       "lips, the same soft natural brows, the same sweet gentle expression. Keep her own center-parted "
       "long straight black hair exactly as it is. " + KEEP_W)
FE3 = ("Change only her clothing and background: dress her as an ordinary 2001 Taiwanese college student "
       "in a simple plain knit top of natural slightly worn fabric, placed in a dim old-bookstore aisle "
       "with warm tungsten light and shelves of worn paper books behind her. Keep her face and hairstyle "
       "exactly identical - the same softly round face with full apple cheeks, the same big dark "
       "double-lidded eyes, the same small nose, the same rosy lips, and the same long straight hair "
       "with a solid blunt full fringe. Subtle 2001 film grain, warm telecine skin tones.")

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=60).read())

def upload_image(path, name=None):
    fn = name or os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----femaleera" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return r.get("name", fn)

def graph(prompt_text, seed, img1, img2=None, steps=40, cfg=4.0, denoise=0.65):
    g = {
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["158", 0], "filename_prefix": "femaleera"}},
    }
    if img2:
        g["165"] = {"class_type": "LoadImage", "inputs": {"image": img2}}
        g["151"]["inputs"]["image2"] = ["165", 0]
        g["149"]["inputs"]["image2"] = ["165", 0]
    return g

def run_one(name, prompt_text, seed, img1, img2=None, steps=40, cfg=4.0, denoise=0.65):
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
    vvr = upload_image(os.path.join(D3, "V3_vvr_goddess.png"))
    j1 = upload_image(os.path.join(D3, "J1_jolin_portrait.png"))
    print("uploaded:", vvr, j1, flush=True)
    run_one("W1_goddess_eraDNA", W1, 7201, vvr, img2=j1, denoise=0.65)
    run_one("W2_goddess_softDNA", W2, 7202, vvr, img2=j1, denoise=0.65)
    run_one("W3_campus_sweet", W3, 7203, j1, denoise=0.6)
    print("FEMALEERA DONE", flush=True)

if __name__ == "__main__":
    main()
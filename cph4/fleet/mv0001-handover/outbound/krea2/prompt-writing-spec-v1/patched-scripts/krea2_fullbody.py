# -*- coding: utf-8 -*-
# krea2_fullbody.py - full-body + multi-view extension of approved male-lead canon F5_seed7306_dn80
# Recipe mirrors krea2_fastface.py (Lightning 4-step, dn 0.8) with F5 canon as identity base.
import json, time, os, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\fullbody"
os.makedirs(OUT, exist_ok=True)
SRC = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\fastface\F5_seed7306_dn80.png"

UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
LIGHTNING = "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
# v2 (O-20261009-1815/1830): ID block positive-only (Korean-styling negation removed),
# NO_TEXT removed; full-body framing verbs kept verbatim (CEO-approved batch recipe).
ID_BLOCK = ("the same young man from the photo: oval face with soft full cheeks, small dark monolid eyes "
            "with a low sleepy detached gaze, straight dark eyebrows hidden under his heavy straight "
            "blunt-cut black fringe covering the eyebrows, soft rounded nose tip, full relaxed lips, "
            "era-authentic plainly kept natural look, warm 2001 telecine grade, natural film grain. ")

W1 = ("Recreate the same young man as a FULL-BODY standing portrait, feet visible at the bottom edge, "
      "standing straight facing the camera, wearing the same red hoodie with plain loose dark jeans and "
      "simple sneakers, hands relaxed at his sides, plain dark studio background, full figure from head "
      "to shoes in frame. He is " + ID_BLOCK)
W2 = ("Recreate the same young man as a FULL-BODY walking pose, three-quarter view mid-stride, same red "
      "hoodie with plain loose dark jeans, walking through a quiet night street in 2001 Taipei, warm "
      "sodium street lamps, full figure from head to shoes in frame. He is " + ID_BLOCK)
W3 = ("Recreate the same young man as a FULL-BODY shot standing in an ancient Babylonian scriptorium, "
      "wearing a rough hand-woven undyed linen tunic with a simple rope belt, holding a wet clay tablet "
      "in both hands, clay tablet shelves and a single clay oil lamp around him, lit strictly from the "
      "left, warm amber monochrome, deep shadows, full figure from head to bare feet in frame. He is " + ID_BLOCK)
W4 = ("Recreate the same young man as a FULL-BODY shot seated at a long wooden library desk between tall "
      "bookshelves, leaning over an open book, warm desk lamp light from the side, 2001 reading room "
      "atmosphere, full seated figure in frame. He is " + ID_BLOCK)
W5 = ("Recreate the same young man as a FULL-BODY shot standing in front of a glass shop window at night, "
      "his reflection faintly visible in the glass, 2001 Taipei street with warm shop lights, full "
      "figure from head to shoes in frame. He is " + ID_BLOCK)
W6 = ("Recreate the same young man as a FULL-BODY shot seen from behind, walking away down an aisle "
      "between tall dark bookshelves, head slightly bowed, same red hoodie and dark jeans, single warm "
      "ceiling lamp glow, full figure in frame. He is " + ID_BLOCK)

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=60).read())

def upload_image(path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----fullbody" + uuid.uuid4().hex
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["158", 0], "filename_prefix": "fullbody"}},
    }

def run_one(name, seed, img1, prompt_text, denoise=0.8):
    print("START %s ..." % name, flush=True)
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed, img1, denoise),
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
    print("uploaded canon F5:", src, flush=True)
    for nm, sd, pt in [("W1_stand_front", 7401, W1), ("W2_walk_street", 7402, W2),
                      ("W3_scribe_room", 7403, W3), ("W4_library_seat", 7404, W4),
                      ("W5_shopwindow", 7405, W5), ("W6_back_aisle", 7406, W6)]:
        run_one(nm, sd, src, pt)
    print("FULLBODY DONE", flush=True)

if __name__ == "__main__":
    main()
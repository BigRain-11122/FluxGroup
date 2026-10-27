# -*- coding: utf-8 -*-
# krea2_qwen2511_edit.py - Qwen-Image-Edit-2511 int8 true-edit pipeline (identity-preserving)
# Wiring mirrors official template image_qwen_image_edit_2511_int8.json:
#   base image -> FluxKontextImageScale -> VAEEncode (latent) + TextEncodeQwenImageEditPlus.image1 (x2 pos/neg)
#   pos/neg conditioning both through FluxKontextMultiReferenceLatentMethod(index_timestep_zero)
#   Lightning 4-step LoRA path: steps=4 cfg=1.0 (off: steps=40 cfg=4.0)
# v2 (O-20261009-1815/1830): all edit prompts rebuilt per prompt-spec v1.1 sec.4 -
#   one direct change sentence + positive keep list; zero negatives anywhere (NO_TEXT / ANTI_K removed;
#   "no beautification / no makeup" walls replaced by positive skin-texture keep lines).
import json, time, os, sys, urllib.request, uuid

SERVER = "http://127.0.0.1:8188"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\qedit"
os.makedirs(OUT, exist_ok=True)

UNET = "qwen_image_edit_2511_int8_convrot.safetensors"
CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
LIGHTNING = "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=60).read())

def upload_image(path, name=None):
    fn = name or os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----qedit" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return r.get("name", fn)

def graph(prompt_text, seed, img1, img2=None, img3=None, steps=4, cfg=1.0, lightning=True, denoise=1.0):
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
            "model": ["153", 0], "positive": ["148", 0], "negative": ["147", 0],
            "latent_image": ["156", 0], "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "simple", "denoise": denoise}},
        "158": {"class_type": "VAEDecode", "inputs": {"samples": ["169", 0], "vae": ["146", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["158", 0], "filename_prefix": "qedit"}},
    }
    if lightning:
        g["153"] = {"class_type": "LoraLoaderModelOnly",
                    "inputs": {"model": ["152", 0], "lora_name": LIGHTNING, "strength_model": 1.0}}
    else:
        g["169"]["inputs"]["model"] = ["152", 0]
    if img2:
        g["165"] = {"class_type": "LoadImage", "inputs": {"image": img2}}
        g["151"]["inputs"]["image2"] = ["165", 0]
        g["149"]["inputs"]["image2"] = ["165", 0]
    if img3:
        g["166"] = {"class_type": "LoadImage", "inputs": {"image": img3}}
        g["151"]["inputs"]["image3"] = ["166", 0]
        g["149"]["inputs"]["image3"] = ["166", 0]
    return g

def run_one(name, prompt_text, seed, img1, img2=None, img3=None, steps=4, cfg=1.0, lightning=True, denoise=1.0):
    print("START %s ..." % name, flush=True)
    pid = post(SERVER + "/prompt", {"prompt": graph(prompt_text, seed, img1, img2, img3, steps, cfg, lightning, denoise),
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

FR = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\mvframes"
ERA = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\jayphotos\era"
WEB = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\jayphotos"
OLD = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\jay-face-v1"
CHARS = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\character-design-v1"

# ---- v2 edit prompts: change sentence + positive keep list (zero negatives) ----
KEEP_FACE = ("Keep the face completely unchanged - identical face shape and head angle, "
             "identical half-lidded sleepy eyes with the same downward gaze, identical nose, mouth, "
             "chin and jawline, identical skin with natural 2001 film grain and visible pores.")
REF3 = "The third image shows the same man from another angle for identity reference. "

A1 = ("Edit only the background: replace the background with a plain dark studio wall. "
      "Keep the man completely unchanged - identical face shape and head angle, identical half-lidded "
      "sleepy eyes with the same downward gaze, identical nose, mouth, chin and jawline, identical messy "
      "black fringe, identical clothing, identical skin with natural 2001 film grain and visible pores.")
A2 = ("Change only the man's hairstyle: give him the hairstyle shown in the second image - a layered black "
      "shag with a long fringe swept diagonally across the forehead, brows partly visible, jaw-length sides. "
      + REF3 + KEEP_FACE + " Only the hairstyle changes.")
A3 = ("Change only the man's hairstyle: give him the hairstyle shown in the second image - black layered "
      "hair with a heavier straight fringe hanging down over the eyebrows. " + REF3 + KEEP_FACE +
      " Only the hairstyle changes.")
A4 = ("Change only the man's hairstyle: trim it into a shorter, neat black college-student cut with a short "
      "fringe above the eyebrows. " + REF3 + "Keep his face completely unchanged - identical face shape and "
      "head angle, identical half-lidded sleepy eyes with the same downward gaze, identical nose, mouth, chin "
      "and jawline, identical skin with natural 2001 film grain and pores. Only the hairstyle changes.")
A5 = ("Change only the man's gaze: make him look directly into the camera with eyes fully open, natural "
      "relaxed eyelids. " + REF3 + "Keep everything else completely unchanged - identical face shape, head "
      "angle, nose, mouth, chin, jawline, identical messy black fringe, identical skin with natural 2001 "
      "film grain and visible pores. Only the gaze changes.")
A6 = ("Edit only the background: replace the background with a plain dark studio wall. "
      "Keep the man completely unchanged - identical face shape and head angle, identical eyes and gaze, "
      "identical nose, mouth, chin and jawline, identical messy black fringe, identical clothing, identical "
      "skin with natural film grain and visible pores.")
B1 = ("Change only his clothing and lighting: replace his shirt with the plain dark tunic of an ancient "
      "Babylonian scribe, and light him strictly from the left by a single clay oil lamp with an open "
      "flame at 2000K, the right side falling into soft shadow. " + REF3 + KEEP_FACE +
      " Warm amber monochrome grade, subtle 35mm film grain, deep shadows.")

RESTORE = ("Restore the man's face in the first image to exactly match the man in the second image: the same "
           "wide flat cheekbones, the same blunt rounded jaw with a short chin and wide lower face, the same "
           "small single-lidded sleepy eyes with heavy relaxed lids, the same flat round nose tip, the same "
           "thick lower lip, the same thick messy black fringe falling over his eyebrows, the same natural "
           "skin with visible pores. Keep the first image's pose, costume, lighting, color grade, composition "
           "and background completely unchanged.")

SWAP = ("Replace the man in the second image with the man from the first image. The output must show the "
        "exact face of the man in the first image: the same bone structure, eyes, nose and lips, the same "
        "wide flat cheekbones and blunt rounded jaw, the same small single-lidded sleepy eyes, the same "
        "thick messy black fringe. The third image shows the same man from another angle. Keep the second "
        "image's pose, costume, lighting, composition, color grade and background unchanged, with natural "
        "2001 film grain.")
SWAP2 = ("Replace the face of the man in the first image with the face of the man in the second image: "
         "the same bone structure, eyes, nose and lips, the same wide flat cheekbones and blunt rounded "
         "jaw, the same small single-lidded sleepy eyes, the same thick messy black fringe. The third "
         "image shows the same man from another angle. Keep the first image's pose, composition, framing, "
         "costume, lighting, color grade and background completely unchanged, with natural 2001 film grain.")
# short inline swap used by batchT/batchB (was repeated verbatim 4x with NO_TEXT appended)
SWAP_T3 = ("Replace the man in the second image with the man from the first image. The output must show the "
           "exact face of the man in the first image: the same bone structure, eyes, nose and lips. The third "
           "image shows the same man from another angle. Keep the second image's pose, costume, lighting, "
           "composition, color grade and background unchanged.")

V3_CANON = ("Edit only the background: replace the background with a plain dark studio wall. Keep the man "
            "completely unchanged - identical face, identical head angle, identical eyes and gaze, identical "
            "nose, mouth, chin and jawline, identical hair, and keep his own original clothing from the photo, "
            "with the natural film photo texture of grain and pores.")
V3_SCRIBE = ("Change only his clothing and lighting: replace his shirt with a rough hand-woven undyed "
             "linen tunic in a loose plain cut with a simple rope belt, weathered dusty working fabric of "
             "ancient Mesopotamia. Light him strictly from the left by a single clay oil lamp with an open "
             "flame at 2000K, the right side falling into soft shadow. Keep his face completely unchanged - "
             "identical face shape and head angle, identical half-lidded sleepy eyes with the same downward "
             "gaze, identical nose, mouth, chin and jawline, identical messy black fringe, identical skin "
             "with natural 2001 film grain and pores. Warm amber monochrome grade, subtle 35mm film grain, "
             "deep shadows.")

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    full = os.environ.get("QEDIT_FULL", "0") == "1"  # 1 = 40 steps cfg 4.0 no Lightning
    st, cf, lt = (40, 4.0, False) if full else (4, 1.0, True)
    print("MODE: steps=%d cfg=%.1f lightning=%s" % (st, cf, lt), flush=True)
    fr81 = upload_image(os.path.join(FR, "fr_0081_crop.png"))
    print("uploaded fr_0081_crop:", fr81, flush=True)
    if which == "smoke":
        run_one("SMOKE_idtest", A1, 7001, fr81, steps=st, cfg=cf, lightning=lt)
    elif which == "batchA":
        bd1 = upload_image(os.path.join(ERA, "bd_1.jpg"))
        yhm3 = upload_image(os.path.join(ERA, "yhm_3.jpg"))
        web5 = upload_image(os.path.join(WEB, "web_5.jpg"))
        fr65 = upload_image(os.path.join(FR, "fr_0065_crop.png"))
        dn = float(os.environ.get("QEDIT_DN", "0.55"))
        print("HAIR BATCH denoise=%.2f" % dn, flush=True)
        run_one("A2_hair2002", A2, 7002, fr81, img2=bd1, img3=fr65, steps=st, cfg=cf, lightning=lt, denoise=dn)
        run_one("A3_hair2003", A3, 7003, fr81, img2=yhm3, img3=fr65, steps=st, cfg=cf, lightning=lt, denoise=dn)
        run_one("A4_campus", A4, 7004, fr81, img3=fr65, steps=st, cfg=cf, lightning=lt, denoise=dn)
        run_one("A5_eyesopen", A5, 7005, fr81, img3=fr65, steps=st, cfg=cf, lightning=lt, denoise=dn)
        run_one("A6_web5base", A6, 7006, web5, steps=st, cfg=cf, lightning=lt, denoise=dn)
    elif which == "batchT":
        bn2 = upload_image(os.path.join(OLD, "BN2_seed9046.png"))
        m2 = upload_image(os.path.join(CHARS, "M2_scribe.png"))
        fr65 = upload_image(os.path.join(FR, "fr_0065_crop.png"))
        run_one("T1_bgswap_dn55", A1, 7021, fr81, img3=fr65, steps=st, cfg=cf, lightning=lt, denoise=0.55)
        run_one("T2_scribe", B1, 7022, fr81, img3=fr65, steps=st, cfg=cf, lightning=lt)
        run_one("T3_intoBN2", SWAP_T3, 7023, fr81, img2=bn2, img3=fr65, steps=st, cfg=cf, lightning=lt)
        run_one("T4_intoM2", SWAP_T3, 7024, fr81, img2=m2, img3=fr65, steps=st, cfg=cf, lightning=lt)
    elif which == "restore":
        qe = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\scratch\mv-carve-bma\krea2-out\qedit"
        dn = float(os.environ.get("QEDIT_DN", "0.6"))
        for src, nm, sd in [("T2_scribe.png", "R1_scribe_fix", 7031), ("T3_intoBN2.png", "R2_bn2_fix", 7032),
                            ("T4_intoM2.png", "R3_m2_fix", 7033)]:
            p = os.path.join(qe, src)
            if not os.path.exists(p):
                print("SKIP %s (missing %s)" % (nm, src), flush=True)
                continue
            s1 = upload_image(p)
            run_one(nm, RESTORE, sd, s1, img2=fr81, steps=st, cfg=cf, lightning=lt, denoise=dn)
    elif which == "official":
        dn = float(os.environ.get("QEDIT_DN", "0.55"))
        fr65 = upload_image(os.path.join(FR, "fr_0065_crop.png"))
        bd3 = upload_image(os.path.join(ERA, "bd_3.jpg"))
        bd1 = upload_image(os.path.join(ERA, "bd_1.jpg"))
        run_one("O1_bd3_relight", A6, 7041, bd3, steps=st, cfg=cf, lightning=lt, denoise=dn)
        run_one("O2_bd1_relight", A6, 7042, bd1, steps=st, cfg=cf, lightning=lt, denoise=dn)
    elif which == "batchM":
        fr65 = upload_image(os.path.join(FR, "fr_0065_crop.png"))
        for tgt, nm, sd in [("M1_portrait.png", "M_S1_portrait", 7051), ("M3_modern2001.png", "M_S2_modern", 7052),
                            ("M4_overshoulder_v2.png", "M_S3_shoulder", 7053), ("M6_hands_writing.png", "M_S4_writing", 7054)]:
            t = upload_image(os.path.join(CHARS, tgt))
            run_one(nm, SWAP, sd, fr81, img2=t, img3=fr65, steps=st, cfg=cf, lightning=lt)
        bn2b = upload_image(os.path.join(OLD, "BN2_seed9046.png"))
        run_one("M_S5_bn2_seedb", SWAP, 7055, fr81, img2=bn2b, img3=fr65, steps=st, cfg=cf, lightning=lt)
    elif which == "batchN":
        fr65 = upload_image(os.path.join(FR, "fr_0065_crop.png"))
        t = upload_image(os.path.join(CHARS, "M1_portrait.png"))
        run_one("N_S1_compkeep", SWAP2, 7061, t, img2=fr81, img3=fr65, steps=st, cfg=cf, lightning=lt)
    elif which == "v3":
        dn = float(os.environ.get("QEDIT_DN", "0.45"))
        web5 = upload_image(os.path.join(WEB, "web_5.jpg"))
        bd3 = upload_image(os.path.join(ERA, "bd_3.jpg"))
        run_one("V3A_web5_canon", V3_CANON, 7071, web5, steps=st, cfg=cf, lightning=lt, denoise=dn)
        run_one("V3B_bd3_canon", V3_CANON, 7072, bd3, steps=st, cfg=cf, lightning=lt, denoise=dn)
        run_one("V3C_scribe_antik", V3_SCRIBE, 7073, fr81, steps=st, cfg=cf, lightning=lt, denoise=0.6)
        run_one("V3D_fr81_dn45", V3_CANON, 7074, fr81, steps=st, cfg=cf, lightning=lt, denoise=dn)
    elif which == "batchB":
        bn2 = upload_image(os.path.join(OLD, "BN2_seed9046.png"))
        m2 = upload_image(os.path.join(CHARS, "M2_scribe.png"))
        fr65 = upload_image(os.path.join(FR, "fr_0065_crop.png"))
        run_one("B1_scribe", B1, 7011, fr81, img3=fr65, steps=st, cfg=cf, lightning=lt)
        run_one("B2_intoBN2", SWAP_T3, 7012, fr81, img2=bn2, img3=fr65,
              steps=st, cfg=cf, lightning=lt)
        run_one("B3_intoM2", SWAP_T3, 7013, fr81, img2=m2, img3=fr65,
              steps=st, cfg=cf, lightning=lt)
    print("BATCH %s DONE" % which, flush=True)

if __name__ == "__main__":
    main()

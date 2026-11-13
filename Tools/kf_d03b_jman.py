# -*- coding: utf-8 -*-
# kf_d03b_jman.py - mv0001 v729 D03b 男主身份锁 KF 四候选批产（重建版 2026-11-13）
#
# 缘起：v729 令（docs/orders.md 2026-11-13 21:55 行）——D03b 男主弃文字描述改 jman 身份锁。
# 原窗脚本随 CLI 重启丢失；本重建以盘上正身为准：
#   工作流 = krea2_jay_bone.py（三官方参考图 TextEncodeQwenImageEditPlus 身份流）
#   LoRA   = jman_v1_rank32.safetensors（v729 令点名；r2 批实测 strength 0.9）
#   提示词 = D03b_kf_reanchor.png 构图权威（正面近景直视/右上琥珀硬侧光/浮雕楔形文字墙）
#            + mv_full_kf_r2.py ID_BLOCK 骨相正典 + v723 B5 表演意图（静帧层）
#   资产   = krea2_turbo_fp8_scaled + qwen3vl_4b_fp8_scaled + qwen_image_vae（本机在位实测）
# 用法: python Tools/kf_d03b_jman.py [--server http://127.0.0.1:8188] [--strength 0.9]
import argparse, json, os, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, 'media', 'mv-album-001-jay', 'v729-candidates')
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 1344, 768

NO_TEXT = ("Absolutely no readable modern text, no typography, no letters, no logos, no watermark, pure imagery only.")

# 男主身份块 = mv_full_kf_r2.py ID_BLOCK 正典逐字 + jman trigger
ID_BLOCK = ("a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, "
            "softly rounded cheeks, a flat round nose tip, a blunt rounded jaw and natural "
            "unretouched skin with visible pores, his thick black fringe lying flat over his "
            "eyebrows, wearing a rough hand-woven undyed linen tunic with a simple rope belt")

# D03b_direct_gaze 场景词（构图权威=D03b_kf_reanchor.png：正面近景·直视·右上琥珀硬侧光·浮雕楔形文字墙·暖金铜低明度）
PROMPT = ("jman, " + ID_BLOCK + ", "
          "frontal close-up, head and shoulders, facing the camera with a direct level gaze, "
          "his eyes lifted, still and deliberate, lips relaxed and closed, the face carved out of darkness "
          "by a single hard amber torch flame from the upper right, the left side of his face falling into "
          "deep shadow in a Rembrandt split, warm rim light on his black fringe. "
          "Behind him a dark basalt temple wall carries horizontal bands of carved cuneiform wedge signs "
          "and shallow relief figures of seated gods, softly out of focus at f/2.8 on a 50mm lens. "
          "A reed-bundle torch in a cast bronze sconce breathing at the frame edge. "
          "Warm amber monochrome grade, deep crushed shadows, shot on 35mm Kodak Vision 500T 5279, "
          "visible grain, halation on the flame, cinematic film still from a 2001 Taiwanese music video. "
          "NOT a Korean idol, no K-pop styling, no makeup, no glossy idol look. " + NO_TEXT)

SEEDS = [30972901, 30972902, 30972903, 30972904]  # v729 段，避开 r2 批 30700001 段与 20260001 老段


def graph(prompt_text, seed, lora_strength):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "15": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["10", 0], "lora_name": "jman_v1_rank32.safetensors", "strength_model": lora_strength}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "69": {"class_type": "LoadImage", "inputs": {"image": "ref_main_9.jpg"}},
        "70": {"class_type": "LoadImage", "inputs": {"image": "ref_close_1.jpg"}},
        "71": {"class_type": "LoadImage", "inputs": {"image": "ref_mv_91.jpg"}},
        "52": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {
            "clip": ["11", 0], "vae": ["12", 0], "image1": ["69", 0], "image2": ["70", 0], "image3": ["71", 0], "prompt": prompt_text}},
        "53": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["52", 0], "reference_latents_method": "index_timestep_zero"}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["53", 0]}},
        "64": {"class_type": "ModelSamplingFlux", "inputs": {"model": ["15", 0], "max_shift": 1.15, "base_shift": 0.5, "width": W, "height": H}},
        "57": {"class_type": "CFGGuider", "inputs": {"model": ["64", 0], "positive": ["53", 0], "negative": ["13", 0], "cfg": 1.0}},
        "63": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "59": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "60": {"class_type": "BasicScheduler", "inputs": {"model": ["64", 0], "scheduler": "simple", "steps": 8, "denoise": 1.0}},
        "61": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "58": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["63", 0], "guider": ["57", 0], "sampler": ["59", 0], "sigmas": ["60", 0], "latent_image": ["61", 0]}},
        "62": {"class_type": "VAEDecode", "inputs": {"samples": ["58", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["62", 0], "filename_prefix": "v729_d03b"}},
    }


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())


def run_one(server, name, seed, strength):
    dst = os.path.join(OUT_DIR, name + ".png")
    if os.path.isfile(dst) and os.path.getsize(dst) > 100000:
        print("SKIP", name, flush=True)
        return True
    pid = post(server + "/prompt", {"prompt": graph(PROMPT, seed, strength), "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(3)
        try:
            h = get(server + "/history/" + pid)
        except Exception:
            continue
        if pid in h:
            if h[pid].get("status", {}).get("status_str") == "error":
                print("ERROR %s: %s" % (name, json.dumps(h[pid]["status"].get("messages", []))[:400]), flush=True)
                return False
            for nid, out in h[pid]["outputs"].items():
                for img in out.get("images", []):
                    data = urllib.request.urlopen(
                        "%s/view?filename=%s&subfolder=%s&type=%s" % (
                            server, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                        timeout=90).read()
                    open(dst, "wb").write(data)
                    print("SAVED %s (%.0fs)" % (name, time.time() - t0), flush=True)
                    return True
    print("TIMEOUT " + name, flush=True)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--strength", type=float, default=0.9)
    args = ap.parse_args()
    get(args.server + "/system_stats")  # alive check
    done, fail = [], []
    for i, s in enumerate(SEEDS):
        name = "D03b_jman_c%d_seed%d" % (i + 1, s)
        ok = run_one(args.server, name, s, args.strength)
        (done if ok else fail).append(name)
    print("BATCH DONE ok=%d fail=%d -> %s" % (len(done), len(fail), OUT_DIR), flush=True)
    sys.exit(0 if not fail else 1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""POOL-0021 leg-2 smoke: Qwen-Image-2.1 Turbo int8 text-to-image on the v0.42
sidecar (127.0.0.1:8199). Verifies the four-file stack end to end and records
speed / VRAM / output for the three-account table.

Params per recipe cph4/fleet/bm-b-model-stack-20261016.md:
  1024x1024, 8 steps, cfg 1 (turbo LoRA), euler/simple, QwenImage21Cache(auto).
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.request

SERVER = "http://127.0.0.1:8199"
OUTDIR = r"K:\Fluxgroup\FluxGroup\media\comfy-sidecar\smoke"
os.makedirs(OUTDIR, exist_ok=True)

DIT = "qwen_image_2.1_turbo_int8_convrot.safetensors"
TE = "qwen3vl_8b_w4a8.safetensors"
VAE = "qwen_image_2.1_vae_bf16.safetensors"
LORA = "qwen_image_2.1_turbo_lora_avg_rank_178_bf16.safetensors"

PROMPT = ("A single vintage cassette on a wooden desk in slanted late-afternoon window light, "
          "dust motes in the air, shallow depth of field, warm film tone, fine grain, still life photograph")
NEG = ""

SEED = 991001


def http(path, data=None, timeout=240):
    req = urllib.request.Request(SERVER + path,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def vram():
    try:
        q = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                    stderr=subprocess.DEVNULL).decode().strip().splitlines()
        return int(q[0])
    except Exception:
        return -1


GRAPH = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": DIT, "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": TE, "type": "qwen_image"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
    "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": LORA, "strength_model": 1.0}},
    "5": {"class_type": "QwenImage21Cache", "inputs": {"model": ["4", 0], "device": "auto", "dtype": "default"}},
    "6": {"class_type": "TextEncodeQwenImage21",
          "inputs": {"clip": ["2", 0], "prompt": PROMPT, "negative_prompt": NEG, "resolution": 1024}},
    "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "8": {"class_type": "KSampler",
          "inputs": {"model": ["5", 0], "positive": ["6", 0], "negative": ["6", 1], "latent_image": ["6", 2],
                     "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                     "denoise": 1.0}},
    "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
    "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "qwen21_smoke"}},
}


def main():
    t0 = time.time()
    base = vram()
    print("VRAM before %d MB" % base, flush=True)
    resp = http("/prompt", {"prompt": GRAPH, "client_id": "bmc-qwen21-smoke"})
    pid = resp.get("prompt_id")
    if not pid:
        print("SUBMIT FAIL", json.dumps(resp)[:400])
        return 2
    print("submitted", pid, flush=True)
    peak = base
    t_submit = time.time()
    while time.time() - t_submit < 1800:
        time.sleep(2)
        cur = vram()
        peak = max(peak, cur)
        try:
            h = http("/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h.get(pid)
        if not e:
            continue
        st = e.get("status", {})
        if st.get("status_str") == "error":
            print("EXEC ERROR", json.dumps(st)[:1200])
            return 3
        imgs = []
        for o in e.get("outputs", {}).values():
            imgs += o.get("images", [])
        if imgs:
            im = imgs[0]
            u = "%s/view?filename=%s&subfolder=%s&type=%s" % (SERVER, im["filename"],
                                                              urllib.parse.quote(im.get("subfolder", "")),
                                                              im.get("type", "output"))
            raw = urllib.request.urlopen(u, timeout=120).read()
            dst = os.path.join(OUTDIR, "qwen21_smoke_1024_s%d.png" % SEED)
            io.open(dst, "wb").write(raw)
            wall = time.time() - t0
            rec = {"server": SERVER, "stack": "qwen21 turbo int8", "params": {"w": 1024, "h": 1024, "steps": 8,
                   "cfg": 1.0, "sampler": "euler", "scheduler": "simple", "seed": SEED, "lora": LORA},
                   "wall_s": round(wall, 1), "peak_vram_mb": peak, "out": dst, "bytes": os.path.getsize(dst),
                   "prompt": PROMPT}
            with open(os.path.join(OUTDIR, "qwen21_smoke_receipt.json"), "w", encoding="utf-8") as f:
                json.dump(rec, f, indent=1, ensure_ascii=False)
            print("SMOKE-OK wall=%.1fs peakvram=%dMB out=%s bytes=%d" % (wall, peak, dst, rec["bytes"]))
            return 0
    print("TIMEOUT")
    return 4


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main())
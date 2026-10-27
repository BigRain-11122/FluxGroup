# -*- coding: utf-8 -*-
"""mv_kf_smoke.py - one-shot Krea2 keyframe smoke test against a local ComfyUI.

Why: the legacy mv_full_kf.py still names krea2_turbo_fp8_scaled + qwen3vl_4b_fp8, but the
box now carries krea2_turbo_int8_convrot and only qwen3vl_32b / qwen_2.5_vl_7b. Never assume
a model name - verify by generating one frame and looking at it.

Usage:
  py mv_kf_smoke.py --prompt "..." --out smoke.png [--clip qwen_2.5_vl_7b_fp8_scaled.safetensors]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import uuid


def build(prompt, seed, clip, unet, w, h):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip, "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
            "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0], "negative": ["6", 0],
            "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "mv_kf"}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", default="smoke.png")
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--clip", default="qwen_2.5_vl_7b_fp8_scaled.safetensors")
    ap.add_argument("--unet", default="krea2_turbo_int8_convrot.safetensors")
    ap.add_argument("--width", type=int, default=1344)
    ap.add_argument("--height", type=int, default=768)
    a = ap.parse_args()

    def post(path, payload):
        req = urllib.request.Request(a.server + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=120).read())

    def get(path):
        return json.loads(urllib.request.urlopen(a.server + path, timeout=30).read())

    g = build(a.prompt, a.seed, a.clip, a.unet, a.width, a.height)
    pid = post("/prompt", {"prompt": g, "client_id": str(uuid.uuid4())})["prompt_id"]
    print("queued prompt_id=%s" % pid, flush=True)

    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(2)
        h = get("/history/" + pid)
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                print("ERROR: " + json.dumps(st)[:1200])
                return 2
            for out in h[pid]["outputs"].values():
                for img in out.get("images", []):
                    url = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                        a.server, img["filename"], img.get("subfolder", ""), img.get("type", "output"))
                    data = urllib.request.urlopen(url, timeout=120).read()
                    with open(a.out, "wb") as f:
                        f.write(data)
                    print("OK %s (%d bytes, %.1fs)" % (a.out, len(data), time.time() - t0))
                    return 0
    print("TIMEOUT")
    return 3


if __name__ == "__main__":
    sys.exit(main())
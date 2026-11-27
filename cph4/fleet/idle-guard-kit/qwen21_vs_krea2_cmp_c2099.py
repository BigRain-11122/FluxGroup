# -*- coding: utf-8 -*-
"""POOL-0021 leg-3: Qwen-Image-2.1-Turbo vs Krea2-turbo comparison board on the
same prompts (KF-representative subjects), plus the three-account table.

  account 1  speed      : wall time per frame, both stacks, same prompts
  account 2  vram       : peak VRAM per frame (nvidia-smi samples)
  account 3  quality    : side-by-side board at 1344x768-class framing for
                          director/agent blind read (this script does NOT
                          self-grade; the board is the evidence face)

Qwen stack runs on the v0.42 sidecar (8199), Krea2 stack on the production
server (8188). They are serialised (never parallel) so the 16GB card is not
oversubscribed; the sidecar is freed after its turn.

Subjects (KF-representative, scene/prop class only -- ID faces stay on Krea2 per
POOL-0021 scope): night sky constellation / cassette close-up / dusk silhouette.
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

Q = "http://127.0.0.1:8199"   # qwen21 sidecar (v0.42)
K = "http://127.0.0.1:8188"   # krea2 production (v0.36)
OUT = r"K:\Fluxgroup\FluxGroup\media\comfy-sidecar\compare"
os.makedirs(OUT, exist_ok=True)

W, H, SEED = 1344, 768, 991210

SUBJECTS = [
    ("sky", "deep indigo night sky, four bright stars with tight glowing cores joined by thin solid light lines "
            "into one connected chain across the middle of the frame, faint Milky Way band, film grain, "
            "35mm film grain, telecine texture, 2001 Taiwan music video look"),
    ("cassette", "close-up of a clear vintage audio cassette on a wooden desk, slanted warm window light, "
                 "dust motes in the beam, shallow depth of field, 35mm film grain, telecine texture, "
                 "2001 Taiwan music video look"),
    ("dusk", "backlit silhouettes of a young couple standing back to back in a grass field against a burnt-orange "
             "dusk sky, strong halo rim light, 35mm film grain, telecine texture, 2001 Taiwan music video look"),
]


def vram():
    try:
        q = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                    stderr=subprocess.DEVNULL).decode().strip().splitlines()
        return int(q[0])
    except Exception:
        return -1


def post_json(server, path, body, timeout=120):
    req = urllib.request.Request(server + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())


def get_json(server, path, timeout=60):
    return json.loads(urllib.request.urlopen(server + path, timeout=timeout).read().decode())


def queue_empty(server):
    try:
        q = get_json(server, "/queue", timeout=15)
        return not q.get("queue_running") and not q.get("queue_pending")
    except Exception:
        return False


def run(server, graph, tag):
    t0 = time.time()
    base = vram()
    pid = post_json(server, "/prompt", {"prompt": graph, "client_id": "bmc-qwen21-cmp"})["prompt_id"]
    peak = base
    while time.time() - t0 < 1800:
        time.sleep(2)
        peak = max(peak, vram())
        try:
            h = get_json(server, "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h.get(pid)
        if not e:
            continue
        if e.get("status", {}).get("status_str") == "error":
            return {"tag": tag, "ok": False, "err": json.dumps(e.get("status", {}))[:600]}
        imgs = []
        for o in e.get("outputs", {}).values():
            imgs += o.get("images", [])
        if imgs:
            im = imgs[0]
            u = "%s/view?filename=%s&subfolder=%s&type=%s" % (server, urllib.parse.quote(im["filename"]),
                                                              urllib.parse.quote(im.get("subfolder", "")),
                                                              im.get("type", "output"))
            dst = os.path.join(OUT, "%s.png" % tag)
            io.open(dst, "wb").write(urllib.request.urlopen(u, timeout=180).read())
            return {"tag": tag, "ok": True, "wall_s": round(time.time() - t0, 1), "peak_vram_mb": peak,
                    "out": dst, "bytes": os.path.getsize(dst)}
    return {"tag": tag, "ok": False, "err": "timeout"}


def qwen_graph(prompt):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2.1_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_8b_w4a8.safetensors", "type": "qwen_image"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "qwen_image_2.1_turbo_lora_avg_rank_178_bf16.safetensors", "strength_model": 1.0}},
        "5": {"class_type": "QwenImage21Cache", "inputs": {"model": ["4", 0], "device": "auto", "dtype": "default"}},
        "6": {"class_type": "TextEncodeQwenImage21", "inputs": {"clip": ["2", 0], "prompt": prompt, "negative_prompt": "", "resolution": 1024}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["5", 0], "positive": ["6", 0], "negative": ["6", 1],
              "latent_image": ["6", 2], "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
              "scheduler": "simple", "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "qwencmp"}},
    }


def krea_graph(prompt):
    # same as 星晴 A-批 正档 recipe (xq_abatch_r1057): krea2 turbo 8 steps cfg1 + jman
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "20": {"class_type": "LoraLoaderModelOnly", "inputs": {"lora_name": "jman_v1_640_rank32_final.safetensors",
               "strength_model": 0.6, "model": ["10", 0]}},
        "3": {"class_type": "KSampler", "inputs": {"seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
              "scheduler": "simple", "denoise": 1.0, "model": ["20", 0], "positive": ["6", 0],
              "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "kreacmp"}},
    }


def main():
    rows = []
    for name, prompt in SUBJECTS:
        # qwen turn (sidecar), then free, then krea turn (production) -- serialised
        if not queue_empty(Q):
            print("qwen queue busy -- abort FIFO law")
            return 2
        rq = run(Q, qwen_graph(prompt), "qwen_%s" % name)
        print("QWEN", name, rq, flush=True)
        try:
            post_json(Q, "/free", {"unload_models": True, "free_memory": True}, timeout=90)
        except Exception as e:
            print("free failed", e)
        if not queue_empty(K):
            print("krea queue busy -- abort FIFO law")
            return 2
        rk = run(K, krea_graph(prompt), "krea_%s" % name)
        print("KREA", name, rk, flush=True)
        rows.append({"subject": name, "prompt": prompt, "qwen": rq, "krea": rk})
    # board: 3 rows x 2 cols
    from PIL import Image, ImageDraw
    tw, th = 640, 366
    board = Image.new("RGB", (tw * 2 + 12, (th + 24) * len(rows) + 8), (18, 18, 20))
    dr = ImageDraw.Draw(board)
    for i, row in enumerate(rows):
        for j, key in enumerate(("qwen", "krea")):
            r = row[key]
            if not r.get("ok"):
                continue
            im = Image.open(r["out"]).convert("RGB").resize((tw - 8, th - 8), Image.LANCZOS)
            x = 6 + j * tw
            y = 6 + i * (th + 24)
            board.paste(im, (x + 2, y + 20))
            dr.text((x + 4, y + 5), "%s  %s  %.1fs  peak %dMB" % (row["subject"], key, r["wall_s"], r["peak_vram_mb"]),
                    fill=(235, 220, 175))
    bp = os.path.join(OUT, "QWEN21-vs-KREA2-board-c2099.jpg")
    board.save(bp, quality=86)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "seed": SEED, "krea_res": [W, H],
           "qwen_res": "1024 (QwenImage21 native latent)", "rows": rows, "board": bp,
           "note": "serialised runs; sidecar freed between turns; quality face = board blind read (not self-graded)"}
    with open(os.path.join(OUT, "compare_receipt.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, ensure_ascii=False)
    print("BOARD", bp, os.path.getsize(bp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
# -*- coding: utf-8 -*-
# jayredo_kf_r1025.py -- MV V4 男主 Jay 化重做 KF 批 runner (bm-c r1025, POOL-0014)
# Source of truth: JAY-REDO-PACK-v1.py SHOTS (14 real KF reshoots; 3 校验件 excluded here)
# Law: Krea2 turbo 8 steps 1344x768 + LoraLoaderModelOnly(jman_v1_rank32, 0.80) + JAY_BONE v2 anchor
#      (pack header: KF 全烧 -> LOOKBOARD 上链 -> poke bm-a 导演席 -> 过线件才进 i2v)
# Detached-batch trio: stdout guard + safe-area log (media/) + progress json w/ pid.
import json, os, sys, time, urllib.request, uuid, importlib.util

if not sys.stdout:            # pythonw guard (10-14 law)
    sys.stdout = open(os.devnull, "w")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\logs"
OUTDIR = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\jayredo\kf_r1025"
for d in (LOGDIR, OUTDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "jayredo_kf_r1025.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "jayredo_kf_r1025.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

P("=== jayredo_kf_r1025 start %s pid=%d ===" % (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid()))

# ---- load pack (hyphenated filename -> importlib) ----
spec = importlib.util.spec_from_file_location("jay_redo_pack", os.path.join(BASE, "JAY-REDO-PACK-v1.py"))
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)
REAL = [s for s in pack.SHOTS if not s[2].startswith("校验")]
VERIFY = [s for s in pack.SHOTS if s[2].startswith("校验")]
P("pack shots=%d real=%d verify=%d" % (len(pack.SHOTS), len(REAL), len(VERIFY)))
assert len(REAL) == 14 and len(VERIFY) == 3, "pack shape drift (expect 14+3)"

SERVER = "http://127.0.0.1:8188"
PROG_PATH = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001\jayredo\jayredo_kf_r1025_progress.json"
PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "kf",
        "done": {}, "meta": {"pack": "JAY-REDO-PACK-v1.py", "jman_strength": 0.80,
                             "res": "1344x768", "seed_base": 9500, "verify_items": [v[0] for v in VERIFY]}}
# resume law (mv_full_kf 断点续跑): merge existing progress file if present
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(open(PROG_PATH, encoding="utf-8"))
        if isinstance(_old.get("done"), dict):
            PROG["done"].update(_old["done"])
            P("resumed done entries: %d" % len(PROG["done"]))
    except Exception as e:
        P("resume read failed (fresh start): %r" % e)
def save_prog():
    PROG["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(PROG, open(PROG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
save_prog()

def graph(prompt_text, seed, use_jman=True, w=1344, h=768, prefix="jayredo"):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "20": {"class_type": "LoraLoaderModelOnly",
               "inputs": {"lora_name": "jman_v1_640_rank32_final.safetensors",
                          "strength_model": 0.80, "model": ["10", 0]}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": ["20", 0], "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }
    return g

def http(url, data=None, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def run_one(job, seed):
    resp = http(SERVER + "/prompt", {"prompt": graph(job["kf"], seed), "client_id": "bmc-r1025"})
    pid = resp.get("prompt_id") if isinstance(resp, dict) else None
    if not pid:
        P("POST /prompt no prompt_id in resp: %s" % str(resp)[:200])
        return None
    t0 = time.time()
    while time.time() - t0 < 1500:
        time.sleep(4)
        h = http(SERVER + "/history/" + pid)
        if pid in h:
            outs = h[pid].get("outputs", {})
            for node, o in outs.items():
                for im in o.get("images", []):
                    if im["type"] == "output":
                        src = SERVER + "/view?filename=%s&subfolder=%s&type=output" % (im["filename"], im.get("subfolder", ""))
                        dst = os.path.join(OUTDIR, im["filename"])
                        with urllib.request.urlopen(src, timeout=120) as r, open(dst, "wb") as f:
                            f.write(r.read())
                        return dst
            return None
    P("timeout waiting prompt_id=%s" % pid)
    return None

seed = 9500
for shot in REAL:
    name, win, kf_prompt, i2v_prompt = shot
    tag = name
    if tag in PROG["done"]:
        P("skip done", tag); continue
    seed += 1
    try:
        dst = run_one({"kf": kf_prompt}, seed)
    except Exception as e:
        P("EXC on %s: %r" % (tag, e))
        import traceback; traceback.print_exc(file=ERR)
        dst = None
    ok = dst is not None
    PROG["done"][tag] = {"ok": ok, "file": os.path.basename(dst) if ok else "", "seed": seed,
                         "win": win, "ts": time.strftime("%H:%M:%S")}
    save_prog()
    P("%s -> %s (seed %d)" % (tag, PROG["done"][tag]["file"], seed))

# ---- LOOKBOARD (q88 contact sheet, slot labels) ----
PROG["stage"] = "board"; save_prog()
P("--- building LOOKBOARD ---")
from PIL import Image, ImageDraw

entries = [(t, os.path.join(OUTDIR, PROG["done"][t]["file"])) for t in [s[0] for s in REAL]
           if PROG["done"].get(t, {}).get("ok")]
cols = 5
tw, th, pad = 250, 143, 10
rows_n = (len(entries) + cols - 1) // cols
W = cols * (tw + pad) + pad
H = rows_n * (th + 18 + pad) + pad + 28
im = Image.new("RGB", (W, H), (16, 15, 13))
d = ImageDraw.Draw(im)
d.text((pad, 6), "JAY-REDO KF batch 14 -- 1344x768 jman@0.80 JAY_BONE v2 -- bm-c r1025 -- %s" % time.strftime("%Y-%m-%d %H:%M"), fill=(240, 200, 120))
for i, (tag, f) in enumerate(entries):
    r_, c_ = divmod(i, cols)
    x = pad + c_ * (tw + pad)
    y = pad + 28 + r_ * (th + 18 + pad)
    try:
        pic = Image.open(f).convert("RGB").resize((tw, th))
        im.paste(pic, (x, y))
    except Exception:
        d.rectangle([x, y, x + tw, y + th], outline=(90, 40, 40))
    d.text((x, y + th + 2), tag.replace(".mp4", ""), fill=(200, 200, 190))
board_out = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012\bmc\JAY-REDO-KF-BOARD-r1025.jpg"
im.save(board_out, quality=88)
P("LOOKBOARD -> %s (%d cells)" % (board_out, len(entries)))

PROG["stage"] = "done"
ok_n = sum(1 for v in PROG["done"].values() if v.get("ok"))
PROG["summary"] = "done %d/%d KF ok; board=%s" % (ok_n, len(REAL), board_out)
save_prog()
P("=== runner complete: %s ===" % PROG["summary"])

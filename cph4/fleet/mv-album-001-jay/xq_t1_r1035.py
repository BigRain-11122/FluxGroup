# -*- coding: utf-8 -*-
# xq_t1_r1035.py -- 星晴 T1 海选 wave-1 runner (bm-c r1035, POOL-0015)
# Gate: _r1033bmc_t1_gate.md SIGNED (bm-a director 2026-10-15 18:0x) -- 33 A-frames unlocked.
# Law: T1 海选制 = Krea2 turbo 672x384 8-step cfg1.0, jman_v1_rank32 @ 0.6 (PACK-A),
#      ladder early-stop 8-first (全负即停=sea-review verdict; wave-1 = 8 seeds/frame only),
#      two-tier sea-review AFTER this wave (tier-1 multimodal board 24/板 -> tier-2 expert pick 2/frame).
# Frames: runtime-extracted from group origin 星晴-SHOTLIST-v3.md §一表 (r587 zero-transcription).
# Prompt: [ID const if face frame] + [light phrase from 光位列] + [per-frame post-FIX anchor verbatim]
#         + [official closing block] -- 禁增删主体句语义 (PACK-A 八块序).
# Lint: NEG/VAGUE/CONCEPT three lists (PROMPT-SPEC v1.3 §二) -- any hit = abort.
# Detached trio: stdout guard + media safe-area logs + progress json (pid+resume, skip-if-exists).
import io, json, os, re, subprocess, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
SHOTLIST_REL = "cph4/fleet/mv-album-001-jay/星晴-SHOTLIST-v3.md"
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
T1DIR = os.path.join(MEDIA, "xingqing", "t1")
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(T1DIR, "xq_t1_r1035_progress.json")
BMC = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
BASE = os.path.join(BMC, "..")  # kf-demo dir (boards live in album lane instead)
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
ATOMIC = os.path.join(GROUP_ROOT, "quant", "bigmoney", ".codely-cli", "scratch", "git-atomic-push-bmc.py")
SERVER = "http://127.0.0.1:8188"
BMA_POKE = "http://100.110.185.62:8790/poke"
for d in (T1DIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "xq_t1_r1035.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "xq_t1_r1035.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

# ---------------- extract frames from origin blob (zero transcription) ----------------
md = subprocess.run(["git", "-C", GROUP_ROOT, "show", "origin/main:" + SHOTLIST_REL],
                    capture_output=True).stdout.decode("utf-8", "replace")
rows = [l for l in md.splitlines() if l.startswith("|") and not l.startswith("|---") and not l.startswith("| 镜位")]

LIGHT = {"①": "warm 5200K golden daylight", "②": "2800K dusk backlight with warm halo",
         "③": "single 2200K warm lamp light", "④": "indigo night with cool starlight",
         "⑤": "slanted warm window light with dust motes"}
ID_CONST = ("a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, "
            "softly rounded cheeks and a thick black fringe lying flat over his eyebrows, "
            "natural matte skin with visible pores")  # PROMPT-SPEC §三 ID slot (逐字) + no-makeup 正写
ID_FRAMES = {"S5-30"}          # 唯一侧脸近景 (演唱锚②); 背影/剪影/手部/物件镜免挂 (PACK-A)
CLOSING = "35mm film grain, telecine texture, 2001 Taiwan music video look"
MULTI = re.compile(r"(S2-1[123]|S5-2[678]):\s*")

FRAMES = []  # (frame_id, batch, anchor)
for l in rows:
    c = [x.strip() for x in l.split("|")]
    if len(c) < 10:
        continue
    fid, batch, anchor = c[1], c[8], c[9]
    if batch != "A":
        continue
    if fid in ("S2-11/12/13", "S5-26/27/28"):     # 三帧分态锚 cell
        parts = [p for p in MULTI.split(anchor) if p and not MULTI.fullmatch(p)]
        # parts = [id1, text1, id2, text2, id3, text3]
        for i in range(0, len(parts) - 1, 2):
            FRAMES.append((parts[i], "A", parts[i + 1].strip(), c[6]))
    else:
        FRAMES.append((fid, "A", anchor, c[6]))

# light column = c[6] (光位) captured above as 4th tuple element
def build_prompt(f):
    fid, anchor, light_cell = f[0], f[2], f[3]
    m = re.search(r"[①②③④⑤]", light_cell or "")
    lp = LIGHT[m.group(0)] if m else ""
    seg = []
    if fid in ID_FRAMES:
        seg.append(ID_CONST)
    if lp:
        seg.append("lit by " + lp + ",")
    seg.append(anchor if anchor.endswith(".") else anchor + ".")
    seg.append(CLOSING + ".")
    p = " ".join(seg)
    return p

# ---------------- lint (three lists, PROMPT-SPEC v1.3 §二) ----------------
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|"
                   r"cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)

def lint(p):
    return sorted(set((NEG.findall(p) or []) + (VAGUE.findall(p) or []) + (CONCEPT.findall(p) or [])))

PROMPTS = {}
for f in FRAMES:
    p = build_prompt(f)
    hits = lint(p)
    if hits:
        P("LINT FAIL %s: %r -- ABORT" % (f[0], hits))
        print("LINT-FAIL", f[0], hits)
        sys.exit(3)
    PROMPTS[f[0]] = p

n_words = {k: len(v.split()) for k, v in PROMPTS.items()}
over = {k: v for k, v in n_words.items() if v > 200}
if over:
    P("LENGTH GATE FAIL (>200 words): %s" % over)
    print("LEN-FAIL", over)
    sys.exit(3)

P("=== xq_t1_r1035 start %s pid=%d === frames=%d prompts=%d words[min,max]=%d,%d" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(FRAMES), len(PROMPTS),
   min(n_words.values()), max(n_words.values())))

if len(FRAMES) != 33:
    P("FRAME COUNT DRIFT: %d (expect 33) -- ABORT" % len(FRAMES))
    print("FRAME-DRIFT", len(FRAMES))
    sys.exit(3)

# ---------------- progress + resume ----------------
PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "burn",
        "done": {}, "meta": {"wave": "T1-1", "frames": 33, "seeds_per_frame": 8,
                             "res": "672x384", "steps": 8, "jman_strength": 0.6,
                             "seed_base": 20000, "gate": "_r1033bmc_t1_gate.md SIGNED 2026-10-15 18:0x"}}
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

# ---------------- ComfyUI ----------------
def graph(prompt_text, seed, w=672, h=384):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "20": {"class_type": "LoraLoaderModelOnly",
               "inputs": {"lora_name": "jman_v1_640_rank32_final.safetensors",
                          "strength_model": 0.6, "model": ["10", 0]}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": ["20", 0], "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqT1"}},
    }

def http(url, data=None, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def dl(v, out):
    u = "%s/view?filename=%s&subfolder=%s&type=%s" % (SERVER, v["filename"], v.get("subfolder", ""), v.get("type", "output"))
    io.open(out, "wb").write(urllib.request.urlopen(u, timeout=300).read())

# FIFO 共服纪律: queue must be empty before wave start
q = http(SERVER + "/queue")
qr = q.get("queue_running", []) if isinstance(q, dict) else []
qp = q.get("queue_pending", []) if isinstance(q, dict) else []
if qr or qp:
    P("queue non-empty (running=%d pending=%d) -- ABORT, FIFO law" % (len(qr), len(qp)))
    print("QUEUE-BUSY", len(qr), len(qp))
    sys.exit(2)
P("queue empty 0/0 -- wave start")

def burn(fid, prompt, seed, out):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed), "client_id": "bmc-xqT1"})
    pid = resp.get("prompt_id") if isinstance(resp, dict) else None
    if not pid:
        return False, "submit-fail"
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(4)
        try:
            h = http(SERVER + "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h.get(pid)
        if e is None:
            continue
        if e.get("status", {}).get("status_str") == "error":
            return False, "exec-error"
        for node, o in e.get("outputs", {}).items():
            imgs = (o.get("images") or []) + (o.get("gifs") or []) + (o.get("videos") or [])
            for v in imgs:
                dl(v, out)
                return True, ""
        return False, "no-output"
    return False, "timeout"

# ---------------- wave-1 ladder burn: 8 seeds per frame ----------------
SEEDS = 8
for fi, f in enumerate(FRAMES):
    fid = f[0]
    if all(PROG["done"].get("%s_s%d" % (fid, k), {}).get("ok") for k in range(SEEDS)):
        P("skip done frame %s" % fid)
        continue
    for k in range(SEEDS):
        key = "%s_s%d" % (fid, k)
        if PROG["done"].get(key, {}).get("ok"):
            continue
        seed = 20000 + fi * SEEDS + k
        out = os.path.join(T1DIR, "%s_s%d.png" % (fid, seed))
        if os.path.isfile(out) and os.path.getsize(out) > 50000:
            PROG["done"][key] = {"ok": True, "file": os.path.basename(out), "seed": seed}
            save_prog()
            continue
        ok, err = burn(fid, PROMPTS[fid], seed, out)
        PROG["done"][key] = {"ok": ok, "file": os.path.basename(out) if ok else "",
                             "seed": seed, "err": err}
        save_prog()
        P("[%s s%d] %s (%d/%d frames done=%d)" %
          (fid, seed, "OK" if ok else "FAIL " + err, fi + 1, len(FRAMES),
           sum(1 for v in PROG["done"].values() if v.get("ok"))))
ok_all = sum(1 for v in PROG["done"].values() if v.get("ok"))
P("wave-1 burns: %d/%d" % (ok_all, 33 * SEEDS))

# ---------------- contact boards (tier-1 sea-review face): 24 imgs/board ----------------
try:
    from PIL import Image, ImageDraw, ImageFont
    files = sorted(x for x in os.listdir(T1DIR) if x.endswith(".png"))
    PER = 24
    for bi in range(0, len(files), PER):
        chunk = files[bi:bi + PER]
        tw, th = 336, 192
        cols = 4
        rowsn = (len(chunk) + cols - 1) // cols
        board = Image.new("RGB", (cols * tw + 20, rowsn * (th + 22) + 14), (24, 22, 20))
        dr = ImageDraw.Draw(board)
        for i, fn in enumerate(chunk):
            im = Image.open(os.path.join(T1DIR, fn)).convert("RGB").resize((tw - 8, th - 8))
            x = 10 + (i % cols) * tw
            y = 8 + (i // cols) * (th + 22)
            board.paste(im, (x + 4, y + 4))
            dr.text((x + 6, y + th + 2), fn.replace(".png", ""), fill=(200, 180, 140))
        bpath = os.path.join(ALBUM, "xq-T1-BOARD-%02d-r1035.jpg" % (bi // PER + 1))
        board.save(bpath, quality=88)
        P("board -> %s" % bpath)
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

# ---------------- receipt + atomic push + poke ----------------
receipt = {"wave": "T1-1", "gate": "PROMPT-GATE 星晴-KF-PACK-A v1 SIGNED (bm-a director 2026-10-15 18:0x)",
           "frames": [{"frame": f[0], "seeds": [20000 + i * SEEDS + k for k in range(SEEDS)],
                       "prompt": PROMPTS[f[0]], "light_cell": f[3],
                       "burn_ok": [bool(PROG["done"].get("%s_s%d" % (f[0], k), {}).get("ok")) for k in range(SEEDS)]}
                      for i, f in enumerate(FRAMES)],
           "stats": {"ok": ok_all, "total": 33 * SEEDS, "res": "672x384x8step", "jman": 0.6,
                     "words": {"min": min(n_words.values()), "max": max(n_words.values())},
                     "lint": "NEG/VAGUE/CONCEPT zero-hit (33/33 frames)"}}
rpath = os.path.join(ALBUM, "xq-T1-RECEIPT-r1035.json")
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)

def atomic_push(files, message, tag):
    sp = {"message": message, "retry": 5, "gate_depth": 10, "files": files}
    sp_path = os.path.join(LOGDIR, "atomic_spec_%s.json" % tag)
    json.dump(sp, open(sp_path, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        env_ap = dict(os.environ); env_ap["PYTHONIOENCODING"] = "utf-8"  # GBK console crash fix (r1035 jayredo pushC/E precedent)
        r = subprocess.run([sys.executable, ATOMIC, sp_path], capture_output=True, cwd=GROUP_ROOT, timeout=1200, env=env_ap)
    except subprocess.TimeoutExpired:
        P("[atomic %s] TIMEOUT-1200 (payload stays local, next window retries)" % tag)
        return False
    out = (r.stdout or b"").decode("utf-8", "replace")
    P("[atomic %s] rc=%d %s" % (tag, r.returncode, out[-600:]))
    return r.returncode == 0

rel = lambda p: "cph4/fleet/mv-album-001-jay/" + p
files = [{"mode": "full", "path": rel("xq-T1-RECEIPT-r1035.json"), "local": rpath, "expect_origin_blob": "NEW"}]
n_boards = 0
for bi in range(0, min(len([x for x in os.listdir(T1DIR) if x.endswith('.png')]), 33 * SEEDS), PER):
    n_boards += 1
    bpath = os.path.join(ALBUM, "xq-T1-BOARD-%02d-r1035.jpg" % (bi // PER + 1))
    if os.path.isfile(bpath):
        files.append({"mode": "full", "path": rel(os.path.basename(bpath)), "local": bpath, "expect_origin_blob": "NEW"})
ord_row = ("| %s | **【@bm-c 回执】星晴 T1 海选 wave-1 烧毕上链（POOL-0015 执行·_r1033bmc_t1_gate.md 签发件）** | "
           "33 帧×8 种子=264 张 672×384 8步 Krea2 turbo+jman0.6（帧正身=origin SHOTLIST-v3 §一表运行时提取零转录·"
           "lint 三名单 33/33 零命中·光位列→色温词组装·S5-30 ID 常量逐字）→%d 板拼板+xq-T1-RECEIPT-r1035.json 上链"
           "→**两级海审**：一级多模态拼板海筛（六维快分）→二级专家团细审每镜取 2→verdict 板；"
           "阶梯早停执法：任一帧 8 种全负=回炉 prompt 不补烧 | in-flight（bm-c r1035·候海审） |"
           % (time.strftime("%Y-%m-%d %H:%M"), n_boards))
files.append({"mode": "append", "path": "docs/orders.md", "line": ord_row})
ok_push = atomic_push(files, "bm-c r1035: xingqing T1 wave-1 sea-selection 33x8 burned (gate-signed, lint-clean, boards+receipt for two-tier sea review)", "xqT1")
PROG["push"] = "OK" if ok_push else "FAIL"
PROG["stage"] = "done"
save_prog()

def poke_bma(reason):
    try:
        body = json.dumps({"reason": reason, "tasks": [], "repos": []}).encode()
        req = urllib.request.Request(BMA_POKE, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15).read()
        P("[poke bm-a] OK: %s" % reason)
    except Exception as ex:
        P("[poke bm-a] FAIL %r (orders row 已上链·bm-a 循环自拉兜底)" % ex)

if ok_push:
    poke_bma("bmc r1035 xingqing T1 wave-1 264 images burned, boards+receipt pushed, two-tier sea review requested")
P("=== runner complete: %s ===" % PROG["push"])

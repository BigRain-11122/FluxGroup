# -*- coding: utf-8 -*-
# xq_abatch_r1057.py -- 星晴 A 批正档 KF runner (bm-c r1057)
# Authorization: xq-T1-DIRECTOR-SIGNOFF-r1026.md §六 -- 26 signed positions GO (52 primary grids),
#   plus §五 adjudication/recheck grids + collected backups (10) = 62 burns, all signed/收编 designated.
# Params per 星晴-KF-PACK-A-v1: 正档 1344x768, 8 steps, cfg 1.0, jman_v1_640_rank32_final @ 0.6.
# Frames: runtime-extracted from group origin 星晴-SHOTLIST-v3.md §一表 (zero transcription).
# Lint: NEG/VAGUE/CONCEPT three lists -- any hit = abort (fail-loud, zero burn).
# Detached trio: stdout guard + media-area logs + progress json (skip-if-exists resume).

import io, json, os, re, subprocess, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
SHOTLIST_REL = "cph4/fleet/mv-album-001-jay/星晴-SHOTLIST-v3.md"
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
ABDIR = os.path.join(MEDIA, "xingqing", "abatch")
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(ABDIR, "xq_abatch_r1057_progress.json")
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
SERVER = "http://127.0.0.1:8188"
for d in (ABDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "xq_abatch_r1057.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "xq_abatch_r1057.err.log"), "a", encoding="utf-8", buffering=1)
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

FRAMES = []  # (frame_id, anchor, light_cell)
for l in rows:
    c = [x.strip() for x in l.split("|")]
    if len(c) < 10:
        continue
    fid, batch, anchor = c[1], c[8], c[9]
    if batch != "A":
        continue
    if fid in ("S2-11/12/13", "S5-26/27/28"):     # 三帧分态锚 cell
        parts = [p for p in MULTI.split(anchor) if p and not MULTI.fullmatch(p)]
        for i in range(0, len(parts) - 1, 2):
            FRAMES.append((parts[i], parts[i + 1].strip(), c[6]))
    else:
        FRAMES.append((fid, anchor, c[6]))

def build_prompt(f):
    fid, anchor, light_cell = f[0], f[1], f[2]
    m = re.search(r"[①②③④⑤]", light_cell or "")
    lp = LIGHT[m.group(0)] if m else ""
    seg = []
    if fid in ID_FRAMES:
        seg.append(ID_CONST)
    if lp:
        seg.append("lit by " + lp + ",")
    seg.append(anchor if anchor.endswith(".") else anchor + ".")
    seg.append(CLOSING + ".")
    return " ".join(seg)

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

# ---------------- SIGNOFF r1026 §二 whitelist (26 positions x 2) + §五/收编 extras ----------------
WHITELIST = {
    "F0-01a": [20003, 20007], "F0-01b": [20012, 20009], "S0-02": [20016, 20020],
    "S0-03": [20031, 20027], "S0-04": [20039, 20033], "S0-05": [20044, 20043],
    "S0-06": [20048, 20054], "S1-07": [20058, 20056], "S1-09": [20064, 20070],
    "S2-10": [20072, 20074], "S2-11": [20086, 20080], "S2-14": [20105, 20108],
    "S2-15": [20112, 20116], "S2-16": [20120, 20125], "S3-18": [20128, 20135],
    "S3-19": [20138, 20140], "S3-20": [20146, 20150], "S4-22": [20158, 20157],
    "S4-23": [20164, 20160], "S5-25": [20176, 20177], "S5-26": [20191, 20185],
    "S5-27": [20192, 20193], "S5-28": [20202, 20205], "S5-30": [20222, 20223],
    "F5-33a": [20234, 20233], "F5-33b": [20242, 20246],
}
EXTRA = [  # §五 裁决/复核格 + 收编/备选 (全部签章指定)
    ("S3-19", 20143, "adjudicate-fan-fingers"), ("S3-19", 20136, "backup-kept"),
    ("S4-22", 20153, "adjudicate-erhu-color"), ("S4-22", 20159, "collected-backup"),
    ("S0-06", 20053, "headcount-recheck"), ("S1-09", 20069, "hand-recheck-pink"),
    ("F5-33b", 20243, "collected-backup"), ("S4-23", 20163, "collected-backup"),
    ("S5-25", 20182, "collected-backup"), ("S3-18", 20132, "director-added"),
]

missing = [k for k in WHITELIST if k not in PROMPTS]
missing += [e[0] for e in EXTRA if e[0] not in PROMPTS]
if missing:
    P("WHITELIST FRAME MISSING from SHOTLIST: %s -- ABORT" % sorted(set(missing)))
    print("WL-MISSING", sorted(set(missing)))
    sys.exit(3)

JOBS = []
for fid, seeds in WHITELIST.items():
    for s in seeds:
        JOBS.append((fid, s, "primary"))
for fid, s, tag in EXTRA:
    JOBS.append((fid, s, tag))

P("=== xq_abatch_r1057 start %s pid=%d === jobs=%d (52 primary + %d extra) prompts=%d words[min,max]=%d,%d" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(JOBS), len(EXTRA), len(PROMPTS),
   min(n_words.values()), max(n_words.values())))

# ---------------- progress + resume ----------------
PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "burn",
        "done": {}, "meta": {"wave": "A-batch-final", "jobs": len(JOBS),
                             "res": "1344x768", "steps": 8, "jman_strength": 0.6,
                             "auth": "xq-T1-DIRECTOR-SIGNOFF-r1026.md §六 GO (bm-a 2026-10-17 02:0x)"}}
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

# ---------------- ComfyUI (Krea2 turbo + jman 0.6, 正档 1344x768) ----------------
def graph(prompt_text, seed, w=1344, h=768):
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqAB"}},
    }

def http(url, data=None, timeout=240):
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
P("queue empty 0/0 -- A-batch start")

def burn(prompt, seed, out):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed), "client_id": "bmc-xqAB"})
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

# ---------------- burn loop (62 jobs, skip-if-exists resume) ----------------
t_wave = time.time()
for ji, (fid, seed, tag) in enumerate(JOBS):
    key = "%s_s%d" % (fid, seed)
    out = os.path.join(ABDIR, "%s_s%d.png" % (fid, seed))
    if PROG["done"].get(key, {}).get("ok"):
        continue
    if os.path.isfile(out) and os.path.getsize(out) > 50000:
        PROG["done"][key] = {"ok": True, "file": os.path.basename(out), "seed": seed, "tag": tag}
        save_prog()
        continue
    ok, err = burn(PROMPTS[fid], seed, out)
    PROG["done"][key] = {"ok": ok, "file": os.path.basename(out) if ok else "",
                         "seed": seed, "tag": tag, "err": err}
    save_prog()
    P("[%d/%d] %s s%d %s (%.0fs elapsed)" %
      (ji + 1, len(JOBS), fid, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))

ok_all = sum(1 for v in PROG["done"].values() if v.get("ok"))
P("A-batch burns: %d/%d" % (ok_all, len(JOBS)))

# ---------------- contact boards (QC face, 24 imgs/board) ----------------
try:
    from PIL import Image, ImageDraw
    files = sorted(x for x in os.listdir(ABDIR) if x.endswith(".png"))
    PER = 24
    for bi in range(0, len(files), PER):
        chunk = files[bi:bi + PER]
        tw, th, cols = 336, 192, 4
        rowsn = (len(chunk) + cols - 1) // cols
        board = Image.new("RGB", (cols * tw + 20, rowsn * (th + 22) + 14), (24, 22, 20))
        dr = ImageDraw.Draw(board)
        for i, fn in enumerate(chunk):
            im = Image.open(os.path.join(ABDIR, fn)).convert("RGB").resize((tw - 8, th - 8))
            x = 10 + (i % cols) * tw
            y = 8 + (i // cols) * (th + 22)
            board.paste(im, (x + 4, y + 4))
            dr.text((x + 6, y + th + 2), fn.replace(".png", ""), fill=(200, 180, 140))
        bpath = os.path.join(ALBUM, "xq-AB-BOARD-%02d-r1057.jpg" % (bi // PER + 1))
        board.save(bpath, quality=88)
        P("board -> %s" % bpath)
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

# ---------------- receipt (local; window closeout pushes) ----------------
receipt = {"wave": "A-batch-final", "runner": "bm-c r1057",
           "auth": "xq-T1-DIRECTOR-SIGNOFF-r1026.md §六 (26 positions GO, 52 primary grids)",
           "params": {"res": "1344x768", "steps": 8, "cfg": 1.0, "jman": 0.6,
                      "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled"},
           "whitelist": {k: v for k, v in WHITELIST.items()},
           "extras": [{"frame": e[0], "seed": e[1], "tag": e[2]} for e in EXTRA],
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"ok": ok_all, "total": len(JOBS),
                     "lint": "NEG/VAGUE/CONCEPT zero-hit",
                     "words": {"min": min(n_words.values()), "max": max(n_words.values())}},
           "out_dir": "media/MV/mv0001/xingqing/abatch",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, "xq-AB-RECEIPT-r1057.json")
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: %d/%d ===" % (ok_all, len(JOBS)))

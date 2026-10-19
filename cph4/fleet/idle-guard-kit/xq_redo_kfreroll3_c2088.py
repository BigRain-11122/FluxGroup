# -*- coding: utf-8 -*-
# xq_redo_kfreroll3_c2088.py -- X2670 KF-reroll leg: 3 units x 2 candidates x (draft 672x384 + full 1344x768)
# Authorization: xq-PACKA-REDO-ORDER-20261019.md (X2670, bm-a director seat 05:23) sec-2/sec-3.1/sec-3.4 +
#   xq-PACKA-REDO-R1-PROGRESS-20261019.md sec-5 next-slice prescription (C2086 spec stow / C2087 harvest note).
# Layer verdicts (C2083, native recheck): F5-33a = pseudo-write seed on reel edge / S4-24 = KF-native
#   gibberish label ("STUK STORS TOO ILNL" + pseudo print band + fake TD logo) / S3-19 = KF-native
#   vertical-smear degeneration, dusk sky unreadable -> all three = KF-sick layer -> KF reroll.
# Prompt law (zero transcription): F5-33a + S3-19 anchors runtime-extracted from origin SHOTLIST v3
#   (abatch parsing law, same LIGHT dict / closing block); S4-24 verbatim from xq-T1R1-RECEIPT-r1057.json
#   positions[].prompt + label-softening surgery (X2670 A-draft anchor slot, count==1 asserted).
# Anchor surgeries (X2670 sec-2 verbatim):
#   F5-33a + "the cassette's paper label blank and age-worn" (positive, zero-text law; aligns the
#     passed F5-33b frame whose own anchor reads "revealing the blank label side" -- frame consistency)
#   S4-24: "handwritten label with strokes too small and out of focus to read" ->
#     "its small paper label soft, plain and out of focus" (strokes clause = pseudo-text incubator)
#   S3-19: unchanged anchor (degeneration was generative, seed renewal rebuilds the dusk sky)
# Seeds: id-MD5 law mirroring h3_i2v_album.seed_for -- new id family XQ_<unit>-redo-r1-kf1/kf2;
#   renewal assert: derived seeds must NOT collide with the original KF seed pool.
# Trial-composition law (sec-3.1): per candidate burn 672x384 draft then 1344x768 full.
# Retry budget (sec-3.4): <=2 burns per unit == exactly 2 candidates per unit; both failing review
#   at harvest -> comparison board escalation to director seat (r1061 sec-2 law).
# PASS gate (harvest): KF-REROLL-END ok=6 in bank log tail + 6 full PNGs >=50KB in
#   media/MV/mv0001/xingqing/kfreroll-r1 + progress json + comparison board xq-KFREROLL3-BOARD-c2088.jpg.

import hashlib, io, json, os, re, subprocess, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
SHOTLIST_REL = "cph4/fleet/mv-album-001-jay/星晴-SHOTLIST-v3.md"
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
KFDIR = os.path.join(MEDIA, "xingqing", "kfreroll-r1")
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(KFDIR, "xq_kfreroll3_c2088_progress.json")
T1R1_RECEIPT = os.path.join(ALBUM, "xq-T1R1-RECEIPT-r1057.json")
SERVER = "http://127.0.0.1:8188"
for d in (KFDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "xq_kfreroll3_c2088.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "xq_kfreroll3_c2088.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a, flush=True)
    print(*a, file=LOG)

def seed_for(oid):
    # mirrors local-i2v/h3_i2v_album.py seed_for (id-MD5 law)
    return int.from_bytes(hashlib.md5(oid.encode("utf-8")).digest()[:4], "big") % 999983

# ---------------- prompt assembly (zero transcription + X2670 anchor surgery) ----------------
LIGHT = {"①": "warm 5200K golden daylight", "②": "2800K dusk backlight with warm halo",
         "③": "single 2200K warm lamp light", "④": "indigo night with cool starlight",
         "⑤": "slanted warm window light with dust motes"}
CLOSING = "35mm film grain, telecine texture, 2001 Taiwan music video look"

md = subprocess.run(["git", "-C", GROUP_ROOT, "show", "origin/main:" + SHOTLIST_REL],
                    capture_output=True).stdout.decode("utf-8", "replace")
ANCHORS = {}
LIGHTCELL = {}
for l in md.splitlines():
    if not l.startswith("|") or l.startswith("|---") or l.startswith("| 镜位"):
        continue
    c = [x.strip() for x in l.split("|")]
    if len(c) < 10 or c[8] != "A":
        continue
    if c[1] in ("F5-33a", "S3-19"):
        ANCHORS[c[1]] = c[9]
        LIGHTCELL[c[1]] = c[6]
missing = [k for k in ("F5-33a", "S3-19") if k not in ANCHORS]
if missing:
    P("SHOTLIST anchor missing for %s -- ABORT" % missing)
    print("ANCHOR-MISSING", missing, flush=True)
    sys.exit(3)

def build_from_shotlist(fid):
    m = re.search(r"[①②③④⑤]", LIGHTCELL[fid] or "")
    lp = LIGHT[m.group(0)] if m else ""
    seg = []
    if lp:
        seg.append("lit by " + lp + ",")
    anchor = ANCHORS[fid]
    seg.append(anchor if anchor.endswith(".") else anchor + ".")
    seg.append(CLOSING + ".")
    return " ".join(seg)

# F5-33a surgery: blank age-worn label clause before the trailing "film grain" clause
F5_CLAUSE = "the cassette's paper label blank and age-worn"
a = ANCHORS["F5-33a"]
if a.count(", film grain") != 1:
    P("F5-33a anchor tail unexpected (count!=1) -- ABORT")
    print("ANCHOR-TAIL-FAIL", flush=True)
    sys.exit(3)
ANCHORS["F5-33a"] = a.replace(", film grain", ", " + F5_CLAUSE + ", film grain", 1)
PROMPTS = {"F5-33a": build_from_shotlist("F5-33a"), "S3-19": build_from_shotlist("S3-19")}

# S4-24 surgery: receipt verbatim + label-softening (X2670 A-draft anchor slot)
S4_OLD = "handwritten label with strokes too small and out of focus to read"
S4_NEW = "its small paper label soft, plain and out of focus"
rec = json.load(io.open(T1R1_RECEIPT, encoding="utf-8"))
s4 = None
for pos in rec.get("positions", []):
    if pos.get("frame") == "S4-24":
        s4 = pos["prompt"]
        break
if not s4:
    P("S4-24 prompt missing from T1R1 receipt -- ABORT")
    print("S424-MISSING", flush=True)
    sys.exit(3)
if s4.count(S4_OLD) != 1:
    P("S4-24 label clause count!=1 -- ABORT")
    print("S424-CLAUSE-FAIL", flush=True)
    sys.exit(3)
PROMPTS["S4-24"] = s4.replace(S4_OLD, S4_NEW, 1)

# ---------------- lint (three lists, PROMPT-SPEC v1.3 sec-2) ----------------
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|"
                   r"cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)
for fid, p in PROMPTS.items():
    hits = sorted(set((NEG.findall(p) or []) + (VAGUE.findall(p) or []) + (CONCEPT.findall(p) or [])))
    if hits:
        P("LINT FAIL %s: %r -- ABORT" % (fid, hits))
        print("LINT-FAIL", fid, hits, flush=True)
        sys.exit(3)
P("lint zero-hit 3/3 (2 shotlist-extracted + 1 receipt-surgical)")

# ---------------- seeds: id-MD5 renewal law + collision assert ----------------
UNITS = ["F5-33a", "S4-24", "S3-19"]
CANDS = {}  # unit -> [(cand_id, seed), (cand_id, seed)]
for u in UNITS:
    CANDS[u] = []
    for k in (1, 2):
        oid = "XQ_%s-redo-r1-kf%d" % (u, k)
        CANDS[u].append((oid, seed_for(oid)))
ORIG_SEEDS = {20233, 20234, 20136, 20138, 20140, 20143, 21037, 21039}
derived = [s for v in CANDS.values() for _, s in v]
if len(set(derived)) != len(derived):
    P("derived seed collision between candidates -- ABORT")
    print("SEED-COLLISION", flush=True)
    sys.exit(3)
if ORIG_SEEDS & set(derived):
    P("derived seed collides with original KF pool (renewal law) -- ABORT")
    print("SEED-RENEWAL-FAIL", flush=True)
    sys.exit(3)
P("seeds renewed (id-MD5 family): %s" %
  "; ".join("%s=%s" % (u, ",".join(str(s) for _, s in CANDS[u])) for u in UNITS))

# DRY gate (pre-stow verification path): assemble + lint + seeds, print, exit before any burn
if os.environ.get("XQ_KFREROLL_DRY") == "1":
    for fid, p in PROMPTS.items():
        P("DRY prompt %s (%d words): %s" % (fid, len(p.split()), p))
    print("DRY-OK", flush=True)
    sys.exit(0)

# ---------------- progress + resume ----------------
PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "burn",
        "done": {},
        "meta": {"wave": "xq-redo-kf-reroll3", "runner": "bm-c C2088",
                 "auth": "xq-PACKA-REDO-ORDER-20261019.md sec-3.1 (X2670) + PROGRESS sec-5",
                 "res_full": "1344x768", "res_draft": "672x384", "steps": 8, "cfg": 1.0,
                 "jman_strength": 0.6, "sampler": "euler simple",
                 "model": "krea2_turbo_fp8_scaled",
                 "candidates": {u: [c[0] for c in CANDS[u]] for u in UNITS},
                 "retry_budget": "2 burns/unit = 2 candidates (X2670 sec-3.4)"}}
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(io.open(PROG_PATH, encoding="utf-8"))
        if isinstance(_old.get("done"), dict):
            PROG["done"].update(_old["done"])
            P("resumed done entries: %d" % len(PROG["done"]))
    except Exception as e:
        P("resume read failed (fresh start): %r" % e)

def save_prog():
    PROG["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(PROG, io.open(PROG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
save_prog()

# ---------------- ComfyUI graph (Krea2 turbo + jman 0.6, proven abatch/t1r1hd params) ----------------
def graph(prompt_text, seed, w, h):
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqKFREROLL3"}},
    }

def http(url, data=None, timeout=240):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def dl(v, out):
    u = "%s/view?filename=%s&subfolder=%s&type=%s" % (SERVER, v["filename"], v.get("subfolder", ""), v.get("type", "output"))
    io.open(out, "wb").write(urllib.request.urlopen(u, timeout=300).read())

# unload any resident stack first (i2v lanes leave MiniMax loaded; free VRAM before KF swap)
try:
    http(SERVER + "/free", {"unload_models": True}, timeout=90)
    P("models unloaded (/free)")
except Exception as e:
    P("/free skipped: %r" % e)

# FIFO shared-server discipline: queue must be empty before wave start
q = http(SERVER + "/queue")
qr = q.get("queue_running", []) if isinstance(q, dict) else []
qp = q.get("queue_pending", []) if isinstance(q, dict) else []
if qr or qp:
    P("queue non-empty (running=%d pending=%d) -- ABORT, FIFO law" % (len(qr), len(qp)))
    print("QUEUE-BUSY", len(qr), len(qp), flush=True)
    sys.exit(2)
P("queue empty 0/0 -- KF-reroll3 start")

def burn(prompt, seed, out, w, h):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed, w, h), "client_id": "bmc-xqKFREROLL3"})
    pid = resp.get("prompt_id") if isinstance(resp, dict) else None
    if not pid:
        return False, "submit-fail"
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(4)
        try:
            hst = http(SERVER + "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = hst.get(pid)
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

# ---------------- burn loop: per unit, per candidate: draft 672x384 then full 1344x768 ----------------
P("=== xq_kfreroll3 start %s pid=%d === units=%d candidates=2 drafts+fulls=%d jobs" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(UNITS), 2 * len(UNITS) * 2))
t_wave = time.time()
fails = []
ok_fulls = 0
for u in UNITS:
    for cand_id, seed in CANDS[u]:
        # draft 672x384 (trial-composition law, X2670 sec-3.1)
        dkey = "%s_%s_draft" % (u, cand_id)
        dout = os.path.join(KFDIR, "%s_s%d_mini672.png" % (u, seed))
        if not (PROG["done"].get(dkey, {}).get("ok") or
                (os.path.isfile(dout) and os.path.getsize(dout) > 50000)):
            ok, err = burn(PROMPTS[u], seed, dout, 672, 384)
            PROG["done"][dkey] = {"ok": ok, "file": os.path.basename(dout) if ok else "", "err": err}
            save_prog()
            P("[%s] draft s%d %s (%.0fs)" % (u, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
            if not ok:
                fails.append(dkey)
        # full 1344x768 (official KF face for review + downstream i2v first_frame)
        fkey = "%s_%s_full" % (u, cand_id)
        fout = os.path.join(KFDIR, "%s_s%d.png" % (u, seed))
        if not (PROG["done"].get(fkey, {}).get("ok") or
                (os.path.isfile(fout) and os.path.getsize(fout) > 50000)):
            ok, err = burn(PROMPTS[u], seed, fout, 1344, 768)
            PROG["done"][fkey] = {"ok": ok, "file": os.path.basename(fout) if ok else "", "err": err}
            save_prog()
            P("[%s] full s%d %s (%.0fs)" % (u, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
            if not ok:
                fails.append(fkey)
        if PROG["done"].get(fkey, {}).get("ok"):
            ok_fulls += 1

P("KF-reroll3 burns: fulls ok=%d/6 fails=%s" % (ok_fulls, ",".join(fails) or "none"))

# ---------------- comparison board (harvest review face: FAIL original vs new candidates) ----------------
board_path = ""
try:
    from PIL import Image, ImageDraw
    ORIG = {"F5-33a": os.path.join(MEDIA, "xingqing", "abatch", "F5-33a_s20234.png"),
            "S4-24": os.path.join(MEDIA, "xingqing", "t1r1hd", "S4-24_s21037.png"),
            "S3-19": os.path.join(MEDIA, "xingqing", "abatch", "S3-19_s20143.png")}
    REF = {"F5-33a": os.path.join(MEDIA, "xingqing", "abatch", "F5-33b_s20242.png")}  # passed sibling
    tw, th, cols = 448, 256, 4
    rows = []
    for u in UNITS:
        cells = [(ORIG[u], u + " ORIG-FAIL")]
        for _, seed in CANDS[u]:
            f = os.path.join(KFDIR, "%s_s%d.png" % (u, seed))
            cells.append((f, "%s cand s%d" % (u, seed)))
            d = os.path.join(KFDIR, "%s_s%d_mini672.png" % (u, seed))
            cells.append((d, "%s draft s%d" % (u, seed)))
        if u in REF:
            cells.append((REF[u], u + " REF-passed"))
        rows.append(cells)
    board = Image.new("RGB", (cols * tw + 20, len(rows) * (th + 22) + 14), (24, 22, 20))
    dr = ImageDraw.Draw(board)
    for ri, cells in enumerate(rows):
        for ci in range(cols):
            x = 10 + ci * tw
            y = 8 + ri * (th + 22)
            path, label = cells[ci] if ci < len(cells) else ("", "")
            if path and os.path.isfile(path):
                im = Image.open(path).convert("RGB").resize((tw - 8, th - 8))
                board.paste(im, (x + 4, y + 4))
            dr.text((x + 6, y + th + 2), label, fill=(200, 180, 140))
    board_path = os.path.join(ALBUM, "xq-KFREROLL3-BOARD-c2088.jpg")
    board.save(board_path, quality=88)
    P("board -> %s (%dB)" % (board_path, os.path.getsize(board_path)))
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

# ---------------- receipt ----------------
receipt = {"wave": "xq-redo-kf-reroll3", "runner": "bm-c C2088",
           "auth": "xq-PACKA-REDO-ORDER-20261019.md sec-3.1/sec-3.4 (X2670 bm-a director seat)",
           "layer_verdicts_src": "xq-PACKA-REDO-R1-PROGRESS-20261019.md sec-1 (C2083 native recheck)",
           "params": {"res_full": "1344x768", "res_draft": "672x384", "steps": 8, "cfg": 1.0,
                      "jman": 0.6, "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled"},
           "units": {u: {"prompt": PROMPTS[u],
                         "surgery": ("+blank age-worn label clause (align F5-33b)" if u == "F5-33a"
                                     else "label-softening replace (A-draft anchor slot)" if u == "S4-24"
                                     else "unchanged (seed renewal rebuilds dusk sky)"),
                         "candidates": [{"id": c, "seed": s} for c, s in CANDS[u]]}
                     for u in UNITS},
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"fulls_ok": ok_fulls, "fulls_total": 6, "fails": fails,
                     "lint": "NEG/VAGUE/CONCEPT zero-hit 3/3"},
           "out_dir": "media/MV/mv0001/xingqing/kfreroll-r1",
           "board": os.path.basename(board_path) if board_path else "",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, "xq-KFREROLL3-RECEIPT-c2088.json")
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: fulls %d/6 ===" % ok_fulls)
print("KF-REROLL-END ok=%d/6 fails=%s" % (ok_fulls, ",".join(fails) or "none"), flush=True)
print("KF-REROLL-END ok=%d/6 fails=%s" % (ok_fulls, ",".join(fails) or "none"), file=LOG)

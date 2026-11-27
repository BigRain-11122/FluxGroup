# -*- coding: utf-8 -*-
# xq_f533c_reroll2_c2111.py -- F5-33c reroll round 2 (mini 8 seeds, 672x384)
# Authorization: xq-AB-DIRECTOR-RATIFY-r1017.md sec-3 table row "F5-33c: HOLD (1/8)" + sec-7
#   "F5-33c 回炉二轮（mini 8 种子·bm-c 候 GPU）" fix recipe:
#     1) stroke lock upgrade = heavy defocus, pencil-tip outlines only, no readable English word,
#        no horizontal-line notepad form
#     2) carrier lock = one corner of the cassette shell in frame so the object reads as a cassette
#     3) keep window dust-mote atmosphere + pen pausing a beat (SHOTLIST F5-33c body)
# Acceptance (same line as r1017 sec-7): >= 2 clean frames out of 8.
# Prompt: anchor runtime-extracted from origin SHOTLIST v3 row F5-33c (zero transcription),
#   then three positive-phrasing surgeries (NO negative words -> lint clean).
# Seeds: id-MD5 renewal family XQ_F5-33c-reroll2-m<k>, collision-asserted against the original pool.
# PASS gate: F533C-REROLL2-END ok=8 in log tail + 8 PNGs >=50KB in xingqing/f533c-reroll2 +
#   progress json + comparison board xq-F533C-REROLL2-BOARD-c2111.jpg (orig fail frame + 8 cands).

import hashlib, io, json, os, re, subprocess, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
SHOTLIST_REL = "cph4/fleet/mv-album-001-jay/\u661f\u6674-SHOTLIST-v3.md"
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
OUTDIR = os.path.join(MEDIA, "xingqing", "f533c-reroll2")
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(OUTDIR, "xq_f533c_reroll2_c2111_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (OUTDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "xq_f533c_reroll2_c2111.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "xq_f533c_reroll2_c2111.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a, flush=True)
    print(*a, file=LOG)

def seed_for(oid):
    return int.from_bytes(hashlib.md5(oid.encode("utf-8")).digest()[:4], "big") % 999983

LIGHT = {"\u2460": "warm 5200K golden daylight",
         "\u2461": "2800K dusk backlight with warm halo",
         "\u2462": "single 2200K warm lamp light",
         "\u2463": "indigo night with cool starlight",
         "\u2464": "slanted warm window light with dust motes"}
CLOSING = "35mm film grain, telecine texture, 2001 Taiwan music video look"

md = subprocess.run(["git", "-C", GROUP_ROOT, "show", "origin/main:" + SHOTLIST_REL],
                    capture_output=True).stdout.decode("utf-8", "replace")
ANCHOR = None
LIGHTCELL = ""
for l in md.splitlines():
    if not l.startswith("|"):
        continue
    c = [x.strip() for x in l.split("|")]
    if len(c) < 10 or c[1] != "F5-33c":
        continue
    ANCHOR = c[9]
    LIGHTCELL = c[6]
if not ANCHOR:
    P("SHOTLIST anchor missing for F5-33c -- ABORT")
    print("ANCHOR-MISSING", flush=True)
    sys.exit(3)

# --- surgeries (r1017 sec-7, positive phrasing only) ---
OLD_TEXT = "characters unreadable at a glancing angle"
NEW_TEXT = "the pencil strokes heavily defocused into soft pencil-tip outlines only"
OLD_LABEL = "the blank cassette label"
NEW_LABEL = "the small square plain paper cassette label"
if ANCHOR.count(OLD_TEXT) != 1:
    P("F5-33c text clause count!=1 -- ABORT")
    print("TEXT-CLAUSE-FAIL", flush=True)
    sys.exit(3)
if ANCHOR.count(OLD_LABEL) != 1:
    P("F5-33c label clause count!=1 -- ABORT")
    print("LABEL-CLAUSE-FAIL", flush=True)
    sys.exit(3)
anchor = ANCHOR.replace(OLD_LABEL, NEW_LABEL, 1).replace(OLD_TEXT, NEW_TEXT, 1)
CARRIER = "the corner of a clear plastic cassette shell in frame"
PEN_BEAT = "pen pausing a beat between strokes"
if anchor.count(PEN_BEAT) != 1:
    P("F5-33c pen-beat clause count!=1 -- ABORT")
    print("BEAT-CLAUSE-FAIL", flush=True)
    sys.exit(3)
anchor = anchor.replace(PEN_BEAT, PEN_BEAT + ", " + CARRIER, 1)

m = re.search(r"[\u2460-\u2464]", LIGHTCELL or "")
lp = LIGHT[m.group(0)] if m else ""
seg = []
if lp and lp.split(" with ")[0] not in anchor:
    seg.append("lit by " + lp + ",")
seg.append(anchor if anchor.endswith(".") else anchor + ".")
seg.append(CLOSING + ".")
PROMPT = " ".join(seg)

# ---------------- lint (three lists, PROMPT-SPEC v1.3 sec-2) ----------------
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|"
                   r"cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)
hits = sorted(set((NEG.findall(PROMPT) or []) + (VAGUE.findall(PROMPT) or []) + (CONCEPT.findall(PROMPT) or [])))
if hits:
    P("LINT FAIL F5-33c: %r -- ABORT" % (hits,))
    print("LINT-FAIL", hits, flush=True)
    sys.exit(3)
P("lint zero-hit 1/1 (shotlist anchor + 3 surgeries)")

# ---------------- seeds: id-MD5 renewal law + collision assert ----------------
CANDS = []
for k in range(1, 9):
    oid = "XQ_F5-33c-reroll2-m%d" % k
    CANDS.append((oid, seed_for(oid)))
ORIG_SEEDS = {20233, 20234, 20136, 20138, 20140, 20143, 21037, 21039, 20222, 20223}
derived = [s for _, s in CANDS]
if len(set(derived)) != len(derived):
    P("derived seed collision -- ABORT")
    print("SEED-COLLISION", flush=True)
    sys.exit(3)
if ORIG_SEEDS & set(derived):
    P("derived seed collides with original KF pool (renewal law) -- ABORT")
    print("SEED-RENEWAL-FAIL", flush=True)
    sys.exit(3)
P("seeds renewed: %s" % ",".join(str(s) for _, s in CANDS))

FULL_SEED = int(sys.argv[2]) if (len(sys.argv) > 2 and sys.argv[1] == "full") else None
if FULL_SEED:
    CANDS = [("XQ_F5-33c-winner-full", FULL_SEED)]
    RES = (1344, 768)
    SUF = ""
    ENDTOK, RNAME = "F533C-FULL-END", "xq-F533C-FULL-RECEIPT-c2111.json"
    BNAME = "xq-F533C-FULL-BOARD-c2111.jpg"
else:
    RES = (672, 384)
    SUF = "_mini672"
    ENDTOK, RNAME = "F533C-REROLL2-END", "xq-F533C-REROLL2-RECEIPT-c2111.json"
    BNAME = "xq-F533C-REROLL2-BOARD-c2111.jpg"

if os.environ.get("XQ_F533C_DRY") == "1":
    P("DRY prompt (%d words): %s" % (len(PROMPT.split()), PROMPT))
    print("DRY-OK", flush=True)
    sys.exit(0)

# ---------------- progress + resume ----------------
PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "burn",
        "done": {},
        "meta": {"wave": "xq-f533c-reroll2", "runner": "bm-c C2111",
                 "auth": "xq-AB-DIRECTOR-RATIFY-r1017.md sec-3/sec-7",
                 "res_mini": "672x384", "steps": 8, "cfg": 1.0, "jman_strength": 0.6,
                 "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled",
                 "candidates": [c[0] for c in CANDS], "seeds": {c[0]: c[1] for c in CANDS}}}
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqF533C"}},
    }

def http(url, data=None, timeout=240):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def dl(v, out):
    u = "%s/view?filename=%s&subfolder=%s&type=%s" % (SERVER, v["filename"], v.get("subfolder", ""), v.get("type", "output"))
    io.open(out, "wb").write(urllib.request.urlopen(u, timeout=300).read())

try:
    http(SERVER + "/free", {"unload_models": True}, timeout=90)
    P("models unloaded (/free)")
except Exception as e:
    P("/free skipped: %r" % e)

q = http(SERVER + "/queue")
qr = q.get("queue_running", []) if isinstance(q, dict) else []
qp = q.get("queue_pending", []) if isinstance(q, dict) else []
if qr or qp:
    P("queue non-empty (running=%d pending=%d) -- ABORT, FIFO law" % (len(qr), len(qp)))
    print("QUEUE-BUSY", len(qr), len(qp), flush=True)
    sys.exit(2)
P("queue empty 0/0 -- F5-33c reroll2 start")

def burn(prompt, seed, out, w, h):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed, w, h), "client_id": "bmc-xqF533C"})
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

P("=== xq_f533c_reroll2 start %s pid=%d === candidates=%d res=%s" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(CANDS), str(RES)))
t_wave = time.time()
fails = []
ok_n = 0
for cand_id, seed in CANDS:
    out = os.path.join(OUTDIR, ("F5-33c_s%d%s.png" % (seed, SUF)))
    if PROG["done"].get(cand_id, {}).get("ok") or (os.path.isfile(out) and os.path.getsize(out) > 50000):
        ok_n += 1
        continue
    ok, err = burn(PROMPT, seed, out, RES[0], RES[1])
    PROG["done"][cand_id] = {"ok": ok, "file": os.path.basename(out) if ok else "", "err": err, "seed": seed}
    save_prog()
    P("[F5-33c] %s s%d %s (%.0fs)" % (cand_id, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
    if ok:
        ok_n += 1
    else:
        fails.append(cand_id)

P("F5-33c burns: ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"))

# ---------------- comparison board (harvest face: original FAIL unit + 8 candidates) ----------------
board_path = ""
try:
    from PIL import Image, ImageDraw
    ORIGF = os.path.join(MEDIA, "xingqing", "abatch", "F5-33c_s20234.png")
    REF = os.path.join(MEDIA, "xingqing", "abatch", "F5-33b_s20242.png")
    cells = []
    if os.path.isfile(ORIGF):
        cells.append((ORIGF, "F5-33c ORIG-FAIL"))
    if os.path.isfile(REF):
        cells.append((REF, "F5-33b REF-passed"))
    for cand_id, seed in CANDS:
        cells.append((os.path.join(OUTDIR, ("F5-33c_s%d%s.png" % (seed, SUF))), "%s s%d" % (cand_id, seed)))
    tw, th, cols = 448, 256, 4
    rows = (len(cells) + cols - 1) // cols
    board = Image.new("RGB", (cols * tw + 20, rows * (th + 22) + 14), (24, 22, 20))
    dr = ImageDraw.Draw(board)
    for i, (path, label) in enumerate(cells):
        r, c = divmod(i, cols)
        x, y = 10 + c * tw, 8 + r * (th + 22)
        if os.path.isfile(path):
            im = Image.open(path).convert("RGB").resize((tw - 8, th - 8))
            board.paste(im, (x + 4, y + 4))
        dr.text((x + 6, y + th + 2), label, fill=(200, 180, 140))
    board_path = os.path.join(ALBUM, BNAME)
    board.save(board_path, quality=88)
    P("board -> %s (%dB)" % (board_path, os.path.getsize(board_path)))
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

receipt = {"wave": "xq-f533c-reroll2", "runner": "bm-c C2111",
           "auth": "xq-AB-DIRECTOR-RATIFY-r1017.md sec-3 HOLD row + sec-7 fix recipe",
           "prompt": PROMPT,
           "surgeries": ["stroke lock: text clause -> heavy defocus pencil-tip outlines only",
                         "label form: small square plain paper patch (no notepad form)",
                         "carrier lock: corner of clear plastic cassette shell in frame",
                         "kept: slanted warm window light with dust motes + pen pause beat"],
           "params": {"res_mini": "672x384", "steps": 8, "cfg": 1.0, "jman": 0.6,
                      "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled"},
           "candidates": [{"id": c, "seed": s} for c, s in CANDS],
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"ok": ok_n, "total": 8, "fails": fails, "lint": "NEG/VAGUE/CONCEPT zero-hit"},
           "out_dir": "media/MV/mv0001/xingqing/f533c-reroll2",
           "board": os.path.basename(board_path) if board_path else "",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, RNAME)
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: ok %d/8 ===" % ok_n)
print("%s ok=%d/%d fails=%s" % (ENDTOK, ok_n, len(CANDS), ",".join(fails) or "none"), flush=True)
print("%s ok=%d/%d fails=%s" % (ENDTOK, ok_n, len(CANDS), ",".join(fails) or "none"), file=LOG)
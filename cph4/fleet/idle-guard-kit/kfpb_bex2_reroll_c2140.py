# -*- coding: utf-8 -*-
# kfpb_bex2_reroll_c2140.py -- KF-PACK-B B-EX2 single-frame variant runner (3 seeds, 672x384)
# Authorization: bank job kfpb-bex2-reroll-c2140 (C2140 native board read: B-EX2 = MINOR -
#   the girl's hand placement never resolves and the eyelines do not connect; the other five
#   probe frames PASS). Same recipe and same canonical B face as kfpb_probe_c2139.py.
# Difference from the probe: one frame only, three candidate seeds, and an explicit
#   hand-geometry + eyeline clause appended to the anchor.
# PASS gate: BEX2-REROLL-END ok=3/3 in the log tail + 3 PNGs >=50KB + strip board + receipt.
import hashlib, io, json, os, re, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
# Optional overrides so the same audited runner can test the main-pass resolution:
#   BEX2_TAG=xq-kfpb-bex2-hd-c2142  BEX2_RES=1344x768  BEX2_SEEDS=206038,207158
TAG = os.environ.get("BEX2_TAG") or "xq-kfpb-bex2-reroll-c2140"
OUTDIR = os.path.join(MEDIA, "xingqing", TAG)
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(OUTDIR, "kfpb_bex2_reroll_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (OUTDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "kfpb_bex2_reroll.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "kfpb_bex2_reroll.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR


def P(*a):
    print(*a, flush=True)
    print(*a, file=LOG)


# ---- shared blocks (KF-PACK-A-v1 sec-1, verbatim from the c2139 probe) ----
ID_F_B = ("a woman of about nineteen or twenty with long straight dark hair and a soft air fringe, "
          "gentle rounded brows, quiet smiling eyes, a small clean face, natural skin texture with "
          "visible pores and subtle unevenness")
ID_M_2001 = ("a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, "
             "softly rounded cheeks and a thick black fringe lying flat over his eyebrows")
WORLD = ("Taiwan countryside around Taitung-Danshui hills, 2000 era, faded single center line road, "
         "golden grass fields, small tin-and-brick farmhouse")
LIGHT_DUSK = "lit by 2800K dusk backlight with a warm halo"
CLOSING = "35mm film grain, telecine texture, 2001 Taiwan music video look"

# SHOTLIST v3 sec-1 KF column anchor, verbatim, plus the C2140 repair clause:
# the hand must be readable as a hand (five separated fingers, thumb outside the fabric)
# and the two eyelines must meet at one height.
ANCHOR_BASE = "close-up of her fingers lightly hooking the hem of his jacket during a wish, backlit dusk"
ANCHOR_REPAIR = ("her right hand clearly readable with five separated fingers curling over the jacket "
                 "hem, thumb resting outside the fabric, wrist relaxed; their eyes meeting each other, "
                 "both heads turned toward one another at the same height, shoulders facing")

# Original probe seed for XQ-KFPB-B-EX2 (same derivation as the probe), then two fresh ones.
def seed_for(oid):
    return int.from_bytes(hashlib.md5(oid.encode("utf-8")).digest()[:4], "big") % 999983


SEED_ORIG = seed_for("XQ-KFPB-B-EX2")
_over = os.environ.get("BEX2_SEEDS", "").strip()
if _over:
    SEEDS = [int(s) for s in _over.split(",") if s.strip()]
else:
    SEEDS = [SEED_ORIG, (SEED_ORIG + 1117) % 999983, (SEED_ORIG + 2237) % 999983]


def prompt_for(seed, with_repair):
    parts = [WORLD,
             ID_F_B + ", standing beside " + ID_M_2001 + ", " + ANCHOR_BASE,
             ANCHOR_REPAIR if with_repair else "",
             LIGHT_DUSK,
             CLOSING]
    return ". ".join(p for p in parts if p) + "."


# ---- lint: same three lists as the casting/f5-33c/probe runners ----
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)

CANDS = []
for sidx, seed in enumerate(SEEDS):
    # candidate 1 keeps the original seed (isolates the clause effect); 2 and 3 are fresh draws
    repair = True
    pr = prompt_for(seed, repair)
    cid = "B-EX2-r%d" % (sidx + 1)
    hits = sorted(set((NEG.findall(pr) or []) + (VAGUE.findall(pr) or []) + (CONCEPT.findall(pr) or [])))
    if hits:
        P("LINT FAIL %s: %r -- ABORT" % (cid, hits))
        print("LINT-FAIL", hits, flush=True)
        sys.exit(3)
    if len(pr.split()) > 200:
        P("WORD BUDGET FAIL %s: %d words -- ABORT" % (cid, len(pr.split())))
        print("WORDCOUNT-FAIL", len(pr.split()), flush=True)
        sys.exit(3)
    CANDS.append((cid, seed, pr))
if len(set(c[1] for c in CANDS)) != len(CANDS):
    P("derived seed collision -- ABORT")
    print("SEED-COLLISION", flush=True)
    sys.exit(3)
P("lint zero-hit %d/%d; seeds unique %d/%d; words %s (orig probe seed=%d)" % (
    len(CANDS), len(CANDS), len({c[1] for c in CANDS}), len(CANDS),
    ",".join("%s=%d" % (c[0], len(c[2].split())) for c in CANDS), SEED_ORIG))

if os.environ.get("BEX2_DRY") == "1":
    for cid, seed, pr in CANDS:
        P("DRY %s s%d words=%d: %s" % (cid, seed, len(pr.split()), pr))
    print("DRY-OK", flush=True)
    sys.exit(0)

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "reroll", "done": {},
        "meta": {"wave": "xq-kfpb-bex2-reroll-c2140", "runner": "bm-c C2142",
                 "auth": "bank job kfpb-bex2-reroll-c2140 / C2140 board read (B-EX2 MINOR)",
                 "res_mini": "672x384", "steps": 8, "cfg": 1.0, "jman": "0.6 (frame shows the boy)",
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

RES = (672, 384)
_res_over = os.environ.get("BEX2_RES", "").strip()
if _res_over:
    _w, _h = _res_over.lower().split("x")
    RES = (int(_w), int(_h))


def graph(prompt_text, seed, use_jman, strength, w, h):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqKfpbBex2"}},
    }
    model = ["10", 0]
    if use_jman:
        g["20"] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"lora_name": "jman_v1_640_rank32_final.safetensors",
                              "strength_model": strength, "model": ["10", 0]}}
        model = ["20", 0]
    g["3"] = {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": model, "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}}
    return g


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

try:
    q = http(SERVER + "/queue")
except Exception as e:
    P("queue probe failed -- ABORT: %r" % e)
    print("QUEUE-PROBE-FAIL", flush=True)
    sys.exit(2)
qr = q.get("queue_running", []) if isinstance(q, dict) else []
qp = q.get("queue_pending", []) if isinstance(q, dict) else []
if qr or qp:
    P("queue non-empty (running=%d pending=%d) -- ABORT, FIFO law" % (len(qr), len(qp)))
    print("QUEUE-BUSY", len(qr), len(qp), flush=True)
    sys.exit(2)
P("queue empty 0/0 -- bex2 reroll start")


def burn(prompt, seed, out, w, h, use_jman, strength):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed, use_jman, strength, w, h), "client_id": "bmc-bex2"})
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


P("=== kfpb_bex2_reroll_c2140 start %s pid=%d === candidates=%d res=%s" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(CANDS), str(RES)))
t_wave = time.time()
fails = []
ok_n = 0
for cid, seed, pr in CANDS:
    out = os.path.join(OUTDIR, ("KFPB_BEX2_hem_%s_s%d.png" % (cid.replace("B-EX2-", ""), seed)))
    if PROG["done"].get(cid, {}).get("ok") or (os.path.isfile(out) and os.path.getsize(out) > 50000):
        ok_n += 1
        continue
    ok, err = burn(pr, seed, out, RES[0], RES[1], True, 0.6)
    PROG["done"][cid] = {"ok": ok, "file": os.path.basename(out) if ok else "", "err": err, "seed": seed}
    save_prog()
    P("[BEX2] %s s%d %s (%.0fs)" % (cid, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
    if ok:
        ok_n += 1
    else:
        fails.append(cid)

P("BEX2 burns: ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"))

# ---------------- strip board: 1 row x 3 cols ----------------
board_path = ""
try:
    from PIL import Image, ImageDraw
    tw, th = 448, 256
    ncol = 3
    nrow = (len(CANDS) + ncol - 1) // ncol
    board = Image.new("RGB", (ncol * tw + 20, nrow * (th + 22) + 40), (24, 22, 20))
    dr = ImageDraw.Draw(board)
    for idx, (cid, seed, pr) in enumerate(CANDS):
        row, col = divmod(idx, ncol)
        x, y = 10 + col * tw, 30 + row * (th + 22)
        path = os.path.join(OUTDIR, ("KFPB_BEX2_hem_%s_s%d.png" % (cid.replace("B-EX2-", ""), seed)))
        if os.path.isfile(path):
            im = Image.open(path).convert("RGB").resize((tw - 8, th - 8))
            board.paste(im, (x + 4, y + 4))
        dr.text((x + 6, y + th + 2), "%s / dusk / s%d" % (cid, seed), fill=(200, 180, 140))
    dr.text((10, 6), "XQ KF-PACK-B B-EX2 REROLL c2140 (672x384, hand + eyeline clause, 3 seeds)",
            fill=(235, 215, 170))
    board_path = os.path.join(ALBUM, "xq-KFPB-BEX2-BOARD-%s.jpg" % TAG.replace("xq-kfpb-bex2-", ""))
    board.save(board_path, quality=88)
    P("board -> %s (%dB)" % (board_path, os.path.getsize(board_path)))
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

receipt = {"wave": TAG, "runner": "bm-c C2142",
           "auth": "bank job kfpb-bex2-reroll-c2140; C2140 native board read B-EX2 MINOR (hand placement + eyeline)",
           "blocks": {"id_f_b": ID_F_B, "id_m_2001": ID_M_2001, "world": WORLD, "light_dusk": LIGHT_DUSK,
                      "closing": CLOSING, "anchor_base": ANCHOR_BASE, "anchor_repair": ANCHOR_REPAIR},
           "frames": [{"id": c[0], "shot": "B-EX2", "light": "dusk", "seed": c[1], "prompt": c[2]} for c in CANDS],
           "params": {"res": "%dx%d" % (RES[0], RES[1]), "steps": 8, "cfg": 1.0, "jman": "0.6",
                      "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled",
                      "orig_probe_seed": SEED_ORIG},
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"ok": ok_n, "total": len(CANDS), "fails": fails, "lint": "NEG/VAGUE/CONCEPT zero-hit"},
           "out_dir": "media/MV/mv0001/xingqing/" + TAG,
           "board": os.path.basename(board_path) if board_path else "",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, "xq-KFPB-BEX2-RECEIPT-%s.json" % TAG.replace("xq-kfpb-bex2-", ""))
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: ok %d/%d ===" % (ok_n, len(CANDS)))
print("BEX2-REROLL-END ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"), flush=True)
print("BEX2-REROLL-END ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"), file=LOG)
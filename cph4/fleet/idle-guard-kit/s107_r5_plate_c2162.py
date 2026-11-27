# -*- coding: utf-8 -*-
# s107_r5_plate_c2162.py -- Xingqing S1-07 R5 plate runner (plate replacement, no cloud figure)
# Authorization: xq-CASTING-VERDICT-c2136-full.md sec-5 (C2142 ruling): the B-EX2 anchor as written
#   is unrenderable - five frames across two resolutions all show 3-4 fused finger shapes with no
#   readable thumb, so the defect is the anchor, not the seed. New birth gate: hand close-ups
#   occupying >8% of the frame are rejected at birth. B-EX2 is re-anchored as an occluded-hand
#   composition: her hand disappears behind the jacket hem, camera from behind her shoulder, the
#   gesture is read from the arm angle. The eyeline mismatch is structurally removed because her
#   face is turned away from camera and only his face carries an eyeline.
# Same recipe/model/jman as kfpb_probe_c2139.py. Default fires at the main-pass size (1344x768)
#   because the probe size was proven too small to judge anything about hands.
# PASS gate: S107-R5-PLATE-END ok=3/3 in the log tail + 3 PNGs >=200KB + strip board + receipt.
import hashlib, io, json, os, re, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
TAG = os.environ.get("S107R5_TAG") or "xq-s107-r5-plate-c2162"
OUTDIR = os.path.join(MEDIA, "xingqing", TAG)
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(OUTDIR, "s107_r5_plate_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (OUTDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "s107_r5_plate.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "s107_r5_plate.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR


def P(*a):
    print(*a, flush=True)
    print(*a, file=LOG)


# ---- shared blocks (KF-PACK-A-v1 sec-1, verbatim from the c2139 probe) ----
# Her block is re-authored for this camera: she is seen from behind, so the frontal face detail
# would be wasted pixels at the frame edge; hair + the lit edge of her cheek carry the identity.
ID_F_B_BACK = ("a woman of about nineteen or twenty with long straight dark hair and a soft air fringe, "
               "seen from behind her right shoulder, the edge of her cheek and one ear catching the "
               "backlight, natural skin texture with visible pores")
ID_M_2001 = ("a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, "
             "softly rounded cheeks and a thick black fringe lying flat over his eyebrows")
WORLD = ("Taiwan countryside around Taitung-Danshui hills, 2000 era, faded single center line road, "
         "golden grass fields, small tin-and-brick farmhouse")
LIGHT_GOLD = "lit by a low golden-hour sun with warm haze near the horizon"
CLOSING = "35mm film grain, telecine texture, 2001 Taiwan music video look"

# Re-anchored composition (verdict sec-5): the hand never reads as a hand because it is not shown.
# The wish gesture is carried by the arm angle, the fabric fold and his eyeline.
# R5 plate for S1-07: the cloud is weather, never a body. The plate carries a low cumulus band
# only, so the i2v pass has nothing humanoid to lock onto (C2162 verdict: both R4 takes kept the
# figure because the plate itself fed it in).
ANCHOR_S107 = ("two riders on one old bicycle travelling across the frame: he sits forward pedalling "
               "with a loose hold on the chrome handlebar, she sits behind him with both arms around "
               "his waist, both faces in three-quarter view looking along the road; a wide low band of "
               "cumulus cloud with ragged wind-eroded edges filling the left half of the sky, its "
               "underside thinning into haze above the grass line, clear open air between the cloud "
               "and the riders")


def seed_for(oid):
    return int.from_bytes(hashlib.md5(oid.encode("utf-8")).digest()[:4], "big") % 999983


SEED_ORIG = seed_for("XQ-S107-R5")
# Candidate 1 keeps the canonical B seed so the anchor change is isolated from the seed change;
# 2 and 3 are fresh draws in the same residue band the B face was canonised on.
SEEDS = [SEED_ORIG, (SEED_ORIG + 4109) % 999983, (SEED_ORIG + 6971) % 999983]
_over = os.environ.get("S107R5_SEEDS", "").strip()
if _over:
    SEEDS = [int(s) for s in _over.split(",") if s.strip()]


def prompt_for():
    parts = [WORLD,
             ID_F_B_BACK + " riding pillion behind " + ID_M_2001 + ", " + ANCHOR_S107,
             LIGHT_GOLD,
             CLOSING]
    return ". ".join(p for p in parts if p) + "."


# ---- lint: same three lists as the casting/f5-33c/probe runners ----
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)

CANDS = []
for sidx, seed in enumerate(SEEDS):
    pr = prompt_for()
    cid = "S1-07-r5-%d" % (sidx + 1)
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
P("lint zero-hit %d/%d; seeds unique %d/%d; words %s (canonical B seed=%d)" % (
    len(CANDS), len(CANDS), len({c[1] for c in CANDS}), len(CANDS),
    ",".join("%s=%d" % (c[0], len(c[2].split())) for c in CANDS), SEED_ORIG))

if os.environ.get("S107R5_DRY") == "1":
    for cid, seed, pr in CANDS:
        P("DRY %s s%d words=%d: %s" % (cid, seed, len(pr.split()), pr))
    print("DRY-OK", flush=True)
    sys.exit(0)

RES = (1344, 768)
_res_over = os.environ.get("S107R5_RES", "").strip()
if _res_over:
    _w, _h = _res_over.lower().split("x")
    RES = (int(_w), int(_h))

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "reanchor", "done": {},
        "meta": {"wave": TAG, "runner": "bm-c C2162",
                 "auth": "bank job kfpb-bex2-reanchor-c2143 / verdict c2136 sec-5",
                 "res": "%dx%d" % RES, "steps": 8, "cfg": 1.0, "jman": "0.6 (frame shows the boy)",
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


def graph(prompt_text, seed, use_jman, strength, w, h):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqKfpbBex2Occl"}},
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
P("queue empty 0/0 -- bex2 re-anchor start")


def burn(prompt, seed, out, w, h, use_jman, strength):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed, use_jman, strength, w, h), "client_id": "bmc-bex2o"})
    pid = resp.get("prompt_id") if isinstance(resp, dict) else None
    if not pid:
        return False, "submit-fail"
    t0 = time.time()
    while time.time() - t0 < 900:
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


P("=== kfpb_bex2_occl_c2143 start %s pid=%d === candidates=%d res=%s" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(CANDS), str(RES)))
t_wave = time.time()
fails = []
ok_n = 0
for cid, seed, pr in CANDS:
    out = os.path.join(OUTDIR, ("S107_R5_plate_%s_s%d.png" % (cid, seed)))
    if PROG["done"].get(cid, {}).get("ok") or (os.path.isfile(out) and os.path.getsize(out) > 50000):
        ok_n += 1
        continue
    ok, err = burn(pr, seed, out, RES[0], RES[1], True, 0.6)
    PROG["done"][cid] = {"ok": ok, "file": os.path.basename(out) if ok else "", "err": err, "seed": seed}
    save_prog()
    P("[S107R5] %s s%d %s (%.0fs)" % (cid, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
    if ok:
        ok_n += 1
    else:
        fails.append(cid)

P("BEX2O burns: ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"))

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
        path = os.path.join(OUTDIR, ("S107_R5_plate_%s_s%d.png" % (cid, seed)))
        if os.path.isfile(path):
            im = Image.open(path).convert("RGB").resize((tw - 8, th - 8))
            board.paste(im, (x + 4, y + 4))
        dr.text((x + 6, y + th + 2), "%s / dusk / s%d" % (cid, seed), fill=(200, 180, 140))
    dr.text((10, 6), "XQ KF-PACK-B B-EX2 RE-ANCHOR c2143 (%dx%d, occluded hand, 3 seeds)" % RES,
            fill=(235, 215, 170))
    board_path = os.path.join(ALBUM, "xq-S107-R5-BOARD-%s.jpg" % TAG.replace("xq-s107-r5-plate-", ""))
    board.save(board_path, quality=88)
    P("board -> %s (%dB)" % (board_path, os.path.getsize(board_path)))
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

receipt = {"wave": TAG, "runner": "bm-c C2162",
           "auth": "verdict c2136 sec-5: hand close-ups >8% of frame rejected at birth; B-EX2 re-anchored as occluded-hand composition",
           "blocks": {"id_f_b_back": ID_F_B_BACK, "id_m_2001": ID_M_2001, "world": WORLD,
                      "light_dusk": LIGHT_DUSK, "closing": CLOSING, "anchor_occl": ANCHOR_OCCL},
           "frames": [{"id": c[0], "shot": "B-EX2", "light": "dusk", "seed": c[1], "prompt": c[2]} for c in CANDS],
           "params": {"res": "%dx%d" % (RES[0], RES[1]), "steps": 8, "cfg": 1.0, "jman": "0.6",
                      "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled",
                      "canonical_b_seed": SEED_ORIG},
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"ok": ok_n, "total": len(CANDS), "fails": fails, "lint": "NEG/VAGUE/CONCEPT zero-hit"},
           "out_dir": "media/MV/mv0001/xingqing/" + TAG,
           "board": os.path.basename(board_path) if board_path else "",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, "xq-S107-R5-RECEIPT-%s.json" % TAG.replace("xq-s107-r5-plate-", ""))
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: ok %d/%d ===" % (ok_n, len(CANDS)))
print("S107-R5-PLATE-END ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"), flush=True)
print("S107-R5-PLATE-END ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"), file=LOG)
# -*- coding: utf-8 -*-
# NOTE c2145: cid must stay unique per seed - the skip-if-done guard keys on cid,
#   so three seeds sharing one cid burn only the first one (hit in the first run, fixed here).
# kfpb_s317_feet_c2145.py -- Xingqing KF-PACK-B S3-17 feet re-roll (1344x768, 3 seeds)
# Authorization: bank job kfpb-mainpass-author-c2144; xq-CASTING-VERDICT-c2136-full.md sec-4/5;
#   Xingqing-KF-PACK-A-v1.md sec-2 ("probe at 672x384 first, then the 1344x768 main pass").
# Seeds: every non-B-EX2 seed is the one canonised by the c2139 probe board read (receipt
#   xq-KFPB-RECEIPT-c2139-probe.json). B-EX2 uses seed 204921, locked by the C2143 native read of
#   the re-anchored occluded-hand composition (verdict in bank job kfpb-bex2-occl-verdict-c2143).
# B-EX2 keeps the re-anchored prompt verbatim from kfpb_bex2_occl_c2143.py: her hand disappears
#   behind the jacket hem, camera from behind her shoulder, gesture carried by the arm angle and by
#   his single eyeline. A hand close-up here would violate the c2136 sec-5 birth gate.
# Same recipe/model/jman as the probe: krea2_turbo_fp8_scaled, qwen3vl CLIP, 8 steps, cfg 1.0,
#   euler/simple, jman LoRA 0.6 on the two frames that show the boy.
# PASS gate: KFPB-MAINPASS-END ok=6/6 in the log tail + 6 PNGs >=900KB + strip board + receipt.
import hashlib, io, json, os, re, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
OUTDIR = os.path.join(MEDIA, "xingqing", "xq-kf-s317-feet-c2145")
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(OUTDIR, "kfpb_s317_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (OUTDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "kfpb_s317.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "kfpb_s317.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR


def P(*a):
    print(*a, flush=True)
    print(*a, file=LOG)

# ---- shared blocks (KF-PACK-A-v1 sec-1, verbatim) ----
ID_F_B = ("a woman of about nineteen or twenty with long straight dark hair and a soft air fringe, "
          "gentle rounded brows, quiet smiling eyes, a small clean face, natural skin texture with "
          "visible pores and subtle unevenness")
# B-EX2 camera sits behind her shoulder, so the frontal face detail is replaced by hair + cheek edge.
ID_F_B_BACK = ("a woman of about nineteen or twenty with long straight dark hair and a soft air fringe, "
               "seen from behind her right shoulder, the edge of her cheek and one ear catching the "
               "backlight, natural skin texture with visible pores")
ID_M_2001 = ("a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower lip, "
             "softly rounded cheeks and a thick black fringe lying flat over his eyebrows")
WORLD = ("Taiwan countryside around Taitung-Danshui hills, 2000 era, faded single center line road, "
         "golden grass fields, small tin-and-brick farmhouse")
LIGHTS = {
    "noon": "lit by warm 5200K late-afternoon sunlight",
    "dusk": "lit by 2800K dusk backlight with a warm halo",
    "night": "lit by indigo night sky with cool starlight and a warm lamp edge",
}
CLOSING = "35mm film grain, telecine texture, 2001 Taiwan music video look"
# Re-anchored B-EX2 composition, verbatim from kfpb_bex2_occl_c2143.py (verdict c2136 sec-5).
ANCHOR_OCCL = ("he faces the camera, she stands with her back to it, her right arm folded across to the "
               "hem of his jacket where the fabric creases over her wrist and keeps the hand fully "
               "behind the cloth, her forearm angled in a light steady hold, his eyes lowered toward "
               "her hand then lifting to her face, both heads at the same height")

# ---- six frames: id, shot, light, needs_male_id, anchor, locked seed ----
# Seeds are the ones canonised by the c2139 probe board read; B-EX2 is the 204921 locked by C2143.
FRAMES = [
    ("S3-17a", "S3-17", "dusk", False,
     "an extreme close-up of two pairs of feet cropped at the ankles, stepping along the white "
     "centre line of the road, one pair in lace-up sneakers and one pair in plain canvas shoes, "
     "the rhythm of counting steps, the frame filled by feet and road only", 266291),
    ("S3-17b", "S3-17", "dusk", False,
     "an extreme close-up of two pairs of feet cropped at the ankles, stepping along the white "
     "centre line of the road, one pair in lace-up sneakers and one pair in plain canvas shoes, "
     "the rhythm of counting steps, the frame filled by feet and road only", 310477),
    ("S3-17c", "S3-17", "dusk", False,
     "an extreme close-up of two pairs of feet cropped at the ankles, stepping along the white "
     "centre line of the road, one pair in lace-up sneakers and one pair in plain canvas shoes, "
     "the rhythm of counting steps, the frame filled by feet and road only", 410233),
]

TYPE_NAME = {"S1-08": "hands", "S3-17": "feet", "S3-21": "lookup",
             "S5-31": "twoshot", "B-EX1": "spool", "B-EX2": "occl"}


def prompt_for(shot, light, needs_male, anchor):
    parts = [WORLD]
    if shot == "B-EX2":
        parts.append(ID_F_B_BACK + ", standing beside " + ID_M_2001 + ", " + anchor)
    elif needs_male:
        parts.append(ID_F_B + ", standing beside " + ID_M_2001 + ", " + anchor)
    elif shot in ("S1-08", "S3-17"):
        parts.append(anchor)
    else:
        parts.append(ID_F_B + ", " + anchor)
    parts.append(LIGHTS[light])
    parts.append(CLOSING)
    return ". ".join(parts) + "."


# ---- lint: same three lists as the casting/probe runners ----
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)

CANDS = []
for sid, shot, light, male, anchor, seed in FRAMES:
    oid = "XQ-KFPB-%s" % sid
    pr = prompt_for(shot, light, male, anchor)
    hits = sorted(set((NEG.findall(pr) or []) + (VAGUE.findall(pr) or []) + (CONCEPT.findall(pr) or [])))
    if hits:
        P("LINT FAIL %s: %r -- ABORT" % (oid, hits))
        print("LINT-FAIL", hits, flush=True)
        sys.exit(3)
    if len(pr.split()) > 200:
        P("WORD BUDGET FAIL %s: %d words -- ABORT" % (oid, len(pr.split())))
        print("WORDCOUNT-FAIL", len(pr.split()), flush=True)
        sys.exit(3)
    CANDS.append((oid, shot, light, male, anchor, pr, seed))
if len(set(c[6] for c in CANDS)) != len(CANDS):
    P("seed collision -- ABORT")
    print("SEED-COLLISION", flush=True)
    sys.exit(3)
P("lint zero-hit %d/%d; seeds unique %d/%d; words %s" % (
    len(CANDS), len(CANDS), len({c[6] for c in CANDS}), len(CANDS),
    ",".join("%s=%d" % (c[1], len(c[5].split())) for c in CANDS)))

if os.environ.get("KFPB_MAIN_DRY") == "1":
    for cid, shot, light, male, anchor, pr, seed in CANDS:
        P("DRY %s s%d words=%d male=%s: %s" % (cid, seed, len(pr.split()), male, pr))
    print("DRY-OK", flush=True)
    sys.exit(0)

RES = (1344, 768)
_res_over = os.environ.get("KFPB_MAIN_RES", "").strip()
if _res_over:
    _w, _h = _res_over.lower().split("x")
    RES = (int(_w), int(_h))

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "mainpass", "done": {},
        "meta": {"wave": "xq-kf-packb-mainpass-c2144", "runner": "bm-c C2144",
                 "auth": "bank job kfpb-mainpass-author-c2144; verdict c2136 sec-4 (KF-PACK-B unlocked) "
                         "and sec-5 (B-EX2 occluded-hand anchor); probe seeds from c2139 board read",
                 "res": "%dx%d" % RES, "steps": 8, "cfg": 1.0, "jman": "0.6 on frames showing the boy",
                 "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled",
                 "candidates": [c[0] for c in CANDS], "seeds": {c[0]: c[6] for c in CANDS}}}
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
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqKfpbMP"}},
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

q = http(SERVER + "/queue")
qr = q.get("queue_running", []) if isinstance(q, dict) else []
qp = q.get("queue_pending", []) if isinstance(q, dict) else []
if qr or qp:
    P("queue non-empty (running=%d pending=%d) -- ABORT, FIFO law" % (len(qr), len(qp)))
    print("QUEUE-BUSY", len(qr), len(qp), flush=True)
    sys.exit(2)
P("queue empty 0/0 -- s3-17 feet reroll start")


def burn(prompt, seed, out, w, h, use_jman, strength):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed, use_jman, strength, w, h), "client_id": "bmc-kfpb-s317"})
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


P("=== kfpb_s317_feet_c2145 start %s pid=%d === candidates=%d res=%s" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(CANDS), str(RES)))
t_wave = time.time()
fails = []
ok_n = 0
for cid, shot, light, male, anchor, pr, seed in CANDS:
    out = os.path.join(OUTDIR, ("KFPB_MP_%s_%s_s%d.png" % (shot, TYPE_NAME[shot], seed)))
    if PROG["done"].get(cid, {}).get("ok") or (os.path.isfile(out) and os.path.getsize(out) > 400000):
        ok_n += 1
        continue
    ok, err = burn(pr, seed, out, RES[0], RES[1], male, 0.6)
    PROG["done"][cid] = {"ok": ok, "file": os.path.basename(out) if ok else "", "err": err, "seed": seed}
    save_prog()
    P("[KFPBMP] %s s%d %s (%.0fs)" % (cid, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
    if ok:
        ok_n += 1
    else:
        fails.append(cid)

sizes = {c[0]: (os.path.getsize(os.path.join(OUTDIR, "KFPB_MP_%s_%s_s%d.png" % (c[1], TYPE_NAME[c[1]], c[6])))
                if os.path.isfile(os.path.join(OUTDIR, "KFPB_MP_%s_%s_s%d.png" % (c[1], TYPE_NAME[c[1]], c[6]))) else 0)
         for c in CANDS}
small = [k for k, v in sizes.items() if v < 900000]
P("KFPB s317 reroll burns: ok=%d/%d fails=%s sizes=%s" % (
    ok_n, len(CANDS), ",".join(fails) or "none",
    ",".join("%s=%dKB" % (k, v // 1024) for k, v in sizes.items())))

# ---------------- strip board: 3 rows x 2 cols ----------------
board_path = ""
try:
    from PIL import Image, ImageDraw
    tw, th = 640, 366
    ncol = 2
    nrow = (len(CANDS) + ncol - 1) // ncol
    board = Image.new("RGB", (ncol * tw + 20, nrow * (th + 24) + 44), (24, 22, 20))
    dr = ImageDraw.Draw(board)
    for idx, (cid, shot, light, male, anchor, pr, seed) in enumerate(CANDS):
        row, col = divmod(idx, ncol)
        x, y = 10 + col * tw, 34 + row * (th + 24)
        path = os.path.join(OUTDIR, ("KFPB_MP_%s_%s_s%d.png" % (shot, TYPE_NAME[shot], seed)))
        if os.path.isfile(path):
            im = Image.open(path).convert("RGB").resize((tw - 8, th - 8))
            board.paste(im, (x + 4, y + 4))
        dr.text((x + 6, y + th + 4), "%s / %s / s%d" % (shot, light, seed), fill=(200, 180, 140))
    dr.text((10, 8), "XQ KF-PACK-B S3-17 FEET REROLL c2145 (1344x768, 3 seeds)", fill=(235, 215, 170))
    board_path = os.path.join(ALBUM, "xq-KFPB-S317-BOARD-c2145.jpg")
    board.save(board_path, quality=88)
    P("board -> %s (%dB)" % (board_path, os.path.getsize(board_path)))
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

receipt = {"wave": "xq-kf-s317-feet-c2145", "runner": "bm-c C2145",
           "auth": "bank job kfpb-mainpass-author-c2144; verdict c2136 sec-4/5; seeds from c2139 probe read "
                   "and the C2143 B-EX2 native verdict",
           "blocks": {"id_f_b": ID_F_B, "id_f_b_back": ID_F_B_BACK, "id_m_2001": ID_M_2001,
                      "world": WORLD, "lights": LIGHTS, "closing": CLOSING, "anchor_occl": ANCHOR_OCCL},
           "frames": [{"id": c[0], "shot": c[1], "light": c[2], "male_id": c[3],
                       "anchor": c[4], "prompt": c[5], "seed": c[6], "bytes": sizes.get(c[0], 0)} for c in CANDS],
           "params": {"res": "%dx%d" % RES, "steps": 8, "cfg": 1.0, "jman": "0.6 (frames showing the boy)",
                      "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled",
                      "s317_seeds": [266291, 310477, 410233]},
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"ok": ok_n, "total": len(CANDS), "fails": fails,
                     "under_900kb": small, "lint": "NEG/VAGUE/CONCEPT zero-hit"},
           "out_dir": "media/MV/mv0001/xingqing/xq-kf-s317-feet-c2145",
           "board": os.path.basename(board_path) if board_path else "",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, "xq-KFPB-S317-RECEIPT-c2145.json")
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: ok %d/%d, under-900KB=%d ===" % (ok_n, len(CANDS), len(small)))
print("KFPB-S317-END ok=%d/%d fails=%s small=%s" % (
    ok_n, len(CANDS), ",".join(fails) or "none", ",".join(small) or "none"), flush=True)
print("KFPB-S317-END ok=%d/%d fails=%s small=%s" % (
    ok_n, len(CANDS), ",".join(fails) or "none", ",".join(small) or "none"), file=LOG)
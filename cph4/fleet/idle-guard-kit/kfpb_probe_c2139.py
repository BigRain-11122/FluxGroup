# -*- coding: utf-8 -*-
# kfpb_probe_c2139.py -- Xingqing KF-PACK-B composition probe (6 face/limb frames, 672x384, 1 seed each)
# Authorization: cph4/fleet/mv-album-001-jay/xq-CASTING-VERDICT-c2136-full.md sec-4 step-2
#   ("KF-PACK-B unlocked: S1-08 / S3-17 / S3-21 / S5-31 + B two extra frames") and
#   Xingqing-KF-PACK-A-v1.md sec-1/sec-2 ("probe law: 672x384 one seed per shot, composition
#   eyeball check before the 1344x768 main pass").
# Face identity: the canonical B block fixed by the c2136-full verdict (not a new cast).
# Male identity: PROMPT-SPEC sec-3 ID_M_2001 verbatim, jman LoRA 0.6 only on the frame that shows him.
# PASS gate: KFPB-PROBE-END ok=6/6 in the log tail + 6 PNGs >=50KB + strip board + receipt.
import hashlib, io, json, os, re, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
OUTDIR = os.path.join(MEDIA, "xingqing", "xq-kf-packb-probe-c2139")
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(OUTDIR, "kfpb_probe_c2139_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (OUTDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "kfpb_probe_c2139.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "kfpb_probe_c2139.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR


def P(*a):
    print(*a, flush=True)
    print(*a, file=LOG)


def seed_for(oid):
    return int.from_bytes(hashlib.md5(oid.encode("utf-8")).digest()[:4], "big") % 999983


# ---- shared blocks (KF-PACK-A-v1 sec-1, verbatim) ----
ID_F_B = ("a woman of about nineteen or twenty with long straight dark hair and a soft air fringe, "
          "gentle rounded brows, quiet smiling eyes, a small clean face, natural skin texture with "
          "visible pores and subtle unevenness")
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

# ---- six frames: id, shot, light, needs_male_id, anchor (SHOTLIST v3 sec-1 KF column, verbatim) ----
FRAMES = [
    ("S1-08", "S1-08", "noon", False,
     "a young woman's hands gripping the bicycle seat frame, wind in the fabric of her school-casual "
     "clothes, tight side crop with her face out of frame"),
    ("S3-17", "S3-17", "dusk", False,
     "two pairs of feet stepping along a white road line, one pair in sneakers and one in canvas shoes, "
     "the rhythm of counting steps"),
    ("S3-21", "S3-21", "dusk", False,
     "she lowers her head with a soft smile then looks up, shy joy, era-accurate hair"),
    ("S5-31", "S5-31", "night", True,
     "a young couple turning to face each other and holding hands, close two-shot, warm skin tones in "
     "the cool night air"),
    ("B-EX1", "B-EX1", "dusk", False,
     "she winds the kite spool with a focused face, both hands on the line"),
    ("B-EX2", "B-EX2", "dusk", True,
     "close-up of her fingers lightly hooking the hem of his jacket during a wish, backlit dusk"),
]
TYPE_NAME = {"S1-08": "hands", "S3-17": "feet", "S3-21": "lookup",
             "S5-31": "twoshot", "B-EX1": "spool", "B-EX2": "hem"}


def prompt_for(shot, light, needs_male, anchor):
    parts = [WORLD]
    if needs_male:
        parts.append(ID_F_B + ", standing beside " + ID_M_2001 + ", " + anchor)
    elif shot in ("S1-08", "S3-17", "B-EX2"):
        parts.append(anchor)
    else:
        parts.append(ID_F_B + ", " + anchor)
    parts.append(LIGHTS[light])
    parts.append(CLOSING)
    return ". ".join(parts) + "."


# ---- lint: same three lists as the casting/f5-33c runners ----
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)

CANDS = []
for sid, shot, light, male, anchor in FRAMES:
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
    CANDS.append((oid, shot, light, male, anchor, pr, seed_for(oid)))
if len(set(c[6] for c in CANDS)) != len(CANDS):
    P("derived seed collision -- ABORT")
    print("SEED-COLLISION", flush=True)
    sys.exit(3)
P("lint zero-hit %d/%d; seeds unique %d/%d; words %s" % (
    len(CANDS), len(CANDS), len({c[6] for c in CANDS}), len(CANDS),
    ",".join("%s=%d" % (c[1], len(c[5].split())) for c in CANDS)))

if os.environ.get("KFPB_DRY") == "1":
    for cid, shot, light, male, anchor, pr, seed in CANDS:
        P("DRY %s s%d words=%d male=%s: %s" % (cid, seed, len(pr.split()), male, pr))
    print("DRY-OK", flush=True)
    sys.exit(0)

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "probe", "done": {},
        "meta": {"wave": "xq-kf-packb-probe-c2139", "runner": "bm-c C2139",
                 "auth": "xq-CASTING-VERDICT-c2136-full sec-4 step-2 (KF-PACK-B unlocked); "
                         "KF-PACK-A-v1 sec-2 probe law (672x384 one seed before the 1344x768 main pass)",
                 "res_mini": "672x384", "steps": 8, "cfg": 1.0, "jman": "0.6 on frames showing the boy",
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

RES = (672, 384)


def graph(prompt_text, seed, use_jman, strength, w, h):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqKfpb"}},
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
P("queue empty 0/0 -- kf-pack-b probe start")


def burn(prompt, seed, out, w, h, use_jman, strength):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed, use_jman, strength, w, h), "client_id": "bmc-kfpb"})
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


P("=== kfpb_probe_c2139 start %s pid=%d === candidates=%d res=%s" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(CANDS), str(RES)))
t_wave = time.time()
fails = []
ok_n = 0
for cid, shot, light, male, anchor, pr, seed in CANDS:
    out = os.path.join(OUTDIR, ("KFPB_%s_%s_s%d.png" % (shot, TYPE_NAME[shot], seed)))
    if PROG["done"].get(cid, {}).get("ok") or (os.path.isfile(out) and os.path.getsize(out) > 50000):
        ok_n += 1
        continue
    ok, err = burn(pr, seed, out, RES[0], RES[1], male, 0.6)
    PROG["done"][cid] = {"ok": ok, "file": os.path.basename(out) if ok else "", "err": err, "seed": seed}
    save_prog()
    P("[KFPB] %s s%d %s (%.0fs)" % (cid, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
    if ok:
        ok_n += 1
    else:
        fails.append(cid)

P("KFPB burns: ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"))

# ---------------- strip board: 3 rows x 2 cols ----------------
board_path = ""
try:
    from PIL import Image, ImageDraw
    tw, th = 448, 256
    ncol = 2
    nrow = (len(CANDS) + ncol - 1) // ncol
    board = Image.new("RGB", (ncol * tw + 20, nrow * (th + 22) + 40), (24, 22, 20))
    dr = ImageDraw.Draw(board)
    for idx, (cid, shot, light, male, anchor, pr, seed) in enumerate(CANDS):
        row, col = divmod(idx, ncol)
        x, y = 10 + col * tw, 30 + row * (th + 22)
        path = os.path.join(OUTDIR, ("KFPB_%s_%s_s%d.png" % (shot, TYPE_NAME[shot], seed)))
        if os.path.isfile(path):
            im = Image.open(path).convert("RGB").resize((tw - 8, th - 8))
            board.paste(im, (x + 4, y + 4))
        dr.text((x + 6, y + th + 2), "%s / %s / s%d" % (shot, light, seed), fill=(200, 180, 140))
    dr.text((10, 6), "XQ KF-PACK-B PROBE c2139 (672x384, 1 seed per shot)", fill=(235, 215, 170))
    board_path = os.path.join(ALBUM, "xq-KFPB-BOARD-c2139-probe.jpg")
    board.save(board_path, quality=88)
    P("board -> %s (%dB)" % (board_path, os.path.getsize(board_path)))
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

receipt = {"wave": "xq-kf-packb-probe-c2139", "runner": "bm-c C2139",
           "auth": "xq-CASTING-VERDICT-c2136-full sec-4 step-2; KF-PACK-A-v1 sec-2 probe law",
           "blocks": {"id_f_b": ID_F_B, "id_m_2001": ID_M_2001, "world": WORLD, "lights": LIGHTS, "closing": CLOSING},
           "frames": [{"id": c[0], "shot": c[1], "light": c[2], "male_id": c[3],
                       "anchor": c[4], "prompt": c[5], "seed": c[6]} for c in CANDS],
           "params": {"res_mini": "672x384", "steps": 8, "cfg": 1.0, "jman": "0.6 (frames showing the boy)",
                      "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled"},
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"ok": ok_n, "total": len(CANDS), "fails": fails, "lint": "NEG/VAGUE/CONCEPT zero-hit"},
           "out_dir": "media/MV/mv0001/xingqing/xq-kf-packb-probe-c2139",
           "board": os.path.basename(board_path) if board_path else "",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, "xq-KFPB-RECEIPT-c2139-probe.json")
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: ok %d/%d ===" % (ok_n, len(CANDS)))
print("KFPB-PROBE-END ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"), flush=True)
print("KFPB-PROBE-END ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"), file=LOG)
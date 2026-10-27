# -*- coding: utf-8 -*-
# xq_casting_c2136.py -- Xingqing female-lead casting candidate board (4 types x 2 light x 2 seeds)
# Authorization: cph4/fleet/mv-album-001-jay/XQ-casting CASE v1 -- "candidate board burn (GPU batch,
#   queued after MV V3)" + "4 types x 4 seeds 672x384 composition board". V3 is long closed and the
#   GPU lane is free, so this is the due step that unblocks KF-PACK-B (6 face-dependent frames).
# Types: verbatim ID blocks from the casting case (zero transcription drift), light variants:
#   two seeds in B1 golden-grass dusk backlight + two seeds in indigo night with warm lamp edge,
#   which is what the case demands ("board must carry the dusk rim-light look, B1 grass + night").
# Female face: base Krea2 turbo WITHOUT the jman (male) LoRA -- the LoRA is a male-ID adapter and
#   would drag the face male. jman is recorded in the receipt as deliberately omitted.
# PASS gate: CASTING-END ok=16 in log tail + 16 PNGs >=50KB + receipt + contact board.
# Companion gate: reverse-name test (multimodal) must not name a real celebrity for the board.

import hashlib, io, json, os, subprocess, sys, time, urllib.request

if not sys.stdout:
    sys.stdout = open(os.devnull, "w")

GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
ALBUM = os.path.join(GROUP_ROOT, "cph4", "fleet", "mv-album-001-jay")
MEDIA = os.path.join(GROUP_ROOT, "media", "MV", "mv0001")
OUTDIR = os.path.join(MEDIA, "xingqing", "xq-casting-c2136")
LOGDIR = os.path.join(MEDIA, "logs")
PROG_PATH = os.path.join(OUTDIR, "xq_casting_c2136_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (OUTDIR, LOGDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "xq_casting_c2136.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "xq_casting_c2136.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR


def P(*a):
    print(*a, flush=True)
    print(*a, file=LOG)


def seed_for(oid):
    return int.from_bytes(hashlib.md5(oid.encode("utf-8")).digest()[:4], "big") % 999983


# ---- casting case v1, section "candidate four types" (verbatim ID blocks) ----
TYPES = {
    "A": "high dark ponytail, bright crescent-smile eyes, soft rounded cheeks, even white teeth, "
         "sun-warmed clear skin, a few freckles across the nose",
    "B": "long straight dark hair with a soft air fringe, gentle rounded brows, quiet smiling eyes, "
         "small clean face",
    "C": "chin-length dark bob, bright boyish grin, small expressive face, lively brows",
    "D": "low twin braids, clear bare face, neat simple features, bright honest gaze",
}
TYPE_NAME = {"A": "ponytail", "B": "soft-long", "C": "bob", "D": "braids"}

LIGHTS = {
    "dusk": "lit by 2800K dusk backlight with a warm halo, standing in a golden grass field, "
            "rim of warm light along her hair",
    "night": "lit by indigo night sky with cool starlight and a warm lamp edge, standing outdoors "
             "after dark",
}

ERA = ("a Taiwanese girl around nineteen, 2000 era Taipei ordinary-girl look, simple summer outfit, "
       "natural skin texture with visible pores, natural hair texture, head-and-shoulders portrait, "
       "facing the viewer")

# Fix pass v2 (issued after the c2136 board read: bone-age 14-17 instead of ~19, and night frames
# read waxy/over-smoothed). Both defects are prompt-level and belong at the generation station.
V2 = os.environ.get("XQ_CAST_V2") == "1"
FULL = os.environ.get("XQ_CAST_FULL") == "1"
if FULL:
    # 正档 stage: the two leading types from the c2136 v2 read, 1344x768, three seeds per light.
    V2 = True
if V2:
    ERA = ("a woman of about nineteen or twenty, first-year university student in 2000 era Taipei, "
           "mature facial structure with a defined jawline, calm confident bearing, simple summer outfit, "
           "natural skin texture with visible pores and subtle unevenness, natural hair texture, "
           "head-and-shoulders portrait, facing the viewer")
    LIGHTS["night"] = ("lit by practical warm street-lamp light with soft falloff against an indigo night sky, "
                       "film grain visible in the shadows, standing outdoors after dark")
    TYPES["A"] = TYPES["A"].replace("soft rounded cheeks", "soft rounded cheekbones", 1)
    OUTDIR = os.path.join(MEDIA, "xingqing", "xq-casting-c2136-full" if FULL else "xq-casting-c2136-v2")
    LOGDIR = os.path.join(MEDIA, "logs")
    PROG_PATH = os.path.join(OUTDIR, "xq_casting_c2136_%s_progress.json" % ("full" if FULL else "v2"))
    for d in (OUTDIR,):
        os.makedirs(d, exist_ok=True)
CLOSING = "35mm film grain, telecine texture, 2001 Taiwan music video look"

CANDS = []
for t in (("A", "B") if FULL else ("A", "B", "C", "D")):
    for light in ("dusk", "night"):
        for k in ((1, 2, 3) if FULL else ((1,) if V2 else (1, 2))):
            oid = "XQ-CAST-c2136%s-%s-%s-s%d" % ("full" if FULL else ("v2" if V2 else ""), t, light, k)
            CANDS.append((oid, t, light, seed_for(oid)))

RES = (1344, 768) if FULL else (672, 384)
ENDTOK = "CASTING-FULL-END" if FULL else ("CASTING-V2-END" if V2 else "CASTING-END")
RNAME = "xq-CASTING-RECEIPT-c2136%s.json" % ("-full" if FULL else ("-v2" if V2 else ""))
BNAME = "xq-CASTING-BOARD-c2136%s.jpg" % ("-full" if FULL else ("-v2" if V2 else ""))


def prompt_for(t, light):
    return "%s, %s, %s, %s." % (ERA, TYPES[t], LIGHTS[light], CLOSING)


# ---- lint: three lists (PROMPT-SPEC v1.3 sec-2), same rule set as the F5-33c runner ----
import re
NEG = re.compile(r"\b(no|not|never|without|avoid|non-)\b|don't|can't|won't|isn't|doesn't", re.I)
VAGUE = re.compile(r"\b(beautiful|stunning|aesthetic|masterpiece|8k|dreamy|ethereal|whimsical|cozy|"
                   r"glass skin|porcelain skin|airbrushed|vibrant|epic|photorealistic|iconic|"
                   r"cinematic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|idol|salon|makeup|watermark|typography|logo)\b", re.I)
for cid, t, light, seed in CANDS:
    pr = prompt_for(t, light)
    hits = sorted(set((NEG.findall(pr) or []) + (VAGUE.findall(pr) or []) + (CONCEPT.findall(pr) or [])))
    if hits:
        P("LINT FAIL %s: %r -- ABORT" % (cid, hits))
        print("LINT-FAIL", hits, flush=True)
        sys.exit(3)
if len(set(s for _, _, _, s in CANDS)) != len(CANDS):
    P("derived seed collision -- ABORT")
    print("SEED-COLLISION", flush=True)
    sys.exit(3)
P("lint zero-hit %d/%d; seeds unique %d/%d" % (len(CANDS), len(CANDS), len(set(s for _, _, _, s in CANDS)), len(CANDS)))

if os.environ.get("XQ_CASTING_DRY") == "1":
    for cid, t, light, seed in CANDS:
        P("DRY %s s%d: %s" % (cid, seed, prompt_for(t, light)))
    print("DRY-OK", flush=True)
    sys.exit(0)

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "burn", "done": {},
        "meta": {"wave": "xq-casting-c2136", "runner": "bm-c C2136",
                 "auth": "XQ casting CASE v1 (candidate board, GPU batch after MV V3)",
                 "res_mini": "672x384", "steps": 8, "cfg": 1.0, "jman": "omitted (male adapter)",
                 "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled",
                 "candidates": [c[0] for c in CANDS], "seeds": {c[0]: c[3] for c in CANDS}}}
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
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": ["10", 0], "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "xqCast"}},
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
P("queue empty 0/0 -- casting board start")


def burn(prompt, seed, out, w, h):
    resp = http(SERVER + "/prompt", {"prompt": graph(prompt, seed, w, h), "client_id": "bmc-xqCast"})
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


P("=== xq_casting_c2136 start %s pid=%d === candidates=%d res=%s" %
  (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid(), len(CANDS), str(RES)))
t_wave = time.time()
fails = []
ok_n = 0
for cid, t, light, seed in CANDS:
    out = os.path.join(OUTDIR, ("CAST_%s_%s_%s_s%d.png" % (t, TYPE_NAME[t], light, seed)))
    if PROG["done"].get(cid, {}).get("ok") or (os.path.isfile(out) and os.path.getsize(out) > 50000):
        ok_n += 1
        continue
    ok, err = burn(prompt_for(t, light), seed, out, RES[0], RES[1])
    PROG["done"][cid] = {"ok": ok, "file": os.path.basename(out) if ok else "", "err": err, "seed": seed}
    save_prog()
    P("[CAST] %s s%d %s (%.0fs)" % (cid, seed, "OK" if ok else "FAIL " + err, time.time() - t_wave))
    if ok:
        ok_n += 1
    else:
        fails.append(cid)

P("CASTING burns: ok=%d/%d fails=%s" % (ok_n, len(CANDS), ",".join(fails) or "none"))

# ---------------- contact board: 4 rows (types) x 4 cols (dusk s1, dusk s2, night s1, night s2) ----------
board_path = ""
try:
    from PIL import Image, ImageDraw
    tw, th = 448, 256
    per_row = {t: [(c, l, s) for c, tt, l, s in CANDS if tt == t] for t in ("A", "B", "C", "D")}
    cols = max(len(v) for v in per_row.values())
    rows = 4
    board = Image.new("RGB", (cols * tw + 20, rows * (th + 22) + 40), (24, 22, 20))
    dr = ImageDraw.Draw(board)
    for row, t in enumerate(("A", "B", "C", "D")):
        for col, (cid, light, seed) in enumerate(per_row[t]):
            x, y = 10 + col * tw, 30 + row * (th + 22)
            path = os.path.join(OUTDIR, ("CAST_%s_%s_%s_s%d.png" % (t, TYPE_NAME[t], light, seed)))
            if os.path.isfile(path):
                im = Image.open(path).convert("RGB").resize((tw - 8, th - 8))
                board.paste(im, (x + 4, y + 4))
            dr.text((x + 6, y + th + 2), "%s %s / %s / s%d" % (t, TYPE_NAME[t], light, seed), fill=(200, 180, 140))
        dr.text((10, 30 + row * (th + 22) - 14), "TYPE %s  %s" % (t, TYPE_NAME[t]), fill=(235, 215, 170))
    tag = " full-res A/B (1344x768, 3 seeds per light)" if FULL else (" v2 (age/skin fix pass)" if V2 else "  (cols: dusk s1 / dusk s2 / night s1 / night s2)")
    dr.text((10, 6), "XQ CASTING BOARD c2136" + tag, fill=(235, 215, 170))
    board_path = os.path.join(ALBUM, BNAME)
    board.save(board_path, quality=88)
    P("board -> %s (%dB)" % (board_path, os.path.getsize(board_path)))
except Exception as ex:
    P("board build failed (non-fatal, files on disk): %r" % ex)

receipt = {"wave": "xq-casting-c2136" + ("-full" if FULL else ("-v2" if V2 else "")), "runner": "bm-c C2136",
           "auth": "cph4/fleet/mv-album-001-jay/XQ casting CASE v1 -- candidate board, GPU batch after MV V3",
           "fix_pass": ("v2: bone age raised to 19-20 (first-year university student, defined jawline) and "
                        "night light switched to practical lamp with shadow grain, after the v1 board read "
                        "14-17 and waxy night skin") if V2 else "",
           "types": {t: TYPES[t] for t in TYPES},
           "lights": LIGHTS,
           "era_block": ERA, "closing": CLOSING,
           "params": {"res_mini": "672x384", "steps": 8, "cfg": 1.0, "jman": "omitted",
                      "sampler": "euler simple", "model": "krea2_turbo_fp8_scaled"},
           "candidates": [{"id": c, "type": t, "light": l, "seed": s} for c, t, l, s in CANDS],
           "burn_ok": {k: bool(v.get("ok")) for k, v in PROG["done"].items()},
           "stats": {"ok": ok_n, "total": len(CANDS), "fails": fails, "lint": "NEG/VAGUE/CONCEPT zero-hit"},
           "out_dir": "media/MV/mv0001/xingqing/xq-casting-c2136",
           "board": os.path.basename(board_path) if board_path else "",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
rpath = os.path.join(ALBUM, RNAME)
json.dump(receipt, io.open(rpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % rpath)
P("=== runner complete: ok %d/%d ===" % (ok_n, len(CANDS)))
print("%s ok=%d/%d fails=%s" % (ENDTOK, ok_n, len(CANDS), ",".join(fails) or "none"), flush=True)
print("%s ok=%d/%d fails=%s" % (ENDTOK, ok_n, len(CANDS), ",".join(fails) or "none"), file=LOG)
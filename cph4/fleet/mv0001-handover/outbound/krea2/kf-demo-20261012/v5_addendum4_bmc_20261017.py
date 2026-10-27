# -*- coding: utf-8 -*-
# v5_addendum4_bmc_20261017.py — V5 追加单 4 镜重烧 runner（@bm-c 交互窗·CEO O-20261017-1020 优先级最高）
# 正身: V5-REBURN-ADDENDUM-4shot-20261017.md（bm-a 导演席 09:0x 签发）+ V5-REBURN-SPEC-20261016.md
# D01/C04/E01c = 重做 KF（追加单新构图指令）·INT5 = 同 KF(s9910 审定) 只重烧 i2v（背线正锚+HOLD）
# 三阶段: --phase kf (6 KF: 3 镜 x 2 种子 9930/9931) -> --phase trial (4 x 480P INT4 低清验证·重烧禁盲烧)
#         -> --phase official (4 x INT8 768P 正片·min_duration>=5.0s 断言·同名覆盖 bmc/i2v/v5redo/)
# 铁律: ID 块逐字复用（load PACK 常量）·零否定零模糊 lint·音轨禁令（工作流零 audio 链）·detached 三件套
import os, sys, time, json, re, uuid, argparse, urllib.request, subprocess, importlib.util

if not sys.stdout:            # pythonw guard (10-14 law)
    sys.stdout = open(os.devnull, "w")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
MEDIA = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001"
V5DIR = os.path.join(MEDIA, "v5redo")
LOGDIR = os.path.join(MEDIA, "logs")
KFDIR = os.path.join(V5DIR, "kf_add4")
TRIALDIR = os.path.join(V5DIR, "trials_add4")
OUTDIR = os.path.join(BASE, "bmc", "i2v", "v5redo")
WF_480P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_480p_v4.json")
WF_768P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_768p_v4.json")
WINNERS = os.path.join(V5DIR, "add4_winners.json")
PROG_PATH = os.path.join(V5DIR, "v5_addendum4_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (LOGDIR, KFDIR, TRIALDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "v5_addendum4_bmc.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "v5_addendum4_bmc.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

ap = argparse.ArgumentParser(); ap.add_argument("--phase", required=True, choices=["kf", "trial", "official"])
args = ap.parse_args()
P("=== v5_addendum4 phase=%s start %s pid=%d ===" % (args.phase, time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid()))

def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

pk = load_mod(os.path.join(BASE, "V5-REDO-PACK-r1054.py"), "v5_pack")

# ---- 追加单四镜（D01/C04/E01c=新 KF 词面·INT5=复用审定 KF 只换 i2v 词面）----
D01_KF = ("A close-up over the shoulder at eye level of %s leaning over a wet clay tablet flat on the wooden work "
          "table, the tablet face large in the foreground carrying one half-finished row of large crisp cuneiform "
          "wedge marks, each sign a tight cluster of wedge strokes with clean triangular heads and tapering tails, "
          "thin ruled lines between the rows, the row ending in one last freshly cut sign with raw pale edges, his "
          "right hand holding the bronze chisel still at the row's end with his fingertip resting light on the "
          "carved marks, a wooden mallet resting clear of the chisel as two separate tools at the tablet's right "
          "side, the wall behind him plain unmarked workshop mudbrick dark in the candlelight, the workshop still "
          "around him, his profile at the frame edge. %s %s" % (pk.HIM_SCRIBE, pk.TORCH_RIM, pk.STYLE))
C04_KF = ("A close-up at eye level of one low register of large crisp fresh-cut cuneiform wedge marks across black "
          "basalt, each character a tight cluster of wedge-shaped strokes, every stroke a clean triangular head "
          "pressed wide into the stone with a long tapering tail, the signs arranged in one neat horizontal row "
          "separated by thin ruled lines, the raw cut edges pale and fresh as new carving, the row filling the "
          "frame like a line of new words in still warm light. %s %s" % (pk.UNSEEN_TORCH, pk.STYLE))
E01C_KF = ("A close-up at eye level of %s with his bronze chisel lifted clear of the black basalt wall and hovering "
           "mid-air, his wrist raised high with the chisel tip aimed at the next uncut mark, one finished row of "
           "fresh-cut wedge marks already carved in the stone behind the tip, the new cuts pale at their edges, "
           "warm raking torchlight tracing the chisel edge and his hand. %s %s" % (pk.HIM_SCRIBE, pk.TORCH_STELE, pk.STYLE))

SHOTS4 = {
    "D01_carver_words_v5": {"kf": D01_KF, "jman": True,  "seeds": (9930, 9931), "reuse": None},
    "C04_words_alive_v5":  {"kf": C04_KF, "jman": False, "seeds": (9930, 9931), "reuse": None},
    "E01c_first_line_v5":  {"kf": E01C_KF, "jman": True, "seeds": (9930, 9931), "reuse": None},
    "INT5_head_bow_v5":    {"kf": None, "jman": True, "seeds": (9910,), "reuse": os.path.join(V5DIR, "kf_r1054", "INT5_head_bow_v5_s9910.png")},
}
I2V4 = {
    "D01_carver_words_v5": ("Single continuous take at 24fps, 16:9. A close-up over the shoulder at eye level; the "
                            "camera holds a locked-off tripod frame while the chisel rests at the row's end, his "
                            "fingertip riding one slow pass across the fresh-cut marks, his gaze traveling the row "
                            "out past the frame edge. %s" % pk.I2V_TAIL),
    "C04_words_alive_v5": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a "
                            "near-static frame with only the warm light breathing slowly across the fresh-cut "
                            "strokes, fine dust motes drifting through the amber air. %s" % pk.I2V_TAIL),
    "E01c_first_line_v5": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a "
                           "locked-off tripod frame while the chisel tip hovers steady above the next uncut mark, "
                           "then one clean strike lands the cut, the chisel stopping dead at the stone for a held "
                           "beat, pale stone chips jumping and hanging in the torchlight, his breath easing out. %s"
                           % pk.I2V_TAIL),
    "INT5_head_bow_v5": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a "
                         "locked-off tripod frame while he sits tall with his gaze on the page, his shoulders "
                         "easing down a little and his head bowing slowly in a tired arc, the back line staying "
                         "long and upright the whole way, only his breath moving, then his eyes closing one slow "
                         "beat and opening again. %s" % pk.I2V_TAIL),
}
BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)
VAGUE = re.compile(r"\b(glowing|beautiful|stunning|dramatic|iconic|aesthetic)\b", re.I)
for sid, s in SHOTS4.items():
    for label, p in (("kf", s["kf"]), ("i2v", I2V4[sid])):
        if p is None:
            continue
        for rx, tag in ((BAD, "NEG"), (VAGUE, "VAGUE")):
            hits = rx.findall(p)
            assert not hits, "LINT-FAIL %s/%s %s: %s" % (sid, label, tag, hits)
assert os.path.isfile(SHOTS4["INT5_head_bow_v5"]["reuse"]), "INT5 approved KF missing"
P("pre-flight lint PASS (4 shots zero-neg zero-vague) + INT5 s9910 KF verified")

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "phase": args.phase,
        "kf": {}, "trial": {}, "official": {}}
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(open(PROG_PATH, encoding="utf-8-sig"))
        for k in ("kf", "trial", "official"):
            if isinstance(_old.get(k), dict):
                PROG[k] = _old[k]
        P("resumed: kf=%d trial=%d official=%d" % (len(PROG["kf"]), len(PROG["trial"]), len(PROG["official"])))
    except Exception as e:
        P("resume read fail (fresh): %r" % e)
def save_prog():
    PROG["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(PROG, open(PROG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
save_prog()

def http_json(url, payload=None, timeout=60):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def submit_retry(g, tag, retries=3):
    for att in range(1, retries + 1):
        try:
            return http_json(SERVER + "/prompt", {"prompt": g, "client_id": "bmc-add4"}, timeout=120).get("prompt_id")
        except Exception as ex:
            P("[%s] submit FAIL att%d: %r" % (tag, att, ex))
            time.sleep(45)
    return None

def kf_graph(prompt_text, seed, use_jman, prefix="v5add4"):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": ["20", 0] if use_jman else ["10", 0],
              "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }
    if use_jman:
        g["20"] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"lora_name": "jman_v1_640_rank32_final.safetensors",
                              "strength_model": 0.80, "model": ["10", 0]}}
    return g

def gen_kf(prompt, seed, use_jman, out_png, tag, timeout=900):
    if os.path.isfile(out_png) and os.path.getsize(out_png) > 100000:
        P("[%s] SKIP (exists)" % tag); return True
    pid = submit_retry(kf_graph(prompt, seed, use_jman), tag)
    if not pid:
        return False
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(5)
        try:
            h = http_json(SERVER + "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h.get(pid)
        if e is None:
            continue
        if e.get("status", {}).get("status_str") == "error":
            P("[%s] ERROR %s" % (tag, json.dumps(e["status"].get("messages", []))[:300]))
            return False
        for nid, out in e.get("outputs", {}).items():
            for im in out.get("images", []):
                if im["type"] == "output":
                    u = "%s/view?filename=%s&subfolder=%s&type=output" % (SERVER, im["filename"], im.get("subfolder", ""))
                    with urllib.request.urlopen(u, timeout=120) as r, open(out_png, "wb") as f:
                        f.write(r.read())
                    P("[%s] SAVED %s (%.1f min)" % (tag, os.path.basename(out_png), (time.time() - t0) / 60.0))
                    return True
        return False
    P("[%s] TIMEOUT" % tag)
    return False

def upload_frame(path):
    fn = os.path.basename(path)
    boundary = "----v5a" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + open(path, "rb").read() + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)

def duration_of(mp4):
    try:
        r = subprocess.run(["ffmpeg", "-i", mp4], capture_output=True, timeout=120)
        m = re.search(rb"Duration: (\d+):(\d+):([\d.]+)", (r.stderr or b"") + (r.stdout or b""))
        if not m:
            return 0.0
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        return 0.0

def _winner_seed(sid):
    w = json.load(open(WINNERS, encoding="utf-8-sig"))
    w2 = w.get("winners", w)
    return int(w2[sid]["seed"])

def winner_of(sid):
    s = SHOTS4[sid]
    if s["reuse"]:
        return s["reuse"]
    try:
        seed = _winner_seed(sid)
    except Exception as e:
        P("[winner] %s FAIL %r -- KF QC pending, abort this shot" % (sid, e))
        return None
    p = os.path.join(KFDIR, "%s_s%d.png" % (sid, seed))
    return p if os.path.isfile(p) else None

def burn_i2v(sid, wf_path, w, h, out_mp4, tag, timeout):
    if os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 200000 and duration_of(out_mp4) >= 5.0:
        P("[%s] SKIP (exists+contract-ok)" % tag); return True
    kf = winner_of(sid)
    if not kf or not os.path.isfile(kf):
        P("[%s] KF-MISSING %s" % (tag, kf)); return False
    seed = SHOTS4[sid]["seeds"][0] if SHOTS4[sid]["reuse"] else None
    if seed is None:
        try:
            seed = _winner_seed(sid)
        except Exception:
            P("[%s] winners missing -- KF QC pending" % tag); return False
    img = upload_frame(kf)
    wf = json.load(open(wf_path, encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = I2V4[sid]; n6["length"] = 124; n6["width"] = w; n6["height"] = h
    wf["10"]["inputs"]["noise_seed"] = seed
    pid = submit_retry(wf, tag)
    if not pid:
        return False
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(15)
        try:
            h2 = http_json(SERVER + "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h2.get(pid)
        if e is None:
            if int(time.time() - t0) % 300 < 20:
                P("[%s] %4ds running..." % (tag, time.time() - t0))
            continue
        if e.get("status", {}).get("status_str") == "error":
            P("[%s] ERROR %s" % (tag, json.dumps(e["status"].get("messages", []))[:300]))
            return False
        for nid, out in e.get("outputs", {}).items():
            for vid in (out.get("gifs") or []) + (out.get("videos") or []) + (out.get("images") or []):
                u = "%s/view?filename=%s&subfolder=%s&type=%s" % (SERVER, vid["filename"], vid.get("subfolder", ""), vid.get("type", "output"))
                open(out_mp4, "wb").write(urllib.request.urlopen(u, timeout=300).read())
                dur = duration_of(out_mp4); sz = os.path.getsize(out_mp4)
                okc = dur >= 5.0 and sz > 200000
                P("[%s] SAVED %s dur=%.2fs size=%dB contract=%s (%.1f min)" % (tag, os.path.basename(out_mp4), dur, sz, "OK" if okc else "FAIL", (time.time() - t0) / 60.0))
                return okc
        return False
    P("[%s] TIMEOUT" % tag)
    return False

if args.phase == "kf":
    P("--- Phase KF: 3 shots x 2 seeds ---")
    for sid, s in SHOTS4.items():
        if s["kf"] is None:
            P("[kf] %s reuses approved KF -- skip" % sid)
            continue
        for seed in s["seeds"]:
            tag = "%s_s%d" % (sid, seed)
            if PROG["kf"].get(tag, {}).get("ok"):
                continue
            try:
                ok = gen_kf(s["kf"], seed, s["jman"], os.path.join(KFDIR, tag + ".png"), tag)
            except Exception as e:
                P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
            PROG["kf"][tag] = {"ok": ok, "ts": time.strftime("%H:%M:%S")}
            save_prog()
    P("Phase KF done: %d/%d ok" % (sum(1 for v in PROG["kf"].values() if v.get("ok")), len(PROG["kf"]) or 6))

elif args.phase == "trial":
    P("--- Phase trial: 4 x 480P INT4 (low-res verification per CEO law) ---")
    for sid in SHOTS4:
        tag = sid + "_t480"
        if PROG["trial"].get(sid, {}).get("ok"):
            continue
        try:
            ok = burn_i2v(sid, WF_480P, 864, 480, os.path.join(TRIALDIR, sid + "_t480.mp4"), tag, 1800)
        except Exception as e:
            P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
        PROG["trial"][sid] = {"ok": ok, "ts": time.strftime("%H:%M:%S")}
        save_prog()
    P("Phase trial done: %d/4 ok" % sum(1 for v in PROG["trial"].values() if v.get("ok")))

elif args.phase == "official":
    P("--- Phase official: 4 x 768P INT8 (overwrite bmc/i2v/v5redo/) ---")
    for sid in SHOTS4:
        tag = sid + "_p768"
        if PROG["official"].get(sid, {}).get("ok"):
            continue
        try:
            ok = burn_i2v(sid, WF_768P, 1344, 768, os.path.join(OUTDIR, sid + ".mp4"), tag, 2400)
        except Exception as e:
            P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
        PROG["official"][sid] = {"ok": ok, "ts": time.strftime("%H:%M:%S")}
        save_prog()
    P("Phase official done: %d/4 ok" % sum(1 for v in PROG["official"].values() if v.get("ok")))

PROG["stage"] = args.phase + "_done"
save_prog()
P("=== v5_addendum4 phase=%s complete ===" % args.phase)

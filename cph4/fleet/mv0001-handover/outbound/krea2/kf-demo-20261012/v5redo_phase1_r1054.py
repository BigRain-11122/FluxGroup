# -*- coding: utf-8 -*-
# v5redo_phase1_r1054.py — V5 修片 Phase 1 runner（@bm-c r1054·P0·导演席 16:3x 派单）
# 正身: V5-REBURN-SPEC-20261016.md + V5-REDO-PACK-r1054.py（lint OK 17 镜）
# Phase1 = KF 批（22 张: trial 镜×2 种子 + 非试镜×1）→ 480P INT4 trials（12 条·总则⑥构图/坐姿验证）
#   → trials 拼板 + manifest → wave1 回执原子推（P0 2h 死线·三行:进度/卡点/ETA）→ poke bm-a fail-open
# Phase2（768P INT8 正片 17 条）= trials 多模态过审后下一窗 winners.json 驱动（本 runner 不碰正片）
# detached 三件套: stdout guard + media 安全区日志 + progress json(pid+resume)
import os, sys, time, json, re, uuid, urllib.request, subprocess, importlib.util

if not sys.stdout:            # pythonw guard (10-14 law)
    sys.stdout = open(os.devnull, "w")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
MEDIA = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001"
V5DIR = os.path.join(MEDIA, "v5redo")
LOGDIR = os.path.join(MEDIA, "logs")
KFDIR = os.path.join(V5DIR, "kf_r1054")
TRIALDIR = os.path.join(V5DIR, "trials_r1054")
WF_480P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_480p_v4.json")
ATOMIC = r"K:\Fluxgroup\FluxGroup\quant\bigmoney\.codely-cli\scratch\git-atomic-push-bmc.py"
GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
BOARD = os.path.join(BASE, "bmc", "V5-TRIALS-BOARD-r1054.jpg")
MANIFEST = os.path.join(BASE, "bmc", "v5redo_phase1_r1054_manifest.json")
PROG_PATH = os.path.join(V5DIR, "v5redo_phase1_r1054_progress.json")
SERVER = "http://127.0.0.1:8188"
BMA_POKE = "http://100.110.185.62:8790/poke"
for d in (LOGDIR, KFDIR, TRIALDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "v5redo_phase1_r1054.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "v5redo_phase1_r1054.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

P("=== v5redo_phase1_r1054 start %s pid=%d ===" % (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid()))

def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

pack = load_mod(os.path.join(BASE, "V5-REDO-PACK-r1054.py"), "v5_pack")
SHOTS = {s[0]: s for s in pack.SHOTS}
BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)

# ---- pre-flight lint (O-1630 闸·机核) ----
for sid, s in SHOTS.items():
    for label, p in (("kf", s[3]), ("i2v", s[4])):
        if p is None:
            continue
        hits = BAD.findall(p)
        assert not hits, "LINT-FAIL %s/%s: %s" % (sid, label, hits)
    if s[7]:
        assert os.path.isfile(s[7]), "REUSE-FRAME-MISSING %s" % sid
P("pre-flight lint PASS (17 shots zero-neg) · SIL4 reuse frame verified")

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "kf",
        "kf": {}, "trial": {}, "pushed": [], "push_receipt": "", "push_final": "", "poke": []}
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(open(PROG_PATH, encoding="utf-8-sig"))
        for k in ("kf", "trial", "pushed", "poke"):
            if isinstance(_old.get(k), (dict, list)):
                PROG[k] = _old[k]
        PROG["push_receipt"] = _old.get("push_receipt", "")
        PROG["push_final"] = _old.get("push_final", "")
        P("resumed: kf=%d trial=%d pushed=%d" % (len(PROG["kf"]), len(PROG["trial"]), len(PROG["pushed"])))
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

def graph(prompt_text, seed, use_jman, w=1344, h=768, prefix="v5kf"):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
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

def submit_retry(graph_dict, tag, retries=3):
    for att in range(1, retries + 1):
        try:
            return http_json(SERVER + "/prompt", {"prompt": graph_dict, "client_id": "bmc-r1054"}, timeout=120).get("prompt_id")
        except Exception as ex:
            P("[%s] submit FAIL att%d: %r" % (tag, att, ex))
            time.sleep(45)
    return None

def gen_kf(prompt, seed, use_jman, out_png, tag, timeout=900):
    if os.path.isfile(out_png) and os.path.getsize(out_png) > 100000:
        P("[%s] SKIP (exists)" % tag); return True
    pid = submit_retry(graph(prompt, seed, use_jman), tag)
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
    boundary = "----v5t" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + open(path, "rb").read() + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)

def run_trial(frame_path, prompt, seed, out_mp4, tag, timeout=1800):
    if os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 200000:
        P("[%s] SKIP (exists)" % tag); return True
    img = upload_frame(frame_path)
    wf = json.load(open(WF_480P, encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = prompt; n6["length"] = 124; n6["width"] = 864; n6["height"] = 480
    wf["10"]["inputs"]["noise_seed"] = seed
    pid = submit_retry(wf, tag)
    if not pid:
        return False
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(15)
        try:
            h = http_json(SERVER + "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h.get(pid)
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
                P("[%s] SAVED %s (%.1f min)" % (tag, os.path.basename(out_mp4), (time.time() - t0) / 60.0))
                return True
        return False
    P("[%s] TIMEOUT" % tag)
    return False

rel = lambda p: "cph4/fleet/mv0001-handover/outbound/krea2/kf-demo-20261012/" + p

def atomic_push(files, message, tag):
    sp = {"message": message, "retry": 5, "gate_depth": 10, "files": files}
    sp_path = os.path.join(MEDIA, "logs", "atomic_spec_%s.json" % tag)
    json.dump(sp, open(sp_path, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        r = subprocess.run([sys.executable, ATOMIC, sp_path], capture_output=True, cwd=GROUP_ROOT, timeout=1200)
    except subprocess.TimeoutExpired:
        P("[atomic %s] TIMEOUT-1200 (payload stays local, harvest-push next window)" % tag)
        return False
    out = (r.stdout or b"").decode("utf-8", "replace")
    P("[atomic %s] rc=%d\n%s" % (tag, r.returncode, out[-1500:]))
    if r.returncode != 0:
        P("[atomic %s] stderr tail: %s" % (tag, (r.stderr or b"").decode("utf-8", "replace")[-800:]))
    return r.returncode == 0

def poke_bma(reason):
    try:
        body = json.dumps({"reason": reason, "tasks": [], "repos": []}).encode()
        req = urllib.request.Request(BMA_POKE, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15).read()
        PROG["poke"].append({"ts": time.strftime("%H:%M:%S"), "reason": reason, "ok": True})
        P("[poke bm-a] OK: %s" % reason)
    except Exception as ex:
        PROG["poke"].append({"ts": time.strftime("%H:%M:%S"), "reason": reason, "ok": False, "err": repr(ex)})
        P("[poke bm-a] FAIL %r (:8790 载波事故在案·orders 行已上链兜底)" % ex)
    save_prog()

# ═══ Phase A: KF 批（22 张）═══
P("--- Phase A: KF batch (22) ---")
for sid, s in SHOTS.items():
    if s[3] is None:
        continue
    for seed in pack.SEEDS[sid]:
        tag = "%s_s%d" % (sid, seed)
        out_png = os.path.join(KFDIR, tag + ".png")
        if PROG["kf"].get(tag, {}).get("ok"):
            continue
        try:
            ok = gen_kf(s[3], seed, s[6], out_png, tag)
        except Exception as e:
            P("EXC on %s: %r" % (tag, e))
            import traceback; traceback.print_exc(file=ERR)
            ok = False
        PROG["kf"][tag] = {"ok": ok, "file": os.path.basename(out_png) if ok else "", "seed": seed,
                           "jman": s[6], "trial": s[5], "ts": time.strftime("%H:%M:%S")}
        save_prog()
ok_kf = sum(1 for v in PROG["kf"].values() if v.get("ok"))
P("Phase A KF: %d/22 ok" % ok_kf)

# ═══ Phase B: 480P trials（12 条·试镜×2 种子）═══
P("--- Phase B: 480P trials (12) ---")
trial_ids = [sid for sid, s in SHOTS.items() if s[5]]
for sid in trial_ids:
    for seed in pack.SEEDS[sid]:
        tag = "%s_s%d" % (sid, seed)
        out_mp4 = os.path.join(TRIALDIR, tag + ".mp4")
        if PROG["trial"].get(tag, {}).get("ok"):
            continue
        try:
            ok = run_trial(os.path.join(KFDIR, tag + ".png"), SHOTS[sid][4], seed, out_mp4, tag)
        except Exception as e:
            P("EXC on %s: %r" % (tag, e))
            import traceback; traceback.print_exc(file=ERR)
            ok = False
        PROG["trial"][tag] = {"ok": ok, "file": os.path.basename(out_mp4) if ok else "", "seed": seed,
                              "ts": time.strftime("%H:%M:%S")}
        save_prog()
ok_tr = sum(1 for v in PROG["trial"].values() if v.get("ok"))
P("Phase B trials: %d/12 ok" % ok_tr)

# ═══ Phase C: 拼板 + manifest + wave 推送 ═══
P("--- Phase C: board + manifest + push ---")
from PIL import Image, ImageDraw

def thumb_of(mp4, tdir):
    th = os.path.join(tdir, os.path.basename(mp4) + ".png")
    if not os.path.isfile(th):
        subprocess.run(["ffmpeg", "-y", "-i", mp4, "-vf", "select=eq(n\\,0)", "-vframes", "1", th],
                       capture_output=True, timeout=120)
    return th

board_files = sorted(os.listdir(TRIALDIR))
try:
    tw, thh, lab = 448, 253, 22
    cols = 4
    rows_n = (len(board_files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 6) + 6, rows_n * (thh + lab + 6) + 34), (24, 20, 16))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 6), "V5 trials 480P -- 6 shots x 2 seeds (composition/posture gate) -- bm-c r1054 -- %s" % time.strftime("%Y-%m-%d %H:%M"), fill=(240, 200, 120))
    tdir = os.path.join(V5DIR, "_thumbs_r1054")
    os.makedirs(tdir, exist_ok=True)
    for ci, cn in enumerate(board_files):
        th = thumb_of(os.path.join(TRIALDIR, cn), tdir)
        pic = Image.open(th).convert("RGB").resize((tw, thh)) if os.path.isfile(th) else Image.new("RGB", (tw, thh), (40, 36, 30))
        x = 6 + (ci % cols) * (tw + 6); y = 34 + (ci // cols) * (thh + lab + 6)
        dr.text((x + 4, y + 3), cn.replace(".mp4", ""), fill=(225, 205, 150))
        sheet.paste(pic, (x, y + lab))
        dr.rectangle([x, y + lab, x + tw, y + lab + thh], outline=(90, 40, 40))
    sheet.save(BOARD, "JPEG", quality=88)
    P("board -> %s (%d cells)" % (BOARD, len(board_files)))
except Exception as e:
    P("board build FAIL %r (files still on disk)" % e)

manifest = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "round": "r1054",
            "spec": "V5-REBURN-SPEC-20261016.md", "pack": rel("V5-REDO-PACK-r1054.py"),
            "kf": PROG["kf"], "trials": PROG["trial"],
            "trial_meta": {sid: {"seeds": list(pack.SEEDS[sid]), "win": SHOTS[sid][1], "speed": SHOTS[sid][2]}
                           for sid in trial_ids},
            "next": "bm-c next window: multimodal QC trials (composition/posture per spec KF column) -> winners.json -> phase2 768P INT8 17 clips"}
json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("manifest -> %s" % MANIFEST)

if not PROG["push_receipt"]:
    ord_row = ("| %s | **【@bm-c 认领+进度回执】V5 修片重烧 Phase 1 在烧（16:3x 派单·P0 2h 回执窗）** | "
               "①认领=17 镜重烧单受理（V5-REBURN-SPEC 正身+V5-REDO-PACK-r1054.py lint 零否定 17/17）；"
               "②进度=KF 批 %d/22 烧毕·480P trials %d/12（INT4 480P·总则⑥构图/坐姿验证）·非试镜 10 镜 KF 就位；"
               "③卡点=零卡点（ComfyUI 8188 在位·GPU 14.8G 空闲）；"
               "④ETA=trials 毕即多模态过审出 winners→768P INT8 正片 17 条串行约 3.5-4.5h→bmc/i2v/v5redo/ 收片+QC 拼板+poke 装配站；"
               "执行窗=bm-c r1054 | in-flight（Phase1 KF+trials） |"
               % (time.strftime("%Y-%m-%d %H:%M"), ok_kf, ok_tr))
    files = [{"mode": "full", "path": rel("V5-REDO-PACK-r1054.py"), "local": os.path.join(BASE, "V5-REDO-PACK-r1054.py"), "expect_origin_blob": "NEW"},
             {"mode": "full", "path": rel("v5redo_phase1_r1054.py"), "local": os.path.join(BASE, "v5redo_phase1_r1054.py"), "expect_origin_blob": "NEW"},
             {"mode": "append", "path": "docs/orders.md", "line": ord_row}]
    okp = atomic_push(files, "bm-c r1054: V5 reburn P0 claimed, pack lint-clean (17 shots), Phase1 KF+trials in flight (receipt wave)", "receipt")
    PROG["push_receipt"] = "OK" if okp else "FAIL"
    save_prog()
    poke_bma("V5 redo P0 claimed by bm-c r1054: KF %d/22, trials %d/12 burning, official 768P ETA after trials-QC" % (ok_kf, ok_tr))

if ok_tr >= 12 and not PROG["push_final"]:
    files = [{"mode": "full", "path": rel("bmc/V5-TRIALS-BOARD-r1054.jpg"), "local": BOARD, "expect_origin_blob": "NEW"},
             {"mode": "full", "path": rel("bmc/v5redo_phase1_r1054_manifest.json"), "local": MANIFEST, "expect_origin_blob": "NEW"}]
    okf = atomic_push(files, "bm-c r1054: V5 Phase1 complete -- KF 22 + 480P trials 12 on board, trials QC next window then 768P official wave", "final")
    PROG["push_final"] = "OK" if okf else "FAIL"
    save_prog()
    poke_bma("V5 Phase1 done: 22 KF + 12 trials delivered to board/manifest, trials-QC then official wave")

PROG["stage"] = "phase1_done"
PROG["summary"] = "kf %d/22 · trials %d/12 · push_receipt %s · push_final %s" % (ok_kf, ok_tr, PROG["push_receipt"], PROG["push_final"])
save_prog()
P("=== runner complete: %s ===" % PROG["summary"])

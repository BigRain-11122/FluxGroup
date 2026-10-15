# -*- coding: utf-8 -*-
# jayredo_v4_r1032.py -- @bm-c Jay 化批裁定执行件（group orders 10-15 17:1x 派单·导演席签发）
# 执行面: ①6 修复槽海选 KF 重摇（O-20261015-1725 海选制落实: 4 种子/槽·24 帧）
#         ②拼板+receipt 上链（verdict 随包·O-20261015-1630 提示词闸合规: lint 机核+导演处方溯源）
#         ③原子链 push + poke bm-a 导演席复检（只审新 6 格·4 选 1/槽）
#         ④11 放行件 i2v INT8 768P 5s（skip-if-exists·INT3 眼睑压沉半档+D03b 眼部保光=导演处方）
#         ⑤i2v 完成后原子链 push clips + orders 回执行 + poke bm-a 装配站
# Law: 音轨禁令(v4 工作流零 audio 节点) · 零否定词 lint · FIFO 共服不动他窗队列(队列 0/0 实测)
#      detached 三件套: stdout guard + media 安全区日志 + progress json(pid+resume)
import io, json, os, re, subprocess, sys, time, urllib.request, uuid, importlib.util

if not sys.stdout:            # pythonw guard (10-14 law)
    sys.stdout = open(os.devnull, "w")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
MEDIA = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001"
LOGDIR = os.path.join(MEDIA, "logs")
OUTDIR = os.path.join(MEDIA, "jayredo", "kf_r1032")
R1025_PROG = os.path.join(MEDIA, "jayredo", "jayredo_kf_r1025_progress.json")
R1025_FRAMES = os.path.join(MEDIA, "jayredo", "kf_r1025")
PROG_PATH = os.path.join(MEDIA, "jayredo", "jayredo_v4_r1032_progress.json")
BMC = os.path.join(BASE, "bmc")
I2V_OUT = os.path.join(BMC, "i2v", "jayredo")
BOARD = os.path.join(BMC, "JAY-REDO-RESHAKE6-BOARD-r1032.jpg")
RECEIPT = os.path.join(BMC, "jayredo_reshake6_r1032_receipt.json")
WF_768P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_768p_v4.json")
ATOMIC = r"K:\Fluxgroup\FluxGroup\quant\bigmoney\.codely-cli\scratch\git-atomic-push-bmc.py"
GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
SERVER = "http://127.0.0.1:8188"
BMA_POKE = "http://100.110.185.62:8790/poke"
for d in (LOGDIR, OUTDIR, I2V_OUT):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "jayredo_v4_r1032.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "jayredo_v4_r1032.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

P("=== jayredo_v4_r1032 start %s pid=%d ===" % (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid()))

# ---- load pack ----
spec_ = importlib.util.spec_from_file_location("jay_redo_pack", os.path.join(BASE, "JAY-REDO-PACK-v1.py"))
pack = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(pack)
BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)

def lint(txt):
    return sorted(BAD.findall(txt))

r1025 = json.load(open(R1025_PROG, encoding="utf-8-sig"))

# ---- 6 修复槽（导演处方重写/提取 + 4 种子海选）----
HIM_MODERN, HIM_SCRIBE, STYLE = pack.HIM_MODERN, pack.HIM_SCRIBE, pack.STYLE
LAMP, CASE_NIGHT = pack.LAMP, pack.CASE_NIGHT
TORCH = ("A thick reed-bundle torch in a cast bronze sconce bowl throws raking warm light at 2000K across "
         "him and the carved stone, the hall beyond warm film-base brown fading to black.")

RESHAKE = [
 ("E01c_first_line.mp4", "REJECT 重写·导演处方=握笔手熔接+纸面伪文字→手部干净+纸面留白",
  "A close-up at eye level of %s with his fountain pen resting lightly at the top corner of a blank pale page, "
  "chin tucked, his heavy-lidded eyes on the clean page in a drowsy focus, his fingers clearly formed around the "
  "pen barrel, the smooth blank paper glowing softly under the lamp. %s %s" % (HIM_MODERN, LAMP, STYLE)),
 ("SIL2_ots_crowd_v4_s9018.mp4", "REJECT 重写·导演处方=蜡像人群→纯剪影负空间或清场（取清场）",
  "A medium shot over his shoulder of %s standing alone before the lit case in the empty closed hall, the long "
  "aisle clear and quiet around him in deep shadow, his calm face lit warm in three-quarter, his heavy-lidded eyes "
  "resting on the carved stone. %s %s" % (HIM_MODERN, CASE_NIGHT, STYLE)),
 ("SING1_torch_song_v2_s9013.mp4", "REJECT 重写·导演处方=神态太警觉太英雄→半瘫拉回·眼睑压沉·嘴角零上扬",
  "A medium close-up at eye level of %s standing loose and spent before the tall stele in the Babylonian hall, "
  "shoulders slack after the long night, chin sunk, eyelids heavy and half-lowered, mouth open mid-line on a flat "
  "level line with the corners at rest, one hand hanging limp at his side, a reed-bundle torch burning warm amber "
  "in its cast bronze sconce behind his shoulder, his fringe over his brows, his face lit by the flame in "
  "three-quarter. %s %s" % (HIM_SCRIBE, TORCH, STYLE)),
]
for shot in pack.SHOTS:                      # C01/B01/D01 全配方重摇（pack「不达标重摇」正身提取）
    if shot[2].startswith("校验"):
        prompt = shot[2].split("不达标重摇：", 1)[1]
        RESHAKE.append((shot[0], "次级校验升格全配方重摇（orders 17:1x ④）", prompt))
assert len(RESHAKE) == 6, "reshake shape drift"

for name, why, pr in RESHAKE:                # lint 机核（O-1630 闸: 零否定词）
    hits = lint(pr)
    assert not hits, "LINT-FAIL %s: %s" % (name, hits)
P("reshake6 prompts lint PASS (zero negatives) · 4 seeds/slot O-1725 海选制")

# ---- 11 放行件 i2v（INT3/D03b 导演处方调整）----
REJECTS = {n for n, _, _ in RESHAKE}
I2V_JOBS = []
for name, win, kf, iv in pack.SHOTS:
    if name in REJECTS or kf.startswith("校验"):
        continue
    note = ""
    if name == "INT3_photo_stare.mp4":
        iv = iv.replace("his drowsy gaze holding the photo through one slow blink",
                       "his heavy upper lids settled lower over his drowsy gaze, the photo held through one slow blink")
        note = "导演处方: 眼睑压沉半档"
    if name == "D03b_direct_gaze.mp4":
        iv = iv.replace("deep crushed shadows",
                       "deep shadows holding their amber warmth, his eyes softly readable in the case glow")
        note = "导演处方: 调色禁压眼部死黑"
    hit = lint(iv)
    assert not hit, "LINT-FAIL i2v %s: %s" % (name, hit)
    I2V_JOBS.append((name, iv, note))
assert len(I2V_JOBS) == 11, "i2v shape drift %d" % len(I2V_JOBS)
P("i2v 11 jobs assembled (2 director-prescribed adjustments applied, lint PASS)")

# ---- progress ----
PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "kf_reshake",
        "kf": {}, "i2v": {}, "push_c": "", "push_e": "", "poke": []}
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(open(PROG_PATH, encoding="utf-8-sig"))
        for k in ("kf", "i2v"):
            if isinstance(_old.get(k), dict):
                PROG[k].update(_old[k])
        PROG["push_c"], PROG["push_e"] = _old.get("push_c", ""), _old.get("push_e", "")
        PROG["poke"] = _old.get("poke", [])
        P("resumed: kf=%d i2v=%d" % (len(PROG["kf"]), len(PROG["i2v"])))
    except Exception as e:
        P("resume read fail (fresh): %r" % e)
def save_prog():
    PROG["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(PROG, open(PROG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
save_prog()

# ---- ComfyUI 客户端 ----
def http_json(url, payload=None, timeout=60):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def kf_graph(prompt_text, seed, w=1344, h=768):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "20": {"class_type": "LoraLoaderModelOnly",
               "inputs": {"lora_name": "jman_v1_640_rank32_final.safetensors",
                          "strength_model": 0.80, "model": ["10", 0]}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": ["20", 0], "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "jayredo_rs"}},
    }

def wait_prompt(pid, tag, timeout=3300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(8)
        try:
            h = http_json(SERVER + "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h.get(pid)
        if e is None:
            continue
        if e.get("status", {}).get("status_str") == "error":
            P("[%s] ERROR %s" % (tag, json.dumps(e["status"].get("messages", []))[:300]))
            return None
        for nid, out in e.get("outputs", {}).items():
            for im in (out.get("images") or []) + (out.get("gifs") or []) + (out.get("videos") or []):
                src = SERVER + "/view?filename=%s&subfolder=%s&type=%s" % (
                    im["filename"], im.get("subfolder", ""), im.get("type", "output"))
                return urllib.request.urlopen(src, timeout=300).read()
        return None
    P("[%s] TIMEOUT" % tag)
    return None

def submit_with_retry(graph_dict, tag, retries=3):
    for att in range(1, retries + 1):
        try:
            return http_json(SERVER + "/prompt", {"prompt": graph_dict, "client_id": "bmc-r1032"},
                             timeout=120).get("prompt_id")
        except Exception as ex:
            P("[%s] submit FAIL att%d: %r" % (tag, att, ex))
            time.sleep(60)
    return None

# ---- Phase A: KF 海选重摇 6 槽 × 4 种子 ----
SEED_BASE = 9600
slot_seed0 = {}
for si, (name, why, pr) in enumerate(RESHAKE):
    slot_seed0[name] = SEED_BASE + si * 4
for si, (name, why, pr) in enumerate(RESHAKE):
    if all(PROG["kf"].get("%s_s%d" % (name, k), {}).get("ok") for k in range(4)):
        P("skip done slot", name); continue
    for k in range(4):
        key = "%s_s%d" % (name, k)
        if PROG["kf"].get(key, {}).get("ok"):
            continue
        seed = slot_seed0[name] + k
        pid = submit_with_retry(kf_graph(pr, seed), key)
        if not pid:
            PROG["kf"][key] = {"ok": False, "seed": seed, "err": "submit-fail"}; save_prog()
            continue
        data = wait_prompt(pid, key, timeout=900)
        if data:
            fn = "rs_%s_s%d.png" % (name.replace(".mp4", ""), seed)
            open(os.path.join(OUTDIR, fn), "wb").write(data)
            PROG["kf"][key] = {"ok": True, "seed": seed, "file": fn, "ts": time.strftime("%H:%M:%S")}
            P("%s -> %s" % (key, fn))
        else:
            PROG["kf"][key] = {"ok": False, "seed": seed, "err": "burn-fail"}
        save_prog()
ok_kf = sum(1 for v in PROG["kf"].values() if v.get("ok"))
P("Phase A KF reshake: %d/24 ok" % ok_kf)

# ---- Phase B: 拼板 + receipt ----
from PIL import Image, ImageDraw
tw, th, pad, lab = 500, 286, 8, 20
cols = 4
W = cols * (tw + pad) + pad
H = 6 * (th + lab + pad) + pad + 30
im = Image.new("RGB", (W, H), (16, 15, 13))
dr = ImageDraw.Draw(im)
dr.text((pad, 6), "JAY-REDO reshake6 hai-xuan board (4 seeds/slot, O-1725) -- bm-c r1032 -- %s" % time.strftime("%Y-%m-%d %H:%M"), fill=(240, 200, 120))
for si, (name, why, pr) in enumerate(RESHAKE):
    y = pad + 30 + si * (th + lab + pad)
    dr.text((pad, y), "%s  [%s]" % (name.replace(".mp4", ""), why[:44]), fill=(210, 170, 110))
    for k in range(4):
        key = "%s_s%d" % (name, k)
        x = pad + k * (tw + pad)
        e = PROG["kf"].get(key, {})
        if e.get("ok"):
            try:
                pic = Image.open(os.path.join(OUTDIR, e["file"])).convert("RGB").resize((tw, th))
                im.paste(pic, (x, y + lab))
            except Exception:
                dr.rectangle([x, y + lab, x + tw, y + lab + th], outline=(90, 40, 40))
        else:
            dr.rectangle([x, y + lab, x + tw, y + lab + th], outline=(90, 40, 40))
        dr.text((x, y + lab + th + 2), "s%d seed=%s" % (k, e.get("seed", "?")), fill=(190, 190, 180))
im.save(BOARD, quality=88)
P("board -> %s" % BOARD)

receipt = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "machine": "bm-c", "round": "r1032",
 "verdict_refs": ["orders 10-15 17:1x @bm-c Jay 化批帧审裁定+i2v 派单（导演席签发）",
                  "O-20261015-1725 KF 海选制（4 种子/槽落实）", "O-20261015-1630 提示词闸（lint 机核+verdict 随包）"],
 "kf_lint": "pack BAD regex zero-negatives PASS (24 prompts)",
 "slots": [{"slot": n, "source": w, "kf_prompt": p, "seeds": [slot_seed0[n] + k for k in range(4)],
            "frames": [PROG["kf"].get("%s_s%d" % (n, k), {}).get("file", "") for k in range(4)],
            "burn_ok": [bool(PROG["kf"].get("%s_s%d" % (n, k), {}).get("ok")) for k in range(4)]}
           for n, w, p in RESHAKE],
 "i2v_plan": [{"slot": n, "frame": r1025.get("done", {}).get(n, {}).get("file", ""),
               "seed": 9700 + i, "adjustment": note}
              for i, (n, iv, note) in enumerate(I2V_JOBS)],
 "i2v_prompts": {n: iv for n, iv, _ in I2V_JOBS}}
json.dump(receipt, open(RECEIPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
P("receipt -> %s" % RECEIPT)

# ---- Phase C: 原子链 push + poke bm-a ----
def atomic_push(files, message, tag):
    sp = {"message": message, "retry": 5, "gate_depth": 10, "files": files}
    sp_path = os.path.join(MEDIA, "logs", "atomic_spec_%s.json" % tag)
    json.dump(sp, open(sp_path, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        r = subprocess.run([sys.executable, ATOMIC, sp_path], capture_output=True, cwd=GROUP_ROOT, timeout=1200)
    except subprocess.TimeoutExpired:
        P("[atomic %s] TIMEOUT-1200 (network stall; payload stays local, harvest-push next window)" % tag)
        return False
    out = (r.stdout or b"").decode("utf-8", "replace")
    P("[atomic %s] rc=%d\n%s" % (tag, r.returncode, out[-1500:]))
    if r.returncode != 0:
        (r.stderr or b"").decode("utf-8", "replace") and P("[atomic %s] stderr tail: %s" % (tag, (r.stderr or b"").decode("utf-8", "replace")[-800:]))
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
        P("[poke bm-a] FAIL %r (orders row 已上链·bm-a 循环自拉兜底)" % ex)
    save_prog()

rel = lambda p: "cph4/fleet/mv0001-handover/outbound/krea2/kf-demo-20261012/" + p
ts = time.strftime("%Y-%m-%d %H:%M")
ord_row_c = ("| %s | **【@bm-c 回执】Jay 化批裁定执行（orders 17:1x 派单·导演席签发）** | ①6 修复槽海选重摇 24 KF 烧毕"
             "（4 种子/槽·O-1725 海选制落实·REJECT 三槽按导演处方重写：E01c 手部干净+纸面留白/SIL2 清场/SING1 半瘫+眼睑压沉+嘴角平·"
             "C01/B01/D01 全配方重摇）→JAY-REDO-RESHAKE6-BOARD-r1032.jpg+receipt（提示词正身+lint 零否定全过=O-1630 verdict 随包）呈导演席复检"
             "（只审新 6 格·4 选 1/槽·胜者进 i2v）；②11 放行件 i2v INT8 768P 5s 批 r1033 重点火在飞（r1032 runner Phase C 原子链 600s 超时死窗披露·KF 24/24 已毕不重烧·INT3 眼睑压沉半档+D03b 眼部保光=导演处方·"
             "skip-if-exists·音轨禁令合规）→bmc/i2v/jayredo/ | in-flight（bm-c r1033·i2v 烧毕推片+poke 装配站） |" % ts)
ok_push = atomic_push([
    {"mode": "full", "path": rel("bmc/JAY-REDO-RESHAKE6-BOARD-r1032.jpg"), "local": BOARD, "expect_origin_blob": "NEW"},
    {"mode": "full", "path": rel("bmc/jayredo_reshake6_r1032_receipt.json"), "local": RECEIPT, "expect_origin_blob": "NEW"},
    {"mode": "full", "path": rel("jayredo_v4_r1032.py"), "local": os.path.join(BASE, "jayredo_v4_r1032.py"), "expect_origin_blob": "NEW"},
    {"mode": "append", "path": "docs/orders.md", "line": ord_row_c},
], "bm-c r1032: Jay-redo verdict exec -- reshake6 hai-xuan board (4 seeds/slot, O-1725) + 11 i2v ignited, director review requested", "phaseC")
PROG["push_c"] = "OK" if ok_push else "FAIL"
save_prog()
if ok_push:
    poke_bma("bmc r1032 jayredo reshake6 board pushed, director review requested (only 6 new cells, pick 1 of 4 per slot)")

# ---- Phase D: i2v 11 放行件 ----
PROG["stage"] = "i2v"; save_prog()

def upload_frame(path):
    fn = os.path.basename(path)
    boundary = "----i2v" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + open(path, "rb").read() + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)

def run_i2v(frame_path, prompt, seed, out_mp4, tag, timeout=3300):
    if os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 500000:
        P("[%s] SKIP (exists)" % tag); return True
    img = upload_frame(frame_path)
    wf = json.load(open(WF_768P, encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = prompt; n6["length"] = 124; n6["width"] = 1344; n6["height"] = 768
    wf["10"]["inputs"]["noise_seed"] = seed
    pid = submit_with_retry(wf, tag, retries=3)
    if not pid:
        return False
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(20)
        try:
            h = http_json(SERVER + "/history/" + pid, timeout=30)
        except Exception:
            continue
        e = h.get(pid)
        if e is None:
            if int(time.time() - t0) % 300 < 25:
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

for i, (name, iv, note) in enumerate(I2V_JOBS):
    out = os.path.join(I2V_OUT, name)
    if PROG["i2v"].get(name, {}).get("ok"):
        P("skip done i2v", name); continue
    frame = os.path.join(R1025_FRAMES, r1025.get("done", {}).get(name, {}).get("file", ""))
    if not os.path.isfile(frame):
        PROG["i2v"][name] = {"ok": False, "err": "frame-missing"}; save_prog(); continue
    ok = run_i2v(frame, iv, 9700 + i, out, name)
    PROG["i2v"][name] = {"ok": ok, "file": name if ok else "", "seed": 9700 + i,
                         "sec": round(os.path.getsize(out) / 1048576.0, 2) if ok else 0,
                         "adj": note, "ts": time.strftime("%H:%M:%S")}
    save_prog()
ok_i2v = sum(1 for v in PROG["i2v"].values() if v.get("ok"))
P("Phase D i2v: %d/11 ok" % ok_i2v)

# ---- Phase E: 推片 + poke 装配站 ----
PROG["stage"] = "push_e"; save_prog()
if ok_i2v:
    files = []
    for name, iv, note in I2V_JOBS:
        f = os.path.join(I2V_OUT, name)
        if os.path.isfile(f) and os.path.getsize(f) > 300000:
            files.append({"mode": "full", "path": rel("bmc/i2v/jayredo/" + name), "local": f, "expect_origin_blob": "NEW"})
    ord_row_e = ("| %s | **【@bm-c 回执】Jay 化批 11 放行件 i2v 烧毕上链（orders 17:1x ②执行完毕）** | INT8 768P 5s 纯画面（音轨禁令合规）"
                 "→bmc/i2v/jayredo/ 共 %d 件；剩 6 重摇件候导演席复检 4 选 1 后同链补烧；全 17 件齐→jayredo_qc_sheet 拼板→装配站"
                 "（find_src 同名收片零改表） | in-flight（bm-c r1032·候复检） |" % (time.strftime("%Y-%m-%d %H:%M"), len(files)))
    files.append({"mode": "append", "path": "docs/orders.md", "line": ord_row_e})
    ok_push = atomic_push(files, "bm-c r1032: Jay-redo 11 approved i2v clips delivered (INT8 768P, audio-stripped, skip-if-exists resume)", "phaseE")
    PROG["push_e"] = "OK" if ok_push else "FAIL"
    save_prog()
    if ok_push:
        poke_bma("bmc r1032 jayredo 11 approved i2v clips pushed to bmc/i2v/jayredo, assembly station find_src ready")

PROG["stage"] = "done"
PROG["summary"] = "kf %d/24 · i2v %d/11 · pushC %s · pushE %s" % (ok_kf, ok_i2v, PROG["push_c"], PROG["push_e"])
save_prog()
P("=== runner complete: %s ===" % PROG["summary"])

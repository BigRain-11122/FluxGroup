# -*- coding: utf-8 -*-
# v53_reburn3_bmc_20261017.py — V5.3 三镜重烧 runner（@bm-c 生成窗·CEO O-20261017-1741「MV 马上弄好」产线最高优先）
# 正身: cph4/fleet/mv0001-handover/canon/V5.3-REBURN-ADDENDUM-3shot-20261017.md（bm-a 导演席 13:5x 签发·O-20261017-1330 定谳）
# 三镜: P1-1 D04_her_brush（竹简形制→泥板+苇刷·刷杆完整入画·红甲手保留）
#       P1-2 SIL1_stele_backlit_v4b（符带心形刻符→只许楔形/星/日/几何·同 seed s9021 同构图同布光）
#       P2-3 C01_carver_face（闭目→半阖目垂视工作面+持刻刀之手入画）
# 三阶段: --phase kf (5 KF: D04x2 + C01x2 @s9932/9933 + SIL1 @s9021) -> trial (3x480P INT4·重烧禁盲烧)
#         -> official (3x INT8 768P 同名覆盖 bmc/i2v/v5redo/·旧件备份 old_v53_backup)
# 铁律: ID 块逐字复用（load V5-REDO-PACK 常量）·零否定零模糊零概念 lint 三名单·音轨禁令·detached 三件套
import os, sys, time, json, re, uuid, argparse, urllib.request, subprocess, importlib.util

if not sys.stdout:            # pythonw guard (10-14 law)
    sys.stdout = open(os.devnull, "w")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
MEDIA = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001"
V5DIR = os.path.join(MEDIA, "v5redo")
LOGDIR = os.path.join(MEDIA, "logs")
KFDIR = os.path.join(V5DIR, "kf_add5")
TRIALDIR = os.path.join(V5DIR, "trials_add5")
OUTDIR = os.path.join(BASE, "bmc", "i2v", "v5redo")
OLD_BAK = os.path.join(V5DIR, "old_v53_backup")
WF_480P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_480p_v4.json")
WF_768P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_768p_v4.json")
WINNERS = os.path.join(V5DIR, "v53_winners.json")
PROG_PATH = os.path.join(V5DIR, "v53_reburn3_progress.json")
SERVER = "http://127.0.0.1:8188"
for d in (LOGDIR, KFDIR, TRIALDIR):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "v53_reburn3_bmc.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "v53_reburn3_bmc.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

ap = argparse.ArgumentParser(); ap.add_argument("--phase", required=True, choices=["kf", "kf2", "trial", "official", "trial2", "official2"])
args = ap.parse_args()
P("=== v53_reburn3 phase=%s start %s pid=%d ===" % (args.phase, time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid()))

def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

pk = load_mod(os.path.join(BASE, "V5-REDO-PACK-r1054.py"), "v5_pack")

# ---- V5.3 三镜（正身=V5.3-REBURN-ADDENDUM-3shot 修法逐条转译）----
# P1-1 D04: 病=竹简/木牍形制(两河错位)+刷杆不可辨 -> 修=湿泥板+苇笔描字+刷杆完整入画+红甲针织袖手保留(展柜前临摹场景)
D04_KF = ("A close-up from a high angle of her hand with the oatmeal chunky-knit wool sleeve and red-lacquered "
          "fingernails, a slim reed brush held in a clear grip with its long pale handle fully in frame, its reed "
          "tip pressed into the smooth wet clay face of a clay tablet dense with incised cuneiform wedge rows, one "
          "fresh wedge sign glistening moist where she has just traced it, the finished rows sharp and legible "
          "around it, fine pale dust lifting in the warm lamplight, the lit glass of the display case resting soft "
          "out of focus beyond her wrist. %s %s" % (pk.CASE_NIGHT, pk.STYLE))
# P2-3 C01: 病=闭目垂首无刻具=读作祈祷 -> 修=半阖目垂视工作面+持刻刀之手入画锚定刻写·保留火光侧光与面部构图基调
C01_KF = ("A close-up at eye level of %s in profile at his work, a half-cut row of large fresh wedges before him, "
          "his eyes half-open in a downcast gaze resting on the half-cut sign, the weight of long work held in his "
          "shoulders, his closed lips still, his hand holding the bronze chisel resting on the stone at the row's "
          "end. %s %s" % (pk.HIM_SCRIBE, pk.TORCH_RIM, pk.STYLE))
# P1-2 SIL1 v4b 同 seed 重烧: 血统=V3-NEWKF base + r977 v2 patches + fix3 v3 patches (词源审计逐条继承)
#   + V5.3 符带正向锚 (ancient votive symbols: cuneiform wedges, eight-pointed stars, sun discs, stepped geometric motifs only)
#   「发光」一律 lit (V5-REDO-PACK 头律: glowing -> lit)
SIL1_KF = ("The same young man from the reference portrait — a young Taiwanese man around twenty with a soft rounded "
           "face, small level eyes, heavy straight brows, full lips and a thick blunt fringe — seen entirely from "
           "behind, standing very still before a towering monolith of deep black basalt — dense dark volcanic "
           "stone reading almost pure black — in a torch-lit Babylonian chamber, his modern charcoal-black jacket "
           "over a white tee marking him as a visitor out of time, his shoulders squared, his head tilted slightly "
           "upward reading the carved rows, the whole figure reading as a deep black silhouette against the amber "
           "glow. Two heavy iron wall-sconce torches flank the stele, each a plain iron bracket holding one slim "
           "flame that rises straight upward on a smooth continuous base with a soft orange core, the left flame "
           "slightly taller than the right, both flames kept small and low so their glow reaches the carved rows "
           "yet leaves the stone mass itself in darkness, and one thin warm rim of light traces the edge of his "
           "hair, shoulders and jacket while the stele's flat uncarved stone stays deep near-black volcanic basalt "
           "reading almost pure black even where the torchlight grazes it, only the carved rows of cuneiform "
           "wedges lit faint amber in sharp legible relief, each incised stroke throwing its own small shadow, the "
           "carved registers carrying only ancient votive symbols of cuneiform wedges, eight-pointed stars, sun "
           "discs and stepped geometric motifs. Setting: theatrical music-video stage — black velvet darkness, "
           "clean clear air, a pool of orange firelight on the stone floor. Lighting: torch flames at 2000K "
           "burning behind the figure, hard rim light carving his silhouette out of pure black, deep crushed "
           "shadows. Camera: static medium-wide shot at chest height, 35mm lens with a shallow cinematic focus "
           "plane held on the figure, the chamber walls falling softly out of focus, the figure weighted low in "
           "the frame. Style: shot on Kodak Vision 5279 35mm film in 2001, telecine transfer, strong halation "
           "blooming around the torch flames, amber monochrome palette over crushed blacks, fine organic grain, "
           "authentic 2001 Taiwanese music video cinematography.")

SHOTS3 = {
    "D04_her_brush_v5":            {"kf": D04_KF,  "jman": (0.0, None),                                  "seeds": (9932, 9933)},
    "C01_carver_face_v5":          {"kf": C01_KF,  "jman": (0.80, "jman_v1_640_rank32_final.safetensors"), "seeds": (9932, 9933)},
    "SIL1_stele_backlit_v4b_s9021": {"kf": SIL1_KF, "jman": (0.60, "jman_v1_rank32.safetensors"),           "seeds": (9021,)},
}
I2V3 = {
    "D04_her_brush_v5": ("Single continuous take at 24fps, 16:9. A close-up from a high angle; the camera holds a "
                         "locked-off tripod frame while the reed brush eases through one slow stroke across the wet "
                         "clay face, the tip pressing one fresh wedge sign into the moist clay, fine pale dust "
                         "lifting and folding behind the bristles, her fingers holding the tablet still. %s"
                         % pk.I2V_TAIL),
    "C01_carver_face_v5": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a "
                           "locked-off tripod frame while his half-open gaze rests down on the half-cut wedge, his "
                           "hand lifting the bronze chisel and driving one clean strike into the stone, the chisel "
                           "stopping at the cut, his breath easing out, the flame flickering once, his closed lips "
                           "holding still. %s" % pk.I2V_TAIL),
    "SIL1_stele_backlit_v4b_s9021": ("Single continuous take at 24fps, 16:9. A medium-wide shot at chest height; the "
                           "camera holds perfectly still while his silhouette holds completely still before the "
                           "stele, only the torch flames behind him breathing with tiny flickers, one slow breath "
                           "lifting his shoulders once, torch key light from behind the figure outside the frame, "
                           "faint amber fill on the stele face, faint ambient glow so the black still breathes. %s"
                           % pk.I2V_TAIL),
}
BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)
VAGUE = re.compile(r"\b(glowing|beautiful|stunning|dramatic|iconic|aesthetic)\b", re.I)
CONCEPT = re.compile(r"\b(korean|k-pop|makeup|watermark)\b", re.I)
for sid, s in SHOTS3.items():
    for label, p in (("kf", s["kf"]), ("i2v", I2V3[sid])):
        for rx, tag in ((BAD, "NEG"), (VAGUE, "VAGUE"), (CONCEPT, "CONCEPT")):
            hits = rx.findall(p)
            assert not hits, "LINT-FAIL %s/%s %s: %s" % (sid, label, tag, hits)
for f in (WF_480P, WF_768P):
    assert os.path.isfile(f), "WF-MISSING %s" % f
P("pre-flight lint PASS (3 shots zero-neg zero-vague zero-concept) + workflows verified")

# ---- KF QC r1 判读 (18:2x): C01 双种子全 CLEAN(s9932 定 winner);
#      D04 双种子 CLEAN 但笔尖悬于展柜玻璃上方(描字语义弱·tablet 在柜内) -> v2 = spec 备选框架
#      「手持泥板道具临摹」(一手按板一手执笔·笔尖压入湿泥面) x s9934/9935;
#      SIL1 s9021 判负(符带 A/S/T、5/M 形疑字母+人形/手形超纲象形符) -> v2 = 符带白名单句
#      独立成句强化(逐符族枚举+连续古铭文语) 同 seed s9021 再战(r1 判负帧保全 .prev1)
D04_KF2 = ("A close-up from a high angle of her hands at the lit display case: one hand with the oatmeal "
           "chunky-knit wool sleeve and red-lacquered fingernails holding a hand-held clay tablet steady on a "
           "spread cloth while her other hand holds a slim reed brush by its long pale handle fully in frame, "
           "the reed tip pressed into the smooth wet clay face of the tablet dense with incised cuneiform wedge "
           "rows, one fresh wedge sign glistening moist where she has just traced it, the finished rows sharp "
           "and legible around the tip, fine pale dust lifting in the warm lamplight. %s %s"
           % (pk.CASE_NIGHT, pk.STYLE))
SIL1_KF2 = SIL1_KF.replace(
    "only the carved rows of cuneiform wedges lit faint amber in sharp legible relief, each incised stroke "
    "throwing its own small shadow, the carved registers carrying only ancient votive symbols of cuneiform "
    "wedges, eight-pointed stars, sun discs and stepped geometric motifs.",
    "only the carved rows lit faint amber in sharp legible relief, each incised stroke throwing its own "
    "small shadow. Every register holds only hand-cut ancient votive signs — tight clusters of cuneiform "
    "wedges with clean triangular heads, plain eight-pointed stars, plain ring-and-dot sun discs and "
    "stepped geometric zigzag motifs — one continuous ancient script running band over band, every sign "
    "abstract, ceremonial and centuries old.")
assert SIL1_KF2 != SIL1_KF, "SIL1 band anchor strengthen failed"
RETRY = [
    ("D04_her_brush_v5", D04_KF2, (0.0, None), 9934),
    ("D04_her_brush_v5", D04_KF2, (0.0, None), 9935),
    ("SIL1_stele_backlit_v4b_s9021", SIL1_KF2, (0.60, "jman_v1_rank32.safetensors"), 9021),
]
for sid, kp_, jm, sd in RETRY:
    for rx, tag in ((BAD, "NEG"), (VAGUE, "VAGUE"), (CONCEPT, "CONCEPT")):
        hits = rx.findall(kp_)
        assert not hits, "LINT-FAIL retry %s s%d %s: %s" % (sid, sd, tag, hits)
P("retry block lint PASS (D04 v2 x2 + SIL1 v2 x1)")

# ---- V5.3 official r1 dense QC (19:0x) FAIL 定向返工块: D04 PASS 留用不动;
#      C01 FAIL = 眼区 frames2-3 塌闭 + 手/刻刀糊团无击打动量 + 面骨漂移熔化 + 光跳;
#      SIL1 FAIL = 左符带 t=2.6s 心形刻符 morph 入侵 (480P trial 同 KF/seed 曾 PASS = 768P INT8 分辨率尺度回归)。
#      修法 (KF winner 不动·帧级已判 CLEAN): I2V3B 逐失败模式强化正向运动锚 + 换新 i2v noise_seed
#      破 768P 坏 roll; 先 trial2 480P INT4 过闸 (盲烧禁律) 再 official2 768P INT8 同名覆盖。
I2V3B = {
    "C01_carver_face_v5": ("Single continuous take at 24fps, 16:9. A close-up at eye level; the camera holds a "
                           "locked-off tripod frame through the whole take. His eyes stay half-open in the same "
                           "steady downcast gaze resting on the half-cut wedge from the first frame to the last, "
                           "his facial features holding still and sharp, his lips staying closed, his head steady. "
                           "His hand lifts the bronze chisel in a clear firm grip, brings the chisel tip over the "
                           "half-cut wedge, and drives one clean downward strike that lands firm in the stone, the "
                           "chisel stopping in the cut, fine stone chips jumping once, his breath easing out, the "
                           "torch flame holding a soft steady flicker with the warm rim light steady on his face. %s"
                           % pk.I2V_TAIL),
    "SIL1_stele_backlit_v4b_s9021": ("Single continuous take at 24fps, 16:9. A medium-wide shot at chest height; the "
                           "camera holds perfectly still through the whole take. His silhouette holds completely "
                           "still before the stele, one slow breath lifting his shoulders once. The stele face stays "
                           "a static carved stone surface through the whole take: every register holds fixed, every "
                           "cuneiform wedge cluster, eight-pointed star, ring-and-dot sun disc and stepped zigzag "
                           "band keeping its exact hand-cut shape from the first frame to the last, the amber relief "
                           "staying sharp and steady. The torch flames behind him breathe with tiny flickers, torch "
                           "key light from behind the figure outside the frame, faint amber fill on the stele face, "
                           "faint ambient glow so the black still breathes. %s" % pk.I2V_TAIL),
}
I2V_SEED2 = {"C01_carver_face_v5": 9944, "SIL1_stele_backlit_v4b_s9021": 9027}
for sid, p in I2V3B.items():
    for rx, tag in ((BAD, "NEG"), (VAGUE, "VAGUE"), (CONCEPT, "CONCEPT")):
        hits = rx.findall(p)
        assert not hits, "LINT-FAIL i2v2 %s %s: %s" % (sid, tag, hits)
P("official2 block lint PASS (C01/SIL1 strengthened motion anchors + fresh i2v seeds s9944/s9027)")

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "phase": args.phase,
        "kf": {}, "trial": {}, "official": {}, "trial2": {}, "official2": {}}
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(open(PROG_PATH, encoding="utf-8-sig"))
        for k in ("kf", "trial", "official", "trial2", "official2"):
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
            return http_json(SERVER + "/prompt", {"prompt": g, "client_id": "bmc-v53"}, timeout=120).get("prompt_id")
        except Exception as ex:
            P("[%s] submit FAIL att%d: %r" % (tag, att, ex))
            time.sleep(45)
    return None

def kf_graph(prompt_text, seed, jman_strength, lora_name, prefix="v53rb3"):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": ["20", 0] if jman_strength > 0 else ["10", 0],
              "positive": ["6", 0], "negative": ["13", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }
    if jman_strength > 0:
        g["20"] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"lora_name": lora_name, "strength_model": jman_strength, "model": ["10", 0]}}
    return g

def gen_kf(prompt, seed, jman_strength, lora_name, out_png, tag, timeout=900):
    if os.path.isfile(out_png) and os.path.getsize(out_png) > 100000:
        P("[%s] SKIP (exists)" % tag); return True
    pid = submit_retry(kf_graph(prompt, seed, jman_strength, lora_name), tag)
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
    boundary = "----v53b" + uuid.uuid4().hex
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
    s = SHOTS3[sid]
    if len(s["seeds"]) == 1:
        seed = s["seeds"][0]
    else:
        try:
            seed = _winner_seed(sid)
        except Exception as e:
            P("[winner] %s FAIL %r -- KF QC pending, abort this shot" % (sid, e))
            return None
    p = os.path.join(KFDIR, "%s_s%d.png" % (sid, seed))
    return p if os.path.isfile(p) else None

def burn_i2v(sid, wf_path, w, h, out_mp4, tag, timeout, seed_override=None, motion_override=None):
    if os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 200000 and duration_of(out_mp4) >= 5.0:
        P("[%s] SKIP (exists+contract-ok)" % tag); return True
    kf = winner_of(sid)
    if not kf or not os.path.isfile(kf):
        P("[%s] KF-MISSING %s" % (tag, kf)); return False
    if seed_override is not None:
        seed = int(seed_override)
    elif len(SHOTS3[sid]["seeds"]) == 1:
        seed = SHOTS3[sid]["seeds"][0]
    else:
        try:
            seed = _winner_seed(sid)
        except Exception:
            P("[%s] winners missing -- KF QC pending" % tag); return False
    img = upload_frame(kf)
    wf = json.load(open(wf_path, encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = motion_override if motion_override is not None else I2V3[sid]
    n6["length"] = 124; n6["width"] = w; n6["height"] = h
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

def backup_old(name):
    src = os.path.join(OUTDIR, name)
    if os.path.isfile(src):
        os.makedirs(OLD_BAK, exist_ok=True)
        dst = os.path.join(OLD_BAK, name)
        if not os.path.isfile(dst):
            import shutil
            shutil.copy2(src, dst)
            P("[backup] %s -> old_v53_backup (%dB)" % (name, os.path.getsize(src)))

if args.phase == "kf2":
    P("--- Phase KF2: D04 v2 x s9934/9935 + SIL1 v2 s9021 (r1 QC 定向复烧) ---")
    for sid, kp_, jm, sd in RETRY:
        tag = "%s_s%d" % (sid, sd)
        ent = PROG["kf"].get(tag, {})
        if ent.get("retried"):
            continue
        out_png = os.path.join(KFDIR, tag + ".png")
        try:
            if os.path.isfile(out_png) and os.path.getsize(out_png) > 100000:
                os.rename(out_png, out_png + ".prev1")
                P("[%s] r1 frame preserved as .prev1" % tag)
            ok = gen_kf(kp_, sd, jm[0], jm[1], out_png, tag)
        except Exception as e:
            P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
        PROG["kf"][tag] = {"ok": bool(ok), "ts": time.strftime("%H:%M:%S"), "retried": True}
        save_prog()
    P("Phase KF2 done")

elif args.phase == "kf":
    P("--- Phase KF: D04/C01 x2 seeds(9932/9933) + SIL1 s9021 ---")
    for sid, s in SHOTS3.items():
        for seed in s["seeds"]:
            tag = "%s_s%d" % (sid, seed)
            if PROG["kf"].get(tag, {}).get("ok"):
                continue
            try:
                ok = gen_kf(s["kf"], seed, s["jman"][0], s["jman"][1],
                            os.path.join(KFDIR, tag + ".png"), tag)
            except Exception as e:
                P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
            PROG["kf"][tag] = {"ok": ok, "ts": time.strftime("%H:%M:%S")}
            save_prog()
    P("Phase KF done: %d/%d ok" % (sum(1 for v in PROG["kf"].values() if v.get("ok")), len(PROG["kf"]) or 5))

elif args.phase == "trial":
    P("--- Phase trial: 3 x 480P INT4 (low-res verification per CEO law) ---")
    for sid in SHOTS3:
        tag = sid + "_t480"
        if PROG["trial"].get(sid, {}).get("ok"):
            continue
        try:
            ok = burn_i2v(sid, WF_480P, 864, 480, os.path.join(TRIALDIR, sid + "_t480.mp4"), tag, 1800)
        except Exception as e:
            P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
        PROG["trial"][sid] = {"ok": ok, "ts": time.strftime("%H:%M:%S")}
        save_prog()
    P("Phase trial done: %d/3 ok" % sum(1 for v in PROG["trial"].values() if v.get("ok")))

elif args.phase == "official":
    P("--- Phase official: 3 x 768P INT8 (overwrite bmc/i2v/v5redo/ with old_v53_backup) ---")
    for sid in SHOTS3:
        if PROG["official"].get(sid, {}).get("ok"):
            continue
        name = sid + ".mp4"
        tag = sid + "_p768"
        try:
            backup_old(name)
            p = os.path.join(OUTDIR, name)
            if os.path.isfile(p) and os.path.getsize(p) > 200000 and duration_of(p) >= 5.0:
                # existing file = old version (backed up above) -> remove so the fresh burn lands
                # (fresh-burn resume is guarded by PROG["official"] only)
                if not PROG["official"].get(sid, {}).get("ok"):
                    os.remove(p)
                    P("[%s] old %s removed (backed up) for fresh burn" % (tag, name))
            ok = burn_i2v(sid, WF_768P, 1344, 768, p, tag, 2400)
        except Exception as e:
            P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
        PROG["official"][sid] = {"ok": ok, "ts": time.strftime("%H:%M:%S")}
        save_prog()
    P("Phase official done: %d/3 ok" % sum(1 for v in PROG["official"].values() if v.get("ok")))

elif args.phase == "trial2":
    P("--- Phase trial2: C01/SIL1 x 480P INT4 strengthened motion + fresh i2v seed (r1 official QC fail fix·盲烧禁律) ---")
    for sid in I2V_SEED2:
        if PROG["trial2"].get(sid, {}).get("ok"):
            continue
        tag = sid + "_t480b"
        try:
            ok = burn_i2v(sid, WF_480P, 864, 480, os.path.join(TRIALDIR, sid + "_t480b.mp4"), tag, 1800,
                          seed_override=I2V_SEED2[sid], motion_override=I2V3B[sid])
        except Exception as e:
            P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
        PROG["trial2"][sid] = {"ok": ok, "ts": time.strftime("%H:%M:%S"), "seed": I2V_SEED2[sid]}
        save_prog()
    P("Phase trial2 done: %d/%d ok" % (sum(1 for v in PROG["trial2"].values() if v.get("ok")), len(I2V_SEED2)))

elif args.phase == "official2":
    P("--- Phase official2: C01/SIL1 re-burn 768P INT8 (强锚 i2v + 新 noise_seed·KF winner 不动·r1 败件保全 fail_v53) ---")
    for sid in I2V_SEED2:
        if PROG["official2"].get(sid, {}).get("ok"):
            continue
        name = sid + ".mp4"
        tag = sid + "_p768b"
        try:
            p = os.path.join(OUTDIR, name)
            if os.path.isfile(p) and os.path.getsize(p) > 200000 and duration_of(p) >= 5.0:
                faildir = os.path.join(V5DIR, "fail_v53"); os.makedirs(faildir, exist_ok=True)
                dst = os.path.join(faildir, name.replace(".mp4", ".fail1.mp4"))
                if not os.path.isfile(dst):
                    import shutil; shutil.copy2(p, dst)
                    P("[%s] r1 failed official preserved %s (%dB)" % (tag, dst, os.path.getsize(p)))
                os.remove(p)
                P("[%s] r1 failed official removed for fresh re-burn" % tag)
            ok = burn_i2v(sid, WF_768P, 1344, 768, p, tag, 2400,
                          seed_override=I2V_SEED2[sid], motion_override=I2V3B[sid])
        except Exception as e:
            P("EXC %s: %r" % (tag, e)); import traceback; traceback.print_exc(file=ERR); ok = False
        PROG["official2"][sid] = {"ok": ok, "ts": time.strftime("%H:%M:%S"), "seed": I2V_SEED2[sid]}
        save_prog()
    P("Phase official2 done: %d/%d ok" % (sum(1 for v in PROG["official2"].values() if v.get("ok")), len(I2V_SEED2)))

PROG["stage"] = args.phase + "_done"
save_prog()
P("=== v53_reburn3 phase=%s complete ===" % args.phase)

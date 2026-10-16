# -*- coding: utf-8 -*-
# v5redo_phase2_r1054.py — V5 修片 Phase 2 runner（@bm-c r1054·768P INT8 正片 17 条）
# 正身: V5-REBURN-SPEC-20261016.md + V5-REDO-PACK-r1054.py；trials-QC winners（本窗多模态 12/12 PASS）
# 交付契约: bmc/i2v/v5redo/<id>.mp4 · min_duration>=5.0s 断言 · 音轨禁令（工作流零 audio 链）· INT8 768P 5s 124帧
# detached 三件套: stdout guard + media 安全区日志 + progress json(resume)；推收归下一窗 harvest（本 runner 零 push）
import os, sys, time, json, re, uuid, urllib.request, subprocess, importlib.util

if not sys.stdout:            # pythonw guard (10-14 law)
    sys.stdout = open(os.devnull, "w")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
MEDIA = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001"
V5DIR = os.path.join(MEDIA, "v5redo")
LOGDIR = os.path.join(MEDIA, "logs")
KFDIR = os.path.join(V5DIR, "kf_r1054")
OUTDIR = os.path.join(BASE, "bmc", "i2v", "v5redo")
WF_768P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_768p_v4.json")
BOARD = os.path.join(BASE, "bmc", "V5-QC-SHEET-17-r1054.jpg")
PROG_PATH = os.path.join(V5DIR, "v5redo_phase2_r1054_progress.json")
SERVER = "http://127.0.0.1:8188"
os.makedirs(OUTDIR, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "v5redo_phase2_r1054.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "v5redo_phase2_r1054.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

P("=== v5redo_phase2_r1054 start %s pid=%d ===" % (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid()))

def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

pack = load_mod(os.path.join(BASE, "V5-REDO-PACK-r1054.py"), "v5_pack")
SHOTS = {s[0]: s for s in pack.SHOTS}
BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)
for sid, s in SHOTS.items():
    hits = BAD.findall(s[4])
    assert not hits, "LINT-FAIL %s" % sid
P("pre-flight lint PASS (17 i2v zero-neg)")

WINNERS = {  # default=本窗 trials 板初选；正身=bmc/v5redo_phase1_winners_r1055.json（导演席 18:05 签发·r1054 收容窗 overlay 执法）
    "INT1_desk_breath_v5": 9901, "INT2_paper_v5": 9904, "INT3_photo_stare_v5": 9905,
    "INT4_rubbing_v5": 9907, "INT5_head_bow_v5": 9910, "B01_weary_v5": 9911,
}
_wj = os.path.join(BASE, "bmc", "v5redo_phase1_winners_r1055.json")
try:
    _w = json.load(open(_wj, encoding="utf-8-sig")).get("winners", {})
    for _k, _v in _w.items():
        if isinstance(_v, dict) and "seed" in _v:
            WINNERS[_k] = int(_v["seed"])
    P("winners overlay (director file authoritative): %s" % WINNERS)
except Exception as _we:
    P("winners overlay FAIL %r -- keep dict" % _we)

def kf_of(sid):
    s = SHOTS[sid]
    if s[7]:
        return s[7], s[7] and os.path.isfile(s[7])
    seed = WINNERS.get(sid, pack.SEEDS[sid][0])
    p = os.path.join(KFDIR, "%s_s%d.png" % (sid, seed))
    return p, os.path.isfile(p)

def noise_seed_of(sid):
    return WINNERS.get(sid, pack.SEEDS[sid][0])

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "burn", "burn": {}}
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(open(PROG_PATH, encoding="utf-8-sig"))
        if isinstance(_old.get("burn"), dict):
            PROG["burn"] = _old["burn"]
        P("resumed: burn=%d" % len(PROG["burn"]))
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

def upload_frame(path):
    fn = os.path.basename(path)
    boundary = "----v5p" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + open(path, "rb").read() + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)

def submit_retry(g, tag, retries=3):
    for att in range(1, retries + 1):
        try:
            return http_json(SERVER + "/prompt", {"prompt": g, "client_id": "bmc-r1054p2"}, timeout=120).get("prompt_id")
        except Exception as ex:
            P("[%s] submit FAIL att%d: %r" % (tag, att, ex))
            time.sleep(45)
    return None

def duration_of(mp4):
    try:
        r = subprocess.run(["ffmpeg", "-i", mp4], capture_output=True, timeout=120)
        m = re.search(rb"Duration: (\d+):(\d+):([\d.]+)", (r.stderr or b"") + (r.stdout or b""))
        if not m:
            return 0.0
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        return 0.0

def burn(sid, tag, out_mp4, timeout=2400):
    if os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 400000 and duration_of(out_mp4) >= 5.0:
        P("[%s] SKIP (exists+contract-ok)" % tag); return True
    kf, ok_kf = kf_of(sid)
    if not ok_kf:
        P("[%s] KF-MISSING %s" % (tag, kf)); return False
    img = upload_frame(kf)
    wf = json.load(open(WF_768P, encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = SHOTS[sid][4]; n6["length"] = 124; n6["width"] = 1344; n6["height"] = 768
    wf["10"]["inputs"]["noise_seed"] = noise_seed_of(sid)
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
                dur = duration_of(out_mp4)
                sz = os.path.getsize(out_mp4)
                okc = dur >= 5.0 and sz > 400000
                P("[%s] SAVED %s dur=%.2fs size=%dB contract=%s (%.1f min)" % (tag, os.path.basename(out_mp4), dur, sz, "OK" if okc else "FAIL-MIN-DURATION", (time.time() - t0) / 60.0))
                return okc
        return False
    P("[%s] TIMEOUT" % tag)
    return False

for sid in [s[0] for s in pack.SHOTS]:
    tag = sid + "_p2"
    out_mp4 = os.path.join(OUTDIR, sid + ".mp4")
    if PROG["burn"].get(sid, {}).get("ok"):
        continue
    try:
        ok = burn(sid, tag, out_mp4)
    except Exception as e:
        P("EXC on %s: %r" % (tag, e))
        import traceback; traceback.print_exc(file=ERR)
        ok = False
    PROG["burn"][sid] = {"ok": ok, "file": os.path.basename(out_mp4), "seed": noise_seed_of(sid),
                         "ts": time.strftime("%H:%M:%S")}
    save_prog()
ok_n = sum(1 for v in PROG["burn"].values() if v.get("ok"))
P("Phase2 burn: %d/17 ok" % ok_n)

# ═══ QC 拼板（17 格·首帧）═══
try:
    from PIL import Image, ImageDraw
    tw, thh, lab, cols = 448, 253, 22, 5
    rows_n = (17 + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 6) + 6, rows_n * (thh + lab + 6) + 34), (24, 20, 16))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 6), "V5 official 768P INT8 -- 17 clips -- bm-c r1054 -- %s" % time.strftime("%Y-%m-%d %H:%M"), fill=(240, 200, 120))
    tdir = os.path.join(V5DIR, "_thumbs_p2_r1054")
    os.makedirs(tdir, exist_ok=True)
    ci = 0
    for sid in [s[0] for s in pack.SHOTS]:
        mp4 = os.path.join(OUTDIR, sid + ".mp4")
        th = os.path.join(tdir, sid + ".png")
        if os.path.isfile(mp4) and not os.path.isfile(th):
            subprocess.run(["ffmpeg", "-y", "-i", mp4, "-vf", "select=eq(n\\,0)", "-vframes", "1", th], capture_output=True, timeout=120)
        pic = Image.open(th).convert("RGB").resize((tw, thh)) if os.path.isfile(th) else Image.new("RGB", (tw, thh), (40, 36, 30))
        x = 6 + (ci % cols) * (tw + 6); y = 34 + (ci // cols) * (thh + lab + 6)
        dr.text((x + 4, y + 3), sid, fill=(225, 205, 150))
        sheet.paste(pic, (x, y + lab))
        dr.rectangle([x, y + lab, x + tw, y + lab + thh], outline=(90, 40, 40))
        ci += 1
    sheet.save(BOARD, "JPEG", quality=88)
    P("board -> %s" % BOARD)
except Exception as e:
    P("board build FAIL %r (files still on disk)" % e)

PROG["stage"] = "phase2_done"
PROG["summary"] = "burn %d/17" % ok_n
save_prog()
P("=== runner complete: %s ===" % PROG["summary"])

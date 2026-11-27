# -*- coding: utf-8 -*-
# jayredo_refire6_r1051.py — @bm-c r1051: 6 槽定选帧 i2v 补烧（P0·O-20261016-1120 直连链·死线 14:05）
# 正身链: JAY-REDO-RESHAKE6-VERDICT-r1033.md 定选表（胜者帧/seed/SIL2 清场覆盖）
#   + JAY-REDO-PACK-v1.py SHOTS iv verbatim（3 校验件按指针=mv_full_shots NEW[x][5] 正文+V4 I2V_TAIL）
# 工作流: h3_i2v_local_768p_v4.json 同 r1032 Phase D（INT8 768P 5s·1344x768·124帧·音轨禁令·skip-if-exists）
# 烧毕: 17 件拼 JAY-REDO-QC-SHEET-17-r1051.jpg -> 原子链 push（clips+sheet+receipt+orders 回执行）-> poke bm-a
# wave 制防攒批（verdict §4 烧毕即推）: 第 3 件后 wave1 push+poke（进度回执）·第 6 件后 wave2 全量+sheet+回执行
# detached 三件套 (10-14 law): stdout guard + media 安全区日志 + progress json(pid+resume)
import os, sys, time, json, re, uuid, urllib.request, subprocess, importlib.util

if not sys.stdout:            # pythonw guard (10-14 law)
    sys.stdout = open(os.devnull, "w")

BASE = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\kf-demo-20261012"
MEDIA = r"K:\Fluxgroup\FluxGroup\media\MV\mv0001"
LOGDIR = os.path.join(MEDIA, "logs")
FRAMES = os.path.join(MEDIA, "jayredo", "kf_r1032")
I2V_OUT = os.path.join(BASE, "bmc", "i2v", "jayredo")
WF_768P = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "h3_i2v_local_768p_v4.json")
MFS = os.path.join(os.path.dirname(BASE), "30s-reel-v1", "mv_full_shots.py")
ATOMIC = r"K:\Fluxgroup\FluxGroup\quant\bigmoney\.codely-cli\scratch\git-atomic-push-bmc.py"
GROUP_ROOT = r"K:\Fluxgroup\FluxGroup"
SHEET = os.path.join(BASE, "bmc", "JAY-REDO-QC-SHEET-17-r1051.jpg")
RECEIPT = os.path.join(BASE, "bmc", "jayredo_refire6_r1051_receipt.json")
PROG_PATH = os.path.join(MEDIA, "jayredo", "jayredo_refire6_r1051_progress.json")
SERVER = "http://127.0.0.1:8188"
BMA_POKE = "http://100.110.185.62:8790/poke"
for d in (LOGDIR, I2V_OUT):
    os.makedirs(d, exist_ok=True)
LOG = open(os.path.join(LOGDIR, "jayredo_refire6_r1051.out.log"), "a", encoding="utf-8", buffering=1)
ERR = open(os.path.join(LOGDIR, "jayredo_refire6_r1051.err.log"), "a", encoding="utf-8", buffering=1)
sys.stderr = ERR

def P(*a):
    print(*a); print(*a, file=LOG)

P("=== jayredo_refire6_r1051 start %s pid=%d ===" % (time.strftime("%Y-%m-%dT%H:%M:%S"), os.getpid()))

def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

pack = load_mod(os.path.join(BASE, "JAY-REDO-PACK-v1.py"), "jay_redo_pack")
mfs = load_mod(MFS, "mv_full_shots")
BAD = re.compile(r"\b(no|not|never|without|don't|doesn't|nope)\b", re.I)
def lint(txt):
    return sorted(BAD.findall(txt))

shots = {s[0]: s for s in pack.SHOTS}
new_rows = {r[0]: r for r in mfs.NEW}
TAIL_SWAP_AT = "Warm amber monochrome grade"

def v4_iv(slot):
    """校验件: mfs NEW 正文 + V4 I2V_TAIL（HOLD 槽律·全片单一视觉语言）"""
    iv = new_rows[slot][5]
    body = iv.split(TAIL_SWAP_AT, 1)[0].rstrip()
    return body + " " + pack.I2V_TAIL

SIL2_OVERRIDE = ("Single continuous take at 24fps, 16:9. A medium shot over his shoulder; the camera holds a "
                 "locked-off tripod frame while his gaze holds the stone through one slow blink, the empty aisle "
                 "still in the amber dark. " + pack.I2V_TAIL)

# (输出名, 胜者帧, i2v seed, iv, 处方注记) — verdict 定选表 verbatim
JOBS = [
    ("E01c_first_line.mp4",           "rs_E01c_first_line_s9600.png",           9800, shots["E01c_first_line.mp4"][3],           "verdict s0"),
    ("SIL2_ots_crowd_v4_s9018.mp4",   "rs_SIL2_ots_crowd_v4_s9018_s9604.png",   9801, SIL2_OVERRIDE,                                "verdict s0 + 清场处方覆盖（导演令）"),
    ("SING1_torch_song_v2_s9013.mp4", "rs_SING1_torch_song_v2_s9013_s9608.png", 9802, shots["SING1_torch_song_v2_s9013.mp4"][3], "verdict s0"),
    ("C01_carver_face.mp4",           "rs_C01_carver_face_s9612.png",           9803, v4_iv("C01_carver_face"),                    "verdict s0 · 校验件同原 i2v（V4 尾）"),
    ("B01_weary.mp4",                 "rs_B01_weary_s9618.png",                 9804, v4_iv("B01_weary"),                          "verdict s2 · 校验件同原 i2v（V4 尾）"),
    ("D01_carver_words.mp4",          "rs_D01_carver_words_s9623.png",          9805, v4_iv("D01_carver_words"),                   "verdict s3 · 校验件同原 i2v（V4 尾）"),
]
for name, frame, seed, iv, note in JOBS:
    hits = lint(iv)
    assert not hits, "LINT-FAIL %s: %s" % (name, hits)
    assert os.path.isfile(os.path.join(FRAMES, frame)), "FRAME-MISSING %s" % frame
P("6 jobs lint PASS (zero negatives) · winner frames verified on disk")

PROG = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "stage": "i2v",
        "i2v": {}, "pushed": [], "push_w1": "", "push_w2": "", "poke": []}
if os.path.exists(PROG_PATH):
    try:
        _old = json.load(open(PROG_PATH, encoding="utf-8-sig"))
        for k in ("i2v", "pushed", "poke"):
            if isinstance(_old.get(k), (dict, list)):
                PROG[k] = _old[k] if k != "i2v" else {**PROG["i2v"], **_old[k]}
        PROG["push_w1"], PROG["push_w2"] = _old.get("push_w1", ""), _old.get("push_w2", "")
        P("resumed: i2v=%d pushed=%d" % (len(PROG["i2v"]), len(PROG["pushed"])))
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
    boundary = "----i2v" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + open(path, "rb").read() + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)

def submit_with_retry(graph_dict, tag, retries=3):
    for att in range(1, retries + 1):
        try:
            return http_json(SERVER + "/prompt", {"prompt": graph_dict, "client_id": "bmc-r1051"},
                             timeout=120).get("prompt_id")
        except Exception as ex:
            P("[%s] submit FAIL att%d: %r" % (tag, att, ex))
            time.sleep(60)
    return None

def run_i2v(frame_path, prompt, seed, out_mp4, tag, timeout=3300):
    if os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 500000:
        P("[%s] SKIP (exists)" % tag); return True
    img = upload_frame(frame_path)
    wf = json.load(open(WF_768P, encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = prompt; n6["length"] = 124; n6["width"] = 1344; n6["height"] = 768
    wf["10"]["inputs"]["noise_seed"] = seed
    pid = submit_with_retry(wf, tag)
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
        P("[poke bm-a] FAIL %r (orders row 上链·bm-a 循环自拉兜底)" % ex)
    save_prog()

def push_clips(done_names, tag):
    files, included = [], []
    for n in done_names:
        if n in PROG["pushed"]:
            continue
        f = os.path.join(I2V_OUT, n)
        if os.path.isfile(f) and os.path.getsize(f) > 300000:
            files.append({"mode": "full", "path": rel("bmc/i2v/jayredo/" + n), "local": f, "expect_origin_blob": "NEW"})
            included.append(n)
    if not files:
        return True
    ok = atomic_push(files, "bm-c r1051: jayredo refire wave (%d clips, verdict r1033 winners, INT8 768P audio-stripped)" % len(files), tag)
    if ok:
        PROG["pushed"].extend(included)
        save_prog()
    return ok

# ---- 烧 6 件（串行·skip-if-exists·烧毕即推防攒批）----
for i, (name, frame, seed, iv, note) in enumerate(JOBS):
    out = os.path.join(I2V_OUT, name)
    if PROG["i2v"].get(name, {}).get("ok"):
        P("skip done i2v", name)
    else:
        ok = run_i2v(os.path.join(FRAMES, frame), iv, seed, out, name)
        PROG["i2v"][name] = {"ok": ok, "file": name if ok else "", "seed": seed, "note": note,
                             "sec": round(os.path.getsize(out) / 1048576.0, 2) if ok else 0,
                             "ts": time.strftime("%H:%M:%S")}
        save_prog()
    if i == 2 and PROG["i2v"].get(name, {}).get("ok"):
        ok1 = push_clips([j[0] for j in JOBS[:3]], "w1")
        PROG["push_w1"] = "OK" if ok1 else "FAIL"; save_prog()
        done_n = sum(1 for j in JOBS[:3] if PROG["i2v"].get(j[0], {}).get("ok"))
        poke_bma("jayredo refire wave1: %d/6 burned+pushed (%s), remaining 3 burning, full ETA ~%s" %
                 (done_n, PROG["push_w1"], time.strftime("%H:%M", time.gmtime(time.time() + 50 * 60 + 8 * 3600))))
ok_i2v = sum(1 for v in PROG["i2v"].values() if v.get("ok"))
P("Phase burn: %d/6 ok" % ok_i2v)

# ---- 17 件拼 QC 板 ----
def build_sheet():
    from PIL import Image, ImageDraw
    clips = sorted(os.listdir(I2V_OUT))
    assert len(clips) >= 17, "clip count %d < 17" % len(clips)
    tw, th, lab = 448, 253, 22
    cols = 6
    rows = (len(clips) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 6) + 6, rows * (th + lab + 6) + 6), (24, 20, 16))
    dr = ImageDraw.Draw(sheet)
    tdir = os.path.join(MEDIA, "jayredo", "_thumbs_r1051")
    os.makedirs(tdir, exist_ok=True)
    for ci, cn in enumerate(clips):
        thumb = os.path.join(tdir, cn + ".png")
        if not os.path.isfile(thumb):
            subprocess.run(["ffmpeg", "-y", "-i", os.path.join(I2V_OUT, cn), "-vf", "select=eq(n\\,0)",
                            "-vframes", "1", thumb], capture_output=True, timeout=120)
        if os.path.isfile(thumb):
            pic = Image.open(thumb).convert("RGB").resize((tw, th))
        else:
            pic = Image.new("RGB", (tw, th), (40, 36, 30))
        x = 6 + (ci % cols) * (tw + 6); y = 6 + (ci // cols) * (th + lab + 6)
        dr.text((x + 4, y + 3), cn.replace(".mp4", ""), fill=(225, 205, 150))
        sheet.paste(pic, (x, y + lab))
        dr.rectangle([x, y + lab, x + tw, y + lab + th], outline=(90, 40, 40))
    sheet.save(SHEET, "JPEG", quality=88)
    P("sheet -> %s (%d cells)" % (SHEET, len(clips)))

if ok_i2v == 6:
    PROG["stage"] = "sheet"; save_prog()
    build_sheet()
    json.dump({"verdict": "JAY-REDO-RESHAKE6-VERDICT-r1033.md", "burned": PROG["i2v"],
               "pushed": PROG["pushed"], "sheet": rel("bmc/JAY-REDO-QC-SHEET-17-r1051.jpg"),
               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(RECEIPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ord_row = ("| %s | **【@bm-c 回执】jayredo 6 定选件 i2v 补烧毕·17/17 全量上链（11:4x @bm-c 派单执行完毕·P0 直连链）** | "
               "INT8 768P 5s 纯画面（音轨禁令合规·SIL2 清场处方覆盖已执行·3 校验件=原 i2v 正文+V4 尾）；6 新件入 bmc/i2v/jayredo/ "
               "+QC 拼板 JAY-REDO-QC-SHEET-17-r1051.jpg（17 格）——装配站 17 件齐可组装 V4→四闸→CERTIFIED 呈 CEO；"
               "E01c/D01 手-工具熔接风险位（verdict 导演提示）候四闸帧级 QC；执行窗=bm-c r1051 | done（17/17 齐候装配） |"
               % time.strftime("%Y-%m-%d %H:%M"))
    files = [{"mode": "full", "path": rel("bmc/JAY-REDO-QC-SHEET-17-r1051.jpg"), "local": SHEET, "expect_origin_blob": "NEW"},
             {"mode": "full", "path": rel("bmc/jayredo_refire6_r1051_receipt.json"), "local": RECEIPT, "expect_origin_blob": "NEW"},
             {"mode": "full", "path": rel("jayredo_refire6_r1051.py"), "local": os.path.join(BASE, "jayredo_refire6_r1051.py"), "expect_origin_blob": "NEW"},
             {"mode": "append", "path": "docs/orders.md", "line": ord_row}]
    ok2 = atomic_push(files, "bm-c r1051: jayredo 6 winner-slot i2v refire complete, 17/17 delivered + QC sheet (verdict r1033, audio-stripped)", "w2")
    PROG["push_w2"] = "OK" if ok2 else "FAIL"; save_prog()
    push_clips([j[0] for j in JOBS], "w2clips")
    if ok2 or PROG["push_w2"] == "OK":
        poke_bma("jayredo 17/17 clips + QC sheet + receipt on origin, assembly station GO (bm-c r1051)")
    else:
        poke_bma("jayredo refire wave2 atomic push FAILED, clips local-complete, bm-c next window harvest-push")

PROG["stage"] = "done"
PROG["summary"] = "i2v %d/6 · push_w1 %s · push_w2 %s" % (ok_i2v, PROG["push_w1"], PROG["push_w2"])
save_prog()
P("=== runner complete: %s ===" % PROG["summary"])

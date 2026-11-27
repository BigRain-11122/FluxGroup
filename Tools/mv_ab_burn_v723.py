# -*- coding: utf-8 -*-
"""mv_ab_burn_v723.py - A/B performance-method validation burns (CEO order 2026-11-08 "你现在就弄").

Waits for the in-flight musubi LoRA training to exit (VRAM frees), starts the
local ComfyUI server, then burns the A/B trio (D03b / B01 / INT1) x 2 prompt
versions at 480P INT4 (CEO efficiency law: trial before 768P), FIFO, one at
a time. A = legacy emotion-word prompt; B = 8-dim action prompt
(AI-ACTOR-PERFORMANCE-v2). Same KF, same seed, same model -> blind-eval pair.

Usage: py Tools/mv_ab_burn_v723.py [--wait-gpu] [--out <dir>]
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid

SERVER = "http://127.0.0.1:8188"
BASE = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1"
WF_PATH = os.path.join(BASE, "h3_i2v_local_480p_v4.json")
KF_DIR = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\canon\kf-reburn-v723"
COMFY = r"D:\AI\comfyui-krea\ComfyUI_windows_portable"
COMFY_PY = os.path.join(COMFY, "python_embeded", "python.exe")
COMFY_MAIN = os.path.join(COMFY, "ComfyUI", "main.py")
COMFY_LOG = os.path.join(COMFY, "comfyui-ab.log")
STATE_FLAG = r"C:\Users\sjs20\Desktop\FluxGroup\.codely-cli\machine-state.flag"
OUT_DEFAULT = r"C:\Users\sjs20\Desktop\FluxGroup\media\MV\mv0001\v723-clips\ab-burns"

TAIL = (" Warm amber monochrome grade with deep crushed shadows, visible 35mm film grain, "
        "highlights blooming softly. Every motion eases in and settles out, in the quiet "
        "camera language of a 2001 Taiwanese music video. Lighting wardrobe hair and set "
        "stay unchanged for the whole shot.")

AB = {
    "D03b": {
        "kf": "D03b_kf.png",
        "A": ("A close-up of a young man looking emotional and intense, staring into the "
              "distance, torchlight flickering on his face, emotional atmosphere, cinematic."),
        "B": ("Single continuous take at 24fps. A close-up at eye level; the camera holds a "
              "locked-off tripod frame. The torch flame breathes once, then his eyes lift "
              "first, his head following half a beat later. One breath in, held. His lip "
              "line eases open a fraction, then settles. The firelight keeps breathing on his skin."),
    },
    "B01": {
        "kf": "B01_kf.png",
        "A": ("A tired ancient scribe looks exhausted and sad, sitting still by the fire, "
              "emotional, cinematic mood."),
        "B": ("Single continuous take at 24fps. A close-up at eye level; the camera holds a "
              "locked-off tripod frame. His shoulders sink lower, then lower again. His elbow "
              "slides onto his knee and his hand props his forehead. He lets out one long "
              "breath, and the firelight dims with it. His other hand stays open on his lap."),
    },
    "INT1": {
        "kf": "INT1_kf.png",
        "A": ("A young man writing lyrics at his desk late at night, feeling frustrated and "
              "nostalgic, warm lamp light, emotional."),
        "B": ("Single continuous take at 24fps. A medium close-up at eye level; the camera "
              "holds a locked-off tripod frame. His pen stops above the page for a beat. His "
              "free hand rubs the root of his brow once. His shoulders drop an inch. One full "
              "slow blink. His gaze returns to the page, pausing in the air just before it lands."),
    },
}

NEG = (" no ", " not ", "without", "don't", "never", "n't ")

WF768 = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\h3_i2v_local_768p_v4.json"

# 2026-11-09 wave: the 7 remaining performance shots (8-dim B prompts only --
# the A/B verdict was 3/3 for the 8-dim method, blind-evaluated). Each new
# prompt burns a 480P trial first (CEO efficiency law / no blind burns),
# sanity-gates on clip size, then the 768P INT8 official.
WAVE = {
    "INT3": ("INT3_kf.png",
             "Single continuous take at 24fps. A close-up at eye level; the camera holds a "
             "locked-off tripod frame. His thumb makes one slow pass along the rubbing's "
             "edge. His gaze travels along the carved row. His lip line eases open a "
             "fraction. One slow blink comes after the thumb pass."),
    "C01": ("C01_kf.png",
            "Single continuous take at 24fps. A close-up at eye level; the camera holds a "
            "locked-off tripod frame. The chisel tip holds against the half-cut mark. His "
            "fingers tighten once around the handle. Fine stone dust drifts from the tip."),
    "D01": ("D01_kf.png",
            "Single continuous take at 24fps. A close-up over the shoulder; the camera "
            "holds a locked-off tripod frame. His fingertip presses along the fresh-cut "
            "row, reading it. His gaze follows the row to the edge of the frame. His "
            "throat moves once."),
    "R06": ("R06_kf.png",
            "Single continuous take at 24fps. A close-up at eye level; the camera holds a "
            "locked-off tripod frame. Her eyes travel the carved row, line by line. Her "
            "fingertip hovers an inch from the glass, resting in the air. One slow blink. "
            "The case light breathes."),
    "E03": ("E03_kf.png",
            "Single continuous take at 24fps. A close-up at eye level; the camera holds a "
            "locked-off tripod frame. The torchlight settles. His eyes stay on her through "
            "the glass first. Her head turns toward him half a beat later. The light "
            "between them breathes once."),
    "INT5": ("INT5_kf.png",
             "Single continuous take at 24fps. A close-up at eye level; the camera holds a "
             "locked-off tripod frame. His shoulders settle, then his head bows slowly "
             "toward the page. His eyes close for one beat, then open. A faint warm glow "
             "grows at the far frame edge."),
    "E04": ("E04_kf.png",
            "Single continuous take at 24fps. A close-up at eye level; the camera holds a "
            "locked-off tripod frame. Two faces surface in the amber light, one after the "
            "other. Each face holds one thing only: hers a slow blink, his a lifted gaze. "
            "The light between them flickers once."),
}


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def train_running():
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'krea2_train_network'}).Count"],
                             capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip() or 0) > 0
    except Exception:
        return True  # fail-safe: assume busy


def free_vram_mb():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total,memory.used",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=15)
        t, u = [int(x) for x in out.stdout.strip().split(",")]
        return t - u
    except Exception:
        return 0


def ceo_yields():
    try:
        return os.path.isfile(STATE_FLAG) and "pause" in open(STATE_FLAG, encoding="utf-8", errors="replace").read().lower()
    except Exception:
        return False


def http_json(url, payload=None, timeout=60):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def server_up():
    try:
        http_json(SERVER + "/system_stats", timeout=5)
        return True
    except Exception:
        return False


def start_server():
    logf = open(COMFY_LOG, "ab")
    subprocess.Popen([COMFY_PY, "-s", COMFY_MAIN, "--listen", "127.0.0.1", "--port", "8188",
                     "--lowvram"],  # 12GB card hosting TE 15G + VAE 5G + DiT 20G: deep offload or OOM crash
                     cwd=COMFY, stdout=logf, stderr=subprocess.STDOUT,
                     creationflags=0x08000000)  # CREATE_NO_WINDOW (zero-desktop-disturb law)
    log("ComfyUI launching (log: %s)" % COMFY_LOG)


def upload_image(path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----ab" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + \
            ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)


def burn(tag, ver, prompt, seed, out_dir, wf=None, w_=864, h_=480, suffix="", kf=None):
    wf_path = wf or WF_PATH
    wf = json.load(open(wf_path, encoding="utf-8"))
    img = upload_image(os.path.join(KF_DIR, kf or AB.get(tag, {}).get("kf", "MISSING_KF.png")))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["first_frame"] = ["16", 0]
    n6["prompt"] = prompt + TAIL
    n6["length"] = 124
    n6["width"] = w_
    n6["height"] = h_
    wf["10"]["inputs"]["noise_seed"] = seed
    wf["15"]["inputs"]["filename_prefix"] = "ab_v723_%s_%s" % (tag, ver)
    pid = http_json(SERVER + "/prompt", {"prompt": wf, "client_id": "ab-v723"})["prompt_id"]
    log("queued %s_%s%s (seed %d)" % (tag, ver, suffix, seed))
    t0 = time.time()
    while time.time() - t0 < 1800:
        time.sleep(10)
        try:
            h = http_json(SERVER + "/history/" + pid, timeout=60)
        except Exception as e:
            log("poll retry %s_%s (%s -- server busy, keep waiting)" % (tag, ver, type(e).__name__))
            continue
        if pid in h:
            outs = h[pid].get("outputs", {})
            for node, o in outs.items():
                for it in (o.get("videos") or o.get("images") or []):
                    fn = it.get("filename")
                    if not fn:
                        continue
                    q = "filename=%s&subfolder=%s&type=%s" % (fn, it.get("subfolder", ""), it.get("type", "output"))
                    with urllib.request.urlopen(SERVER + "/view?" + q, timeout=300) as r:
                        data = r.read()
                    dst = os.path.join(out_dir, "%s_%s_s%d%s.mp4" % (tag, ver, seed, suffix))
                    open(dst, "wb").write(data)
                    log("saved %s (%d bytes)" % (dst, len(data)))
                    return dst
            log("finished without video output for %s_%s" % (tag, ver))
            return None
    log("TIMEOUT %s_%s" % (tag, ver))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait-gpu", action="store_true", help="wait for training exit + VRAM before burning")
    ap.add_argument("--wave", action="store_true", help="full performance wave: 3 validated officials + 7 new (trial->official)")
    ap.add_argument("--force", action="store_true", help="CEO explicit authorization: proceed despite yield flag (CEO word > stale flag)")
    ap.add_argument("--out", default=OUT_DEFAULT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    for tag, spec in AB.items():
        for ver in ("A", "B"):
            p = spec[ver]
            low = " " + p.lower() + " "
            for n in NEG:
                assert n not in low, "NEGATIVE-WORD LINT FAIL %s_%s: %r" % (tag, ver, n)
    log("lint PASS (6 prompts, zero negatives)")

    if a.wait_gpu:
        while True:
            if ceo_yields() and not a.force:
                log("CEO yield flag active -> waiting (burn resumes when CEO is done)")
                time.sleep(180)
                continue
            if not train_running() and free_vram_mb() >= 2500:
                log("GPU usable (%d MB free, lowvram deep-offload mode) -- go" % free_vram_mb())
                break
            log("waiting: train_running=%s free=%dMB" % (train_running(), free_vram_mb()))
            time.sleep(120)

    if not server_up():
        start_server()
        t0 = time.time()
        while not server_up() and time.time() - t0 < 300:
            time.sleep(10)
    if not server_up():
        log("FATAL: ComfyUI did not come up")
        sys.exit(2)
    log("ComfyUI up")

    results = []
    if a.wave:
        for tag, spec in WAVE.items():
            low = " " + spec[1].lower() + " "
            for n in NEG:
                assert n not in low, "NEGATIVE-WORD LINT FAIL %s: %r" % (tag, n)
        log("wave lint PASS (7 prompts, zero negatives)")
        for i, (tag, (kf, prompt)) in enumerate(WAVE.items()):
            if ceo_yields() and not a.force:
                log("CEO yield flag -> wave pauses (resumes when flag clears)")
                time.sleep(180)
                continue
            seed = 20261109 + i
            trial = os.path.join(a.out, "%s_Btrial_s%d.mp4" % (tag, seed))
            if not (os.path.exists(trial) and os.path.getsize(trial) > 200000):
                burn(tag, "Btrial", prompt, seed, a.out, kf=kf)
            else:
                log("trial exists %s" % tag)
            if not (os.path.exists(trial) and os.path.getsize(trial) > 200000):
                log("TRIAL SANITY FAIL %s -- skip official, flag for eyes" % tag)
                continue
            off = os.path.join(a.out, "%s_B_s%d_768.mp4" % (tag, seed))
            if not (os.path.exists(off) and os.path.getsize(off) > 400000):
                r = burn(tag, "B", prompt, seed + 500, a.out, wf=WF768, w_=1344, h_=768, suffix="_768", kf=kf)
                if r:
                    results.append(r)
                else:
                    log("OFFICIAL BURN FAILED %s -- not counted" % tag)
        # the 3 validated shots go straight to 768P officials
        for i, tag in enumerate(AB):
            if tag == "D03b":
                # CEO 2026-11-09 review: the D03b v5 take's face breaks the ancient-male
                # family (round double-lid eyes vs droopy monolid, narrow V jaw). Its
                # first frame IS the wrong face -- burning an official on this KF would
                # bake the wrong face into v724. The slot goes to the jman-anchored KF
                # regeneration batch first.
                log("SKIP D03b official -- KF is the face-break take, needs re-anchor")
                continue
            seed = 20261108 + i * 10 + 1
            kf = AB[tag]["kf"]
            off = os.path.join(a.out, "%s_B_s%d_768.mp4" % (tag, seed))
            if os.path.exists(off) and os.path.getsize(off) > 400000:
                log("official exists %s" % tag)
                results.append(off)
                continue
            burn(tag, "B", AB[tag]["B"], seed, a.out, wf=WF768, w_=1344, h_=768, suffix="_768")
            if os.path.exists(off) and os.path.getsize(off) > 400000:
                results.append(off)
            else:
                log("OFFICIAL BURN FAILED %s -- not counted" % tag)
        log("WAVE-DONE %d official clips -> %s" % (len([r for r in results if r]), a.out))
        return
    done = [r for r in results if r]
    log("BURN-DONE %d/6 clips -> %s" % (len(done), a.out))


if __name__ == "__main__":
    main()

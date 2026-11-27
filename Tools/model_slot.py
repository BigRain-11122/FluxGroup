# -*- coding: utf-8 -*-
"""Model slot switcher (bm-b, deterministic).

Why: 8GB card cannot hold the image lane (ComfyUI SD1.5 ~6-7GB) and a 7B text
model (5.9GB) at the same time; and the 14B text model measures 4.4 tok/s here
(bench-bm-b.json) so it must never sit resident while other lanes need VRAM.
Profiles make the trade-off explicit and reversible instead of leaving whatever
the last job loaded.

Usage:
  py model_slot.py --profile text-fast|text-quality|image|audio|idle
  py model_slot.py --status
Exit 0 = profile applied and VRAM verified; 2 = VRAM gate not satisfied.
"""
import io
import json
import os
import platform
import subprocess
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API = "http://127.0.0.1:11434"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
OLLAMA = r"C:\Fluxgroup\MiniGame\Tools\Ollama\ollama.exe"

# profile -> (model, keep_alive, vram_gate_mb_needed, note)
PROFILES = {
    # 4B is the resident default on purpose: sentinel + work-runner hardcode it
    # (keep_alive=-1) and it leaves 3.3GB headroom on an 8GB card for the image
    # lane; 7B costs +1GB and -18% tok/s for marginal quality gain in lane work.
    "text-fast": ("qwen3.8:4b", "30m", 5400, "常驻默认：77.0 tok/s / 4.9GB（哨兵与工作轮消费此槽）"),
    "text-standard": ("qwen2.5:7b-instruct", "20m", 6300, "更高质量交互：59.6 tok/s / 5.9GB"),
    "text-quality": ("bili-reply-14b:latest", "10m", 7900, "离线批量：4.4 tok/s / 7.9GB，禁与图像同跑"),
    "image": (None, None, 1200, "图像车道：先卸全部文本模型，再起 ComfyUI"),
    "audio": (None, None, 1200, "音频车道：先卸文本，再跑 IndexTTS/GPT-SoVITS"),
    "idle": (None, None, 1200, "全卸，留桌面基线"),
}

# --- machine-aware profiles -------------------------------------------------
# Why: the table above is tuned for bm-b's 8GB card. A host with different VRAM
# (e.g. the 12GB RTX 4070 box) needs its own gate numbers and model names, and
# duplicating this switcher would be the anti-dup violation. So a host may drop
# Tools/model_slot.profiles.<hostname>.json (or the generic ...profiles.json) and
# that file wins; with no file present the built-in table is used unchanged.
_HERE = os.path.dirname(os.path.abspath(__file__))
_TOTAL_MB = None


def _load_machine_profiles():
    """Override PROFILES from a host-specific JSON when one exists."""
    global PROFILES, _TOTAL_MB
    host = platform.node()
    for cand in (os.path.join(_HERE, "model_slot.profiles.%s.json" % host),
                 os.path.join(_HERE, "model_slot.profiles.json")):
        if not os.path.exists(cand):
            continue
        try:
            with open(cand, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            print("[model_slot] profile file unreadable, using built-in: %s" % str(e)[:80])
            return
        prof = cfg.get("profiles") or {}
        if prof:
            PROFILES = {k: (v.get("model"), v.get("keep_alive"), v.get("gate"), v.get("note", ""))
                        for k, v in prof.items()}
            _TOTAL_MB = cfg.get("total_mb")
            print("[model_slot] machine profiles loaded: %s" % os.path.basename(cand))
        return


def total_vram():
    """Total VRAM in MB. Uses the profile file's total_mb when given, else probes."""
    if _TOTAL_MB:
        return float(_TOTAL_MB)
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, timeout=10).stdout.decode().strip().splitlines()[0]
        return float(out)
    except Exception:
        return 8100.0


def get(url, timeout=10):
    if url.startswith("/"):
        url = API + url
    with OPENER.open(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post(path, payload, timeout=300):
    req = urllib.request.Request(API + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with OPENER.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def loaded(retry=3):
    for _ in range(retry):
        try:
            names = [m.get("name") or m.get("model") for m in get("/api/ps").get("models", [])]
            names = [n for n in names if n]
            if names:
                return names
        except Exception:
            pass
        time.sleep(0.7)
    return []


def vram():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, timeout=10).stdout.decode().strip().splitlines()[0]
        return float(out)
    except Exception:
        return None


def unload_all():
    for name in loaded():
        try:
            post("/api/generate", {"model": name, "prompt": "", "keep_alive": 0, "stream": False}, 60)
            print("  unloaded %s" % name)
        except Exception as e:
            print("  unload failed %s: %s" % (name, str(e)[:80]))


def wait_vram(below_mb, seconds=40):
    for _ in range(seconds):
        v = vram()
        if v is not None and v <= below_mb:
            return v
        time.sleep(1)
    return vram()


def load(model, keep_alive):
    post("/api/generate", {"model": model, "prompt": "", "think": False, "stream": False,
                           "keep_alive": keep_alive}, 300)


def status():
    v = vram()
    print("VRAM used = %s MB" % v)
    print("loaded    = %s" % (", ".join(loaded()) or "(none)"))
    return 0


def main(argv):
    _load_machine_profiles()
    profile = None
    i = 0
    while i < len(argv):
        if argv[i] == "--profile":
            i += 1
            profile = argv[i]
        elif argv[i] == "--status":
            return status()
        i += 1
    if not profile or profile not in PROFILES:
        print("profiles: " + ", ".join(PROFILES))
        print(__doc__)
        return 1

    model, keep, gate, note = PROFILES[profile]
    print("profile=%s  (%s)" % (profile, note))
    unload_all()
    v = wait_vram(1500)
    print("  after unload: VRAM=%s MB" % v)
    if model:
        need = gate - (v or 1500)
        if v is not None and v > gate - 400:
            print("VRAM-GATE: used=%s MB, profile needs used<=%d MB before load -> REFUSED"
                  % (v, gate - 400))
            print("  free it first: close browsers/WebView/Feishu, then retry")
            return 2
        load(model, keep)
        v2 = vram()
        cap = total_vram()
        print("  loaded %s keep_alive=%s -> VRAM=%s MB (card %d MB)" % (model, keep, v2, cap))
        if v2 is not None and v2 > cap * 0.92:
            print("VRAM-WARN: near card limit, expect CPU offload and low tok/s")
    else:
        print("  text lane released; start the %s job now (ComfyUI/TTS)" % profile)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
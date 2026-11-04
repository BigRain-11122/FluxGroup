# -*- coding: utf-8 -*-
"""vb_train_card.py - queue-card driver: ONE voice, corpus -> SoVITS s2 train -> receipt.

Why this exists (DE-AI-SPEC A8): the CEO order is open-corpus -> fine-tune, and the only
sanctioned synthesis path is a fine-tuned SoVITS weight (never raw end-to-end TTS). The
fleet runs cards, and cards need one command + one deliverable; this driver wraps
vb_build (the proven hq5/ST-012 pipeline) and writes an inspectable receipt.

GPU hygiene (ST-012 lessons, mandatory): s2 training needs ~7.9GB of this 8GB card, so
before training we open the valve (keepwarm.pause + kill llama-server AND the ollama
daemon), and after training we close it (delete pause, re-enable the two serve tasks).
A training that OOMs because a text model got re-pinned mid-run is a defect of this
driver, not of the card.

Usage:
  python vb_train_card.py --voice aishell3-z01 --raw <dir-of-wav-or-m4a> \
      --receipt <out.json> [--epochs 20] [--minutes 30]

Exit: 0 PASS (weights found) | 3 BLOCKED (no inputs) | 1 FAIL (training failed)
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = r"C:\Fluxgroup\FluxGroup"
GPT_ROOT = os.environ.get("VB_GPT_ROOT", os.path.join(MAIN, "media", "drama-tools", "GPT-SoVITS"))
VB_ROOT = os.environ.get("VB_ROOT", os.path.join(MAIN, "media", "voicebank"))
PAUSE = r"C:\Fluxgroup\MiniGame\Tools\Ollama\keepwarm.pause"
SERVE_TASKS = ("MiniGameOllamaServe", "MiniGameOllamaKeepWarm")
AUD = (".wav", ".m4a", ".mp3", ".flac", ".ogg", ".aac", ".opus", ".wma")


def sh(cmd, timeout=None):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def valve_open(rec):
    """ST-012: kill llama-server AND the daemon, or a re-pinned model OOMs the training."""
    try:
        os.makedirs(os.path.dirname(PAUSE), exist_ok=True)
        open(PAUSE, "w").write("vb_train_card " + time.strftime("%Y-%m-%dT%H:%M:%S"))
    except Exception as e:
        rec["valve_open_error"] = str(e)[:120]
    sh(["taskkill", "/IM", "llama-server.exe", "/F"])
    sh(["taskkill", "/IM", "ollama.exe", "/F"])
    for t in SERVE_TASKS:
        sh(["schtasks", "/Change", "/TN", t, "/DISABLE"])


def valve_close(rec):
    try:
        if os.path.exists(PAUSE):
            os.remove(PAUSE)
    except Exception as e:
        rec["valve_close_error"] = str(e)[:120]
    for t in SERVE_TASKS:
        rc, _ = sh(["schtasks", "/Change", "/TN", t, "/ENABLE"])
        rec.setdefault("restored_tasks", []).append([t, rc])


def to_m4a_dir(raw, work):
    """vb_build expects a folder of m4a; wav slots are converted once, audio-only copy."""
    files = [f for f in sorted(os.listdir(raw)) if f.lower().endswith(AUD)]
    if not files:
        return None, 0
    if all(f.lower().endswith(".m4a") for f in files):
        return raw, len(files)
    os.makedirs(work, exist_ok=True)
    n = 0
    for f in files:
        src = os.path.join(raw, f)
        dst = os.path.join(work, os.path.splitext(f)[0] + ".m4a")
        if os.path.exists(dst):
            n += 1
            continue
        rc, _ = sh(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-c:a", "aac", "-b:a", "256k", dst], timeout=120)
        if rc == 0:
            n += 1
    return work, n


def find_weights(voice):
    pats = [
        os.path.join(GPT_ROOT, "SoVITS_weights_*", "*%s*" % voice + ".pth"),
        os.path.join(GPT_ROOT, "SoVITS_weights_*", "*%s*" % voice + "*.pth"),
    ]
    out = []
    for p in pats:
        out += glob.glob(p)
    return sorted(set(out))


def ensure_torch_python():
    """2026-11-05 bm-b fix: queue cards run with whatever `python` is first on PATH, and
    on this node that interpreter has no torch (verified). vb_build is spawned with
    sys.executable, so the whole card would die on `import torch`. Re-exec under the
    GPT-SoVITS runtime venv (same interpreter for vb_build) - fixes every future
    voice-train card regardless of how its cmd spells python."""
    try:
        import torch  # noqa: F401
        return
    except ImportError:
        pass
    venv_py = os.path.join(GPT_ROOT, "runtime", "Scripts", "python.exe")
    if os.path.exists(venv_py) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_py).lower():
        os.environ["VB_REEXEC_PY"] = sys.executable
        os.execv(venv_py, [venv_py] + sys.argv)
    raise SystemExit("no torch in %s and no runtime venv at %s" % (sys.executable, venv_py))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--minutes", type=float, default=30.0)
    a = ap.parse_args(argv)

    ensure_torch_python()

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "voice": a.voice, "raw": a.raw,
           "epochs": a.epochs, "minutes_target": a.minutes,
           "spec": "DE-AI-SPEC-v1 A7/A8", "verdict": "INIT"}

    if not os.path.isdir(a.raw):
        rec.update({"verdict": "BLOCKED", "rc": 3, "gaps": ["raw dir missing: %s" % a.raw]})
        json.dump(rec, open(a.receipt, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("BLOCKED raw missing")
        return 3

    work = os.path.join(VB_ROOT, "_m4a", a.voice)
    m4a_dir, n_files = to_m4a_dir(a.raw, work)
    rec["raw_files"] = n_files
    if not m4a_dir or n_files == 0:
        rec.update({"verdict": "BLOCKED", "rc": 3,
                    "gaps": ["no audio files in %s" % a.raw]})
        json.dump(rec, open(a.receipt, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("BLOCKED no audio")
        return 3

    os.environ["VB_ROOT"] = VB_ROOT
    os.environ["VB_GPT_ROOT"] = GPT_ROOT

    valve_open(rec)
    try:
        cmd = [sys.executable, os.path.join(HERE, "vb_build.py"),
               "--voice", a.voice, "--raw", m4a_dir,
               "--epochs", str(a.epochs), "--minutes", str(a.minutes)]
        rec["train_cmd"] = " ".join(cmd)
        rc, out = sh(cmd, timeout=14400)
        rec["train_rc"] = rc
        rec["train_tail"] = out[-2000:]
    finally:
        valve_close(rec)

    weights = find_weights(a.voice)
    rec["weights"] = weights
    if rc == 0 and weights:
        rec.update({"verdict": "PASS", "rc": 0})
        ret = 0
    elif rc == 3:
        rec.update({"verdict": "BLOCKED", "rc": 3})
        ret = 3
    else:
        rec.update({"verdict": "FAIL", "rc": rc if rc else 1,
                    "gaps": ["train rc=%s or no weights; see train_tail" % rc]})
        ret = 1
    os.makedirs(os.path.dirname(a.receipt), exist_ok=True)
    json.dump(rec, open(a.receipt, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("TRAIN %s %s weights=%d" % (a.voice, rec["verdict"], len(weights)))
    return ret


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
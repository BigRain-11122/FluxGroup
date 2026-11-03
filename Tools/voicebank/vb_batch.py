# -*- coding: utf-8 -*-
"""vb_batch.py - run the voice-bank queue end to end (build -> demo -> registry).

queue.json rows:
  {"voice": "v01-...", "raw": "…\\raw", "label": "…", "minutes": 25, "epochs": 20}

Registry rows are appended to voicebank/REGISTRY.jsonl (one line per finished voice) so
the bank is auditable: corpus size, pitch profile, QC numbers and weight path together.
"""
import json
import os
import subprocess
import sys
import time

VB = r"E:\Fluxgroup\.codely-cli\voicebank"
PY = r"C:\Fluxgroup\FluxGroup\media\drama-tools\GPT-SoVITS\runtime\Scripts\python.exe"
BANK_BUILD = r"E:\Fluxgroup\.codely-cli\vb_build.py"
BANK_SAY = r"E:\Fluxgroup\.codely-cli\voicebank_say.py"


def run(cmd, env=None):
    e = os.environ.copy()
    e["PYTHONIOENCODING"] = "utf-8"
    if env:
        e.update(env)
    p = subprocess.run([PY, "-u"] + cmd, env=e, capture_output=True, text=True,
                       errors="replace")
    return p.returncode, (p.stdout or "")[-800:], (p.stderr or "")[-400:]


def main():
    queue = json.load(open(os.path.join(VB, "queue.json"), encoding="utf-8"))
    for row in queue:
        voice = row["voice"]
        root = os.path.join(VB, voice)
        if os.path.exists(os.path.join(root, "demo.mp3")):
            print("skip", voice, "(demo exists)")
            continue
        print("build", voice, flush=True)
        rc, o, e = run([BANK_BUILD, "--voice", voice, "--raw", row["raw"],
                        "--minutes", str(row.get("minutes", 25)),
                        "--epochs", str(row.get("epochs", 20))])
        if rc != 0:
            print("BUILD FAIL", voice, rc, e, flush=True)
            continue
        rc, o, e = run([BANK_SAY, voice])
        if rc != 0:
            print("DEMO FAIL", voice, rc, e, flush=True)
            continue
        chk = json.load(open(os.path.join(root, "demo_check.json"), encoding="utf-8"))
        meta = json.load(open(os.path.join(root, "voice.json"), encoding="utf-8"))
        row_out = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "voice": voice,
            "label": row.get("label", ""), "source": row.get("source", ""),
            "corpus_minutes": meta.get("minutes"), "corpus_clips": meta.get("clips"),
            "f0_med": meta.get("f0_med"), "matched": chk.get("match_ratio"),
            "hf_ratio": chk.get("hf_ratio"), "noise_floor_db": chk.get("noise_floor_db"),
            "weights": meta.get("weights"), "demo": os.path.join(root, "demo.mp3"),
        }
        with open(os.path.join(VB, "REGISTRY.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(row_out, ensure_ascii=False) + "\n")
        print("OK", voice, "match=%.2f" % (chk.get("match_ratio") or 0), flush=True)


main()
# -*- coding: utf-8 -*-
"""vb_pickref.py - choose the reference clip that GPT-SoVITS will clone from.

A bad reference pair wrecks the output even when the trained SoVITS is good: xlm-hq5 with
its auto-picked reference produced "书记实在话" and dropped a whole clause (ASR match 0.389),
while the same model with a clean reference scored 0.981.

So a reference must satisfy two things, not one:
  1. it must sound like the target person  -> speaker-embedding cosine vs the host reference
  2. its stored transcript must match the audio -> ASR the clip and compare
Selecting by "longest transcript", which the demo script used to do, checks neither.

Usage:
  python vb_pickref.py --bank <voice_root> --identify-ref <host.wav> [--out pick.json]
"""
import argparse
import json
import os
import re
import sys
import wave

import numpy as np
import torch
import torchaudio

REPO = os.environ.get("VB_GPT_ROOT", r"C:\Fluxgroup\FluxGroup\media\drama-tools\GPT-SoVITS")
ASR_DIR = r"E:\Fluxgroup\.codely-cli\models\faster-whisper-small"
SR = 16000


def load16k(path):
    with wave.open(path, "rb") as w:
        sr, ch = w.getframerate(), w.getnchannels()
        raw = w.readframes(w.getnframes())
    y = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        y = y.reshape(-1, ch).mean(1)
    t = torch.from_numpy(y)
    return torchaudio.functional.resample(t, sr, SR) if sr != SR else t


def wav_dur(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", required=True)
    ap.add_argument("--identify-ref", required=True)
    ap.add_argument("--min-sim", type=float, default=0.0)
    ap.add_argument("--transcript-min", type=float, default=0.85)
    ap.add_argument("--min-hf", type=float, default=0.010,
                    help=">8kHz energy share of the reference clip; it sets the output's "
                         "brightness ceiling (a 0.0001 reference produced a 0.0001 demo)")
    ap.add_argument("--max-eval", type=int, default=80)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    import zhconv
    clean = lambda s: re.sub(r"[^\u4e00-\u9fa5]", "", zhconv.convert(s or "", "zh-cn"))

    seg = os.path.join(a.bank, "seg")
    lst = {}
    with open(os.path.join(a.bank, "exp", "list.txt"), encoding="utf-8") as f:
        for line in f:
            p = line.strip().split("|")
            if len(p) >= 4:
                lst[p[0]] = p[3]

    # GPT-SoVITS wants a 3-10 s reference; aim for the middle where prosody is stable
    cands = []
    for fn, txt in lst.items():
        p = os.path.join(seg, fn)
        if not os.path.exists(p):
            continue
        d = wav_dur(p)
        if not (5.0 <= d <= 9.0):
            continue
        if len(clean(txt)) < 16:
            continue
        cands.append((abs(d - 7.0), fn, txt, d))
    cands.sort()
    cands = cands[:a.max_eval]
    if not cands:
        print("no candidate clips")
        return 2

    cwd0 = os.getcwd()
    os.chdir(REPO)
    sys.path.insert(0, REPO)
    sys.path.insert(0, os.path.join(REPO, "GPT_SoVITS"))
    from sv import SV
    sv = SV("cpu", False)

    def emb(t):
        return sv.compute_embedding3(t.unsqueeze(0))[0].float().cpu().numpy()

    def chunks(t, sec=6.0, min_rms=0.004):
        n = int(sec * SR)
        out = []
        for i in range(0, max(1, len(t) - n // 2), n):
            c = t[i:i + n]
            if len(c) < SR or float(torch.sqrt(torch.mean(c * c))) < min_rms:
                continue
            out.append(c)
        return out

    rv = [emb(c) for c in chunks(load16k(a.identify_ref))]
    rm = np.stack(rv)
    rm = rm / np.linalg.norm(rm, axis=1, keepdims=True)
    cen = rm.mean(0)
    cen = cen / np.linalg.norm(cen)
    os.chdir(cwd0)

    from faster_whisper import WhisperModel
    m = WhisperModel(ASR_DIR, device="cpu", compute_type="int8")

    import vb_build as _B     # reuse the same hf_ratio the QC gate uses

    rows = []
    for i, (_, fn, txt, d) in enumerate(cands):
        p = os.path.join(seg, fn)
        t = load16k(p)
        v = np.mean([emb(x) for x in (chunks(t, min_rms=0.003) or [t])], 0)
        v = v / (np.linalg.norm(v) + 1e-9)
        sim = float(v @ cen)
        xf, srf = _B.read_wav(p)
        hf = _B.hf_ratio(xf, srf)
        got = "".join(s.text for s in m.transcribe(p, language="zh", beam_size=2)[0])
        g, e = clean(got), clean(txt)
        agree = sum(1 for x, y in zip(g, e) if x == y) / max(1, len(e))
        rows.append({"file": fn, "dur": round(d, 2), "sim": round(sim, 4), "hf": round(hf, 4),
                     "transcript": round(agree, 3), "text": txt, "asr": got})
        if (i + 1) % 20 == 0:
            print("evaluated %d/%d" % (i + 1, len(cands)), flush=True)

    ok = [r for r in rows if r["sim"] >= a.min_sim and r["hf"] >= a.min_hf
          and r["transcript"] >= a.transcript_min]
    ok.sort(key=lambda r: -r["sim"])
    print("\n%d/%d candidates pass (sim>=%.2f, hf>=%.3f, transcript>=%.2f)"
          % (len(ok), len(rows), a.min_sim, a.min_hf, a.transcript_min))
    for r in ok[:a.top]:
        print("  sim=%.3f hf=%.4f asr=%.3f %.2fs  %-40s  %s"
              % (r["sim"], r["hf"], r["transcript"], r["dur"], r["file"], r["text"]))
    if not ok:
        print("NO VERIFIED REFERENCE - inspect the distribution before training more")
    if a.out:
        json.dump({"ref_audio": os.path.join("seg", ok[0]["file"]) if ok else "",
                   "ref_text": ok[0]["text"] if ok else "", "candidates": rows},
                  open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
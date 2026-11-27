# -*- coding: utf-8 -*-
"""vb_identify.py - speaker-identity gate for a voice bank.

Pitch was the wrong discriminator. gate_f0() picks the global autocorrelation peak, so it
makes octave errors: one solo speaker measured 190-333 Hz segment to segment, which is how
"two speakers at 237/283 Hz" was concluded from tracker artefacts. Identity has to come
from a speaker-verification model, so this uses ERES2NetV2, which ships with GPT-SoVITS
(zero download), and scores every clip against a reference recording of the target person.

Usage:
  python vb_identify.py --ref <reference.m4a|wav|dir> --dir <voice_root> [--out json]
    --dir may be a bank root (uses <dir>/seg/*.wav) or a folder of wav files.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import torch
import torchaudio
import wave

REPO = os.environ.get("VB_GPT_ROOT", r"C:\Fluxgroup\FluxGroup\media\drama-tools\GPT-SoVITS")
SR = 16000
CHUNK_S = 6.0


def load16k(path):
    # stdlib wave + torch resampling: torchaudio.load() needs the torchcodec FFmpeg DLLs,
    # which are not installed in this runtime (OSError on libtorchcodec_core*.dll)
    with wave.open(path, "rb") as w:
        sr, ch = w.getframerate(), w.getnchannels()
        raw = w.readframes(w.getnframes())
    if w.getsampwidth() != 2:
        raise RuntimeError("expected 16-bit PCM: %s" % path)
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    wav = torch.from_numpy(x)
    if sr != SR:
        wav = torchaudio.functional.resample(wav, sr, SR)
    return wav


def chunks(wav, sec=CHUNK_S, min_rms=0.004):
    n = int(sec * SR)
    out = []
    for i in range(0, max(1, len(wav) - n // 2), n):
        c = wav[i:i + n]
        if len(c) < SR:            # shorter than 1 s carries no usable timbre
            continue
        if float(torch.sqrt(torch.mean(c * c))) < min_rms:
            continue
        out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--is-half", type=int, default=0)
    a = ap.parse_args()

    os.chdir(REPO)
    sys.path.insert(0, REPO)
    sys.path.insert(0, os.path.join(REPO, "GPT_SoVITS"))
    from sv import SV

    sv = SV(a.device, bool(a.is_half))

    def emb(wav):
        # compute_embedding3 iterates the batch dim, so it needs [B, T] (1-D raises IndexError)
        return sv.compute_embedding3(wav.unsqueeze(0).to(a.device))[0].float().cpu().numpy()

    # ---- reference centroid + self-consistency ceiling ----
    refs = ([a.ref] if os.path.isfile(a.ref)
            else sorted(sum([glob.glob(os.path.join(a.ref, e))
                             for e in ("*.wav", "*.m4a", "*.mp3", "*.flac")], [])))
    if not refs:
        print("no reference audio found")
        return 2
    refv = []
    for p in refs:
        for c in chunks(load16k(p)):
            refv.append(emb(c))
    if not refv:
        print("reference produced no usable chunks")
        return 2
    M = np.stack(refv)
    M = M / np.linalg.norm(M, axis=1, keepdims=True)
    centroid = M.mean(0)
    centroid = centroid / np.linalg.norm(centroid)
    # how similar the reference is to itself = the practical ceiling for this model
    ceiling = float(np.median(M @ centroid))

    # ---- score every clip ----
    d = a.dir
    seg = os.path.join(d, "seg")
    if os.path.isdir(seg):
        files = sorted(glob.glob(os.path.join(seg, "*.wav")))
    else:
        files = sorted(glob.glob(os.path.join(d, "*.wav")))
    rows = []
    for i, f in enumerate(files):
        w = load16k(f)
        cs = chunks(w, min_rms=0.003) or [w]
        v = np.mean([emb(c) for c in cs], 0)
        v = v / (np.linalg.norm(v) + 1e-9)
        rows.append({"file": os.path.basename(f), "sim": round(float(v @ centroid), 4)})
        if (i + 1) % 50 == 0:
            print("scored %d/%d" % (i + 1, len(files)), flush=True)

    sims = np.array([r["sim"] for r in rows]) if rows else np.array([])
    rec = {"ref": refs, "ref_chunks": len(refv), "ceiling": round(ceiling, 4),
           "n": len(rows), "files": rows}
    if len(sims):
        rec["stats"] = {"min": round(float(sims.min()), 4), "p10": round(float(np.percentile(sims, 10)), 4),
                        "median": round(float(np.median(sims)), 4), "p90": round(float(np.percentile(sims, 90)), 4),
                        "max": round(float(sims.max()), 4)}
        print("\nceiling(self-sim of reference) = %.3f" % ceiling)
        print("clips=%d  min=%.3f p10=%.3f median=%.3f p90=%.3f max=%.3f"
              % (len(sims), sims.min(), np.percentile(sims, 10), np.median(sims),
                 np.percentile(sims, 90), sims.max()))
        edges = np.arange(0.30, 1.001, 0.05)
        hist, _ = np.histogram(sims, bins=edges)
        for i, h in enumerate(hist):
            print("  %.2f-%.2f  %4d  %s" % (edges[i], edges[i + 1], h,
                                            "#" * (h * 50 // max(1, hist.max()))))

    if a.out:
        json.dump(rec, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
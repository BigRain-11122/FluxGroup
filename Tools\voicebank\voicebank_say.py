# -*- coding: utf-8 -*-
"""voicebank_say.py - demo synthesis + objective QC for one bank voice.

QC recorded with every demo:
  - ASR round-trip match (text fidelity)
  - high-frequency energy ratio (is the output band-limited / muffled?)
  - noise floor dB (is it noisy?)
  - clipping count
A demo that fails the gates is not shipped as "good"; the numbers go in demo_check.json.
"""
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

REPO = os.environ.get("VB_GPT_ROOT", r"C:\Fluxgroup\FluxGroup\media\drama-tools\GPT-SoVITS")
VB = os.environ.get("VB_ROOT", r"E:\Fluxgroup\.codely-cli\voicebank")
FFMPEG = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe"
ASR_DIR = r"E:\Fluxgroup\.codely-cli\models\faster-whisper-small"
BASE_GPT = os.path.join(REPO, "GPT_SoVITS", "pretrained_models", "s1v3.ckpt")
SOVITS_OUT = os.path.join(REPO, "SoVITS_weights_v2Pro")

DEMO = ("说句实在话：这种声音，你在别的地方听不到。它有点粗糙，有点口音，"
        "但正因为这样，它才像一个活人——而不是一段合成音！你听出来了吗？")


def read_wav(p):
    with wave.open(p, "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return x, sr


def hf_ratio(x, sr):
    n = 1 << 15
    if len(x) < n:
        return 0.0
    acc = np.zeros(n // 2 + 1)
    for i in range(0, len(x) - n, n):
        acc += np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n))) ** 2
    freqs = np.fft.rfftfreq(n, 1 / sr)
    tot = acc.sum()
    return float(acc[freqs > 8000].sum() / tot) if tot > 0 else 0.0


def main():
    voice = sys.argv[1]
    root = os.path.join(VB, voice)
    meta = json.load(open(os.path.join(root, "voice.json"), encoding="utf-8"))
    sovits = os.path.join(SOVITS_OUT, meta["weights"])

    lst = {}
    with open(os.path.join(root, "exp", "list.txt"), encoding="utf-8") as f:
        for line in f:
            p = line.strip().split("|")
            if len(p) >= 4:
                lst[p[0]] = p[3]
    cands = []
    for fn, txt in lst.items():
        if re.fullmatch(r"[\u4e00-\u9fa5，。！？、]+", txt or "") and 18 <= len(txt) <= 40:
            cands.append((fn, txt))
    if not cands:
        cands = list(lst.items())[:1]
    ref, ref_text = max(cands, key=lambda x: len(x[1]))
    import shutil
    ref_path = os.path.join(root, "ref.wav")
    shutil.copy(os.path.join(root, "seg", ref), ref_path)
    open(os.path.join(root, "ref.txt"), "w", encoding="utf-8").write(ref_text)

    sys.path.insert(0, REPO)
    sys.path.insert(0, os.path.join(REPO, "GPT_SoVITS"))
    # tools/i18n computes os.path.relpath(__file__); it dies if cwd is on another drive
    os.chdir(REPO)
    import soundfile as sf
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

    cfg = TTS_Config(os.path.join(REPO, "GPT_SoVITS", "configs", "tts_infer.yaml"))
    cfg.device = "cuda"
    cfg.is_half = True
    tts = TTS(cfg)
    tts.init_t2s_weights(BASE_GPT)
    tts.init_vits_weights(sovits)

    raw = os.path.join(root, "demo_raw.wav")
    n = 0
    for sr, audio in tts.run({
        "text": DEMO, "text_lang": "zh",
        "ref_audio_path": ref_path, "prompt_text": ref_text, "prompt_lang": "zh",
        "top_k": 12, "top_p": 1, "temperature": 0.85,
        "text_split_method": "cut5", "batch_size": 1, "speed_factor": 1.0,
        "repetition_penalty": 1.3, "seed": 2026, "parallel_infer": True,
    }):
        sf.write(raw, audio, sr)
        n += 1
    if n == 0:
        print("NO-AUDIO")
        return 2

    wav = os.path.join(root, "demo.wav")
    mp3 = os.path.join(root, "demo.mp3")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", raw,
                    "-af", "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "44100", "-c:a", "pcm_s16le", wav], check=True)
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", wav, "-c:a", "libmp3lame",
                    "-b:a", "192k", mp3], check=True)

    from faster_whisper import WhisperModel
    m = WhisperModel(ASR_DIR, device="cpu", compute_type="int8")
    got = "".join(s.text for s in m.transcribe(wav, language="zh", beam_size=2)[0])
    norm = lambda s: re.sub(r"[^\u4e00-\u9fa5]", "", s)
    a, b = norm(DEMO), norm(got)
    same = sum(1 for x, y in zip(a, b) if x == y)
    x, sr = read_wav(wav)
    win = int(0.03 * sr)
    fr = np.array([float(np.sqrt(np.mean(x[i:i + win] ** 2)))
                   for i in range(0, len(x) - win, win)])
    fr = fr[fr > 1e-5]      # drop digital-silence padding, else log10(0) poisons the stat

    rec = {
        "voice": voice, "sovits": meta["weights"],
        "ref": ref, "ref_text": ref_text,
        "asr": got, "match_ratio": round(same / max(1, len(a)), 3),
        "dur_s": round(len(x) / sr, 2), "sample_rate": sr,
        "hf_ratio": round(hf_ratio(x, sr), 4),
        "noise_floor_db": round(20 * np.log10(np.percentile(fr, 10) + 1e-9), 1),
        "clip_frames": int(np.sum(np.abs(x) > 0.999)),
        "corpus_minutes": meta.get("minutes"), "corpus_clips": meta.get("clips"),
    }
    json.dump(rec, open(os.path.join(root, "demo_check.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


sys.exit(main())
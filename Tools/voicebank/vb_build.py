# -*- coding: utf-8 -*-
"""vb_build.py - high-fidelity corpus builder + SoVITS trainer for the voice bank.

Why this replaces the first pipeline (the "quality was bad" complaint, 2026-10-29):
  1. the first version decoded everything to 16 kHz; the SoVITS target is 32 kHz, so half
     the band was thrown away before training -> dull, "telephone" timbre.
     Now: decode at 44.1 kHz, cut at 44.1 kHz, let the trainer resample once.
  2. no denoise. Now: mild spectral-gate denoise (noisereduce) with a measurable
     noise-floor drop, and the clean/unclean numbers are printed so it is not a vibe.
  3. single short video. Now: many videos of the same speaker, 20-40 minutes of speech.
  4. 8 epochs. Now: configurable (default 20) with per-2-epoch weight snapshots.

Outputs land under voicebank/<voice>/ and the weights in GPT-SoVITS/SoVITS_weights_<ver>.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave

import numpy as np

REPO = os.environ.get("VB_GPT_ROOT", r"C:\Fluxgroup\FluxGroup\media\drama-tools\GPT-SoVITS")
FFMPEG = r"C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe"
ASR_DIR = os.environ.get("VB_ASR", r"E:\Fluxgroup\.codely-cli\models\faster-whisper-small")
# 2026-11-08 bm-c：原值写死 E:\Fluxgroup（别的机器的盘），本机没有，
# vb_build 一开就 FileNotFoundError。改为按仓库位置推导，可用 VB_ROOT 覆盖。
_HOME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VB = os.environ.get("VB_ROOT", os.path.join(_HOME, ".codely-cli", "voicebank"))
os.makedirs(VB, exist_ok=True)

# one minute of usable speech costs a few minutes of source audio (intro/music/pauses)
RAWS_PER_SPEECH = 3.0
VERSION = "v2Pro"
S2G = os.path.join(REPO, "GPT_SoVITS", "pretrained_models", VERSION, "s2G%s.pth" % VERSION)
S2D = os.path.join(REPO, "GPT_SoVITS", "pretrained_models", VERSION, "s2D%s.pth" % VERSION)
SOVITS_OUT = os.path.join(REPO, "SoVITS_weights_%s" % VERSION)
SR = 44100


def log(m):
    line = "%s %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with open(os.path.join(VB, "build.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sh(cmd, cwd=REPO, env=None, timeout=10800):
    e = os.environ.copy()
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONPATH"] = REPO + os.pathsep + os.path.join(REPO, "GPT_SoVITS")
    if env:
        e.update(env)
    # cmd[0] is a .py path: it needs this interpreter, not a PATH lookup
    if str(cmd[0]).lower().endswith(".py"):
        cmd = [sys.executable] + list(cmd)
    p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True,
                       errors="replace", timeout=timeout)
    return p.returncode, p.stdout or "", p.stderr or ""


def read_wav(p):
    with wave.open(p, "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return x, sr


def write_wav(p, x, sr):
    with wave.open(p, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def hf_ratio(x, sr):
    """Fraction of energy above 8 kHz - a hard proxy for 'is the top band still there'."""
    if len(x) < sr:
        return 0.0
    n = 1 << 15
    acc = np.zeros(n // 2 + 1)
    for i in range(0, len(x) - n, n):
        seg = x[i:i + n] * np.hanning(n)
        acc += np.abs(np.fft.rfft(seg)) ** 2
    freqs = np.fft.rfftfreq(n, 1 / sr)
    tot = acc.sum()
    return float(acc[freqs > 8000].sum() / tot) if tot > 0 else 0.0


def gate_f0(x, sr, f0_center=None, min_ratio=0.30):
    win, hop = int(0.04 * sr), int(0.02 * sr)
    f0s = []
    for s in range(0, len(x) - win, hop):
        f = x[s:s + win]
        if np.sqrt(np.mean(f * f)) < 0.004:
            continue
        fc = f - f.mean()
        ac = np.correlate(fc, fc, "full")[win - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        lo, hi = int(sr / 400), int(sr / 55)
        seg = ac[lo:hi]
        if len(seg) == 0:
            continue
        k = int(np.argmax(seg)) + lo
        if ac[k] < min_ratio:
            continue
        f0s.append(sr / k)
    return f0s


def prepare_audio(m4a, dst, denoise=True):
    rc, o, e = sh([FFMPEG, "-y", "-v", "error", "-i", m4a, "-ac", "1", "-ar", str(SR),
                   "-c:a", "pcm_s16le", dst], cwd=os.path.dirname(dst))
    if rc != 0:
        raise RuntimeError("decode failed: %s" % e[-300:])
    x, sr = read_wav(dst)
    m = {"file": dst, "dur_min": round(len(x) / sr / 60, 2), "hf_before": round(hf_ratio(x, sr), 4)}
    if denoise:
        import noisereduce as nr
        y = nr.reduce_noise(y=x, sr=sr, stationary=False, prop_decrease=0.75,
                            time_mask_smooth_ms=64, n_jobs=1)
        # noisereduce can shift level; restore speech RMS to the original
        rx = np.sqrt(np.mean(x ** 2)) + 1e-9
        ry = np.sqrt(np.mean(y ** 2)) + 1e-9
        y = y * (rx / ry)
        write_wav(dst, y, sr)
        x = y
        m["hf_after"] = round(hf_ratio(x, sr), 4)
    m["rms_db"] = round(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9), 1)
    # noise floor = 10th percentile frame energy
    win = int(0.03 * sr)
    fr = [np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)]
    m["noise_floor_db"] = round(20 * np.log10(np.percentile(fr, 10) + 1e-9), 1)
    return m


def transcribe(wav):
    from faster_whisper import WhisperModel
    dev = os.environ.get("VB_DEVICE", "cuda")
    model = WhisperModel(ASR_DIR, device=dev,
                         compute_type="float16" if dev == "cuda" else "int8")
    segs, _ = model.transcribe(wav, language="zh", vad_filter=True,
                               vad_parameters={"min_silence_duration_ms": 350},
                               beam_size=2, condition_on_previous_text=False)
    return model, list(segs)


def _enable_cuda_dlls():
    """CTranslate2 needs cublas64_12/cudnn on PATH; the runtime ships cu13, so the
    pip-installed nvidia-*-cu12 wheels must be prepended or GPU ASR dies at load."""
    base = os.path.join(REPO, "runtime", "Lib", "site-packages", "nvidia")
    dirs = [os.path.join(base, d, "bin") for d in ("cublas", "cudnn")]
    live = [d for d in dirs if os.path.isdir(d)]
    if live and live[0] not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ";".join(live) + ";" + os.environ.get("PATH", "")


_M = None


def _init_worker():
    """Load one ASR model per worker process (spawn-safe)."""
    global _M
    _enable_cuda_dlls() if os.environ.get("VB_DEVICE","cpu")=="cuda" else None
    from faster_whisper import WhisperModel
    dev = os.environ.get("VB_DEVICE", "cpu")
    _M = WhisperModel(ASR_DIR, device=dev,
                      compute_type="float16" if dev == "cuda" else "int8")


def _process_source(payload):
    """Decode is done already; transcribe + pitch-gate + cut one source file.

    Runs inside a worker: returns (clips, f0s, log_line). Segment names carry the source
    stem so parallel workers cannot collide; the parent renumbers them globally.
    """
    global _M
    wav, src, seg_dir, mn, mx = payload
    if _M is None:
        _init_worker()
    try:
        segs, _ = _M.transcribe(wav, language="zh", vad_filter=True,
                                vad_parameters={"min_silence_duration_ms": 350},
                                beam_size=2, condition_on_previous_text=False)
        segs = list(segs)
    except Exception as e:
        return [], [], "ASR FAIL %s %r" % (os.path.basename(wav), e)
    x, sr = read_wav(wav)
    med = float(np.median(gate_f0(x[: sr * 60], sr))) if len(x) > sr else 180.0
    lo, hi = med * 0.72, med * 1.38
    stem = os.path.splitext(os.path.basename(src))[0][:14]
    clips, f0s = [], []
    for i, s in enumerate(segs):
        d = s.end - s.start
        if d < mn or d > mx:
            continue
        txt = (s.text or "").strip()
        if len(txt) < 4 or getattr(s, "no_speech_prob", 0) > 0.5:
            continue
        clip = x[int(s.start * sr):int(s.end * sr)]
        cq = gate_f0(clip, sr)
        if not cq:
            continue
        f0 = float(np.median(cq))
        if not (lo <= f0 <= hi):
            continue
        if float(np.max(np.abs(clip))) > 0.995:
            continue
        p = os.path.join(seg_dir, "tmp_%s_%03d.wav" % (stem, i))
        write_wav(p, clip, sr)
        clips.append({"wav": p, "text": txt, "f0": round(f0, 1), "dur": round(d, 2)})
        f0s.append(f0)
    return clips, f0s, "seg %s +%d clips" % (os.path.basename(wav), len(clips))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--raw", required=True, help="folder of m4a files for ONE speaker")
    ap.add_argument("--minutes", type=float, default=30.0)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--gpt-epochs", type=int, default=0)
    ap.add_argument("--no-denoise", action="store_true")
    ap.add_argument("--min-clip", type=float, default=3.0)
    ap.add_argument("--max-clip", type=float, default=10.0)
    ap.add_argument("--jobs", type=int, default=4,
                    help="parallel source files in the corpus stage (CPU cores / 2 is sane)")
    ap.add_argument("--out-root", default="", help="where segments/exp land (defaults to VB_ROOT)")
    ap.add_argument("--corpus-only", action="store_true",
                    help="stop after list.txt (used by fleet CPU workers that do not train)")
    ap.add_argument("--identify-ref", default="",
                    help="reference audio of the target speaker; keeps only clips whose "
                         "speaker embedding matches it (ERES2NetV2). Repeatable.")
    ap.add_argument("--identify-min", type=float, default=0.58,
                    help="cosine similarity floor for --identify-ref")
    a = ap.parse_args()

    root = os.path.join(a.out_root or VB, a.voice)
    raw_dir = os.path.join(root, "wav44")
    seg_dir = os.path.join(root, "seg")
    exp = os.path.join(root, "exp")
    for d in (root, raw_dir, exp):
        os.makedirs(d, exist_ok=True)
    shutil.rmtree(seg_dir, ignore_errors=True)
    os.makedirs(seg_dir, exist_ok=True)
    log("=== %s raw=%s target_min=%.0f epochs=%d" % (a.voice, a.raw, a.minutes, a.epochs))

    files = sorted(f for f in os.listdir(a.raw) if f.lower().endswith((".m4a", ".mp4", ".wav")))
    if not files:
        log("no source files")
        return 2
    src_meta = []
    # --minutes is the SPEECH target; speech is only ~35% of a source, so the prep budget
    # has to be looser or it silently truncates the source list (xlm-hq3 used 4 of 15)
    budget = a.minutes * 60 * RAWS_PER_SPEECH
    for i, fn in enumerate(files):
        dst = os.path.join(raw_dir, os.path.splitext(fn)[0] + ".wav")
        if not os.path.exists(dst):
            m = prepare_audio(os.path.join(a.raw, fn), dst, denoise=not a.no_denoise)
            src_meta.append(dict(m, src=fn))
            log("audio %s dur=%.1fmin hf %.4f->%.4f noise_floor=%.1fdB"
                % (fn, m["dur_min"], m.get("hf_before", -1), m.get("hf_after", -1),
                   m["noise_floor_db"]))
        else:
            x, sr = read_wav(dst)
            src_meta.append({"file": dst, "src": fn, "dur_min": round(len(x) / sr / 60, 2)})
        budget -= src_meta[-1]["dur_min"] * 60
        if budget <= 0:
            break

    # ---- segment (parallel: one worker per source video, the ASR is the slow leg) ----
    import multiprocessing as mp
    jobs = max(1, min(a.jobs, len(src_meta)))
    payloads = [(m["file"], m["src"], seg_dir, a.min_clip, a.max_clip) for m in src_meta]
    log("segment parallel jobs=%d files=%d" % (jobs, len(payloads)))
    if jobs == 1:
        results = [_process_source(p) for p in payloads]
    else:
        ctx = mp.get_context("spawn")
        with ctx.Pool(jobs) as pool:
            results = pool.map(_process_source, payloads)

    # pitch is reported, never used to delete data. gate_f0() picks the global
    # autocorrelation peak and makes octave errors: on a solo reference video one speaker
    # measured 190-333 Hz segment to segment, and the four sources of ONE person read
    # 237/283/289/296 Hz. Dropping on that basis removed the best-matching source.
    meds = []
    for i, (c_list, f_list, line) in enumerate(results):
        if f_list:
            meds.append((i, float(np.median(f_list)), len(c_list)))
    for i, m, n in meds:
        log("PITCH-INFO %s clips=%d median=%.0f Hz"
            % (os.path.basename(src_meta[i]["src"]), n, m))

    # per-clip sanity band: keeps a gross outlier (a guest at half/double the pitch) out
    # without pretending the estimator is precise
    anchor = max(meds, key=lambda m: m[2])[1] if meds else None
    clips, f0_all = [], []
    for c_list, f_list, line in results:
        keep, off = [], 0
        for c in c_list:
            if anchor and abs(c["f0"] - anchor) / anchor > 0.25:
                os.remove(c["wav"])
                off += 1
                continue
            keep.append(c)
        if off:
            log("PITCH-FILTER %s dropped %d gross-outlier clips" % (os.path.basename(line), off))
        base = len(clips)
        kept2 = []
        for i, c in enumerate(keep):
            # rename to a stable global index so list.txt and the seg dir agree
            new = os.path.join(seg_dir, "%04d_%s" % (base + i + 1, os.path.basename(c["wav"])))
            try:
                if os.path.exists(new):
                    os.remove(new)
                os.replace(c["wav"], new)
                c["wav"] = new
                kept2.append(c)
            except FileNotFoundError:
                # 2026-11-05 fix (three live catches): a previous crashed run or a
                # concurrent build already consumed this tmp segment. Adopt the
                # renamed target when present, otherwise drop the clip - never crash.
                if os.path.exists(new):
                    c["wav"] = new
                    kept2.append(c)
                else:
                    log("SEG-DROP %s (tmp consumed elsewhere, no target)"
                        % os.path.basename(c["wav"]))
        keep = kept2
        clips.extend(keep)
        f0_all.extend(c["f0"] for c in keep)
        log(line)
        if sum(c["dur"] for c in clips) / 60 >= a.minutes:
            break

    mins = round(sum(c["dur"] for c in clips) / 60, 2)
    log("corpus clips=%d minutes=%.2f f0_med=%.1f" % (len(clips), mins,
                                                      float(np.median(f0_all)) if f0_all else 0))

    # ---- speaker-identity gate (the only gate that can actually tell people apart) ----
    if a.identify_ref:
        import wave as _wave
        import torch as _torch
        import torchaudio as _ta
        cwd0 = os.getcwd()
        os.chdir(REPO)
        sys.path.insert(0, REPO)
        sys.path.insert(0, os.path.join(REPO, "GPT_SoVITS"))
        from sv import SV
        sv = SV("cpu", False)

        def _load16k(p):
            with _wave.open(p, "rb") as w:
                sr_, ch_ = w.getframerate(), w.getnchannels()
                raw = w.readframes(w.getnframes())
            y = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if ch_ > 1:
                y = y.reshape(-1, ch_).mean(1)
            t = _torch.from_numpy(y)
            return _ta.functional.resample(t, sr_, 16000) if sr_ != 16000 else t

        def _emb(t):
            return sv.compute_embedding3(t.unsqueeze(0))[0].float().cpu().numpy()

        def _chunks(t, sec=6.0, min_rms=0.004):
            n = int(sec * 16000)
            out = []
            for i in range(0, max(1, len(t) - n // 2), n):
                c = t[i:i + n]
                if len(c) < 16000:
                    continue
                if float(_torch.sqrt(_torch.mean(c * c))) < min_rms:
                    continue
                out.append(c)
            return out

        rv = [_emb(c) for c in _chunks(_load16k(a.identify_ref))]
        if not rv:
            os.chdir(cwd0)
            log("REJECT identify-ref produced no usable chunks")
            return 3
        rm = np.stack(rv)
        rm = rm / np.linalg.norm(rm, axis=1, keepdims=True)
        cen = rm.mean(0)
        cen = cen / np.linalg.norm(cen)
        ceiling = float(np.median(rm @ cen))
        log("identify ref=%s chunks=%d self_sim=%.3f min_sim=%.2f"
            % (os.path.basename(a.identify_ref), len(rv), ceiling, a.identify_min))

        kept, dropped = [], 0
        for c in clips:
            t = _load16k(c["wav"])
            v = np.mean([_emb(x) for x in (_chunks(t, min_rms=0.003) or [t])], 0)
            v = v / (np.linalg.norm(v) + 1e-9)
            c["sim"] = round(float(v @ cen), 4)
            if c["sim"] < a.identify_min:
                os.remove(c["wav"])
                dropped += 1
            else:
                kept.append(c)
        os.chdir(cwd0)
        clips = kept
        mins = round(sum(c["dur"] for c in clips) / 60, 2)
        sims = np.array([c["sim"] for c in clips]) if clips else np.array([0.0])
        log("IDENTIFY dropped=%d kept=%d minutes=%.2f sim_med=%.3f sim_p10=%.3f"
            % (dropped, len(clips), mins, float(np.median(sims)), float(np.percentile(sims, 10))))

    thr = min(8.0, max(3.0, a.minutes * 0.6))
    if mins < thr:
        log("REJECT too little usable speech (<8 min)")
        return 3

    # ---- list + prep ----
    import zhconv
    lst = os.path.join(exp, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for c in clips:
            t = zhconv.convert(c["text"].replace("|", " "), "zh-cn")
            f.write("%s|VB|ZH|%s\n" % (os.path.basename(c["wav"]), t))

    if a.corpus_only:
        log("corpus-only: segments=%d minutes=%.2f list=%s" % (len(clips), mins, lst))
        return 0

    env = {
        "inp_text": lst, "inp_wav_dir": seg_dir, "exp_name": a.voice, "opt_dir": exp,
        "i_part": "0", "all_parts": "1", "version": VERSION, "hz": "25hz", "is_half": "True",
        "bert_pretrained_dir": os.path.join(REPO, "GPT_SoVITS", "pretrained_models",
                                            "chinese-roberta-wwm-ext-large"),
        "cnhubert_base_dir": os.path.join(REPO, "GPT_SoVITS", "pretrained_models",
                                          "chinese-hubert-base"),
        "sv_path": os.path.join(REPO, "GPT_SoVITS", "pretrained_models", "sv",
                                "pretrained_eres2netv2w24s4ep4.ckpt"),
    }
    for script, marker in [("1-get-text.py", "2-name2text.txt"),
                           ("2-get-hubert-wav32k.py", "4-cnhubert"),
                           ("2-get-sv.py", "7-sv_cn")]:
        if os.path.exists(os.path.join(exp, marker)):
            continue
        rc, o, e = sh([os.path.join("GPT_SoVITS", "prepare_datasets", script)], env=env)
        if rc != 0:
            log("prep %s FAILED %s" % (script, e[-400:]))
            return 4
        if script == "1-get-text.py":
            shards = sorted(f for f in os.listdir(exp) if f.startswith("2-name2text-"))
            buf = [open(os.path.join(exp, f), encoding="utf-8").read().rstrip("\n") for f in shards]
            open(os.path.join(exp, "2-name2text.txt"), "w", encoding="utf-8").write(
                "\n".join(x for x in buf if x) + "\n")

    if not os.path.exists(os.path.join(exp, "6-name2semantic.tsv")):
        base = json.load(open(os.path.join(REPO, "GPT_SoVITS", "configs",
                                           "s2%s.json" % VERSION), encoding="utf-8"))
        base["data"].update({"n_speakers": 1, "exp_dir": exp})
        base["s2_ckpt_dir"] = exp
        base["model"].pop("version", None)          # 3-get-semantic passes version= itself
        sem = os.path.join(exp, "tmp", "s2_sem.json")
        os.makedirs(os.path.dirname(sem), exist_ok=True)
        json.dump(base, open(sem, "w", encoding="utf-8"), ensure_ascii=False)
        e2 = dict(env, pretrained_s2G=S2G, s2config_path=sem)
        rc, o, e = sh([os.path.join("GPT_SoVITS", "prepare_datasets", "3-get-semantic.py")], env=e2)
        if rc != 0:
            log("semantic FAILED %s" % e[-400:])
            return 5
        shards = sorted(f for f in os.listdir(exp) if f.startswith("6-name2semantic-"))
        buf = [open(os.path.join(exp, f), encoding="utf-8").read().rstrip("\n") for f in shards]
        open(os.path.join(exp, "6-name2semantic.tsv"), "w", encoding="utf-8").write(
            "\n".join(x for x in buf if x) + "\n")

    # ---- train SoVITS ----
    base = json.load(open(os.path.join(REPO, "GPT_SoVITS", "configs", "s2%s.json" % VERSION),
                          encoding="utf-8"))
    base["train"].update({
        "batch_size": 4, "epochs": a.epochs, "text_low_lr_rate": 0.4,
        "pretrained_s2G": S2G, "pretrained_s2D": S2D,
        "if_save_latest": 0, "if_save_every_weights": True, "save_every_epoch": 2,
        "gpu_numbers": "0", "grad_ckpt": False, "lora_rank": 32,
    })
    base["data"]["n_speakers"] = 1
    base["model"]["version"] = VERSION
    base["data"]["exp_dir"] = base["s2_ckpt_dir"] = exp
    base["save_weight_dir"] = SOVITS_OUT
    base["name"] = a.voice
    base["version"] = VERSION
    cfg = os.path.join(exp, "tmp", "s2.json")
    os.makedirs(os.path.dirname(cfg), exist_ok=True)
    json.dump(base, open(cfg, "w", encoding="utf-8"), ensure_ascii=False)
    os.makedirs(os.path.join(exp, "logs_s2_%s" % VERSION), exist_ok=True)
    log("s2_train start epochs=%d" % a.epochs)
    rc, out, err = sh([os.path.join("GPT_SoVITS", "s2_train.py"), "--config", cfg])
    log("s2_train rc=%d %s" % (rc, (out[-400:] + err[-400:]).replace("\n", " | ")))
    if rc != 0:
        return 6

    weights = sorted((f for f in os.listdir(SOVITS_OUT) if f.startswith(a.voice + "_")),
                     key=lambda f: int(re.search(r"_e(\d+)_", f).group(1))
                     if re.search(r"_e(\d+)_", f) else 0)
    json.dump({"voice": a.voice, "clips": len(clips), "minutes": mins,
               "f0_med": float(np.median(f0_all)) if f0_all else 0,
               "weights": weights[-1] if weights else None, "exp": exp,
               "source_meta": src_meta},
              open(os.path.join(root, "voice.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    log("DONE weights=%s" % (weights[-1] if weights else "NONE"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

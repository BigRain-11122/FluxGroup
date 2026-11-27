# LatentSync trial import-chain gap sweep + fix (tick-C2082)
# Root cause: trial FAIL 16:16:09 ModuleNotFoundError soundfile (lipsync_pipeline L38);
# deeper module-level gaps: util.py L20 matplotlib / L21 imageio / L31 decord;
# runtime gaps: read_audio uses decord.AudioReader (L104), write_video uses imageio ffmpeg.
# Fix policy: pip --no-deps into PYLIBS overlay (zero base-env pollution, no numpy/torch shadow),
# decord = no cp313 wheel -> real ffmpeg-subprocess shim package in overlay (musepose av precedent).
import os
import sys
import json
import time
import subprocess
import importlib

FG = r"K:\Fluxgroup\FluxGroup"
LS = os.path.join(FG, "media", "latentsync")
PYLIBS = os.path.join(FG, "media", "pylibs_latentsync")
PIP = r"D:\ComfyUI\python_embeded\python.exe"
MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

sys.path.insert(0, LS)
sys.path.insert(0, PYLIBS)
os.chdir(LS)


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def probe(mod):
    try:
        importlib.import_module(mod)
        return None
    except Exception as e:
        return "%s: %s" % (type(e).__name__, str(e)[:100])


def pip_install(pkgs):
    if not pkgs:
        return
    log("PIP-INSTALL %s" % " ".join(pkgs))
    r = subprocess.run(
        [PIP, "-m", "pip", "install", "--target", PYLIBS, "--no-deps", *pkgs, "-i", MIRROR],
        capture_output=True, text=True,
    )
    tail = "\n".join((r.stdout or "").strip().splitlines()[-3:])
    log("PIP rc=%d %s" % (r.returncode, tail.replace("\n", " | ")))
    if r.returncode != 0:
        log("PIP-ERR %s" % (r.stderr or "")[-300:])


# ---- Phase A: candidate census with exact trial sys.path ----
candidates = ["soundfile", "tqdm", "matplotlib", "imageio", "imageio_ffmpeg",
              "kornia", "regex", "more_itertools", "packaging", "cffi",
              "PIL", "av", "scipy"]
missing = []
for m in candidates:
    err = probe(m)
    if err:
        missing.append((m, err))
    log("PROBE %-16s %s" % (m, err or "OK"))

install_list = []
mnames = [m for m, _ in missing]
for m in mnames:
    if m == "matplotlib":
        install_list += ["matplotlib", "contourpy", "cycler", "fonttools",
                         "kiwisolver", "pyparsing", "python-dateutil", "six"]
    elif m == "soundfile":
        install_list += ["soundfile"]
        if "cffi" in mnames:
            install_list += ["cffi", "pycparser"]
    else:
        install_list.append(m)

# ---- Phase B: install missing ----
pip_install(sorted(set(install_list)))

# ---- Phase C: decord shim (real AudioReader via ffmpeg subprocess; VideoReader via cv2) ----
decord_dir = os.path.join(PYLIBS, "decord")
os.makedirs(decord_dir, exist_ok=True)
shim_path = os.path.join(decord_dir, "__init__.py")
SHIM = '''# decord shim (tick-C2082): no cp313 wheel on the embedded stack; real implementations
# for the latentsync inference path (AudioReader in utils/util.py read_audio, VideoReader unused
# by trial but implemented for safety). ffmpeg subprocess -> f32le PCM -> numpy.
import subprocess

import numpy as np


class _Batch:
    def __init__(self, arr):
        self._arr = arr

    def asnumpy(self):
        return self._arr


class AudioReader:
    def __init__(self, filename, sample_rate=16000, mono=True, block_size=0, **kwargs):
        self.sample_rate = int(sample_rate)
        self.mono = bool(mono)
        self._pcm = None
        r = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-nostdin", "-i", filename,
             "-ac", "1" if self.mono else "2",
             "-ar", str(self.sample_rate), "-f", "f32le", "-"],
            capture_output=True,
        )
        if r.returncode != 0 or not r.stdout:
            raise RuntimeError("decord-shim AudioReader: ffmpeg decode failed rc=%d" % r.returncode)
        data = np.frombuffer(r.stdout, dtype=np.float32).copy()
        if self.mono:
            data = data.reshape(1, -1)
        else:
            data = data.reshape(2, -1)
        self._pcm = data

    def __len__(self):
        return self._pcm.shape[1]

    def __getitem__(self, item):
        if item == slice(None):
            return _Batch(self._pcm)
        if isinstance(item, slice):
            return _Batch(self._pcm[:, item.start: item.stop: item.step])
        return _Batch(self._pcm[:, item])


class VideoReader:
    def __init__(self, filename, **kwargs):
        import cv2
        cap = cv2.VideoCapture(filename)
        if not cap.isOpened():
            raise RuntimeError("decord-shim VideoReader: cannot open %s" % filename)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        self._frames = np.stack(frames) if frames else np.zeros((0, 4, 4, 3), dtype=np.uint8)

    def __len__(self):
        return self._frames.shape[0]

    def __getitem__(self, item):
        if item == slice(None):
            return _Batch(self._frames)
        if isinstance(item, slice):
            return _Batch(self._frames[item])
        return _Batch(self._frames[item])

    def seek(self, pos):
        pass


def cpu():
    return 0
'''
with open(shim_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(SHIM)
log("DECORD-SHIM written %s (%dB)" % (shim_path, os.path.getsize(shim_path)))

# ---- Phase D: iterative full-chain import (catch stragglers) ----
CHAIN = [
    "torch",
    "omegaconf",
    "diffusers",
    "latentsync.models.unet",
    "latentsync.pipelines.lipsync_pipeline",
    "latentsync.whisper.audio2feature",
]
for attempt in range(1, 16):
    for mod in CHAIN:
        err = probe(mod)
        if err:
            log("CHAIN-ATTEMPT%d %s -> %s" % (attempt, mod, err))
            if err.startswith("ModuleNotFoundError"):
                bad = err.split("'")[1].split(".")[0]
                if bad in ("numpy", "torch", "cv2", "torchvision", "PIL", "transformers", "av"):
                    log("FATAL heavyweight gap: %s -- manual adjudication needed" % bad)
                    sys.exit(2)
                pip_install([bad])
                break
            else:
                log("FATAL non-missing import error in %s: %s" % (mod, err))
                sys.exit(2)
    else:
        log("CHAIN-GREEN all 6 chain modules import OK (attempt %d)" % attempt)
        break

print("SWEEP-DONE")

# Runtime IO smoke for latentsync trial path (tick-C2082) - fresh process, CPU-only
# Verifies: decord-shim AudioReader (util.py read_audio path) + imageio write_video path
# + face_detector shim state on disk (J-30). No GPU, no model load.
import os
import sys
import subprocess

FG = r"K:\Fluxgroup\FluxGroup"
LS = os.path.join(FG, "media", "latentsync")
PYLIBS = os.path.join(FG, "media", "pylibs_latentsync")
WORK = os.path.join(FG, "media", "latentsync-deploy", "trial_c2079")

sys.path.insert(0, LS)
sys.path.insert(0, PYLIBS)
os.chdir(LS)

ok = True


def log(msg):
    print(msg, flush=True)


# 1. AudioReader shim smoke on the real trimmed demo audio (trial input face)
audio_in = os.path.join(WORK, "audio_clip.wav")
src = os.path.join(LS, "assets", "demo1_audio.wav")
os.makedirs(WORK, exist_ok=True)
if not os.path.exists(audio_in):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-nostdin", "-i", src, "-t", "3.2", audio_in], check=True)

import numpy as np
import torch
from decord import AudioReader

ar = AudioReader(audio_in, sample_rate=16000, mono=True)
samples = torch.from_numpy(ar[:].asnumpy()).squeeze(0)
dur = samples.shape[0] / 16000.0
log("AUDIO-OK samples=%d dur=%.2fs dtype=%s finite=%s" % (samples.shape[0], dur, samples.dtype, bool(torch.isfinite(samples).all())))
ok = ok and samples.shape[0] > 40000 and bool(torch.isfinite(samples).all())

# replicate util.read_audio contract exactly
def read_audio(audio_path, audio_sample_rate=16000):
    ar = AudioReader(audio_path, sample_rate=audio_sample_rate, mono=True)
    return torch.from_numpy(ar[:].asnumpy()).squeeze(0)


a2 = read_audio(audio_in)
log("READ-AUDIO-CONTRACT shape=%s" % (tuple(a2.shape),))
ok = ok and a2.shape == samples.shape

# 2. VideoReader shim smoke (not on trial path, safety face)
import cv2
video_in = os.path.join(LS, "assets", "demo1_video.mp4")
cap = cv2.VideoCapture(video_in)
n_ref = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()
from decord import VideoReader

vr = VideoReader(video_in)
log("VIDEO-OK frames=%d expected~%d shape=%s" % (len(vr), n_ref, tuple(vr[:].asnumpy().shape)))
ok = ok and abs(len(vr) - n_ref) <= 2

# 3. write_video path smoke (imageio + libx264, same params as util.write_video)
import imageio

test_out = os.path.join(WORK, "smoke_write.mp4")
frames = (np.random.rand(12, 256, 256, 3) * 255).astype(np.uint8)
with imageio.get_writer(test_out, fps=25, codec="libx264", macro_block_size=None,
                        ffmpeg_params=["-crf", "13"], ffmpeg_log_level="error") as w:
    for f in frames:
        w.append_data(f)
size = os.path.getsize(test_out)
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1", test_out],
                       capture_output=True, text=True)
nf = int(probe.stdout.strip().split("=")[1]) if probe.returncode == 0 else -1
log("WRITE-VIDEO-OK bytes=%d frames=%d" % (size, nf))
ok = ok and size > 10000 and nf == 12
os.remove(test_out)

# 4. face_detector on-disk state (J-30 shim must be the live file; bak exists)
fd = os.path.join(LS, "latentsync", "utils", "face_detector.py")
bak = os.path.join(LS, "latentsync", "utils", "face_detector_insightface.bak.py")
body = open(fd, "r", encoding="utf-8").read()
is_shim = "face_alignment" in body and "insightface" not in body
log("FACE-DETECTOR shim_live=%s bak_exists=%s" % (is_shim, os.path.exists(bak)))
ok = ok and is_shim and os.path.exists(bak)

# 5. weights on disk (trial gate face)
unet = os.path.join(LS, "checkpoints", "latentsync_unet.pt")
log("UNET bytes=%d" % os.path.getsize(unet))
ok = ok and os.path.getsize(unet) >= 5000000000

print("SMOKE-%s" % ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)

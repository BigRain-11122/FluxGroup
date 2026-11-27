# LatentSync v1.5 smoke trial runner (POOL-0016 night-1 leg) - authored by tick-C2079
# J-30 compliance: insightface = NC red-line -> FaceAlignmentDetector shim (face_alignment 1.4.1,
#   2DFAN4 + s3fd, weights pre-seeded by latentsync-weights-dl2 into checkpoints/aux).
# Contract-preserving: ImageProcessor.affine_transform consumes only lmk indices
#   [43,48,49,50,51]=left brow center, [101:106]=right brow center, [74,77,83,86]=nose center;
#   detector bbox is discarded (ImageProcessor overwrites box with warped-face dims).
# v1.5 config reconcile: configs/unet/stage2_512.yaml (cross_attention_dim 384 -> whisper tiny).
# Bank-fired detached runner; verdict JSON + TRIAL-RESULT + TRIAL-END sentinel; VRAM wait gate.
import os
import sys
import json
import time
import shutil
import subprocess

FG = r"K:\Fluxgroup\FluxGroup"
LS = os.path.join(FG, "media", "latentsync")
PYLIBS = os.path.join(FG, "media", "pylibs_latentsync")
DEPLOY = os.path.join(FG, "media", "latentsync-deploy")
SDVAE = os.path.join(FG, "media", "musepose", "pretrained_weights", "sd-vae-ft-mse")
AUX = os.path.join(LS, "checkpoints", "aux")
UNET = os.path.join(LS, "checkpoints", "latentsync_unet.pt")
WHISPER = os.path.join(LS, "checkpoints", "whisper", "tiny.pt")
VD2 = os.path.join(DEPLOY, "weights2_verdict.json")
WORK = os.path.join(DEPLOY, "trial_c2079")
VERDICT = os.path.join(DEPLOY, "latentsync_trial_verdict.json")
RESULT = os.path.join(DEPLOY, "TRIAL-RESULT.txt")
MIN_UNET = 5000000000
VRAM_WAIT_MIN = 8000  # v1.5 8GB tier + headroom (C2074 deploy note)
AUDIO_CLIP_S = 3.2


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def vram_free_mb():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], text=True
        )
        return int(out.strip().splitlines()[0])
    except Exception:
        return 0


def finish(status, payload):
    payload["status"] = status
    payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(VERDICT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=True)
    with open(RESULT, "w", encoding="utf-8") as f:
        f.write("STATUS %s\n" % status)
    log("TRIAL-VERDICT %s -> %s" % (status, VERDICT))
    log("TRIAL-END status=%s" % status)
    sys.exit(0 if status == "PASS" else 1)


# FaceAlignment shim replacing insightface-based face_detector.py (J-30).
# Keeps class name + __call__ contract ((bbox, lmk106) | (None, None)).
SHIM = '''# J-30 shim: insightface swapped for face_alignment (NC red-line compliance, tick-C2079)
import numpy as np


class FaceDetector:
    def __init__(self, device="cuda"):
        import face_alignment

        self.fa = face_alignment.FaceAlignment(face_alignment.LandmarksType.TWO_D, device=device, flip_input=False)

    def __call__(self, frame, threshold=0.5):
        lmks = self.fa.get_landmarks(frame)
        if not lmks:
            return None, None
        # pick the largest face by landmark extent
        def area(p):
            return (p[:, 0].max() - p[:, 0].min()) * (p[:, 1].max() - p[:, 1].min())

        pts = max(lmks, key=area)
        left_brow = pts[17:22].mean(axis=0)
        right_brow = pts[22:27].mean(axis=0)
        nose = pts[27:36].mean(axis=0)
        lmk106 = np.zeros((106, 2))
        for i in (43, 48, 49, 50, 51):
            lmk106[i] = left_brow
        for i in range(101, 106):
            lmk106[i] = right_brow
        for i in (74, 77, 83, 86):
            lmk106[i] = nose
        x1 = float(pts[:, 0].min())
        x2 = float(pts[:, 0].max())
        y1 = float(pts[:, 1].min())
        y2 = float(pts[:, 1].max())
        return (x1, y1, x2, y2), lmk106


def cuda_to_int(cuda_str):
    return 0


LMK_ADAPT_ORIGIN_ORDER = []
'''


def main():
    t0 = time.time()
    log("TRIAL-START LatentSync v1.5 smoke trial (POOL-0016 night-1, C2079, J-30 FaceAlignment)")
    payload = {"leg": "POOL-0016 night-1 latentsync trial", "runner": "latentsync_trial_c2079.py"}

    # 0. gates: weights2 verdict + unet size + whisper + aux models
    if not os.path.exists(VD2):
        finish("FAIL", dict(payload, reason="weights2_verdict.json missing (dl2 not harvested)"))
    if not (os.path.exists(UNET) and os.path.getsize(UNET) >= MIN_UNET):
        finish("FAIL", dict(payload, reason="unet missing/short", unet_bytes=os.path.getsize(UNET) if os.path.exists(UNET) else 0))
    if not (os.path.exists(WHISPER) and os.path.getsize(WHISPER) >= 70000000):
        finish("FAIL", dict(payload, reason="whisper tiny.pt missing/short"))
    for name in ("2DFAN4-cd938726ad.zip", "s3fd-619a316812.pth"):
        if not os.path.exists(os.path.join(AUX, name)):
            finish("FAIL", dict(payload, reason="aux model missing: " + name))

    # 1. torch hub pre-seed (face_alignment loads via torch.hub.get_dir()/checkpoints)
    hubdir = os.path.join(os.path.expanduser("~"), ".cache", "torch", "hub", "checkpoints")
    os.makedirs(hubdir, exist_ok=True)
    for name in ("2DFAN4-cd938726ad.zip", "s3fd-619a316812.pth"):
        dst = os.path.join(hubdir, name)
        if os.path.exists(dst):
            log("HUB-PRESENT %s" % name)
        elif os.path.exists(os.path.join(AUX, name)):
            shutil.copy2(os.path.join(AUX, name), dst)
            log("HUB-SEED %s" % name)
        else:
            finish("FAIL", dict(payload, reason="cannot seed hub file " + name))

    # 2. overlay + repo on sys.path
    sys.path.insert(0, LS)
    sys.path.insert(0, PYLIBS)

    # 3. J-30 shim: swap face_detector.py in-place (backup original once)
    fd_path = os.path.join(LS, "latentsync", "utils", "face_detector.py")
    bak_path = os.path.join(LS, "latentsync", "utils", "face_detector_insightface.bak.py")
    if not os.path.exists(bak_path):
        shutil.copy2(fd_path, bak_path)
        log("SHIM-BACKUP %s" % os.path.basename(bak_path))
    with open(fd_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(SHIM)
    pyc = os.path.join(LS, "latentsync", "utils", "__pycache__", "face_detector.cpython-313.pyc")
    if os.path.exists(pyc):
        os.remove(pyc)
    log("SHIM-WRITE face_detector.py -> FaceAlignmentDetector contract")

    # 4. import chain (fail-loud with exact error into verdict)
    os.chdir(LS)
    try:
        import torch
        from omegaconf import OmegaConf
        from diffusers import AutoencoderKL, DDIMScheduler
        from latentsync.models.unet import UNet3DConditionModel
        from latentsync.pipelines.lipsync_pipeline import LipsyncPipeline
        from latentsync.whisper.audio2feature import Audio2Feature
    except Exception as e:
        finish("FAIL", dict(payload, reason="import chain: " + repr(e)[:500]))

    # 5. VRAM wait gate (comfy server + fleet coexist)
    waited = 0
    while vram_free_mb() < VRAM_WAIT_MIN:
        if waited >= 1200:
            finish("FAIL", dict(payload, reason="vram gate timeout 20min", free_mb=vram_free_mb()))
        time.sleep(30)
        waited += 30
    log("VRAM-GATE open free=%dMB waited=%ds" % (vram_free_mb(), waited))

    # 6. pipeline assembly (v1.5 reconcile: stage2_512 + whisper tiny 384 + local sd-vae)
    cfg = OmegaConf.load(os.path.join(LS, "configs", "unet", "stage2_512.yaml"))
    model_cfg = OmegaConf.to_container(cfg.model)
    if model_cfg.get("cross_attention_dim") != 384:
        finish("FAIL", dict(payload, reason="config reconcile: cross_attention_dim != 384"))
    vae = AutoencoderKL.from_pretrained(SDVAE, torch_dtype=torch.float16)
    vae.config.scaling_factor = 0.18215
    vae.config.shift_factor = 0
    audio_encoder = Audio2Feature(
        model_path=WHISPER,
        device="cuda",
        num_frames=cfg.data.num_frames,
        audio_feat_length=list(cfg.data.audio_feat_length),
    )
    scheduler = DDIMScheduler.from_pretrained("configs")
    try:
        unet, _ = UNet3DConditionModel.from_pretrained(model_cfg, UNET, device="cpu")
    except Exception as e:
        finish("FAIL", dict(payload, reason="unet from_pretrained (v1.5 state-dict reconcile): " + repr(e)[:800]))
    unet = unet.to(dtype=torch.float16)
    pipeline = LipsyncPipeline(
        vae=vae, audio_encoder=audio_encoder, unet=unet, scheduler=scheduler
    ).to("cuda")

    # 7. trial inputs: repo demo assets, audio trimmed to AUDIO_CLIP_S
    video_in = os.path.join(LS, "assets", "demo1_video.mp4")
    audio_src = os.path.join(LS, "assets", "demo1_audio.wav")
    if not (os.path.exists(video_in) and os.path.exists(audio_src)):
        finish("FAIL", dict(payload, reason="repo demo assets missing", video=os.path.exists(video_in), audio=os.path.exists(audio_src)))
    os.makedirs(WORK, exist_ok=True)
    audio_in = os.path.join(WORK, "audio_clip.wav")
    rc = subprocess.call(
        ["ffmpeg", "-y", "-loglevel", "error", "-nostdin", "-i", audio_src, "-t", str(AUDIO_CLIP_S), audio_in],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if rc != 0 or not os.path.exists(audio_in):
        finish("FAIL", dict(payload, reason="ffmpeg audio trim rc=%d" % rc))
    out_mp4 = os.path.join(WORK, "out.mp4")

    # 8. run inference (deepcache off; mask path relative to LS cwd)
    t_inf = time.time()
    try:
        pipeline(
            video_path=video_in,
            audio_path=audio_in,
            video_out_path=out_mp4,
            num_frames=int(cfg.data.num_frames),
            video_fps=int(cfg.data.video_fps),
            audio_sample_rate=int(cfg.data.audio_sample_rate),
            height=512,
            width=512,
            num_inference_steps=20,
            guidance_scale=1.5,
            weight_dtype=torch.float16,
            mask_image_path="latentsync/utils/mask.png",
            temp_dir=os.path.join(WORK, "temp"),
        )
    except Exception as e:
        finish("FAIL", dict(payload, reason="inference: " + repr(e)[:800], wall_s=int(time.time() - t_inf)))

    # 9. adjudicate: mp4 >= 100KB + ffprobe frames > 0 + J-30 evidence (no insightface module)
    out_bytes = os.path.getsize(out_mp4) if os.path.exists(out_mp4) else 0
    frames = -1
    try:
        probe = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
             "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1", out_mp4],
            text=True, stderr=subprocess.DEVNULL)
        frames = int(probe.strip().splitlines()[0].split("=")[1])
    except Exception:
        frames = -1
    j30_ok = "insightface" not in sys.modules
    ok = out_bytes >= 100000 and frames > 0 and j30_ok
    payload.update(out_bytes=out_bytes, frames=frames, j30_no_insightface=j30_ok,
                   inference_wall_s=int(time.time() - t_inf), total_wall_s=int(time.time() - t0),
                   vram_peak_note="sampled free at start %dMB" % vram_free_mb())
    finish("PASS" if ok else "FAIL", payload)


if __name__ == "__main__":
    main()

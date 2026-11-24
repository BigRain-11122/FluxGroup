# musepose_trial_c2066.py -- MusePose night3 smoke trial runner (bm-c C2066,
# POOL-0016 contrast leg). Bank-fired by BmcIdleGuard; self-verifying.
#
# Phases:
#   VERIFY: weights_verdict ok==12 + 6 .pth on disk + mimic onnx DWPose pair
#     + CPU-only import-chain probe (hub stub + torch.load wrapper) -- zero GPU
#     burn before the chain is proven importable.
#   POSE:  render the pose-conditioning video for the trial using the mimic
#     r1058 onnx DWPose detector (proven CPU onnxruntime on this env) +
#     musepose's own pose/script/dwpose.py renderer (keypoint formats are the
#     same normalized openpose-lineage dict; draw_pose consumes it directly).
#     Driver = repo demo assets/videos/dance.mp4, 24 frames, stride 3,
#     rendered short-edge 1024 -> saved short-edge 768 (draw_dwpose.py math),
#     written fps 12 via av. musepose's own mmpose/mmdet extraction chain is
#     NOT installable on py3.13 (C2063 triage law) -- the onnx leg replaces it
#     for smoke purposes only (noted in receipt).
#   TRIAL: tier ladder subprocess via musepose_trial_launcher_c2066.py:
#     tier1 384x640 L24 S24 O4 / tier2 256x448 L16 S16 O4, steps 6 (CEO
#     efficiency law, mimic r1058 precedent), cfg 3.5, seed 42, fps 12.
#     VRAM sampled every 3s; 60-min cap per tier; first rc==0 + mp4>=100KB wins.
#   RECEIPT: trial dir JSON + TRIAL-RESULT.txt + verdict file for bank harvest
#     + TRIAL-END final line (log sentinel law).
# ASCII-only output (B1324 purge law).

import json
import os
import subprocess
import sys
import time

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

REPO = r"K:\Fluxgroup\FluxGroup\media\musepose"
DEPLOY = r"K:\Fluxgroup\FluxGroup\media\musepose-deploy"
MMREPO = r"K:\Fluxgroup\FluxGroup\media\mvtools\MimicMotion"
MMPYLIBS = os.path.join(MMREPO, "pylibs_mimic")
PYLIBS = r"K:\Fluxgroup\FluxGroup\media\pylibs_musepose"
IDLEKIT = r"K:\Fluxgroup\FluxGroup\cph4\fleet\idle-guard-kit"
PYEXE = r"D:\ComfyUI\python_embeded\python.exe"
LAUNCHER = os.path.join(IDLEKIT, "musepose_trial_launcher_c2066.py")

TRIAL = os.path.join(REPO, "trial_c2066")
OUTROOT = os.path.join(REPO, "output")
POSE_MP4 = os.path.join(TRIAL, "pose_dance_c2066.mp4")
DRIVER = os.path.join(REPO, "assets", "videos", "dance.mp4")
REF_PNG = os.path.join(REPO, "assets", "images", "ref.png")
VERDICT_F = os.path.join(DEPLOY, "musepose_trial_verdict.json")
RUNLOG = os.path.join(TRIAL, "trial_run.log")
DWP_ONNX = os.path.join(MMREPO, "models", "DWPose", "dw-ll_ucoco_384.onnx")
YOLOX_ONNX = os.path.join(MMREPO, "models", "DWPose", "yolox_l.onnx")
ONNX_MIN = 100 * 1048576
N_POSE_FRAMES = 24
POSE_STRIDE = 3
POSE_FPS = 12
NO_WINDOW = 0x08000000
TIERS = [  # (W, H, L, S, O)
    (384, 640, 24, 24, 4),
    (256, 448, 16, 16, 4),
]
STEPS = 6
CFG = 3.5
SEED = 42

YAML_TMPL = """pretrained_base_model_path: './pretrained_weights/sd-image-variations-diffusers'
pretrained_vae_path: './pretrained_weights/sd-vae-ft-mse'
image_encoder_path: './pretrained_weights/image_encoder'
denoising_unet_path: "./pretrained_weights/MusePose/denoising_unet.pth"
reference_unet_path: "./pretrained_weights/MusePose/reference_unet.pth"
pose_guider_path: "./pretrained_weights/MusePose/pose_guider.pth"
motion_module_path: "./pretrained_weights/MusePose/motion_module.pth"
inference_config: "./configs/inference_v2.yaml"
weight_dtype: 'fp16'

test_cases:
  '%(ref)s':
    - '%(pose)s'
"""

IMPORT_PROBE = (
    "import sys; p=[%r,%r,%r,%r]; "
    "[sys.path.insert(0,x) for x in p[::-1]]; "
    "import huggingface_hub; "
    "huggingface_hub.cached_download = lambda *a, **k: None; "
    "import torch; _o=torch.load; "
    "torch.load = lambda *a, **k: _o(*a, **{**k, 'weights_only': False}); "
    "import diffusers; "
    "from diffusers import AutoencoderKL, DDIMScheduler; "
    "from diffusers.pipelines.stable_diffusion import StableDiffusionPipeline; "
    "from transformers import CLIPImageProcessor, CLIPVisionModelWithProjection; "
    "from musepose.models.pose_guider import PoseGuider; "
    "from musepose.models.unet_2d_condition import UNet2DConditionModel; "
    "from musepose.models.unet_3d import UNet3DConditionModel; "
    "from musepose.pipelines.pipeline_pose2vid_long import Pose2VideoPipeline; "
    "from musepose.utils.util import get_fps, read_frames, save_videos_grid; "
    "from pose.script.dwpose import draw_pose; "
    "from pose.script.tool import save_videos_from_pil; "
    "from mimicmotion.dwpose.dwpose_detector import DWposeDetector; "
    "import onnxruntime; "
    "print('IMPORT-CHAIN-OK')"
    % (REPO, PYLIBS, MMPYLIBS, MMREPO)
)


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        with open(RUNLOG, "a", encoding="ascii", errors="replace") as f:
            f.write(line + "\n")
    except OSError:
        pass


def fsize(p):
    try:
        return os.path.getsize(p)
    except OSError:
        return 0


def vram_sample():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20,
            creationflags=NO_WINDOW)
        used, total = [int(x.strip()) for x in out.stdout.strip().split(",")]
        return used, total
    except Exception:
        return -1, -1


def verify_phase():
    vf = os.path.join(DEPLOY, "weights_verdict.json")
    ok = False
    try:
        with open(vf, "r", encoding="utf-8") as f:
            vj = json.load(f)
        ok = (vj.get("ok") == vj.get("total") == 12 and not vj.get("missing"))
    except Exception:
        pass
    pw = os.path.join(REPO, "pretrained_weights")
    pth_count = 0
    for root, _dirs, files in os.walk(pw):
        for fn in files:
            if fn.endswith(".pth"):
                pth_count += 1
    onnx_ok = fsize(DWP_ONNX) >= ONNX_MIN and fsize(YOLOX_ONNX) >= ONNX_MIN
    log("VERIFY weights_verdict12=%s pth=%d onnx_pair=%s (%d/%dMB)"
        % (ok, pth_count, onnx_ok, fsize(DWP_ONNX) // 1048576,
           fsize(YOLOX_ONNX) // 1048576))
    if not (ok and pth_count >= 6 and onnx_ok):
        return False
    env = dict(os.environ)
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    try:
        r = subprocess.run([PYEXE, "-c", IMPORT_PROBE], capture_output=True,
                           text=True, timeout=300, env=env,
                           creationflags=NO_WINDOW)
    except subprocess.TimeoutExpired:
        log("VERIFY import probe TIMEOUT")
        return False
    if r.returncode == 0 and "IMPORT-CHAIN-OK" in r.stdout:
        log("VERIFY import-chain probe OK")
        return True
    log("VERIFY import probe FAILED rc=%s" % r.returncode)
    tail = (r.stderr or "")[-1500:]
    log("VERIFY probe stderr tail: %s" % tail.replace("\n", " | "))
    return False


def pose_phase():
    """Extract 24 dwpose keypoint frames from the demo driver video with the
    mimic onnx detector, render them with musepose's own renderer, write the
    pose-conditioning mp4. Returns True on success."""
    if fsize(POSE_MP4) >= 100 * 1024:
        log("POSE existing pose mp4 found (%dMB), skip"
            % (fsize(POSE_MP4) // 1048576))
        return True
    import av
    import cv2
    import numpy as np
    from PIL import Image

    sys.path.insert(0, MMREPO)
    sys.path.insert(0, MMPYLIBS)
    sys.path.insert(0, PYLIBS)
    sys.path.insert(0, REPO)
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    from mimicmotion.dwpose.dwpose_detector import DWposeDetector as MMDet
    from pose.script.dwpose import draw_pose
    from pose.script.tool import save_videos_from_pil

    det = MMDet(model_det=YOLOX_ONNX, model_pose=DWP_ONNX, device="cpu")

    container = av.open(DRIVER)
    vstream = next(s for s in container.streams if s.type == "video")
    src_w, src_h = vstream.width, vstream.height
    need = N_POSE_FRAMES * POSE_STRIDE
    grabbed = 0
    frames = []
    t0 = time.time()
    for packet in container.demux(vstream):
        for frame in packet.decode():
            if grabbed % POSE_STRIDE == 0:
                img = Image.frombytes(
                    "RGB", (frame.width, frame.height),
                    np.ascontiguousarray(frame.to_rgb().to_ndarray()))
                frames.append(img)
                if len(frames) >= N_POSE_FRAMES:
                    grabbed = need  # break outer too
                    break
            grabbed += 1
        if len(frames) >= N_POSE_FRAMES:
            break
    container.close()
    log("POSE read %d/%d frames (%.0fs)"
        % (len(frames), need, time.time() - t0))
    if len(frames) < N_POSE_FRAMES:
        log("POSE short driver video (%d frames), abort" % len(frames))
        return False

    # render geometry per draw_dwpose.py law: short edge 1024 render, 768 save
    k_render = float(1024) / min(src_w, src_h)
    h_render = int(k_render * src_h // 2 * 2)
    w_render = int(k_render * src_w // 2 * 2)
    k_save = float(768) / min(src_w, src_h)
    h_save = int(k_save * src_h // 2 * 2)
    w_save = int(k_save * src_w // 2 * 2)
    t0 = time.time()
    pil_frames = []
    for i, pil_img in enumerate(frames):
        pose = det(np.array(pil_img))
        canvas = draw_pose(pose, h_render, w_render, False)
        canvas = cv2.resize(canvas, (w_save, h_save),
                            interpolation=cv2.INTER_AREA)
        canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        pil_frames.append(Image.fromarray(canvas))
        if (i + 1) % 6 == 0:
            log("POSE rendered %d/%d (%.0fs)" % (i + 1, len(frames),
                                                 time.time() - t0))
    save_videos_from_pil(pil_frames, POSE_MP4, fps=POSE_FPS)
    ok = fsize(POSE_MP4) >= 50 * 1024
    log("POSE pose mp4 %s (%dMB, %d frames, %.0fs)"
        % (POSE_MP4, fsize(POSE_MP4) // 1048576, len(pil_frames),
           time.time() - t0))
    return ok


def run_tier(tier_idx, t):
    w, h, length, s, o = t
    yaml_path = os.path.join(TRIAL, "tier%d_c2066.yaml" % tier_idx)
    with open(yaml_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(YAML_TMPL % {"ref": REF_PNG, "pose": POSE_MP4})
    env = dict(os.environ)
    env["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:256"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    t0 = time.time()
    err_path = os.path.join(TRIAL, "tier%d.err" % tier_idx)
    errf = open(err_path, "wb")
    proc = subprocess.Popen(
        [PYEXE, LAUNCHER, "--config", yaml_path,
         "-W", str(w), "-H", str(h), "-L", str(length),
         "-S", str(s), "-O", str(o),
         "--cfg", str(CFG), "--seed", str(SEED), "--steps", str(STEPS),
         "--skip", "0", "--fps", str(POSE_FPS)],
        creationflags=NO_WINDOW, env=env,
        stdout=subprocess.DEVNULL, stderr=errf)
    peak_mem, samples = 0, 0
    _, total_mem = vram_sample()
    while True:
        rc = proc.poll()
        mem, _tot = vram_sample()
        if mem >= 0:
            samples += 1
            peak_mem = max(peak_mem, mem)
        if rc is not None:
            errf.close()
            break
        if time.time() - t0 > 3600:
            proc.kill()
            errf.close()
            rc = -9
            log("TIER-%d TIMEOUT 60min, killed" % tier_idx)
            break
        time.sleep(3)
    wall = time.time() - t0
    # locate output mp4 (test_stage_2 writes under ./output/video-<date>/...)
    mp4, mp4_size = "", 0
    if os.path.isdir(OUTROOT):
        for root, _dirs, files in os.walk(OUTROOT):
            for fn in files:
                if fn.endswith(".mp4"):
                    p = os.path.join(root, fn)
                    if os.path.getmtime(p) >= t0 and fsize(p) > mp4_size:
                        mp4, mp4_size = p, fsize(p)
    oom = False
    tail = ""
    try:
        tail = open(err_path, "rb").read()[-4000:].decode("utf-8", "replace")
    except OSError:
        pass
    if rc != 0:
        oom = ("out of memory" in tail.lower()
               or "OutOfMemoryError" in tail)
    out_frames, out_w, out_h = -1, -1, -1
    if mp4 and mp4_size >= 100 * 1024:
        try:
            import av
            c = av.open(mp4)
            st = next(x for x in c.streams if x.type == "video")
            out_w, out_h = st.width, st.height
            out_frames = sum(1 for _ in c.decode(st.video))
            c.close()
        except Exception:
            pass
    log("TIER-%d rc=%s wall=%.0fs peak_vram=%dMB(%dMB card) mp4=%s(%dMB) "
        "decoded=%d@%dx%d oom=%s"
        % (tier_idx, rc, wall, peak_mem, total_mem,
           os.path.basename(mp4), mp4_size // 1048576,
           out_frames, out_w, out_h, oom))
    return {"tier": tier_idx, "wh": [w, h], "L": length, "S": s, "O": o,
            "rc": rc, "wall_s": round(wall, 1), "peak_vram_mb": peak_mem,
            "oom": oom, "mp4": mp4, "mp4_bytes": mp4_size,
            "decoded_frames": out_frames, "out_wh": [out_w, out_h],
            "err_tail": tail[-1200:]}


def write_receipt(result):
    os.makedirs(TRIAL, exist_ok=True)
    jp = os.path.join(TRIAL, "bmc_musepose_trial_c2066.json")
    with open(jp, "w", encoding="ascii", errors="replace") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(TRIAL, "TRIAL-RESULT.txt"), "w") as f:
        f.write("%s tier=%s\n" % (result.get("status", "?"),
                                  result.get("passed_tier", "-")))
    v = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "status": result.get("status"),
         "passed_tier": result.get("passed_tier"),
         "attempts": [{k: a.get(k) for k in
                       ("tier", "wh", "L", "rc", "wall_s", "peak_vram_mb",
                        "oom", "mp4_bytes", "decoded_frames")}
                      for a in result.get("attempts", [])],
         "pose_mp4_bytes": fsize(POSE_MP4),
         "runner": "musepose_trial_c2066.py"}
    with open(VERDICT_F, "w", encoding="ascii", errors="replace") as f:
        json.dump(v, f, indent=1)
    log("TRIAL-END status=%s" % result.get("status"))


def main():
    os.makedirs(TRIAL, exist_ok=True)
    log("TRIAL-START MusePose night3 smoke (POOL-0016 contrast leg, C2066)")
    base_mem, total_mem = vram_sample()
    log("BASELINE vram_used=%dMB total=%dMB" % (base_mem, total_mem))
    result = {"started": time.strftime("%Y-%m-%d %H:%M:%S"),
              "pool": "POOL-0016-night3-musepose",
              "runner": "musepose_trial_c2066.py",
              "vram_baseline_mb": base_mem,
              "profile": {"steps": STEPS, "cfg": CFG, "seed": SEED,
                          "pose_frames": N_POSE_FRAMES,
                          "pose_stride": POSE_STRIDE,
                          "pose_fps": POSE_FPS}}
    if not verify_phase():
        result["status"] = "VERIFY_FAILED"
        write_receipt(result)
        return
    # short VRAM wait: weights fp16 ~6GB + transients need ~9GB free
    for i in range(20):
        mem, total = vram_sample()
        if mem < 0 or (total - mem) >= 9000:
            break
        log("VRAM-WAIT r%d used=%dMB free=%dMB <9000MB" % (i, mem, total - mem))
        time.sleep(60)
    if not pose_phase():
        result["status"] = "POSE_FAILED"
        write_receipt(result)
        return
    attempts = []
    for idx, t in enumerate(TIERS):
        att = run_tier(idx, t)
        attempts.append(att)
        if att["rc"] == 0 and att["mp4_bytes"] >= 100 * 1024:
            result["status"] = "PASS"
            result["passed_tier"] = idx + 1
            break
    if "status" not in result:
        result["status"] = "FAIL"
    result["attempts"] = attempts
    write_receipt(result)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        import traceback
        with open(RUNLOG, "a", encoding="ascii", errors="replace") as f:
            f.write("[%s] FATAL-EXC in main()\n" % time.strftime("%H:%M:%S"))
            traceback.print_exc(file=f)
        try:
            write_receipt({"started": "?",
                           "pool": "POOL-0016-night3-musepose",
                           "runner": "musepose_trial_c2066.py",
                           "status": "RUNNER_CRASH", "attempts": []})
        except Exception:
            pass

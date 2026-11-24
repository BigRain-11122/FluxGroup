# musepose_stitch72_c2071.py -- MusePose night3 winner-tool 72f segment-stitch
# runner (bm-c C2071, POOL-0016 tail). Bank-fired by BmcIdleGuard; self-verifying.
# C2070 verdict root-cause: pipeline_pose2vid_long does NOT auto-extend over a
# 72f pose clip (-L caps at the single window). This runner produces the 72f
# clip by segment-stitch: 3 windows of L24 S24 O4 at the proven tier-0 geometry
# (384x640, peak 13373MB, 90s/window), then ffmpeg concat -c copy (stream-safe:
# identical encoder settings per window).
# v2 FIX-1 (C2073, 12:39 FAIL post-mortem): test_stage_2.py treats --skip as a
# frame STRIDE (pose_images[::skip+1]; L//（skip+1)), NOT a window start offset.
# --skip 24 sampled the 72f clip at stride 25 -> L=24//25=0 -> empty pose_list
# -> IndexError at pose_list[-1] (both WIN-1/2 deaths). Fix = pre-cut the pose
# clip into 3 exact 24f segments (ffmpeg select between(n,A,B) re-encode,
# ffprobe-verified) and run EVERY window with --skip 0 (the proven WIN-0 path)
# on its own segment. Zero upstream (test_stage_2.py) surgery.
# v2 FIX-2 (C2073): save_videos_grid also writes a 3-row comparison board
# (suffix __.mp4, ~3x width, LARGER bytes than the clean result). Old max-size
# discovery picked the board (WIN-0 evidence: 1233218B 2312px board vs 958434B
# 768x1364 clean result) -> concat would have assembled boards. Fix = drop
# __-suffix boards, pick the clean result, assert picked width == pose width.
# In-run av decode face (-1 known probe face, C2070) is AVOIDED:
# frame counts via ffprobe, concat via ffmpeg -f concat. av/PIL re-encode is
# the fallback leg only.
# PASS gate (C2070 upgrade kept): all 3 windows rc==0 + mp4>=100KB, stitched
# mp4>=100KB + ffprobe frames>=60 (72 expected).
# ASCII-only output (B1324 purge law).

import json
import os
import shutil
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

TRIAL = os.path.join(REPO, "trial_c2071")
OUTROOT = os.path.join(REPO, "output")
# reuse the 72f pose conditioning clip rendered by C2070 (stride-1, 72 frames)
POSE_MP4 = os.path.join(REPO, "trial_c2070", "pose_dance_c2070.mp4")
DRIVER = os.path.join(REPO, "assets", "videos", "dance.mp4")
REF_PNG = os.path.join(REPO, "assets", "images", "ref.png")
STITCH_MP4 = os.path.join(TRIAL, "stitch72_c2071.mp4")
VERDICT_F = os.path.join(DEPLOY, "musepose_stitch72_verdict.json")
RUNLOG = os.path.join(TRIAL, "stitch_run.log")
DWP_ONNX = os.path.join(MMREPO, "models", "DWPose", "dw-ll_ucoco_384.onnx")
YOLOX_ONNX = os.path.join(MMREPO, "models", "DWPose", "yolox_l.onnx")
ONNX_MIN = 100 * 1048576
POSE_FPS = 12
NO_WINDOW = 0x08000000
# winner geometry from C2070 trial72 tier-0: (W, H, L, S, O)
W, H, L, S, O = 384, 640, 24, 24, 4
# v2: segment start frame indices for the 72f pose clip (NOT --skip values).
# SKIPS meaning changed in C2073: --skip is now hardcoded 0 per window.
SEG_STARTS = [0, 24, 48]
POSE_W = 0  # set by cut_segments() from the pose source (expected 768)
STEPS = 6
CFG = 3.5
SEED = 42
FIX_TAG = "c2073-segcut-cleanpick-v2"
FFMPEG = shutil.which("ffmpeg") or ""
FFPROBE = shutil.which("ffprobe") or ""

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


def ffprobe_frames(path):
    if not FFPROBE:
        return -1
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-count_frames", "-show_entries", "stream=nb_read_frames",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=120,
            creationflags=NO_WINDOW)
        return int(r.stdout.strip().split(",")[-1])
    except Exception:
        return -1


def probe_width(path):
    if not FFPROBE or not path:
        return -1
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=60,
            creationflags=NO_WINDOW)
        return int(r.stdout.strip().split(",")[0])
    except Exception:
        return -1


def cut_segments():
    # FIX-1 face: exact 24f per-window pose segments so --skip can stay 0.
    global POSE_W
    pose_w = probe_width(POSE_MP4)
    if pose_w <= 0:
        log("SEGCUT pose width probe failed")
        return [], -1
    POSE_W = pose_w
    segs = []
    for idx, start in enumerate(SEG_STARTS):
        seg = os.path.join(TRIAL, "pose_seg%d_c2073.mp4" % idx)
        if not (fsize(seg) >= 50 * 1024 and ffprobe_frames(seg) == L):
            r = None
            for flag in (["-fps_mode", "passthrough"], ["-vsync", "0"]):
                r = subprocess.run(
                    [FFMPEG, "-y", "-v", "error", "-i", POSE_MP4,
                     "-vf", "select='between(n,%d,%d)'" % (start, start + L - 1),
                     flag[0], flag[1],
                     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", seg],
                    capture_output=True, text=True, timeout=300,
                    creationflags=NO_WINDOW)
                if r.returncode == 0:
                    break
                log("SEGCUT win%d flag=%s rc=%s err=%s"
                    % (idx, flag[0], r.returncode,
                       (r.stderr or "").strip().replace("\n", " | ")[:300]))
            if r is None or r.returncode != 0:
                log("SEGCUT win%d FAILED both fps-mode fallbacks" % idx)
                return [], pose_w
        n = ffprobe_frames(seg)
        w = probe_width(seg)
        log("SEGCUT win%d seg=%s frames=%d width=%d bytes=%d"
            % (idx, os.path.basename(seg), n, w, fsize(seg)))
        if n != L or w != pose_w or fsize(seg) < 50 * 1024:
            log("SEGCUT win%d gate FAILED (need frames=%d width=%d >=50KB)"
                % (idx, L, pose_w))
            return [], pose_w
        segs.append(seg)
    return segs, pose_w


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
    pose_ok = fsize(POSE_MP4) >= 100 * 1024
    log("VERIFY weights_verdict12=%s pth=%d onnx_pair=%s pose72=%s "
        "ffmpeg=%s ffprobe=%s"
        % (ok, pth_count, onnx_ok, pose_ok,
           os.path.basename(FFMPEG) if FFMPEG else "MISSING",
           os.path.basename(FFPROBE) if FFPROBE else "MISSING"))
    if not (ok and pth_count >= 6 and onnx_ok):
        return False
    if not pose_ok:
        log("VERIFY pose clip missing (expected trial_c2070 72f pose), "
            "abort -- re-render is trial72's face, not stitch's")
        return False
    if not FFMPEG or not FFPROBE:
        log("VERIFY ffmpeg/ffprobe missing, concat leg unavailable")
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


def run_window(idx, pose_src, captured):
    yaml_path = os.path.join(TRIAL, "win%d_c2071.yaml" % idx)
    with open(yaml_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(YAML_TMPL % {"ref": REF_PNG, "pose": pose_src})
    env = dict(os.environ)
    env["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:256"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    t0 = time.time()
    err_path = os.path.join(TRIAL, "win%d.err" % idx)
    errf = open(err_path, "wb")
    proc = subprocess.Popen(
        [PYEXE, LAUNCHER, "--config", yaml_path,
         "-W", str(W), "-H", str(H), "-L", str(L),
         "-S", str(S), "-O", str(O),
         "--cfg", str(CFG), "--seed", str(SEED), "--steps", str(STEPS),
         "--skip", "0", "--fps", str(POSE_FPS)],
        creationflags=NO_WINDOW, env=env,
        stdout=subprocess.DEVNULL, stderr=errf)
    peak_mem = 0
    _, total_mem = vram_sample()
    while True:
        rc = proc.poll()
        mem, _tot = vram_sample()
        if mem >= 0:
            peak_mem = max(peak_mem, mem)
        if rc is not None:
            errf.close()
            break
        if time.time() - t0 > 1800:
            proc.kill()
            errf.close()
            rc = -9
            log("WIN-%d TIMEOUT 30min, killed" % idx)
            break
        time.sleep(3)
    wall = time.time() - t0
    # FIX-2 discovery: the driver also writes a 3-row comparison board
    # (suffix __.mp4, ~3x width, larger bytes). Drop boards, pick the clean
    # result, then assert picked width == pose source width.
    mp4, mp4_size = "", 0
    if os.path.isdir(OUTROOT):
        for root, _dirs, files in os.walk(OUTROOT):
            for fn in files:
                if fn.endswith(".mp4") and not fn.endswith("__.mp4"):
                    p = os.path.join(root, fn)
                    if os.path.getmtime(p) >= t0 and p not in captured \
                            and fsize(p) > mp4_size:
                        mp4, mp4_size = p, fsize(p)
    if mp4:
        captured.add(mp4)
    frames = ffprobe_frames(mp4) if mp4 else -1
    picked_w = probe_width(mp4) if mp4 else -1
    if mp4 and picked_w not in (-1, POSE_W):
        log("WIN-%d PICK-WIDTH-MISMATCH w=%d expected=%d (board leak, drop)"
            % (idx, picked_w, POSE_W))
        mp4, mp4_size, frames = "", 0, -1
    oom = False
    tail = ""
    try:
        tail = open(err_path, "rb").read()[-4000:].decode("utf-8", "replace")
    except OSError:
        pass
    if rc != 0:
        oom = ("out of memory" in tail.lower()
               or "OutOfMemoryError" in tail)
    log("WIN-%d pose=%s rc=%s wall=%.0fs peak_vram=%dMB mp4=%s(%dMB) "
        "ffprobe_frames=%d w=%d oom=%s"
        % (idx, os.path.basename(pose_src), rc, wall, peak_mem,
           os.path.basename(mp4), mp4_size // 1048576, frames, picked_w, oom))
    return {"win": idx, "pose_seg": os.path.basename(pose_src), "rc": rc,
            "wall_s": round(wall, 1), "peak_vram_mb": peak_mem,
            "oom": oom, "mp4": mp4, "mp4_bytes": mp4_size,
            "ffprobe_frames": frames, "picked_w": picked_w,
            "err_tail": tail[-1200:]}


def concat_phase(windows):
    # move window outputs into TRIAL for a stable concat list (ASCII names)
    parts = []
    for w in windows:
        if not w["mp4"] or w["mp4_bytes"] < 100 * 1024:
            continue
        dst = os.path.join(TRIAL, "part%d_c2071.mp4" % w["win"])
        if os.path.abspath(w["mp4"]) != os.path.abspath(dst):
            shutil.copyfile(w["mp4"], dst)
        parts.append(dst)
    if len(parts) != len(windows):
        log("CONCAT only %d/%d usable parts, abort"
            % (len(parts), len(windows)))
        return False, -1
    lst = os.path.join(TRIAL, "concat_list_c2071.txt")
    with open(lst, "w", encoding="ascii", newline="\n") as f:
        for p in parts:
            f.write("file '%s'\n" % p.replace("\\", "/").replace("'", "'\\''"))
    t0 = time.time()
    r = subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", STITCH_MP4],
        capture_output=True, text=True, timeout=600,
        creationflags=NO_WINDOW)
    wall = time.time() - t0
    err = (r.stderr or "").strip().replace("\n", " | ")[:600]
    size = fsize(STITCH_MP4)
    frames = ffprobe_frames(STITCH_MP4) if size else -1
    log("CONCAT rc=%s wall=%.0fs stitch=%dMB ffprobe_frames=%d err=%s"
        % (r.returncode, wall, size // 1048576, frames, err or "none"))
    return r.returncode == 0 and size >= 100 * 1024, frames


def write_receipt(result):
    os.makedirs(TRIAL, exist_ok=True)
    jp = os.path.join(TRIAL, "bmc_musepose_stitch72_c2071.json")
    with open(jp, "w", encoding="ascii", errors="replace") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(TRIAL, "TRIAL-RESULT.txt"), "w") as f:
        f.write("%s frames=%s\n" % (result.get("status", "?"),
                                   result.get("stitch_frames", "-")))
    v = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "status": result.get("status"),
         "fix_tag": result.get("fix_tag"),
         "stitch_frames": result.get("stitch_frames"),
         "stitch_mp4_bytes": fsize(STITCH_MP4),
         "windows": [{k: a.get(k) for k in
                      ("win", "pose_seg", "rc", "wall_s", "peak_vram_mb",
                       "oom", "mp4_bytes", "ffprobe_frames", "picked_w")}
                     for a in result.get("windows", [])],
         "pose_mp4_bytes": fsize(POSE_MP4),
         "runner": "musepose_stitch72_c2071.py"}
    with open(VERDICT_F, "w", encoding="ascii", errors="replace") as f:
        json.dump(v, f, indent=1)
    log("TRIAL-END status=%s" % result.get("status"))


def main():
    os.makedirs(TRIAL, exist_ok=True)
    log("STITCH-START MusePose night3 72f segment-stitch (POOL-0016, C2071)")
    base_mem, total_mem = vram_sample()
    log("BASELINE vram_used=%dMB total=%dMB" % (base_mem, total_mem))
    result = {"started": time.strftime("%Y-%m-%d %H:%M:%S"),
              "pool": "POOL-0016-night3-musepose-72f-stitch",
              "runner": "musepose_stitch72_c2071.py",
              "fix_tag": FIX_TAG,
              "vram_baseline_mb": base_mem,
              "profile": {"steps": STEPS, "cfg": CFG, "seed": SEED,
                          "wh": [W, H], "L": L, "S": S, "O": O,
                          "seg_starts": SEG_STARTS, "skip_arg": 0,
                          "pose_fps": POSE_FPS}}
    if not verify_phase():
        result["status"] = "VERIFY_FAILED"
        result["windows"] = []
        write_receipt(result)
        return
    # short VRAM wait: tier-0 peak was 13373MB total on a 16384MB card
    for i in range(20):
        mem, total = vram_sample()
        if mem < 0 or (total - mem) >= 9000:
            break
        log("VRAM-WAIT r%d used=%dMB free=%dMB <9000MB" % (i, mem, total - mem))
        time.sleep(60)
    segs, pose_w = cut_segments()
    if not segs:
        result["status"] = "SEGCUT_FAILED"
        result["windows"] = []
        write_receipt(result)
        return
    captured = set()
    windows = []
    for idx, seg in enumerate(segs):
        att = run_window(idx, seg, captured)
        windows.append(att)
    result["windows"] = windows
    all_ok = all(a["rc"] == 0 and a["mp4_bytes"] >= 100 * 1024
                 and a["ffprobe_frames"] >= 20 for a in windows)
    if not all_ok:
        result["status"] = "FAIL"
        write_receipt(result)
        return
    ok, frames = concat_phase(windows)
    result["stitch_frames"] = frames
    if ok and frames >= 60:
        result["status"] = "PASS"
    else:
        result["status"] = "FAIL"
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
                           "pool": "POOL-0016-night3-musepose-72f-stitch",
                           "runner": "musepose_stitch72_c2071.py",
                           "status": "RUNNER_CRASH", "windows": []})
        except Exception:
            pass

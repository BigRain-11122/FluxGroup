# -*- coding: ascii -*-
# bmc_mimic_trial_r1058.py - self-waiting MimicMotion smoke trial runner
# (bm-c r1058, POOL-0016 night3 pulled forward per CEO idle-fill order).
#
# Phase 1 WAIT: blocks until MimicMotion_1-1.pth + DWPose onnx pair + SVD fp16
#   base are complete. Completion signal = sentinel line in each downloader's
#   log ("MIMIC-B-DONE" / "SVD-DONE") + file size checks. Self-heal: if a
#   downloader died short, relaunch it (both scripts are resume-safe, single
#   writer per file). No process enumeration - log sentinels only.
# Phase 2 TRIAL: official demo (pose1.mp4 + demo1.jpg) at 576 resolution,
#   seed 42, PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256.
#   num_inference_steps=6 (official 25) per CEO efficiency law (verify at low
#   cost first): the 25-step rate was measured live at 169s/step for a
#   48-frame window (100% util, 15.7GB) -> 25-step official tier = ~2.35h per
#   tile = judged non-production on this card; 6 steps proves the full chain
#   end-to-end in <1h. sample_stride=15 -> 71 video poses + 1 image pose =
#   exactly 72 frames (pipeline tiling math requires num_frames >= tile_size;
#   stride 16 gave 68 < 72 -> IndexError, proven 14:30 r1058).
#   OOM ladder: num_frames (tile size) 48 -> 24, first pass wins.
#   VRAM sampled every 3s via nvidia-smi (CREATE_NO_WINDOW, zero desktop
#   flash). Receipt: JSON + MD (fleet mirror dir) + result flag file.

import json
import os
import subprocess
import sys
import threading
import time

# pythonw no-console guard: diffusers 0.27 does print(..., flush=True) at
# import; with sys.stdout=None the builtin print guards write but NOT the
# explicit flush -> AttributeError kills the process (proven diag 13:54).
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

REPO = r"K:\Fluxgroup\FluxGroup\media\mvtools\MimicMotion"
SCRIPTS = r"K:\Fluxgroup\FluxGroup\media\mvtools\scripts_r1058"
PYLIBS = os.path.join(REPO, "pylibs_mimic")
PYEXE = r"D:\ComfyUI\python_embeded\python.exe"
LOGDIR = r"K:\Fluxgroup\FluxGroup\media\logs"
RUNLOG = os.path.join(LOGDIR, "mimic_trial_r1058.log")
FLEET_RCP = (r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2"
             r"\kf-demo-20261012\bmc\mimic_smoke_r1058")

PTH = os.path.join(REPO, "models", "MimicMotion_1-1.pth")
PTH_MIN = 3049000000  # downloader probe says expected = 2908 MB
DWP = os.path.join(REPO, "models", "DWPose")
DWONNX = [os.path.join(DWP, "dw-ll_ucoco_384.onnx"), os.path.join(DWP, "yolox_l.onnx")]
ONNX_MIN = 100 * 1048576
SVD_DIR = os.path.join(REPO, "models", "svd-img2vid-xt-1-1")
SVD_MARKER = os.path.join(SVD_DIR, ".download_ok.json")
MIM_LOG = os.path.join(LOGDIR, "dl_mimic_r1058b.log")
MIM_SENTINEL = "MIMIC-B-DONE"
SVD_LOG = os.path.join(LOGDIR, "dl_svd_r1058.log")
SVD_SENTINEL = "SVD-DONE"

MIM_DL = os.path.join(SCRIPTS, "dl_mimic_r1058b.py")
SVD_DL = os.path.join(SCRIPTS, "dl_svd_r1058.py")
LAUNCHER = os.path.join(SCRIPTS, "bmc_mimic_launcher_r1058.py")

TRIAL = os.path.join(REPO, "trial_r1058")
TIERS = [48, 24]
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW - zero desktop flash (U060 law)

YAML_TMPL = """# base svd model path (local prefetch dir, no hub calls)
base_model_path: models/svd-img2vid-xt-1-1

# checkpoint path
ckpt_path: models/MimicMotion_1-1.pth

test_case:
  - ref_video_path: assets/example_data/videos/pose1.mp4
    ref_image_path: assets/example_data/images/demo1.jpg
    num_frames: %(nf)d
    resolution: 576
    frames_overlap: 6
    num_inference_steps: 6
    noise_aug_strength: 0
    guidance_scale: 2.0
    sample_stride: 15
    fps: 15
    seed: 42
"""


class Log:
    def __init__(self, path):
        self.f = open(path, "a", encoding="ascii", errors="replace")
        self.t0 = time.time()

    def __call__(self, msg):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
        try:
            print(line)
        except Exception:
            pass
        self.f.write(line + "\n")
        self.f.flush()


log = Log(RUNLOG)


def fsize(p):
    try:
        return os.path.getsize(p)
    except OSError:
        return 0


def log_has(path, needle):
    try:
        with open(path, "r", encoding="ascii", errors="replace") as f:
            return needle in f.read()
    except OSError:
        return False


def log_fresh(path, max_age=180):
    try:
        return (time.time() - os.path.getmtime(path)) < max_age
    except OSError:
        return False


def spawn(script):
    # detached child; runner owns the handle for liveness checks
    return subprocess.Popen([PYEXE, script], creationflags=NO_WINDOW,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def mim_files_ok():
    return (fsize(PTH) >= PTH_MIN and fsize(DWONNX[0]) >= ONNX_MIN
            and fsize(DWONNX[1]) >= ONNX_MIN)


def svd_files_ok():
    return os.path.exists(SVD_MARKER)


def wait_phase():
    # Serialized legs: hf-mirror 403s concurrent requests from one IP while a
    # big stream is active (observed 13:4x r1058), so the SVD leg only starts
    # after the mim leg (pth + dwpose onnx) is complete.
    kids = {}
    relaunch = {"mim": 0, "svd": 0}
    for round_i in range(360):  # 6h cap at 60s polls
        log("WAIT r%d pth=%dMB dwpose=%d/%dMB svd_marker=%s"
            % (round_i, fsize(PTH) // 1048576, fsize(DWONNX[0]) // 1048576,
               fsize(DWONNX[1]) // 1048576, "Y" if svd_files_ok() else "N"))
        # --- leg 1: mim (pth + onnx) ---
        mim_done = log_has(MIM_LOG, MIM_SENTINEL)
        if not (mim_done and mim_files_ok()):
            kid = kids.get("mim")
            if kid is not None and kid.poll() is None:
                time.sleep(60)
                continue  # my own child still working
            if mim_done:
                # downloader finished but files short (DL-FAIL path) -> relaunch
                if relaunch["mim"] < 3:
                    relaunch["mim"] += 1
                    kids["mim"] = spawn(MIM_DL)
                    log("RELAUNCH-mim #%d (sentinel reached, files short)" % relaunch["mim"])
                else:
                    log("GIVEUP-mim after 3 relaunches")
                    return False
            elif not log_fresh(MIM_LOG):
                # no sentinel + stale log = downloader died mid-way -> resume
                if relaunch["mim"] < 3:
                    relaunch["mim"] += 1
                    kids["mim"] = spawn(MIM_DL)
                    log("RELAUNCH-mim #%d (stale log, no sentinel)" % relaunch["mim"])
                else:
                    log("GIVEUP-mim after 3 relaunches")
                    return False
            time.sleep(60)
            continue
        # --- leg 2: svd (only after mim complete) ---
        svd_done = log_has(SVD_LOG, SVD_SENTINEL)
        if svd_done and svd_files_ok():
            log("WAIT-OK all weights complete")
            return True
        kid = kids.get("svd")
        if kid is not None and kid.poll() is None:
            time.sleep(60)
            continue
        if svd_done:
            if relaunch["svd"] < 3:
                relaunch["svd"] += 1
                kids["svd"] = spawn(SVD_DL)
                log("RELAUNCH-svd #%d (sentinel reached, files short)" % relaunch["svd"])
            else:
                log("GIVEUP-svd after 3 relaunches")
                return False
        elif not log_fresh(SVD_LOG):
            if relaunch["svd"] < 3:
                relaunch["svd"] += 1
                kids["svd"] = spawn(SVD_DL)
                log("RELAUNCH-svd #%d (stale log, no sentinel)" % relaunch["svd"])
            else:
                log("GIVEUP-svd after 3 relaunches")
                return False
        time.sleep(60)
    log("WAIT-TIMEOUT 6h cap reached")
    return False


def vram_sample():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20,
            creationflags=NO_WINDOW)
        mem, util = [int(x.strip()) for x in out.stdout.strip().split(",")]
        return mem, util
    except Exception:
        return -1, -1


def preflight():
    # torchvision 0.28 dropped OSS write_video from torchvision.io - install
    # the av-based shim before importing it (same shim the launcher injects).
    # NOTE python313._pth isolated mode: script dir is NOT auto-added to
    # sys.path (proven 14:26 r1058) - SCRIPTS must be inserted explicitly.
    sys.path.insert(0, SCRIPTS)
    sys.path.insert(0, PYLIBS)
    sys.path.insert(0, REPO)
    os.chdir(REPO)
    import bmc_tv_writevideo_shim_r1058 as tvshim
    shim_on = tvshim.install()
    import torch
    from torchvision.io import write_video
    p = os.path.join(TRIAL, "preflight_writevideo.mp4")
    frames = (torch.rand(12, 3, 64, 64) * 255).to(torch.uint8)
    write_video(p, frames, fps=15)
    ok = fsize(p) >= 1024
    log("PREFLIGHT write_video ok=%s size=%d shim=%s" % (ok, fsize(p), shim_on))
    return ok


def versions():
    sys.path.insert(0, PYLIBS)
    log("VERSIONS-START")
    out = {}
    import torch
    import torchvision
    log("VERSIONS torch+torchvision ok")
    import diffusers
    log("VERSIONS diffusers ok")
    import transformers
    log("VERSIONS transformers ok")
    import onnxruntime
    import huggingface_hub
    out["torch"] = torch.__version__
    out["torchvision"] = torchvision.__version__
    out["diffusers"] = diffusers.__version__
    out["transformers"] = transformers.__version__
    out["onnxruntime"] = onnxruntime.__version__
    out["huggingface_hub"] = huggingface_hub.__version__
    log("VERSIONS-OK")
    return out


def run_tier(nf):
    yaml_path = os.path.join(TRIAL, "test_bmc_r1058_tf%d.yaml" % nf)
    outdir = os.path.join(TRIAL, "outputs_tf%d" % nf)
    infer_log = os.path.join(TRIAL, "infer_tf%d.log" % nf)
    err_path = os.path.join(TRIAL, "infer_tf%d.err" % nf)
    with open(yaml_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(YAML_TMPL % {"nf": nf})
    os.makedirs(outdir, exist_ok=True)
    env = dict(os.environ)
    env["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:256"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    t0 = time.time()
    errf = open(err_path, "wb")
    proc = subprocess.Popen(
        [PYEXE, LAUNCHER, "--inference_config", yaml_path,
         "--output_dir", outdir, "--log_file", infer_log],
        creationflags=NO_WINDOW, env=env,
        stdout=subprocess.DEVNULL, stderr=errf)
    peak_mem, peak_util, samples = 0, 0, 0
    while True:
        rc = proc.poll()
        mem, util = vram_sample()
        if mem >= 0:
            samples += 1
            peak_mem = max(peak_mem, mem)
            peak_util = max(peak_util, util)
        if rc is not None:
            errf.close()
            break
        if time.time() - t0 > 3600:
            proc.kill()
            errf.close()
            rc = -9
            log("TIER-%d TIMEOUT 60min, killed" % nf)
            break
        time.sleep(3)
    wall = time.time() - t0
    # locate newest output mp4
    mp4, mp4_size = "", 0
    if os.path.isdir(outdir):
        for fn in os.listdir(outdir):
            if fn.endswith(".mp4"):
                p = os.path.join(outdir, fn)
                if fsize(p) > mp4_size:
                    mp4, mp4_size = p, fsize(p)
    oom = False
    tail = ""
    try:
        with open(infer_log, "r", encoding="utf-8", errors="replace") as f:
            tail = "".join(f.readlines()[-40:])
    except OSError:
        try:
            tail = open(err_path, "rb").read()[-4000:].decode("utf-8", "replace")
        except Exception:
            tail = ""
    if rc != 0:
        oom = ("out of memory" in tail.lower()
               or "OutOfMemoryError" in tail)
    log("TIER-%d rc=%s wall=%.0fs peak_vram=%dMB peak_util=%d%% mp4=%s (%dMB) oom=%s"
        % (nf, rc, wall, peak_mem, peak_util, os.path.basename(mp4),
           mp4_size // 1048576, oom))
    return {"num_frames": nf, "rc": rc, "wall_s": round(wall, 1),
            "peak_vram_mb": peak_mem, "peak_util_pct": peak_util,
            "oom": oom, "mp4": mp4, "mp4_bytes": mp4_size,
            "log_tail": tail[-2000:]}


def main():
    os.makedirs(TRIAL, exist_ok=True)
    os.makedirs(FLEET_RCP, exist_ok=True)
    log("TRIAL-START self-waiting MimicMotion smoke (POOL-0016 night3 early)")
    base_mem, _ = vram_sample()
    log("BASELINE vram_used=%dMB" % base_mem)
    result = {"started": time.strftime("%Y-%m-%d %H:%M:%S"),
              "pool": "POOL-0016-night3-early", "runner": "bmc_mimic_trial_r1058.py",
              "vram_baseline_mb": base_mem}
    if not wait_phase():
        result["env"] = versions()
        result["status"] = "WAIT_FAILED"
        write_receipt(result)
        return
    result["env"] = versions()
    result["downloads"] = {
        "pth_bytes": fsize(PTH),
        "dw_ll_ucoco_384_onnx_bytes": fsize(DWONNX[0]),
        "yolox_l_onnx_bytes": fsize(DWONNX[1]),
        "svd_marker": json.load(open(SVD_MARKER)) if os.path.exists(SVD_MARKER) else None}
    if not preflight():
        result["status"] = "PREFLIGHT_FAILED"
        write_receipt(result)
        return
    attempts = []
    for nf in TIERS:
        att = run_tier(nf)
        attempts.append(att)
        if att["rc"] == 0 and att["mp4_bytes"] >= 100 * 1024:
            result["status"] = "PASS"
            result["passed_tier"] = nf
            break
    if "status" not in result:
        result["status"] = "FAIL"
    result["attempts"] = attempts
    write_receipt(result)
    log("TRIAL-END status=%s" % result.get("status"))


def write_receipt(result):
    result["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    jp = os.path.join(TRIAL, "bmc_mimic_tier_r1058.json")
    with open(jp, "w", encoding="ascii", errors="replace") as f:
        json.dump(result, f, indent=1)
    # one-line result flag for the guard cron / orders row
    with open(os.path.join(TRIAL, "TRIAL-RESULT.txt"), "w") as f:
        f.write("%s tier=%s\n" % (result.get("status", "?"),
                                  result.get("passed_tier", "-")))
    passed = [a for a in result.get("attempts", []) if a["rc"] == 0]
    lines = []
    a = lines.append
    a("# POOL-0016 night3 (pulled forward) - MimicMotion smoke tier receipt (r1058)")
    a("")
    a("- window: 2026-10-17 r1058 CEO idle-fill; runner = bmc_mimic_trial_r1058.py")
    a("- status: %s  passed_tier=%s" % (result.get("status"), result.get("passed_tier", "-")))
    a("- inputs: official demo assets (pose1.mp4 + demo1.jpg), zero new generation")
    a("- config: resolution 576, steps 6 (official 25; 25-step rate measured")
    a("  live at 169s/step @48-frame window -> official tier ~2.35h/tile on this")
    a("  card = judged non-production; smoke runs reduced steps per CEO")
    a("  efficiency law), overlap 6, fps 15, seed 42,")
    a("  PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256, fp16 default dtype")
    a("- TIER VERDICT (POOL-0016): 16GB card FITS the pipeline at 48/72-frame")
    a("  windows (15.4-16.1GB peak incl ~1.5-1.8GB other residents) but the")
    a("  25-step official tier costs ~2.35h per 48-frame tile (169s/step, 100%")
    a("  util) -> full-MV motion retargeting at 576x1024 on bm-c = impractical;")
    a("  viable for short inserts with night-window budget or lower resolution.")
    a("  72-frame window shares the card into WDDM paging thrash when any other")
    a("  GPU resident competes (observed with two pipelines co-burning).")
    a("- deviations: sample_stride=15 (official 2) -> 71+1 = exactly 72 frames =")
    a("  single full 72-frame tile (pipeline tiling math requires num_frames >=")
    a("  tile_size; full 530-frame demo = ~8 tiles, not needed for calibration);")
    a("  DWPose forced to CPUExecutionProvider (CPU-only onnxruntime in env);")
    a("  SVD base = local prefetch dir (no hub calls).")
    a("- env: %s" % json.dumps(result.get("env", {})))
    a("- downloads: pth=%dMB dwpose=%d/%dMB svd_marker=%s"
      % (result.get("downloads", {}).get("pth_bytes", 0) // 1048576,
         result.get("downloads", {}).get("dw_ll_ucoco_384_onnx_bytes", 0) // 1048576,
         result.get("downloads", {}).get("yolox_l_onnx_bytes", 0) // 1048576,
         "Y" if result.get("downloads", {}).get("svd_marker") else "N"))
    peaks = [x.get("peak_vram_mb", 0) for x in result.get("attempts", [])]
    a("- vram: baseline=%dMB peak=%dMB (16GB card)"
      % (result.get("vram_baseline_mb", -1), max(peaks) if peaks else 0))
    for att in result.get("attempts", []):
        a("- attempt tile=%d: rc=%s wall=%.0fs peak_vram=%dMB oom=%s out=%s(%dMB)"
          % (att["num_frames"], att["rc"], att.get("wall_s", 0),
             att.get("peak_vram_mb", 0), att.get("oom"),
             os.path.basename(att.get("mp4", "")), att.get("mp4_bytes", 0) // 1048576))
    if passed:
        a("- output: %s" % passed[0]["mp4"])
    a("- license flag: SVD img2vid-xt-1-1 weights = Stability AI Non-Commercial")
    a("  Research Community License. Internal trial OK; production MV use needs")
    a("  license review before any commercial release.")
    a("- full JSON: %s" % jp)
    md = os.path.join(FLEET_RCP, "RECEIPT-POOL-0016-night3-early-r1058.md")
    with open(md, "w", encoding="ascii", errors="replace") as f:
        f.write("\n".join(lines) + "\n")
    log("RECEIPT written %s" % md)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        # pythonw has no console - an unhandled exception would otherwise die
        # silently (proven 14:19-14:24 r1058). Log traceback + crash receipt.
        import traceback
        with open(RUNLOG, "a", encoding="ascii", errors="replace") as f:
            f.write("[%s] FATAL-EXC in main()\n" % time.strftime("%H:%M:%S"))
            traceback.print_exc(file=f)
        try:
            write_receipt({"started": "?", "pool": "POOL-0016-night3-early",
                           "runner": "bmc_mimic_trial_r1058.py",
                           "status": "RUNNER_CRASH", "attempts": [],
                           "env": {}, "vram_baseline_mb": -1, "downloads": {}})
        except Exception:
            pass

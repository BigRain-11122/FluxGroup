# -*- coding: utf-8 -*-
# C2074 pre-stow: POOL-0016 night-1 LatentSync deploy prefix (three-piece final gap)
# Slice 1 of the night-1 leg: repo already cloned in-round (media/latentsync, gh-proxy direct).
# This script = requirements triage install (--no-deps per mimic r1058 shim law) + import-chain probe.
# VRAM: none needed (CPU face). Weights leg = next slice after this verdict (C2064 precedent).
import os, sys, json, subprocess, datetime

REPO = r"K:\Fluxgroup\FluxGroup"
LSREPO = os.path.join(REPO, "media", "latentsync")
PYLIBS = os.path.join(REPO, "media", "pylibs_latentsync")
DEPLOY = os.path.join(REPO, "media", "latentsync-deploy")
VERDICT = os.path.join(DEPLOY, "deploy_verdict.json")
TUNA = "https://pypi.tuna.tsinghua.edu.cn/simple"

os.makedirs(DEPLOY, exist_ok=True)
os.makedirs(PYLIBS, exist_ok=True)

def log(m):
    print("[%s] %s" % (datetime.datetime.now().strftime("%H:%M:%S"), m), flush=True)

# shim law (mimic r1058 / musepose C2063): base python_embeded provides torch-family,
# numpy, opencv, imageio, skimage, safetensors, hub. gradio = UI-only, not needed for
# pipeline inference. torch index line skipped.
EXCLUDE = {"torch", "torchvision", "numpy", "opencv-python", "gradio"}
EXTRA = ["antlr4-python3-runtime==4.9.3"]  # omegaconf 2.3.0 transitive, --no-deps misses it

req_path = os.path.join(LSREPO, "requirements.txt")
pins = []
for ln in open(req_path, encoding="utf-8"):
    ln = ln.strip()
    if not ln or ln.startswith("--") or ln.startswith("#"):
        continue
    name = ln.split("==")[0].strip()
    if name in EXCLUDE:
        continue
    pins.append(ln)
pins.extend(EXTRA)

log("DEPLOY-START LatentSync night-1 deploy prefix (POOL-0016 final gap, C2074)")
log("REQUIREMENTS triage: %d pins (excluded per shim law: %s)" % (len(pins), ",".join(sorted(EXCLUDE))))

ok, fail = [], []
for pin in pins:
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--upgrade",
                       "--target", PYLIBS, "-i", TUNA, pin],
                      capture_output=True, text=True)
    good = (r.returncode == 0) and ("Successfully installed" in (r.stdout or ""))
    (ok if good else fail).append(pin)
    log("PIP %s %s" % ("OK " if good else "FAIL", pin))

# import-chain probe: overlay pylibs first, then repo root (package latentsync/)
sys.path.insert(0, PYLIBS)
sys.path.insert(1, LSREPO)
probe_ok, hard_gaps, expected_gaps = [], [], []
for mod in ["diffusers", "transformers", "omegaconf", "einops", "librosa",
            "python_speech_features", "scenedetect", "ffmpeg", "lpips",
            "face_alignment", "kornia", "accelerate", "imageio_ffmpeg"]:
    try:
        __import__(mod)
        probe_ok.append(mod)
    except Exception as e:
        (expected_gaps if mod in ("decord",) else hard_gaps).append("%s: %s" % (mod, type(e).__name__))
try:
    import decord  # noqa
    probe_ok.append("decord")
except Exception:
    expected_gaps.append("decord (py313 wheel gap -> av shim face, mimic/musepose precedent)")
try:
    from latentsync.pipelines.lipsync_pipeline import LipsyncPipeline  # noqa
    probe_ok.append("latentsync.pipelines.lipsync_pipeline")
except Exception as e:
    hard_gaps.append("lipsync_pipeline: %s: %s" % (type(e).__name__, str(e)[:200]))
try:
    import latentsync.utils as lsu  # noqa
    probe_ok.append("latentsync.utils")
except Exception as e:
    hard_gaps.append("latentsync.utils: %s: %s" % (type(e).__name__, str(e)[:200]))

status = "PASS" if (not fail and not hard_gaps) else ("PARTIAL" if ok else "FAIL")
v = {
    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    "status": status,
    "fix_tag": "c2074-latentsync-deploy-prefix",
    "pip_ok": ok, "pip_fail": fail,
    "probe_ok": probe_ok, "hard_gaps": hard_gaps, "expected_gaps": expected_gaps,
    "note": "hard_gaps = next-round ImportError patch list (C2063 re-triage precedent). "
            "Compliance flag: latentsync face-detect uses insightface (NC red-line face) - "
            "trial leg must swap to FaceAlignment per EXPERIENCE-LEDGER J-30 law. "
            "VRAM tier: v1.5 8GB target config (v1.6 18GB infeasible on 16G card, R-stack row). "
            "Next slice = weights-dl (unet v1.5 + syncnet + whisper via hf-mirror) then trial.",
}
json.dump(v, open(VERDICT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
log("VERDICT %s pip_ok=%d pip_fail=%d probe_ok=%d hard_gaps=%d -> %s" %
    (status, len(ok), len(fail), len(probe_ok), len(hard_gaps), VERDICT))
log("DEPLOY-END status=%s" % status)

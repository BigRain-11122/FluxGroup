# musepose_import_smoke.py -- import-tier smoke for MusePose night3 trial prefix (bm-c C2064)
# Purpose: build the trial-leg ImportError patch list WITHOUT burning GPU:
# probe base-env (torch/transformers/diffusers/cv2/skimage) + pylibs_musepose
# overlay + all musepose inference-facing modules + omegaconf config parse.
# av/decord are reported as expected GAP (excluded at deps triage) so the
# trial runner can shim them. ASCII-only output (B1324 purge law).
import json, os, sys, time, importlib

REPO = r"K:\Fluxgroup\FluxGroup"
ROOT = os.path.join(REPO, "media", "musepose")
PYLIBS = os.path.join(REPO, "media", "pylibs_musepose")
DEPLOY = os.path.join(REPO, "media", "musepose-deploy")

sys.path.insert(0, PYLIBS)
sys.path.insert(0, ROOT)
os.chdir(ROOT)

EXPECTED_GAPS = {"av": "excluded at deps triage (no cp313 wheel) -> trial shim",
                 "decord": "excluded (no cp313 wheel) -> cv2 VideoReader shim per mimic r1058"}

# (probe_target, import_pkg_for_attr_or_None)
PROBES = [
    ("numpy", None), ("torch", None), ("torchvision", None), ("cv2", None),
    ("skimage", None), ("einops", None), ("omegaconf", None), ("moviepy", None),
    ("diffusers", None), ("transformers", None),
    ("av", None), ("decord", None),
    ("CLIPVisionModelWithProjection", "transformers"),
    ("musepose.models.pose_guider", None),
    ("musepose.models.unet_2d_condition", None),
    ("musepose.models.unet_3d", None),
    ("musepose.pipelines.pipeline_pose2vid_long", None),
    ("musepose.utils.util", None),
]

results = {}
for mod, pkg in PROBES:
    t0 = time.time()
    status, err = "OK", ""
    try:
        if pkg:
            m = importlib.import_module(pkg)
            getattr(m, mod)
        else:
            importlib.import_module(mod)
    except Exception as e:
        root0 = mod.split(".")[0]
        status = "GAP" if root0 in EXPECTED_GAPS else "IMPORT_ERROR"
        err = repr(e).encode("ascii", "replace").decode()[:300]
    results[mod] = {"status": status, "err": err, "ms": int((time.time() - t0) * 1000)}
    print("PROBE %-42s %-12s %s" % (mod, status, err[:120]), flush=True)

# omegaconf config parse face
try:
    from omegaconf import OmegaConf
    OmegaConf.load(os.path.join(ROOT, "configs", "test_stage_2.yaml"))
    OmegaConf.load(os.path.join(ROOT, "configs", "inference_v2.yaml"))
    results["omegaconf-config-parse"] = {"status": "OK", "err": "", "ms": 0}
    print("PROBE %-42s %-12s" % ("omegaconf-config-parse", "OK"), flush=True)
except Exception as e:
    results["omegaconf-config-parse"] = {"status": "ERROR", "err": repr(e)[:200], "ms": 0}
    print("PROBE %-42s %-12s %s" % ("omegaconf-config-parse", "ERROR", repr(e)[:120]), flush=True)

hard = [k for k, v in results.items() if v["status"] == "IMPORT_ERROR"]
gaps = [k for k, v in results.items() if v["status"] == "GAP"]
os.makedirs(DEPLOY, exist_ok=True)
with open(os.path.join(DEPLOY, "import_smoke_verdict.json"), "w", encoding="utf-8") as f:
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "hard_errors": hard,
               "expected_gaps": gaps, "results": results}, f, indent=1, ensure_ascii=False)
print("SMOKE-VERDICT: %s hard=%d gaps=%d" % ("PASS" if not hard else "PATCH-LIST", len(hard), len(gaps)), flush=True)

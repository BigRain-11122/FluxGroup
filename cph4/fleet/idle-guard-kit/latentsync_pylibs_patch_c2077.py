# latentsync_pylibs_patch_c2077.py -- POOL-0016 night-1 PYLIBS overlay patch + import probe, C2077 pre-stow.
# Root fix of deploy hard_gaps=4 (deploy_verdict 13:56:40):
#   transformers 4.48.0 needs tokenizers>=0.21,<0.22 (base env too new; overlay installed --no-deps)
#   ffmpeg-python 0.2.0 needs the `future` pkg (ModuleNotFoundError chain)
#   accelerate ImportError (root cause to be captured by probe, full error string recorded)
#   lipsync_pipeline chained via tokenizers (downstream, heals with 1)
# Patch = pip --no-deps --only-binary into media/pylibs_latentsync overlay (zero base-env pollution).
# Probe = import chain: transformers / ffmpeg / accelerate / diffusers / latentsync.utils.util /
# latentsync.pipelines.lipsync_pipeline. insightface ImportError = EXPECTED gap (NC red-line face,
# J-30 law: trial leg swaps FaceAlignment; overlay already has face_alignment-1.4.1).
# Verdict media/latentsync-deploy/patch_verdict.json + PATCH-VERDICT/PATCH-END sentinels.
import os, sys, json, subprocess, time

REPO = r"K:\Fluxgroup\FluxGroup"
OVL = os.path.join(REPO, "media", "pylibs_latentsync")
LSROOT = os.path.join(REPO, "media", "latentsync")
VD = os.path.join(REPO, "media", "latentsync-deploy", "patch_verdict.json")

def log(m):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), m), flush=True)

log("PATCH-START latentsync PYLIBS overlay patch (POOL-0016 night-1, C2077)")

pkgs = ["tokenizers==0.21.1", "future==1.0.0"]
r = subprocess.run(
    [sys.executable, "-m", "pip", "install", "--target", OVL, "--no-deps",
     "--only-binary=:all:", "--upgrade", "-i",
     "https://pypi.tuna.tsinghua.edu.cn/simple"] + pkgs,
    capture_output=True, text=True, timeout=600)
log("PIP rc=%d" % r.returncode)
for line in (r.stdout or "").strip().splitlines()[-6:]:
    log("pip.out: %s" % line[:160])
for line in (r.stderr or "").strip().splitlines()[-4:]:
    log("pip.err: %s" % line[:160])

def have_dist(name_sub):
    if not os.path.isdir(OVL):
        return False
    return any(name_sub in d for d in os.listdir(OVL))

pip_face = {
    "tokenizers": have_dist("tokenizers-0.21.1.dist-info"),
    "future": have_dist("future-1.0.0.dist-info"),
}
log("PIP-FACE %s" % json.dumps(pip_face))

os.chdir(LSROOT)
sys.path.insert(0, OVL)
sys.path.insert(1, LSROOT)

probes = [
    ("transformers", "transformers"),
    ("ffmpeg", "ffmpeg"),
    ("accelerate", "accelerate"),
    ("diffusers", "diffusers"),
    ("latentsync.utils.util", "latentsync.utils.util"),
    ("lipsync_pipeline", "latentsync.pipelines.lipsync_pipeline"),
]
res, expected_gaps, hard_gaps = {}, [], []
for name, mod in probes:
    try:
        __import__(mod)
        res[name] = "ok"
        log("PROBE %s OK" % name)
    except Exception as e:
        msg = "%s: %s" % (type(e).__name__, str(e))
        res[name] = msg[:300]
        low = msg.lower()
        if "insightface" in low:
            expected_gaps.append(name + " -> insightface (J-30 FaceAlignment swap at trial)")
            log("PROBE %s EXPECTED-GAP insightface" % name)
        else:
            hard_gaps.append("%s | %s" % (name, msg[:200]))
            log("PROBE %s FAIL %s" % (name, msg[:160]))

v = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "status": "OK" if (not hard_gaps and all(pip_face.values())) else ("PARTIAL" if pip_face["tokenizers"] else "FAIL"),
    "pip_face": pip_face, "probe": res,
    "expected_gaps": expected_gaps, "hard_gaps": hard_gaps,
    "note": ("tokenizers 0.21.1 + future 1.0.0 into overlay; import chain probe. Expected gap = insightface "
             "(NC red-line, J-30 FaceAlignment swap at trial leg; 2DFAN4+s3fd weights pre-seeded by dl2). "
             "Trial runner authoring consumes this verdict + weights2_verdict.json."),
}
with open(VD, "w") as f:
    json.dump(v, f, indent=1)
log("PATCH-VERDICT %s pip=%s hard=%d expected=%d -> %s" % (
    v["status"], json.dumps(pip_face), len(hard_gaps), len(expected_gaps), VD))
log("PATCH-END status=%s" % v["status"])

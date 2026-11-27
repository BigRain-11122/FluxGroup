# musepose_trial_launcher_c2066.py -- shim injector + test_stage_2 argv
# pass-through for the MusePose night3 smoke trial (bm-c C2066, POOL-0016).
#
# Shims (per import_smoke_verdict patch list, single root cause each):
#   S1 huggingface_hub.cached_download stub -- diffusers 0.27.2
#      dynamic_modules_utils does `from huggingface_hub import cached_download`;
#      hub 1.28 removed the symbol. Local-only trial never calls it at runtime,
#      the stub only needs to exist at import time.
#   S2 torch.load weights_only default flip -- torch>=2.6 defaults True;
#      test_stage_2.py calls bare torch.load on third-party .pth pickles.
#      Explicit weights_only=True calls (unet_3d.from_pretrained_2d) are
#      preserved via setdefault.
# decord / torchvision write_video shims are NOT needed here (recon C2066):
# musepose test_stage_2 chain reads/writes video via PyAV natively and decord
# only appears in the training dataset files.
import os
import sys

REPO = r"K:\Fluxgroup\FluxGroup\media\musepose"
PYLIBS = r"K:\Fluxgroup\FluxGroup\media\pylibs_musepose"
MMPYLIBS = r"K:\Fluxgroup\FluxGroup\media\mvtools\MimicMotion\pylibs_mimic"
MMREPO = r"K:\Fluxgroup\FluxGroup\media\mvtools\MimicMotion"

# C2067 fix -- transformers parity with the runner's verified import probe:
# diffusers 0.27.2 imports transformers 4.x-only symbols (FLAX_WEIGHTS_NAME)
# that base transformers 5.15 removed; pylibs_mimic ships the 4.x line the
# probe chain resolved against. Insert order mirrors the probe exactly.
sys.path.insert(0, MMREPO)
sys.path.insert(0, MMPYLIBS)
sys.path.insert(0, PYLIBS)
sys.path.insert(0, REPO)
os.chdir(REPO)
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# pythonw no-console guard (r1058 law: explicit flush kills stdout=None procs)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# S1: legacy hub symbol stub (before any diffusers import)
import huggingface_hub

if not hasattr(huggingface_hub, "cached_download"):
    def _cached_download_stub(*args, **kwargs):
        raise RuntimeError("cached_download stub -- offline local-only trial")

    huggingface_hub.cached_download = _cached_download_stub

# S2: torch.load weights_only=False default wrapper (trusted local weights)
import torch

_orig_torch_load = torch.load


def _torch_load_wo_default_false(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _orig_torch_load(*args, **kwargs)


torch.load = _torch_load_wo_default_false

sys.argv = ["test_stage_2.py"] + sys.argv[1:]

import runpy

runpy.run_path(os.path.join(REPO, "test_stage_2.py"), run_name="__main__")

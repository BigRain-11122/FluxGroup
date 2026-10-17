# -*- coding: ascii -*-
# bmc_mimic_launcher_r1058.py - path-injecting launcher for MimicMotion
# inference.py (bm-c r1058). python_embeded python313._pth disables PYTHONPATH,
# so the sys.path injection must happen in-process. Also overrides the DWPose
# singleton device arg: wholebody.py picks CUDAExecutionProvider whenever
# torch.cuda.is_available(), but this env ships CPU-only onnxruntime - without
# the override session creation would fail. Upstream files stay untouched.

import os
import runpy
import sys

# pythonw / CREATE_NO_WINDOW no-console guard: diffusers 0.27 does
# print(..., flush=True) at import; sys.stdout=None makes that raise
# AttributeError. inference.py logging StreamHandler needs a real stderr too.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

REPO = r"K:\Fluxgroup\FluxGroup\media\mvtools\MimicMotion"
PYLIBS = os.path.join(REPO, "pylibs_mimic")
sys.path.insert(0, PYLIBS)
sys.path.insert(0, REPO)
os.chdir(REPO)

from mimicmotion.dwpose import dwpose_detector as _dd

_det, _pose, _dev = _dd.dwpose_detector.args
_dd.dwpose_detector.args = (_det, _pose, "cpu")

sys.argv = ["inference.py"] + sys.argv[1:]
runpy.run_path(os.path.join(REPO, "inference.py"), run_name="__main__")

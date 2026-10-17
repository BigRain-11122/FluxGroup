# -*- coding: ascii -*-
# diag_imports_r1058.py - isolate which import hangs under pythonw (no console).
import sys
import time

P = r"K:\Fluxgroup\FluxGroup\media\logs\diag_imports_r1058.log"


def mark(msg):
    with open(P, "a", encoding="ascii") as f:
        f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))


mark("DIAG-START argv=%s" % sys.executable)
sys.path.insert(0, r"K:\Fluxgroup\FluxGroup\media\mvtools\MimicMotion\pylibs_mimic")
mark("path-injected")
try:
    import torch
    mark("torch OK %s" % torch.__version__)
except Exception as e:
    mark("torch FAIL %r" % e)
try:
    import torchvision
    mark("torchvision OK %s" % torchvision.__version__)
except Exception as e:
    mark("torchvision FAIL %r" % e)
try:
    import diffusers
    mark("diffusers OK %s" % diffusers.__version__)
except Exception as e:
    mark("diffusers FAIL %r" % e)
try:
    import transformers
    mark("transformers OK %s" % transformers.__version__)
except Exception as e:
    mark("transformers FAIL %r" % e)
try:
    import onnxruntime
    mark("onnxruntime OK %s" % onnxruntime.__version__)
except Exception as e:
    mark("onnxruntime FAIL %r" % e)
try:
    import huggingface_hub
    mark("hub OK %s" % huggingface_hub.__version__)
except Exception as e:
    mark("hub FAIL %r" % e)
try:
    import decord
    mark("decord OK")
except Exception as e:
    mark("decord FAIL %r" % e)
mark("DIAG-END")

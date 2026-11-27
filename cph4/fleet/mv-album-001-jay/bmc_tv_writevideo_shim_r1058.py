# -*- coding: ascii -*-
# bmc_tv_writevideo_shim_r1058.py - torchvision 0.28 dropped the OSS video IO
# API from torchvision.io (io/__init__.py only wires Meta-internal fb imports;
# the vestigial video.py itself imports from 'pytorch.vision.fb' = dead for
# OSS). MimicMotion's save_to_mp4 does `from torchvision.io import write_video`
# -> ImportError (proven runner FATAL-EXC 14:24 r1058). This shim installs an
# av(PyAV)-based write_video onto torchvision.io when missing.
# Accepts BOTH layouts: TCHW (torchvision convention) and THWC (mimicmotion
# save_to_mp4 permutes before calling).

_INSTALLED = False


def _write_video_shim(filename, video_array, fps=30, video_codec="libx264",
                      options=None, audio_array=None, audio_fps=None,
                      audio_codec="aac"):
    import av
    import numpy as np
    import torch

    if not isinstance(video_array, torch.Tensor):
        video_array = torch.from_numpy(np.asarray(video_array))
    if video_array.dtype != torch.uint8:
        video_array = video_array.clamp(0, 255).to(torch.uint8)
    if video_array.dim() != 4:
        raise ValueError("write_video shim: expected 4D tensor, got %r"
                         % (tuple(video_array.shape),))
    if video_array.shape[1] == 3:
        arr = video_array.permute(0, 2, 3, 1).numpy()  # TCHW -> THWC
    elif video_array.shape[3] == 3:
        arr = video_array.numpy()                      # already THWC
    else:
        raise ValueError("write_video shim: no channel dim == 3 in %r"
                         % (tuple(video_array.shape),))
    container = av.open(str(filename), mode="w")
    try:
        stream = container.add_stream("libx264", rate=int(fps))
        stream.width = int(arr.shape[2])
        stream.height = int(arr.shape[1])
        stream.pix_fmt = "yuv420p"
        for idx in range(arr.shape[0]):
            frame = av.VideoFrame.from_ndarray(arr[idx], format="rgb24")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    finally:
        container.close()


def install():
    global _INSTALLED
    import torchvision
    if not hasattr(torchvision.io, "write_video"):
        torchvision.io.write_video = _write_video_shim
        _INSTALLED = True
    return _INSTALLED

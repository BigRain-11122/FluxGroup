# -*- coding: ascii -*-
# decord cv2-backend shim (bm-c r1058) - decord 0.6.0 has no cp313 wheel.
# Covers the MimicMotion usage surface (mimicmotion/dwpose/preprocess.py):
#   decord.cpu(0)
#   vr = decord.VideoReader(path, ctx=decord.cpu(0))
#   len(vr); vr.get_avg_fps(); vr.get_batch([i,...]).asnumpy(); vr[0]
# Frames are seek-per-index via CAP_PROP_POS_FRAMES (no full-file cache, keeps
# RAM low); sequential index runs only step forward without re-seeking.

import os

import cv2
import numpy as np


class cpu(object):
    """decord.cpu(0) context placeholder."""

    def __init__(self, device_id=0):
        self.device_id = device_id

    def __repr__(self):
        return "decord.cpu(%d)" % self.device_id


class _Batch(object):
    def __init__(self, arr):
        self._arr = arr

    def asnumpy(self):
        return self._arr

    def __array__(self, dtype=None):
        return self._arr if dtype is None else self._arr.astype(dtype)


class VideoReader(object):
    def __init__(self, path, ctx=None, width=-1, height=-1):
        self.path = path
        if not os.path.exists(path):
            raise IOError("decord shim: video not found: %s" % path)
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise IOError("decord shim: cannot open video: %s" % path)
        self._len = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or 24.0
        self._w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._next_pos = 0  # next frame index the reader will yield

    def __len__(self):
        return self._len

    def get_avg_fps(self):
        return self._fps

    def _seek_read(self, idx):
        if idx != self._next_pos:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise IOError("decord shim: read failed at frame %d of %s" % (idx, self.path))
        self._next_pos = idx + 1
        return frame[:, :, ::-1]  # BGR -> RGB

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return _Batch(self.get_batch(range(*idx.indices(self._len))).asnumpy())
        if idx < 0:
            idx += self._len
        return self._seek_read(int(idx))

    def get_batch(self, indices):
        indices = [int(i) for i in indices]
        if not indices:
            return _Batch(np.zeros((0, self._h, self._w, 3), dtype=np.uint8))
        arr = np.zeros((len(indices), self._h, self._w, 3), dtype=np.uint8)
        for row, i in enumerate(indices):
            if i < 0:
                i += self._len
            if i < 0 or i >= self._len:
                raise IndexError("decord shim: frame index %d out of range %d" % (i, self._len))
            arr[row] = self._seek_read(i)
        return _Batch(arr)

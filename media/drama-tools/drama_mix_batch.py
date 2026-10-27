# -*- coding: utf-8 -*-
"""Batch driver for the r1003 three-layer mixer: any episode range, same code path.

Reuses drama_mix3_r1003.py by overriding its module globals (TTS_DIR / OUT_DIR /
EPS / LOG / DONE / RECEIPT), so the mix math (RMS -20 dBFS dialogue, ducked
ambient, procedural SFX, amix+alimiter) stays byte-identical to the EP001-003 pilot.

Usage: python drama_mix_batch.py EP004-EP060 --tts r1200_ep004_060 --out r1201_ep004_060
"""
import importlib.util
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "drama_mix3_r1003.py")
MIX_OUT = r"C:\Fluxgroup\FluxGroup\media\drama-mix-out"


def parse_range(tok):
    if "-" in tok:
        a, b = tok.split("-", 1)
        return ["EP%03d" % n for n in range(int(a.replace("EP", "")), int(b.replace("EP", "")) + 1)]
    return [tok]


def main(argv):
    eps, tts, out = [], None, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--tts":
            i += 1
            tts = argv[i]
        elif a == "--out":
            i += 1
            out = argv[i]
        elif not a.startswith("--"):
            eps.extend(parse_range(a))
        i += 1
    if not (eps and tts and out):
        print("usage: drama_mix_batch.py EP004-EP060 --tts <tts-batch-dir> --out <mix-dir>")
        return 2

    spec = importlib.util.spec_from_file_location("mx", SRC)
    mx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mx)

    mx.TTS_DIR = os.path.join(r"C:\Fluxgroup\FluxGroup\media\drama-tts-out", tts)
    mx.OUT_DIR = os.path.join(MIX_OUT, out)
    mx.EPS = eps
    mx.LOG = os.path.join(BASE, "mix_%s.log" % out)
    mx.DONE = os.path.join(BASE, "mix_%s.DONE.json" % out)
    if hasattr(mx, "RECEIPT"):
        mx.RECEIPT = os.path.join(BASE, "mix_%s.receipt.json" % out)
    os.makedirs(mx.OUT_DIR, exist_ok=True)
    print("MIX-BATCH eps=%d (%s..%s) tts=%s out=%s" % (len(eps), eps[0], eps[-1], mx.TTS_DIR, mx.OUT_DIR), flush=True)
    rc = mx.main()
    print("MIX-BATCH-DONE rc=%s" % rc, flush=True)
    return rc or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
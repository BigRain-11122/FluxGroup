# -*- coding: utf-8 -*-
"""Batch driver for the r1003 three-layer mixer: any episode range, same code path.

Reuses drama_mix3_r1003.py by overriding its module globals (TTS_DIR / OUT_DIR /
EPS / LOG / DONE / RECEIPT) so the mix math (dialogue RMS -20 dBFS, ducked
ambient, procedural SFX, amix+alimiter) stays identical to the EP001-003 pilot.

The pilot hand-authored BED_PROG / SFX_PROG for EP001-003 only; for any other
episode this driver synthesises a program deterministically from the script
(subtitle/description keyword -> bed / one-shot), sparse by design (<=7 cues).

Usage:
  python drama_mix_batch.py EP001-EP060 --tts r1202_ep001_060 --out r1203_ep001_060
"""
import importlib.util
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "drama_mix3_r1003.py")
MIX_OUT = r"C:\Fluxgroup\FluxGroup\media\drama-mix-out"
EPISODES = r"C:\Fluxgroup\FluxGroup\cph4\fleet\drama-001-stockera\episodes"

BED_RULES = [
    (("\u5927\u5385", "\u4ea4\u6613", "\u76d8\u53e3", "\u8bc1\u5238", "\u7ea2\u9a6c\u7532"), "hall_active"),
    (("\u96e8",), "rain_low"),
    (("\u8857", "\u5df7", "\u8def", "\u5929\u6865", "\u5e7f\u573a"), "city_day"),
    (("\u591c", "\u51cc\u6668"), "city_night"),
    (("\u8bb0\u8005", "\u955c\u5934", "\u91c7\u8bbf", "\u8bdd\u7b52"), "interview"),
    (("\u98ce\u6247", "\u95f7\u70ed", "\u673a\u623f"), "fan_room"),
    (("\u4eba\u7fa4", "\u56f4\u89c2", "\u6563\u6237", "\u558a"), "crowd_hot"),
    (("\u5bb6", "\u5c4b", "\u623f\u95f4", "\u5bbf\u820d", "\u5ba2\u5385", "\u95e8"), "tea_room"),
]

SFX_RULES = [
    (("\u5f00\u95e8", "\u63a8\u95e8", "\u51fa\u9662"), "creak"),
    (("\u7535\u8bdd", "\u5bf9\u8bb2", "\u547c\u53eb"), "walkie"),
    (("\u6454", "\u7838", "\u70b8", "\u5de8\u54cd", "\u62cd\u684c"), "thud"),
    (("\u949f", "\u5f00\u5e02", "\u6536\u76d8"), "bell_open"),
    (("\u811a\u6b65", "\u8dd1", "\u8d70"), "steps"),
]


def parse_range(tok):
    if "-" in tok:
        a, b = tok.split("-", 1)
        return ["EP%03d" % n for n in range(int(a.replace("EP", "")), int(b.replace("EP", "")) + 1)]
    return [tok]


def _ep_text(ep):
    p = os.path.join(EPISODES, ep + ".json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    out = []
    for s in d.get("shots", []):
        blob = " ".join(str(s.get(k) or "") for k in ("sub", "detail_en", "kind", "speaker"))
        out.append((int(s.get("n") or 0), blob))
    return out


def _pick_bed(blob):
    for keys, bed in BED_RULES:
        if any(k in blob for k in keys):
            return bed
    return "hall_faint"


def synth_programs(mx, eps):
    """Fill BED_PROG / SFX_PROG for episodes the pilot never hand-authored."""
    filled = []
    for ep in eps:
        if ep in mx.BED_PROG and ep in mx.SFX_PROG:
            continue
        shots = _ep_text(ep)
        if not shots:
            continue
        beds, sfx = [], []
        last_bed = None
        for n, blob in shots:
            bed = _pick_bed(blob)
            if bed != last_bed:
                beds.append((n, bed, 0.85, 1.0))
                last_bed = bed
            for keys, name in SFX_RULES:
                if name in mx.SFX and any(k in blob for k in keys):
                    sfx.append((n, name, 0.15, 0.8))
                    break
        if "title" in mx.SFX:
            sfx.insert(0, (shots[0][0], "title", 0.1, 0.75))
        if len(sfx) > 7:
            sfx = sfx[:7]
        if not beds:
            beds = [(shots[0][0], "hall_faint", 0.85, 1.0)]
        mx.BED_PROG[ep] = beds
        mx.SFX_PROG[ep] = sfx
        filled.append(ep)
    return filled


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
        print("usage: drama_mix_batch.py EP001-EP060 --tts <tts-dir> --out <mix-dir>")
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

    filled = synth_programs(mx, eps)
    print("MIX-BATCH eps=%d (%s..%s) synthesized_programs=%d tts=%s out=%s"
          % (len(eps), eps[0], eps[-1], len(filled), mx.TTS_DIR, mx.OUT_DIR), flush=True)
    rc = mx.main()
    print("MIX-BATCH-DONE rc=%s" % rc, flush=True)
    return rc or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
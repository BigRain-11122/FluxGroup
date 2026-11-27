# -*- coding: utf-8 -*-
"""Build a partial MANIFEST-r998.json for already-generated episodes, so the
mixer can run before the full batch finishes (the batch only writes the manifest
at the very end).

Usage: py make_partial_manifest.py r1202_ep001_060 EP001,EP002,EP003 [--stage r1202_preview]
"""
import io
import json
import os
import shutil
import sys
import wave

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TTS_ROOT = r"C:\Fluxgroup\FluxGroup\media\drama-tts-out"
EPISODES = r"C:\Fluxgroup\FluxGroup\cph4\fleet\drama-001-stockera\episodes"


def dur(p):
    try:
        with wave.open(p) as w:
            return round(w.getnframes() / float(w.getframerate()), 3)
    except Exception:
        return 0.0


def main(argv):
    src = argv[0]
    eps = argv[1].split(",")
    stage = None
    i = 2
    while i < len(argv):
        if argv[i] == "--stage":
            i += 1
            stage = argv[i]
        i += 1
    src_dir = os.path.join(TTS_ROOT, src)
    out_dir = os.path.join(TTS_ROOT, stage or (src + "_preview"))
    os.makedirs(out_dir, exist_ok=True)

    lines = []
    for ep in eps:
        j = json.load(open(os.path.join(EPISODES, ep + ".json"), encoding="utf-8"))
        s_dir = os.path.join(src_dir, ep)
        d_dir = os.path.join(out_dir, ep)
        os.makedirs(d_dir, exist_ok=True)
        for s in j["shots"]:
            spk = (s.get("speaker") or "").strip()
            sub = (s.get("sub") or "").strip()
            if not (spk and sub):
                continue
            name = "ep%s_line%02d.wav" % (ep[-3:], s["n"])
            p = os.path.join(s_dir, name)
            if not os.path.exists(p):
                continue
            tgt = os.path.join(d_dir, name)
            if not os.path.exists(tgt):
                shutil.copy2(p, tgt)
            lines.append({
                "ep": ep, "n": s["n"], "name": name, "speaker": spk, "text": sub,
                "file": tgt, "ok": True, "audio_s": dur(tgt), "gen_s": 0,
                "shot_dur": float(s.get("dur") or 3.0), "fx": s.get("fx") or "",
                "ref": "", "cast": "",
            })
    mf = {"eps": eps, "lines": lines, "partial": True}
    with open(os.path.join(out_dir, "MANIFEST-r998.json"), "w", encoding="utf-8") as f:
        json.dump(mf, f, ensure_ascii=False, indent=1)
    print("MANIFEST %s eps=%d lines=%d -> %s" % (src, len(eps), len(lines), out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
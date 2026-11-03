# -*- coding: utf-8 -*-
"""vb_assets.py - pack one trained voice into a self-contained, durable asset folder.

Layout (voicebank/assets/<voice>/):
  model.pth        SoVITS weights (the actual trained timbre)
  ref.wav/.txt     reference clip + transcript (needed to reuse the voice)
  demo.wav/.mp3    QC'd sample
  meta.json        sources, corpus size, pitch profile, QC numbers, weight provenance
  corpus.zip       the exact training corpus (segments + list.txt), so the model is
                   reproducible without re-downloading anything

Also appends one row to voicebank/assets/INDEX.jsonl so the library is enumerable.
"""
import json
import os
import shutil
import sys
import time
import zipfile

VB = os.environ.get("VB_ROOT", r"E:\Fluxgroup\.codely-cli\voicebank")
GPT = os.environ.get("VB_GPT_ROOT",
                     r"C:\Fluxgroup\FluxGroup\media\drama-tools\GPT-SoVITS")
SOVITS_DIR = os.path.join(GPT, "SoVITS_weights_v2Pro")
ASSETS = os.path.join(VB, "assets")


def main():
    voice = sys.argv[1]
    # optional tag selects demo.final.* / ref.final.* / demo_check.final.json, so several
    # reference takes can coexist while the packed asset keeps canonical file names
    tag = sys.argv[2] if len(sys.argv) > 2 else ""
    sfx = ("." + tag) if tag else ""
    src = os.path.join(VB, voice)
    meta = json.load(open(os.path.join(src, "voice.json"), encoding="utf-8"))
    chk_path = os.path.join(src, "demo_check%s.json" % sfx)
    chk = json.load(open(chk_path, encoding="utf-8")) if os.path.exists(chk_path) else {}

    dst = os.path.join(ASSETS, voice)
    os.makedirs(dst, exist_ok=True)

    w = meta.get("weights")
    if not w or not os.path.exists(os.path.join(SOVITS_DIR, w)):
        print("MISSING weights for", voice, w)
        return 2
    shutil.copy2(os.path.join(SOVITS_DIR, w), os.path.join(dst, "model.pth"))

    for base in ("ref.wav", "ref.txt", "demo.wav", "demo.mp3"):
        stem, ext = os.path.splitext(base)
        p = os.path.join(src, stem + sfx + ext)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dst, base))

    # corpus: segments + list.txt, zipped so the folder stays tidy
    corpus_zip = os.path.join(dst, "corpus.zip")
    seg = os.path.join(src, "seg")
    lst = os.path.join(src, "exp", "list.txt")
    if os.path.isdir(seg) and not os.path.exists(corpus_zip):
        with zipfile.ZipFile(corpus_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(seg)):
                if f.endswith(".wav"):
                    z.write(os.path.join(seg, f), "seg/" + f)
            if os.path.exists(lst):
                z.write(lst, "list.txt")

    rec = {
        "voice": voice,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "model.pth",
        "weights_name": w,
        "corpus_minutes": meta.get("minutes"),
        "corpus_clips": meta.get("clips"),
        "f0_med": round(meta.get("f0_med") or 0, 1),
        "sample_rate": chk.get("sample_rate"),
        "qc": {k: chk.get(k) for k in
               ("match_ratio", "hf_ratio", "noise_floor_db", "clip_frames", "dur_s")},
        "ref_text": chk.get("ref_text"),
        # identity and spectral headroom of the reference clip decide the clone's likeness
        # and brightness, so they belong in the record next to the QC numbers
        "ref_pick": None,
        "sources": meta.get("source_meta", []),
        "reuse": ("python voicebank_say.py %s  (needs VB_ROOT/VB_GPT_ROOT; "
                  "model.pth goes to SoVITS_weights_v2Pro/)" % voice),
    }
    pk = os.path.join(VB, "pickref-%s.json" % voice)
    if os.path.exists(pk):
        pj = json.load(open(pk, encoding="utf-8"))
        rec["ref_pick"] = {"rule": pj.get("rule"), "chosen": pj.get("chosen")}
    json.dump(rec, open(os.path.join(dst, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with open(os.path.join(ASSETS, "INDEX.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": rec["created"], "voice": voice,
                            "minutes": rec["corpus_minutes"], "f0": rec["f0_med"],
                            "match": rec["qc"]["match_ratio"],
                            "hf": rec["qc"]["hf_ratio"],
                            "model": os.path.join(dst, "model.pth"),
                            "demo": os.path.join(dst, "demo.mp3")},
                           ensure_ascii=False) + "\n")
    size = sum(os.path.getsize(os.path.join(dst, n)) for n in os.listdir(dst))
    print("PACKED %s -> %s (%.1f MB)" % (voice, dst, size / 1e6))
    return 0


sys.exit(main())
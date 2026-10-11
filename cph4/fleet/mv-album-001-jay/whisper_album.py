# -*- coding: utf-8 -*-
# whisper_album.py - 《Jay》十曲词级锚点批（资源库ape已转320k mp3）
import json, os, sys

SRC = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\audio"
OUT = r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv-album-001-jay\anchors"
os.makedirs(OUT, exist_ok=True)

import whisper
m = whisper.load_model("small")

for f in sorted(os.listdir(SRC)):
    if not f.endswith(".mp3"):
        continue
    sid = f.replace("周杰伦 - ", "").replace(".mp3", "")
    jout = os.path.join(OUT, sid + ".json")
    if os.path.isfile(jout):
        print("SKIP", sid, flush=True)
        continue
    r = m.transcribe(os.path.join(SRC, f), word_timestamps=True, language="zh", verbose=False)
    words, lines = [], []
    for seg in r["segments"]:
        sw = seg.get("words") or []
        if sw:
            t0, t1 = sw[0]["start"], sw[-1]["end"]
            text = "".join(w["word"] for w in sw)
        else:
            t0, t1, text = seg["start"], seg["end"], seg["text"]
        lines.append({"t0": round(t0, 2), "t1": round(t1, 2), "text": text.strip()})
        for w in sw:
            words.append({"t0": round(w["start"], 2), "t1": round(w["end"], 2), "w": w["word"].strip()})
    json.dump({"words": words, "lines": lines}, open(jout, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, sid + ".txt"), "w", encoding="utf-8") as fo:
        for L in lines:
            fo.write("%7.2f - %7.2f | %s\n" % (L["t0"], L["t1"], L["text"]))
    print("DONE %s words=%d lines=%d last=%.2f" % (sid, len(words), len(lines), lines[-1]["t1"]), flush=True)
print("ALBUM ANCHORS ALL DONE", flush=True)

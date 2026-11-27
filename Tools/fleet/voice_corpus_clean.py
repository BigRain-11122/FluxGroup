"""语料清洗：剔掉朗读模板句与空段。

LibriVox 每章开头固定有 "Chapter N of ..." / "This Librivox recording is in the public
domain" / 书名作者，这些是模板语音，用作训练会让模型学会重复开场白。

用法：
  python Tools/fleet/voice_corpus_clean.py --qc <qc.json> [--out <clean.json>]
"""
import argparse
import json
import re

# 模板句特征（命中任一即剔除）
TEMPLATE_PATTERNS = [
    r"librivox", r"public domain", r"recording is in the",
    r"chapter\s+\w+\s+of", r"end of chapter", r"this is a librivox",
    r"read by", r"produced by", r"proof[-\s]?listened",
]

MIN_CHARS = 12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qc", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    d = json.load(open(a.qc, encoding="utf-8"))
    keep, dropped = [], []
    for r in d["rows"]:
        if r.get("verdict") != "PASS":
            dropped.append((r["file"], "asr-fail"))
            continue
        t = (r.get("text") or "").lower()
        hit = next((p for p in TEMPLATE_PATTERNS if re.search(p, t)), None)
        if hit:
            dropped.append((r["file"], "template:" + hit))
            continue
        if len(re.sub(r"\s", "", r.get("text") or "")) < MIN_CHARS:
            dropped.append((r["file"], "too-short"))
            continue
        keep.append(r["file"])

    out = {"qc": a.qc, "kept": len(keep), "dropped": len(dropped),
           "files": keep,
           "dropped_detail": [{"file": f, "why": w} for f, w in dropped[:200]]}
    p = a.out or a.qc.replace(".json", "-clean.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("kept %d / %d  dropped %d -> %s" % (len(keep), d["checked"], len(dropped), p))
    from collections import Counter
    for k, v in Counter(w.split(":")[0] for _, w in dropped).most_common():
        print("  %-12s %d" % (k, v))


if __name__ == "__main__":
    main()
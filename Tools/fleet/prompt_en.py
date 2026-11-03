# -*- coding: utf-8 -*-
"""把 ASSET-PROMPTS 里的中文提示翻成 SDXL 读得懂的英文标签，结果落 PROMPTS-EN-v1.json 缓存。

SDXL 的 CLIP 基本读不懂中文，直接用中文提示出图会跑题（实测把道具画成街景）。
本机有 ollama 时用它做转换；没有就直接跳过，调用方回落中文原文。

用法：
  python Tools/fleet/prompt_en.py            # 补齐缓存里缺的条目
  python Tools/fleet/prompt_en.py --force    # 全部重翻
Exit: 0 全部有英文；3 有缺口（ollama 不可达等）
"""
import argparse
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1", "ASSET-PROMPTS-v1.json")
CACHE = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1", "PROMPTS-EN-v1.json")
OLLAMA = "http://127.0.0.1:11434"
MODEL = "qwen3.5:4b-q4_K_M"
VISUAL = ("props", "scenes", "motions", "transitions", "characters", "styles", "typography")

INSTR = (
    "Translate the Chinese asset brief into ONE English Stable Diffusion prompt. "
    "Output ONLY comma-separated visual tags, max 45 words, no explanation, no quotes, no numbering. "
    "Keep the main object as the hero; camera framing and art style must survive the translation.\n"
    "subject: %(subject)s\ncomposition: %(composition)s\nstyle: %(style)s"
)


def ask(item):
    body = {"model": MODEL, "prompt": INSTR % {
                "subject": item.get("subject", ""),
                "composition": item.get("composition", ""),
                "style": item.get("style", "")},
            "stream": False, "think": False,
            "options": {"temperature": 0.2, "num_predict": 200}}
    req = urllib.request.Request(OLLAMA + "/api/generate",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    return " ".join((r.get("response") or "").split())


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)

    spec = json.load(open(SPEC, encoding="utf-8"))
    items = spec.get("items") or {}
    cache = {}
    if os.path.exists(CACHE) and not a.force:
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}
    entries = cache.setdefault("items", {})

    todo = [k for k, v in items.items()
            if v.get("cls") in VISUAL and (a.force or k not in entries)
            and (not a.only or k == a.only)]
    missing = []
    for i, key in enumerate(todo, 1):
        try:
            en = ask(items[key])
        except Exception as e:
            missing.append([key, str(e)[:120]])
            print("[prompt_en] %d/%d %s FAILED %s" % (i, len(todo), key, str(e)[:60]))
            continue
        if not en:
            missing.append([key, "empty"])
            continue
        entries[key] = {"en": en, "model": MODEL,
                        "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        print("[prompt_en] %d/%d %s -> %s" % (i, len(todo), key, en[:80]))

    cache["note"] = ("中文提示在 SDXL 上会跑题，出图时优先用这里的英文标签；"
                     "缺条目时调用方回落 ASSET-PROMPTS 原文。")
    cache["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    have = sum(1 for k, v in items.items() if v.get("cls") in VISUAL and k in entries)
    want = sum(1 for v in items.values() if v.get("cls") in VISUAL)
    print("[prompt_en] 覆盖 %d/%d -> %s" % (have, want, os.path.relpath(CACHE, ROOT)))
    for m in missing[:5]:
        print("   ! ", m[0], m[1])
    return 0 if have == want else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
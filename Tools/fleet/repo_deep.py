#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repo_deep.py - 把没被 repo_map 覆盖的文件做深度摘要（本地 4B 并行）。

为什么：填谷环把卡都标完了、回执也读完了，GPU 又空下来。
仓里还有几千个 tier4 文件没人读——这是真活，不是造卡。
产出：state/deep-summaries.jsonl（文件级摘要，供检索/理解/评审复用）。
用法：python3 Tools/fleet/repo_deep.py --limit 200 --workers 6
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
OUT = os.path.join(STATE, "deep-summaries.jsonl")
IDX = os.path.join(STATE, "deep-index.jsonl")
BASE = "http://127.0.0.1:11434"
MODEL = os.environ.get("DEEP_MODEL") or "qwen3.5:4b-mlx"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".codely-cli", "cph4/fleet/state", "cph4/fleet/queue-receipts"}
EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".md", ".json", ".yml", ".yaml", ".sh", ".ps1", ".html", ".css"}


def seen():
    s = set()
    try:
        for line in open(IDX, encoding="utf-8"):
            s.add(json.loads(line).get("path"))
    except OSError:
        pass
    return s


def walk():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        if any(rel == d or rel.startswith(d + os.sep) for d in SKIP_DIRS):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in EXT:
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) < 200 or os.path.getsize(p) > 400000:
                    continue
            except OSError:
                continue
            yield os.path.relpath(p, ROOT)


def ask(text, path):
    prompt = ("用两句话说明这段文件的作用（第一句总体用途，第二句关键函数/数据结构），不要客套，不要编造。\n"
              "文件：%s\n\n%s" % (path, text[:4000]))
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "think": False, "stream": False, "keep_alive": "10m",
            "options": {"num_ctx": 4096, "num_predict": 120, "temperature": 0.1}}
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    return {"path": path, "summary": ((d.get("message") or {}).get("content") or "").strip()[:500],
            "sec": round(time.time() - t, 2), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    done = seen()
    todo = [p for p in walk() if p not in done][:a.limit]
    if not todo:
        print("no new files")
        return 0
    os.makedirs(STATE, exist_ok=True)
    n = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for res in ex.map(lambda p: safe(p), todo):
            if not res:
                continue
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
            with open(IDX, "a", encoding="utf-8") as f:
                f.write(json.dumps({"path": res["path"]}, ensure_ascii=False) + "\n")
            n += 1
    print("summarized %d/%d" % (n, len(todo)))
    return 0


def safe(p):
    try:
        text = open(os.path.join(ROOT, p), encoding="utf-8", errors="replace").read()
        return ask(text, p)
    except Exception:
        return None


if __name__ == "__main__":
    sys.exit(main())

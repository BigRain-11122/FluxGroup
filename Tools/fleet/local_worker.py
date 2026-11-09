#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_worker.py - 给本机 4B 持续派活：把回执变成一句话结论。

为什么（2026-11-09 CEO「本地算力调用的不积极」）：4B 常驻却常常空转——
判读队列一空就没活。回执是源源不断的事实流（近 7 天 1300+ 份），
正适合 4B：短、结构化、不需要长上下文。

做法：每 5 分钟取最多 20 份未处理回执 → 4B 出一句话（完成了什么/风险）→
写 state/local-digest.jsonl + 追加 cph4/fleet/LOCAL-DIGEST.md。

用法：python3 Tools/fleet/local_worker.py [--limit 20] [--dry]
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
REC = os.path.join(F, "queue-receipts")
STATE = os.path.join(F, "state", "local-digest.jsonl")
MD = os.path.join(F, "LOCAL-DIGEST.md")
OLLAMA = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
MODEL = os.environ.get("WORKER_MODEL") or "qwen3:4b-instruct"


def seen():
    out = set()
    try:
        for line in open(STATE, encoding="utf-8"):
            try:
                out.add(json.loads(line).get("key"))
            except Exception:
                pass
    except OSError:
        pass
    return out


def ask(text):
    body = {"model": MODEL, "messages": [{"role": "user", "content":
            "下面是一份机队回执的片段。用一句中文说明：完成了什么、有没有风险。"
            "不超过 40 字，不要客套。\n\n" + text}],
            "think": False, "stream": False, "keep_alive": "10m",
            "options": {"num_ctx": 4096, "num_predict": 80, "temperature": 0.1}}
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return ((json.loads(r.read()).get("message") or {}).get("content") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    done = seen()
    files = []
    for f in os.listdir(REC):
        p = os.path.join(REC, f)
        if not f.endswith((".json", ".md")):
            continue
        try:
            st = os.stat(p)
        except OSError:
            continue
        key = "%s:%d" % (f, st.st_mtime)
        if key in done:
            continue
        files.append((st.st_mtime, p, key, f))
    files.sort(reverse=True)
    files = files[:a.limit]
    if not files:
        print("no new receipts")
        return 0

    def work(item):
        mtime, p, key, f = item
        try:
            raw = open(p, encoding="utf-8", errors="replace").read()[:1500]
        except OSError:
            return None
        try:
            s = ask(raw)
        except Exception as e:
            s = "本地模型失败：%s" % str(e)[:60]
        return {"key": key, "file": f, "summary": s, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}

    with ThreadPoolExecutor(max_workers=3) as ex:
        rows = [r for r in ex.map(work, files) if r]

    if a.dry:
        for r in rows:
            print(r["file"], "|", r["summary"][:80])
        return 0

    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(MD, "a", encoding="utf-8") as f:
        for r in rows:
            f.write("- %s · %s · %s\n" % (r["ts"][5:16], r["file"], r["summary"][:100]))
    print("digested %d receipts" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())

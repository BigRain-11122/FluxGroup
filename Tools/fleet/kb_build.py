#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_build.py - 用本地 9B 把全仓摘要合成"知识库页"（每个域一页）。

2026-11-10/11：repo_deep 已覆盖 4011 个文件；散摘要不好用，合成域级知识页才可读。
夜间跑（03:10），白天不占会话车道；只用本地模型。
"""
import argparse
import json
import os
import time
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = os.path.join(ROOT, "cph4", "fleet", "state")
OUTDIR = os.path.join(ROOT, "docs", "AI-KB")
MODEL = os.environ.get("KB_MODEL") or "qwen3.5:9b-mlx"
BASE = os.environ.get("KB_BASE") or "http://127.0.0.1:11436"


def group():
    g = defaultdict(list)
    try:
        for line in open(os.path.join(S, "deep-summaries.jsonl"), encoding="utf-8"):
            d = json.loads(line)
            p = d.get("path") or ""
            top = p.split("/")[0] if "/" in p else "(root)"
            g[top].append(d)
    except OSError:
        pass
    return g


def ask(prompt, ctx=32768):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "think": False, "stream": False, "keep_alive": "10m",
            "options": {"num_ctx": ctx, "num_predict": 900, "temperature": 0.3}}
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return ((json.loads(r.read()).get("message") or {}).get("content") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="")
    ap.add_argument("--limit", type=int, default=120)
    a = ap.parse_args()
    g = group()
    os.makedirs(OUTDIR, exist_ok=True)
    for top, items in sorted(g.items(), key=lambda x: -len(x[1])):
        if a.domain and top != a.domain:
            continue
        if len(items) < 3:
            continue
        lines = ["%s :: %s" % (d.get("path"), (d.get("summary") or "")[:220]) for d in items[:a.limit]]
        prompt = ("下面是一个目录下文件的摘要清单。请整理成一页中文知识页：\n"
                  "①这个目录是做什么的 ②关键模块/入口 ③明显的风险或待办。\n"
                  "用 Markdown，不用客套，不要编造清单里没有的文件。\n\n" + "\n".join(lines))
        t0 = time.time()
        try:
            txt = ask(prompt)
        except Exception as e:
            print(top, "ERR", str(e)[:100]); continue
        p = os.path.join(OUTDIR, "KB-%s.md" % top.replace("/", "_"))
        open(p, "w", encoding="utf-8").write("# %s 知识页\n\n> 自动生成 %s，来源 %d 份摘要\n\n%s\n"
                                             % (top, time.strftime("%Y-%m-%d %H:%M"), len(items), txt))
        print(top, "->", p, "%.0fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

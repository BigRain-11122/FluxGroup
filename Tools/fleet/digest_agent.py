#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""digest_agent.py - the aggregator the fleet was missing.

Every seat already drops receipts, but nobody merged them: the CEO had to read six files to
learn one thing. This reads the day's facts (queue counts, receipts, supervisor verdict,
deadline lines) and asks the local 4B for a five-line synthesis - facts only, no invention,
no new work.

Cached by content hash, so an unchanged fleet costs zero model time.
"""
import hashlib, json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "dispatcher", "DIGEST.md")
CACHE = os.path.join(F, "dispatcher", "digest-cache.json")
MODEL = "qwen3:4b-instruct"


def jl(p):
    out = []
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def facts():
    q = jl(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    by = {}
    for r in q:
        by[r.get("state")] = by.get(r.get("state"), 0) + 1
    rec = os.path.join(F, "queue-receipts")
    today = datetime.now().strftime("%Y%m%d")
    new = sorted(f for f in os.listdir(rec) if f.endswith((".md", ".json"))
                 and datetime.fromtimestamp(os.path.getmtime(os.path.join(rec, f))).strftime("%Y%m%d") == today)
    sup = ""
    p = os.path.join(F, "dispatcher", "SUPERVISOR.md")
    if os.path.exists(p):
        sup = "\n".join(open(p, encoding="utf-8").read().splitlines()[:8])
    dl = ""
    p = os.path.join(F, "dispatcher", "DEADLINES.md")
    if os.path.exists(p):
        dl = "\n".join(open(p, encoding="utf-8").read().splitlines()[:8])
    return by, new, sup, dl


def main():
    by, new, sup, dl = facts()
    blob = json.dumps([by, new[:40], sup, dl], ensure_ascii=False)
    h = hashlib.sha256(blob.encode()).hexdigest()[:16]
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}
    if cache.get("hash") == h and cache.get("text"):
        text = cache["text"]
    else:
        prompt = ("你是机队汇总席。只依据下面的事实写 5 行中文结论，每行<=40字："
                  "①今天产出了什么 ②哪里卡住 ③下一步谁该动 ④方向是否对齐 ⑤风险一句。"
                  "不得编造事实、命令、文件名。\n\n事实：\n" + blob[:3000])
        import urllib.request
        body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False, "think": False,
                           "keep_alive": "5m", "options": {"num_ctx": 8192, "temperature": 0.2}}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        text = (json.load(urllib.request.urlopen(req, timeout=180)).get("response") or "").strip()
        if text:
            json.dump({"hash": h, "text": text}, open(CACHE, "w", encoding="utf-8"),
                      ensure_ascii=False)
    body = ["# 一屏汇总 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), "",
            "队列 " + " ".join("%s=%d" % (k, v) for k, v in sorted(by.items())),
            "今日新回执 %d 份" % len(new), "", text or "- 本次未生成（模型不可用）",
            "", "---", "*汇总席 bm-m · 4B · 只读事实*"]
    open(OUT, "w", encoding="utf-8").write("\n".join(body) + "\n")
    print("[digest] receipts=%d cached=%s" % (len(new), cache.get("hash") == h))
    return 0


if __name__ == "__main__":
    sys.exit(main())
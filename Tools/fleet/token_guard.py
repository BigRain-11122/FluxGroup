#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""token_guard.py - 真省 token 的三件事：量、裁、缓。

为什么（2026-11-10 CEO「配一个 GitHub 上能省 token 的工具，要真正有用」）：
  - 量：没有计数就不知道浪费在哪（openai/tiktoken，本机已装 0.14）。
  - 裁：云卡把 when_all 的整份文档塞进 prompt，一次几万 token；超预算就头尾保留、中间标注裁掉。
  - 缓：同题同证据重复判读，直接回缓存（SQLite，零依赖；GPTCache 的思路，不引重依赖）。

用法：
  python3 Tools/fleet/token_guard.py count --file X
  python3 Tools/fleet/token_guard.py shrink --file X --budget 8000
  python3 Tools/fleet/token_guard.py report            # 扫卡面 prompt，列出超预算的
  python3 Tools/fleet/token_guard.py cache-stats
  python3 Tools/fleet/token_guard.py cache-get --key K
  python3 Tools/fleet/token_guard.py cache-put --key K --file Y
库调用：guard(text, budget) -> (text, saved_tokens)
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
DB = os.path.join(STATE, "llm-cache.db")
LOG = os.path.join(STATE, "token-guard.jsonl")
DEFAULT_BUDGET = int(os.environ.get("TOKEN_BUDGET") or 16000)

_ENC = None


def enc():
    global _ENC
    if _ENC is None:
        try:
            import tiktoken
            _ENC = lambda s: len(tiktoken.get_encoding("cl100k_base").encode(s))
        except Exception:
            _ENC = lambda s: max(1, len(s) // 3)
    return _ENC


def count(text):
    return enc()(text or "")


def shrink(text, budget, head_ratio=0.6):
    n = count(text)
    if n <= budget:
        return text, 0
    head_tok = int(budget * head_ratio)
    tail_tok = budget - head_tok - 40
    # 按 token 比例换算成字符位置（近似足够，末尾再标一行）
    head_chars = int(len(text) * head_tok / max(n, 1))
    tail_chars = int(len(text) * max(tail_tok, 1) / max(n, 1))
    cut = n - budget
    out = (text[:head_chars]
           + "\n\n...[token_guard 裁掉约 %d tokens，中间内容省略]...\n\n" % cut
           + text[-tail_chars:])
    return out, n - count(out)


def guard(text, budget=None):
    budget = budget or DEFAULT_BUDGET
    after, saved = shrink(text or "", budget)
    if saved > 0:
        try:
            os.makedirs(STATE, exist_ok=True)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "before": count(text), "after": count(after),
                                    "saved": saved}, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return after, saved


def _db():
    os.makedirs(STATE, exist_ok=True)
    c = sqlite3.connect(DB, timeout=10)
    c.execute("CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, model TEXT, prompt TEXT,"
              " response TEXT, ts REAL, hits INTEGER DEFAULT 0)")
    return c


def cache_get(key, ttl_h=72):
    c = _db()
    row = c.execute("SELECT response, ts FROM cache WHERE key=?", (key,)).fetchone()
    if not row:
        return None
    if ttl_h and time.time() - row[1] > ttl_h * 3600:
        return None
    c.execute("UPDATE cache SET hits=hits+1 WHERE key=?", (key,))
    c.commit()
    return row[0]


def cache_put(key, response, model="", prompt=""):
    c = _db()
    c.execute("INSERT OR REPLACE INTO cache(key,model,prompt,response,ts,hits) VALUES(?,?,?,?,?,0)",
              (key, model, (prompt or "")[:500], response, time.time()))
    c.commit()


def cache_stats():
    c = _db()
    n, hits = c.execute("SELECT COUNT(*), COALESCE(SUM(hits),0) FROM cache").fetchone()
    return {"entries": n, "hits": hits}


def report():
    rows = []
    for p in ("cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/PRODUCTION-BACKLOG.jsonl"):
        try:
            for line in open(os.path.join(ROOT, p), encoding="utf-8"):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                t = str(d.get("prompt") or "")
                if t:
                    rows.append((count(t), d.get("id"), d.get("state")))
        except OSError:
            pass
    rows.sort(reverse=True)
    over = [r for r in rows if r[0] > DEFAULT_BUDGET]
    print("prompt 卡 %d 张，超 %d token 的 %d 张" % (len(rows), DEFAULT_BUDGET, len(over)))
    for n, i, s in rows[:10]:
        print("%7d  %-42s %s" % (n, i, s))
    saved = 0
    try:
        for line in open(LOG, encoding="utf-8"):
            saved += int(json.loads(line).get("saved") or 0)
    except OSError:
        pass
    print("累计裁掉/省下 %d tokens" % saved)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["count", "shrink", "report", "cache-stats", "cache-get", "cache-put", "guard"])
    ap.add_argument("--file", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    ap.add_argument("--key", default="")
    a = ap.parse_args()
    body = a.text
    if a.file:
        body = open(a.file, encoding="utf-8", errors="replace").read()
    if a.cmd == "count":
        print(count(body))
    elif a.cmd == "shrink":
        out, saved = shrink(body, a.budget)
        print(out)
        print("-- saved %d tokens" % saved, file=sys.stderr)
    elif a.cmd == "guard":
        out, saved = guard(body, a.budget)
        print(out)
        print("-- saved %d tokens" % saved, file=sys.stderr)
    elif a.cmd == "report":
        report()
    elif a.cmd == "cache-stats":
        print(json.dumps(cache_stats()))
    elif a.cmd == "cache-get":
        r = cache_get(a.key)
        if r is None:
            sys.exit(1)
        print(r)
    elif a.cmd == "cache-put":
        cache_put(a.key, body)
        print("stored")


if __name__ == "__main__":
    main()

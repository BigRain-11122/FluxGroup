#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repo_rag.py - 本地检索增强：先检索工程原文，再让本机 8B 带着证据回答。

为什么（2026-11-09 实测）：32k 窗口里 12.9k 是系统提示，历史一长就要压缩；
而 8B 在没有上下文时会把 FluxGroup 答成"流量管理软件"。所以把"读工程"从
"塞长历史"改成"检索相关片段"：embedding 找证据 -> 8B 只读这几段 -> 答案带路径。

索引来源：tier1 正典 md 全文（1200 字一块）+ repo_map 的 tier2/3 骨架。
用法：
  python3 Tools/fleet/repo_rag.py index [--max-chunks 4000]
  python3 Tools/fleet/repo_rag.py ask "机队的 bm-d 是干什么的"
  python3 Tools/fleet/repo_rag.py eval
  python3 Tools/fleet/repo_rag.py status
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "repo-rag")
VEC = os.path.join(OUT, "vectors.npy")
META = os.path.join(OUT, "meta.jsonl")
EVAL = os.path.join(OUT, "eval.json")
INV = os.path.join(ROOT, "cph4", "fleet", "state", "repo-map", "inventory.json")
CHUNKS = os.path.join(ROOT, "cph4", "fleet", "state", "repo-map", "chunks.jsonl")
EMBED_URL = os.environ.get("EMBED_URL", "http://127.0.0.1:11434")
ASK_URL = os.environ.get("ASK_URL", "http://127.0.0.1:11436")
EMBED_MODEL = "qwen3-embedding:0.6b"
ASK_MODEL = os.environ.get("ASK_MODEL", "qwen3:8b-dsh32k")


def _post(url, payload, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def embed(texts, batch=16):
    out = []
    for i in range(0, len(texts), batch):
        d = _post(EMBED_URL + "/api/embed",
                  {"model": EMBED_MODEL, "input": texts[i:i + batch]}, 120)
        out.extend(d["embeddings"])
    return out


def _read(path, limit=60000):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except Exception:
        return ""


def chunk_text(path, text, size=1200, overlap=120):
    parts, buf, n = [], [], 0
    for para in text.splitlines():
        if len(buf) + len(para) + 1 > size and buf:
            parts.append("\n".join(buf))
            tail = "\n".join(buf)[-overlap:]
            buf = [tail]
        buf.append(para)
    if buf:
        parts.append("\n".join(buf))
    return [{"path": path, "text": p.strip()} for p in parts if len(p.strip()) > 120]


def build_chunks(max_chunks):
    rows = []
    if os.path.exists(INV):
        inv = json.load(open(INV, encoding="utf-8"))
        for r in inv:
            if r["tier"] != 1 or r["ext"] != ".md" or r["size"] > 300_000:
                continue
            t = _read(r["path"])
            if t:
                rows.extend(chunk_text(r["path"], t))
            if len(rows) >= max_chunks * 0.8:
                break
    if os.path.exists(CHUNKS):
        for line in open(CHUNKS, encoding="utf-8"):
            c = json.loads(line)
            if c["tier"] in (2, 3):
                rows.append({"path": c["path"], "text": c["text"]})
            if len(rows) >= max_chunks:
                break
    return rows[:max_chunks]


def index(max_chunks=4000):
    os.makedirs(OUT, exist_ok=True)
    rows = build_chunks(max_chunks)
    print("chunks:", len(rows))
    t0 = time.time()
    vecs = []
    for i in range(0, len(rows), 16):
        batch = [r["text"][:2000] for r in rows[i:i + 16]]
        vecs.extend(embed(batch, len(batch)))
        if i % 320 == 0:
            print("  embedded %d/%d (%.0fs)" % (i, len(rows), time.time() - t0))
    m = np.array(vecs, dtype=np.float32)
    m /= (np.linalg.norm(m, axis=1, keepdims=True) + 1e-9)
    np.save(VEC, m)
    with open(META, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("indexed %d chunks -> %s (%.0fs)" % (len(rows), VEC, time.time() - t0))
    return 0


def load_index():
    if not (os.path.exists(VEC) and os.path.exists(META)):
        raise SystemExit("先跑 index")
    m = np.load(VEC)
    rows = [json.loads(l) for l in open(META, encoding="utf-8")]
    return m, rows


def search(q, k=6):
    m, rows = load_index()
    qv = np.array(embed([q])[0], dtype=np.float32)
    qv /= (np.linalg.norm(qv) + 1e-9)
    sims = m @ qv
    # 正典优先：根正典/docs/cph4 顶层加分；历史归档/台账/回执降权。
    for i, r in enumerate(rows):
        p = r["path"]
        if p in ("AI.md", "README.md", "RULES.md", "BRAND.md") or p.startswith("docs/"):
            sims[i] += 0.06
        elif p.startswith("cph4/fleet/") and p.count("/") == 2:
            sims[i] += 0.03
        if any(x in p for x in ("orders-archive", "evolution-ledger", "queue-receipts",
                                "dispatcher/LOG", "/LOG", "archive/", "research/")):
            sims[i] -= 0.06
    order = np.argsort(-sims)
    picked, per_path = [], {}
    for i in order:
        p = rows[i]["path"]
        if per_path.get(p, 0) >= 2:
            continue
        per_path[p] = per_path.get(p, 0) + 1
        picked.append(i)
        if len(picked) >= k:
            break
    return [(float(sims[i]), rows[i]) for i in picked]


def answer(q, k=8, model=None, timeout=600):
    hits = search(q, k)
    ctx = "\n\n".join("[%s]\n%s" % (h[1]["path"], h[1]["text"]) for h in hits)
    prompt = ("只根据下面的工程资料回答，资料里没有就写「资料不足」，不要编造，不要用表格。\n"
              "格式：每行一条，最多 8 行，句末用括号标出证据路径。\n\n"
              "资料：\n" + ctx + "\n\n问题：" + q)
    body = {"model": model or ASK_MODEL, "messages": [{"role": "user", "content": prompt}],
            "think": False, "stream": False, "keep_alive": "15m",
            "options": {"num_ctx": 16384, "num_predict": 600, "temperature": 0.0}}
    t0 = time.time()
    d = _post(ASK_URL + "/api/chat", body, timeout)
    txt = (d.get("message") or {}).get("content") or ""
    return txt.strip(), hits, round(time.time() - t0, 1)


QUESTIONS = [
    ("七条业务线分别叫什么、各自仓库路径是什么？",
     ["gaming", "quant", "media", "domain", "life", "compute", "house"]),
    ("CPH4 Labs 的第一职责是什么？", ["元宙", "FluxVerse", "未来", "规划"]),
    ("机队有哪些机器，bm-d 是什么定位？", ["bm-a", "bm-b", "bm-c", "bm-d", "bm-m"]),
    ("机制链从上到下有哪些层？", ["CEO", "委员会", "主AGENT", "巡视", "L1", "L0", "执行", "反馈"]),
    ("本地算力的三层阶梯分别是什么？", ["L1", "L2", "L3", "确定性", "本地", "云端"]),
]


def _score(txt, keys):
    t = txt.lower()
    hit = sum(1 for k in keys if k.lower() in t)
    return round(hit / len(keys), 2)


def _baseline(q, timeout=300):
    body = {"model": ASK_MODEL, "messages": [{"role": "user", "content": q}],
            "think": False, "stream": False, "keep_alive": "15m",
            "options": {"num_ctx": 8192, "num_predict": 300, "temperature": 0.2}}
    d = _post(ASK_URL + "/api/chat", body, timeout)
    return (d.get("message") or {}).get("content") or ""


def run_eval():
    res = []
    for q, keys in QUESTIONS:
        base = _baseline(q)
        rag, hits, sec = answer(q)
        res.append({"q": q, "keys": keys, "baseline": base, "rag": rag,
                    "baseline_score": _score(base, keys), "rag_score": _score(rag, keys),
                    "sec": sec, "sources": [h[1]["path"] for h in hits]})
        print("%-28s base=%.2f rag=%.2f (%.1fs)" % (q[:24], res[-1]["baseline_score"],
                                                   res[-1]["rag_score"], sec))
    b = round(sum(r["baseline_score"] for r in res) / len(res), 2)
    g = round(sum(r["rag_score"] for r in res) / len(res), 2)
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": ASK_MODEL,
           "baseline_mean": b, "rag_mean": g, "items": res}
    json.dump(out, open(EVAL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("mean baseline=%.2f rag=%.2f -> %s" % (b, g, EVAL))
    return 0


def status():
    if os.path.exists(META):
        n = sum(1 for _ in open(META, encoding="utf-8"))
        print("index chunks: %d" % n)
        print("vectors: %s" % (os.path.getsize(VEC) // 1024,))
    else:
        print("no index")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    i = sub.add_parser("index")
    i.add_argument("--max-chunks", type=int, default=4000)
    a = sub.add_parser("ask")
    a.add_argument("question")
    a.add_argument("--k", type=int, default=6)
    sub.add_parser("eval")
    sub.add_parser("status")
    args = ap.parse_args(argv)
    if args.cmd == "index":
        return index(args.max_chunks)
    if args.cmd == "ask":
        txt, hits, sec = answer(args.question, args.k)
        print(txt)
        print("\n-- sources (%.1fs) --" % sec)
        for s, h in hits:
            print("%.3f %s" % (s, h["path"]))
        return 0
    if args.cmd == "eval":
        return run_eval()
    if args.cmd == "status":
        return status()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

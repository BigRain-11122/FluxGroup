#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""corpus_classify.py — 把"认不出属于哪一群人"的语料重新分段（本地嵌入 + 本地小模型命名）。

问题（2026-11-21 实测）：segments.classify 是**关键词命中**，62,786 行里
44,351 行（71%）落进 generic。后果是每段训练集都从"平均嗓"里取料——
段专用件训不出来的真正原因不是模型小，是喂进去的数据根本没分段。

办法（放开用本机算力，不逐行调大模型——44k 次生成要 8 小时，不可行）：
  1 本地嵌入 qwen3-embedding:0.6b 把 generic 行向量化（1024 维，批量）；
  2 单机 k-means 聚成 K 簇（numpy，无 sklearn 依赖）；
  3 每簇取最靠近质心的 5 句，**问一次本地 4B**："这 14 个段里最贴哪个，都不像就说 generic"；
  4 整簇打上该段标签，产出 h → seg2 的对照表；train_build 优先用 seg2。

产出：cph4/fleet/social/corpus/human/SEG2.jsonl（只写判过的；置信不足的不写，回 generic）

用法：
  .venv-housing/bin/python Tools/fleet/corpus_classify.py --k 48
  .venv-housing/bin/python Tools/fleet/corpus_classify.py --dry --k 8 --limit 3000   # 小样试跑
  python3 Tools/fleet/corpus_classify.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
BAKED = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
OUT = os.path.join(SOCIAL, "corpus", "human", "SEG2.jsonl")
REPORT = os.path.join(SOCIAL, "corpus", "human", "SEG2-report.json")
OLLAMA = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
EMB_MODEL = "qwen3-embedding:0.6b"
sys.path.insert(0, HERE)


def embed(texts, batch=64, timeout=180):
    """批量嵌入。ollama 的 /api/embed 支持一次多条，比自己循环快一个数量级。

    2026-11-21 实锚：batch=256 直接 HTTP 400（请求体太大/超 token 上限），
    超长文本也会 400。所以先截断到 200 字，并在 400 时自动减半重试。
    """
    texts = [(t or "")[:200] for t in texts]
    out = []
    i = 0
    while i < len(texts):
        chunk = texts[i:i + batch]
        body = json.dumps({"model": EMB_MODEL, "input": chunk}).encode()
        req = urllib.request.Request(OLLAMA + "/api/embed", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 400 and batch > 1:
                batch = max(1, batch // 2)      # 减半重试，别整批丢
                continue
            raise
        e2 = d.get("embeddings") or []
        if len(e2) != len(chunk):
            raise RuntimeError("嵌入条数不符：%d vs %d" % (len(e2), len(chunk)))
        out.extend(e2)
        i += len(chunk)
    return np.asarray(out, dtype=np.float32)


def kmeans(X, k=48, iters=25, seed=20261121):
    """朴素 k-means（k-means++ 初始化）。numpy 足够，不引 sklearn。"""
    rng = np.random.default_rng(seed)
    n = len(X)
    k = min(k, n)
    # k-means++：先随机一个，再按距离平方采样
    idx = [int(rng.integers(n))]
    d2 = ((X - X[idx[0]]) ** 2).sum(1)
    for _ in range(1, k):
        p = d2 / d2.sum() if d2.sum() > 0 else None
        j = int(rng.choice(n, p=p)) if p is not None else int(rng.integers(n))
        idx.append(j)
        d2 = np.minimum(d2, ((X - X[j]) ** 2).sum(1))
    C = X[idx].copy()
    labels = np.zeros(n, dtype=np.int32)
    for it in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(2) if False else \
            (X ** 2).sum(1)[:, None] - 2 * X @ C.T + (C ** 2).sum(1)[None, :]
        new = d.argmin(1).astype(np.int32)
        if it and np.array_equal(new, labels):
            break
        labels = new
        for c in range(k):
            m = labels == c
            if m.any():
                C[c] = X[m].mean(0)
    return labels, C


def pick_seg(raw, segs):
    """把模型输出收敛成闭集里的段名。宁可变 generic，也不许凭空造段。"""
    t = (raw or "").strip()
    if not t:
        return "generic"
    first = t.split()[0].strip("，。,.、:：\n\t\"'「」")
    if first in segs or first == "generic":
        return first
    for s in segs + ["generic"]:
        if s in t:
            return s
    return "generic"


def ask_seg(samples, segs, timeout=90):
    """问本地 4B：这一簇属于哪一段。只接受闭集里的答案，否则回 generic。"""
    import llm_client as lc
    txt = "\n".join("- " + s[:60] for s in samples[:5])
    p = ("下面是 B 站评论样本：\n%s\n\n从这些人群段里选一个最贴的：%s。\n"
         "只回段名本身，不要解释；都不像就回 generic。"
         % (txt, "、".join(segs)))
    r = lc.generate(p, endpoint=OLLAMA, timeout=timeout, think=False, num_predict=16)
    if not isinstance(r, dict) or not r.get("ok"):
        return "generic", (r or {}).get("why", "")[:60]
    raw = r.get("text") or ""
    return pick_seg(raw, segs), raw.strip()[:40]


def run(k=48, limit=0, dry=False, batch=64, cache=None):
    import segments as sg
    spec = sg.load_spec()
    segs = [s["id"] for s in spec["segments"]]
    rows = []
    for line in open(BAKED, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if (r.get("seg") or "generic") != "generic":
            continue
        if r.get("dup_of"):
            continue
        rows.append(r)
    if limit:
        rows = rows[:limit]
    if not rows:
        return {"error": "没有 generic 行"}

    t0 = time.time()
    texts = [r.get("text") or "" for r in rows]
    # 嵌入很贵（44k 行约 28 分钟），而命名很便宜（几十次小模型调用），
    # 所以缓存向量：训练占着 GPU 时只做嵌入，等空出来再聚类命名。
    X = None
    if cache and os.path.exists(cache):
        try:
            z = np.load(cache, allow_pickle=False)
            if int(z["n"]) == len(texts):
                X = z["X"]
        except Exception:
            X = None
    if X is None:
        # 嵌入是 GPU 活：与训练/自举互斥（拿不到就不抢，用缓存或下次再说）
        try:
            import gpu_lease as _gl
            _got, _why = _gl.acquire("embed", ttl_s=2 * 3600)
        except Exception:
            _got, _why = True, ""
        if not _got:
            return {"skipped": _why}
        try:
            X = embed(texts, batch=batch)
        finally:
            try:
                _gl.release("embed")
            except Exception:
                pass
        if cache:
            np.savez(cache, X=X, n=len(texts))
    X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)   # 归一化，距离=余弦
    emb_s = time.time() - t0

    t1 = time.time()
    labels, C = kmeans(X, k=k)
    km_s = time.time() - t1

    t2 = time.time()
    assigns = {}
    rng = np.random.default_rng(20261121)
    for c in range(len(C)):
        idx = np.where(labels == c)[0]
        if len(idx) < 20:          # 太小的簇不判（噪声）
            continue
        d = ((X[idx] - C[c]) ** 2).sum(1)
        near = idx[np.argsort(d)[:5]]
        # 第二问用"随机 5 条"，跟最近 5 条分开问：两个答案不一致说明这一簇是混杂的，
        # 宁可留 generic 也不要打错标签（2026-11-21 抽查：只问一次时"现在不都这种吗"
        # 被判成 beginner，"显卡贵就贵吧"被判成 tech_nerd 还算对，混杂簇必须拦掉）。
        rand5 = idx[rng.choice(len(idx), size=min(5, len(idx)), replace=False)]
        s1 = [texts[i] for i in near]
        s2 = [texts[i] for i in rand5]
        seg1, raw1 = ask_seg(s1, segs)
        seg2_, raw2 = ask_seg(s2, segs)
        agree = (seg1 == seg2_)
        assigns[c] = {"seg": seg1 if agree else "generic", "raw": "%s|%s" % (raw1[:14], raw2[:14]),
                      "agree": agree, "n": int(len(idx)), "samples": s1}
    ask_s = time.time() - t2

    moved = 0
    out_rows = []
    for i, r in enumerate(rows):
        c = int(labels[i])
        a = assigns.get(c)
        if not a or a["seg"] == "generic":
            continue
        out_rows.append({"h": r.get("h") or (r.get("text") or "")[:40],
                         "seg2": a["seg"], "cluster": c,
                         "text": (r.get("text") or "")[:60]})
        moved += 1

    if not dry and out_rows:
        with open(OUT, "w", encoding="utf-8") as f:
            for r in out_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    rep = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "generic_rows": len(rows),
           "k": k, "clusters_asked": len(assigns), "moved": moved,
           "moved_ratio": round(moved / max(1, len(rows)), 3),
           "emb_sec": round(emb_s, 1), "kmeans_sec": round(km_s, 1), "ask_sec": round(ask_s, 1),
           "total_sec": round(time.time() - t0, 1),
           "assign": {str(c): {"seg": v["seg"], "n": v["n"], "raw": v["raw"], "agree": v.get("agree"),
                               "samples": v["samples"][:3]} for c, v in assigns.items()},
           "seg_counts": dict(Counter(v["seg"] for v in assigns.values()).most_common())}
    if not dry:
        json.dump(rep, open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return rep


def self_test():
    """负控：k-means 必须把两组明显分开的点分到不同簇；ask_seg 只接受闭集答案。"""
    X = np.vstack([np.tile([1.0, 0.0], (20, 1)), np.tile([0.0, 1.0], (20, 1))])
    X = X / np.linalg.norm(X, axis=1, keepdims=True)
    lab, _ = kmeans(X, k=2, iters=10)
    ok_km = bool(len(set(lab[:20].tolist())) == 1 and len(set(lab[20:].tolist())) == 1
                 and lab[0] != lab[-1])
    # 闭集：模型胡说一句"我也不知道"必须落 generic；说对段名必须原样保留
    segs = ["beginner", "memer", "shallow"]
    ok_close = (pick_seg("我也不知道该分哪个", segs) == "generic"
                and pick_seg("memer", segs) == "memer"
                and pick_seg("memer。", segs) == "memer")
    ok = ok_km and ok_close
    print(json.dumps({"self_test": "PASS" if ok else "FAIL",
                      "kmeans分开两组": ok_km, "闭集落generic": ok_close}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=48)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--cache", default=os.path.join(SOCIAL, "corpus", "human", "EMB-cache.npz"),
                    help="嵌入向量缓存（44k 行约 28 分钟，缓存在磁盘上可以分两次跑）")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    r = run(a.k, a.limit, a.dry, a.batch, a.cache or None)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:2500])
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""judge_bench.py - 同题对比两个本地判读模型，只看三件事：准、不编、够快。

Why (CEO 2026-11-02 「这台机器主要就是赋能 AI，轻度办公」): 本机的价值就是把本地模型的
判断力榨到最大。换模型不能凭感觉，要用同一批真题跑出可比较的数：

  1) 可执行性 - 答案是否给出「动作｜理由」这种能直接派工的形式；
  2) 不编造   - 答案里引用的路径/文件名，是否真的在盘上存在（幻觉率）；
  3) 速度     - 端到端秒数与每 token 时间（判读席要在脉冲周期内出结果）。

用法:
  python3 Tools/fleet/judge_bench.py --models qwen3.5:4b,qwen3:8b --n 4
输出: cph4/fleet/queue-receipts/judge-bench-<date>.json + 一屏表格
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OLLAMA = "http://127.0.0.1:11434/api/generate"
JQ = os.path.join(ROOT, "cph4", "fleet", "dispatcher", "JUDGMENT-QUEUE.jsonl")
OUT_DIR = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")

PROMPT = """你是机队主控的判断席。只依据给定证据回答，严禁编造不存在的文件名/路径/命令。
证据不足就只回「需要人工裁决」。
问题：%s
证据：%s
用不超过 60 字给出下一步动作，格式：动作｜理由。"""

PATH_RE = re.compile(r"[A-Za-z0-9_./-]+\.(?:md|json|py|txt|mp4)")


def ask(model, prompt, timeout=180):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "think": False, "options": {"num_ctx": 8192}}).encode()
    t0 = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(
                OLLAMA, data=body, headers={"Content-Type": "application/json"}),
                timeout=timeout) as r:
            d = json.load(r)
    except Exception as e:
        return {"error": str(e)[:120], "sec": round(time.time() - t0, 1)}
    sec = round(time.time() - t0, 1)
    text = (d.get("response") or "").strip()
    ev = int(d.get("eval_count") or 0)
    ev_dur = (d.get("eval_duration") or 0) / 1e9
    return {"text": text, "sec": sec,
            "tok_s": round(ev / ev_dur, 1) if ev_dur > 0 else None}


def hallu(text):
    """引用了盘上不存在的路径即算一条幻觉。"""
    cited = set(PATH_RE.findall(text or ""))
    bad = [c for c in cited
           if not (os.path.exists(os.path.join(ROOT, c)) or os.path.exists(c))]
    return len(cited), bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="qwen3.5:4b,qwen3:8b")
    ap.add_argument("--n", type=int, default=4)
    a = ap.parse_args()
    models = [m.strip() for m in a.models.split(",") if m.strip()]

    qs = []
    try:
        with open(JQ, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    r = json.loads(ln)
                    if r.get("question"):
                        qs.append((r["question"], json.dumps(r.get("evidence") or {},
                                                             ensure_ascii=False)[:600]))
    except Exception:
        pass
    if not qs:
        qs = [("某条线 30 小时没有产出，下一步该做什么？", "{}")]
    qs = qs[:a.n]

    res = {}
    for m in models:
        rows = []
        for q, ev in qs:
            r = ask(m, PROMPT % (q, ev))
            if "error" not in r:
                n, bad = hallu(r["text"])
                r["cited"], r["hallucinated"] = n, bad
                r["actionable"] = bool(re.search(r"｜|\|", r["text"]))
                r["punted"] = "需要人工" in r["text"]
            rows.append(r)
        ok = [x for x in rows if "error" not in x]
        res[m] = {
            "n": len(rows),
            "actionable": sum(1 for x in ok if x.get("actionable")),
            "punted": sum(1 for x in ok if x.get("punted")),
            "hallucinated_citations": sum(len(x.get("hallucinated") or []) for x in ok),
            "avg_sec": round(sum(x["sec"] for x in ok) / len(ok), 1) if ok else None,
            "avg_tok_s": (round(sum(x["tok_s"] or 0 for x in ok) / len(ok), 1) if ok else None),
            "errors": [x["error"] for x in rows if "error" in x],
        }

    payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "questions": a.n, "result": res}
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "judge-bench-%s.json" % time.strftime("%Y%m%d"))
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print("%-16s %8s %8s %8s %10s %8s" % ("model", "可执行", "判不了", "编造引证", "端到端秒", "tok/s"))
    for m, v in res.items():
        print("%-16s %8s %8s %8s %10s %8s" % (m, v["actionable"], v["punted"],
                                              v["hallucinated_citations"], v["avg_sec"], v["avg_tok_s"]))
    print("saved ->", os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
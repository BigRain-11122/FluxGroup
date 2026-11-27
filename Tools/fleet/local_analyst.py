#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_analyst.py - 每小时一次「机队研判」：用闲置的 8B，跑完即卸。

为什么（2026-11-09 CEO「本地算力应用到极致」）：
  8B 单槽（11436，32k）平时只等 DSH 会话，空着浪费。它比 4B 强在归纳，
  正好做"读一堆回执结论 + 巡视旗 + 队列状态，给 5 行研判"这种综合活。
  但 8B 占 7.7GB，不能常驻——所以：跑前只在车道空闲时加载，跑完立刻 keep_alive=0。

用法：python3 Tools/fleet/local_analyst.py [--dry]
"""
import argparse
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
OUT_MD = os.path.join(F, "LOCAL-ANALYST.md")
OUT_JSON = os.path.join(STATE, "local-analyst.json")
LANE = os.environ.get("AGENT_LANE", "http://127.0.0.1:11436")
MODEL = os.environ.get("ANALYST_MODEL", "qwen3.5:4b-mlx")
DIGEST = os.path.join(F, "state", "local-digest.jsonl")
PATROL = os.path.join(STATE, "patrol-local.json")


def post(path, payload, timeout=600):
    req = urllib.request.Request(LANE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def lane_busy():
    try:
        d = json.loads(urllib.request.urlopen(LANE + "/api/ps", timeout=5).read())
        return bool(d.get("models"))
    except Exception:
        return None


def gather():
    lines = []
    try:
        recs = [json.loads(l) for l in open(DIGEST, encoding="utf-8")][-25:]
        lines.append("最近回执判读：")
        for r in recs:
            lines.append("- %s: %s" % (r.get("file"), (r.get("summary") or "")[:60]))
    except OSError:
        pass
    try:
        p = json.load(open(PATROL, encoding="utf-8"))
        reds = [s["domain"] for s in p.get("seats", []) if (s.get("result") or {}).get("verdict") == "RED"]
        lines.append("巡视 RED：%s" % (", ".join(reds) or "无"))
    except Exception:
        pass
    try:
        rows = [json.loads(l) for l in open(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), encoding="utf-8") if l.strip()]
        c = {}
        for r in rows:
            c[r.get("state")] = c.get(r.get("state"), 0) + 1
        lines.append("队列：%s" % json.dumps(c, ensure_ascii=False))
    except OSError:
        pass
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    busy = lane_busy()
    if busy:
        print("lane busy (DSH session?) - skip this hour")
        return 0
    ctx = gather()
    prompt = ("你是集团机队研判席。只依据下面材料，用 5 行中文给出：\n"
              "1 最该先做的三件事 2 最大风险 3 一条给 CEO 的建议。不要客套，不要编造。\n\n" + ctx[:4000])
    t0 = time.time()
    try:
        d = post("/api/chat", {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                               "think": False, "stream": False, "keep_alive": "2m",
                               "options": {"num_ctx": 8192, "num_predict": 300, "temperature": 0.2}})
    except Exception as e:
        print("analyst failed: %s" % str(e)[:120])
        return 1
    txt = ((d.get("message") or {}).get("content") or "").strip()
    wall = round(time.time() - t0, 1)
    if a.dry:
        print(txt)
        return 0
    ts = time.strftime("%Y-%m-%d %H:%M")
    with open(OUT_MD, "a", encoding="utf-8") as f:
        f.write("\n## %s（8B·%.1fs）\n\n%s\n" % (ts, wall, txt))
    json.dump({"ts": ts, "sec": wall, "text": txt},
              open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 跑完即卸，释放 7.7GB
    try:
        post("/api/generate", {"model": MODEL, "keep_alive": 0})
    except Exception:
        pass
    print("analyst ok %.1fs" % wall)
    return 0


if __name__ == "__main__":
    sys.exit(main())

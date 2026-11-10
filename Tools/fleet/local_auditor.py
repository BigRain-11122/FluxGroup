#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_auditor.py - 本地模型做"验收初审"：交付物是否满足验收条款（只出意见，不改状态）。

2026-11-10 全局判断：监控/派活/验收的**决定权必须在确定性脚本**（可复现、可审计）；
本地模型只做三件它擅长的事：读懂交付物、挑可疑、给理由。所以本件：
  - 只读：不写队列、不改卡状态；
  - 只输出 PASS / SUSPECT / FAIL + 一句理由 + 证据指针；
  - SUSPECT/FAIL 汇总进 state/local-audit.jsonl，供主控/日报引用，最终裁决仍走 verify_done/人工。

用法：
  python3 Tools/fleet/local_auditor.py --limit 8
  python3 Tools/fleet/local_auditor.py --report
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
LOG = os.path.join(STATE, "local-audit.jsonl")
OLLAMA = os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434"
MODEL = os.environ.get("AUDIT_MODEL") or "qwen3.5:4b-mlx"


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        pass
    return out


def seen():
    return {(r.get("id"), r.get("at")) for r in rows(LOG)}


def ask(prompt):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "think": False, "stream": False, "keep_alive": "5m",
            "options": {"num_ctx": 8192, "num_predict": 60, "temperature": 0}}
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return ((json.loads(r.read()).get("message") or {}).get("content") or "").strip()


def verdict(text):
    t = text.upper()
    for v in ("FAIL", "SUSPECT", "PASS"):
        if v in t:
            return v
    return "SUSPECT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    if a.report:
        recs = rows(LOG)
        from collections import Counter
        print("audited", len(recs), dict(Counter(r.get("verdict") for r in recs)))
        for r in [x for x in recs if x.get("verdict") != "PASS"][-8:]:
            print(r.get("verdict"), r.get("id"), "|", (r.get("why") or "")[:80])
        return 0

    def _local_first(r):
        d = str(r.get("deliverable") or "")
        import re as _re
        remote = bool(_re.match(r"^[A-Za-z]:[\\/]", d)) or "\\" in d
        return 1 if remote else 0

    done = seen()
    todo = [r for r in rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
            if r.get("state") in ("DONE", "UNVERIFIED")
            and (r.get("id"), r.get("finished_at")) not in done]
    todo.sort(key=_local_first)
    todo = todo[:a.limit]
    if not todo:
        print("no new completed cards")
        return 0

    out = []
    for r in todo:
        deliv = r.get("deliverable") or ""
        path = deliv if os.path.isabs(deliv) else os.path.join(ROOT, deliv)
        at = r.get("finished_at") or ""
        if deliv and not os.path.exists(path):
            import re as _re
            remote = bool(_re.match(r"^[A-Za-z]:[\\/]", deliv)) or "\\" in deliv
            out.append({"id": r.get("id"), "at": at,
                        "verdict": "REMOTE" if remote else "MISSING",
                        "why": ("远端交付物，主控不可见：%s" if remote else "deliverable not found: %s") % deliv,
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
            continue
        body = ""
        try:
            if deliv and os.path.isfile(path):
                body = open(path, encoding="utf-8", errors="replace").read()[:3500]
        except OSError:
            pass
        accept = str(r.get("accept") or "")[:500]
        if not accept and not body:
            continue
        prompt = ("你是验收初审。只依据下面材料判断：交付物是否满足验收条款。\n"
                  "如果满足，第一行写 PASS；明显不满足写 FAIL；信息不足或可疑写 SUSPECT。"
                  "第二行用一句中文说理由（40字内），不要客套。\n\n"
                  "验收条款：%s\n\n交付物片段：\n%s" % (accept or "(未写验收条款)", body or "(交付物为空)"))
        try:
            ans = ask(prompt)
        except Exception as e:
            ans = "SUSPECT 本地模型不可用：%s" % str(e)[:40]
        out.append({"id": r.get("id"), "at": at, "verdict": verdict(ans),
                    "why": ans.replace("\n", " ")[:160],
                    "deliverable": deliv, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})

    os.makedirs(STATE, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("audited %d: %s" % (len(out), [r["verdict"] for r in out]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deep_reason.py - 离线深度推理车道：夜里用 DeepSeek 蒸馏版慢慢想，不接工具。

2026-11-10 CEO 同意：DeepSeek 开源蒸馏版不做 agent（工具调用弱、预填慢），
只做夜间离线深度分析；白天算力留给 4B agent 与机队。

用法：
  python3 Tools/fleet/deep_reason.py --limit 1            # 只在 00:30-07:00 跑
  python3 Tools/fleet/deep_reason.py --force --limit 1    # 手动跑
"""
import argparse
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
BASE = os.environ.get("DEEP_BASE", "http://127.0.0.1:11436")
MODEL = os.environ.get("DEEP_MODEL", "deepseek-r1:14b")
sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))
import fleet_lane as fl


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


def in_window(now=None):
    h = (now or time.localtime()).tm_hour
    return h >= 0 and h < 7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if not a.force and not in_window():
        print("outside offline window (00:30-07:00); use --force")
        return 0
    todo = [r for r in rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
            if r.get("state") == "OPEN" and (r.get("model") or "") == "deep-reason"][:a.limit]
    if not todo:
        print("no deep-reason card")
        return 0
    for r in todo:
        body = {"model": MODEL, "messages": [{"role": "user", "content": r.get("prompt") or ""}],
                "think": True, "stream": False, "keep_alive": "10m",
                "options": {"num_ctx": int(r.get("num_ctx") or 16384), "num_predict": 2048,
                            "temperature": 0.3}}
        req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=1800) as resp:
                d = json.loads(resp.read())
            m = d.get("message") or {}
            text = (m.get("content") or "").strip()
            if not text:
                text = "*（模型只输出了推理过程，未给结论；thinking 长度 %d）*" % len(m.get("thinking") or "")
            out = r.get("deliverable") or ""
            if out:
                p = out if os.path.isabs(out) else os.path.join(ROOT, out)
                os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
                open(p, "w", encoding="utf-8").write(text)
            r["state"] = "DONE" if out and os.path.exists(os.path.join(ROOT, out)) else "UNVERIFIED"
            r["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            r["note"] = "deep-reason %s %.0fs" % (MODEL, time.time() - t0)
        except Exception as e:
            r["state"] = "FAILED"
            r["note"] = "deep-reason error: %s" % str(e)[:100]
        fl.merge_jsonl(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), [r], mirror=False)
        print(r["id"], r["state"], "%.0fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())

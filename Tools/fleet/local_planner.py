#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_planner.py - 每天早上的"作战计划"：本地模型读盘上事实，给 5 件最该做的事。

2026-11-10：丰富智能体职责——不只是执行，还要会排优先级。
只读、只建议；派单仍由 master_agent 决定。
"""
import json, os, time, urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet"); S = os.path.join(F, "state")
OUT = os.path.join(F, "PLAN-TODAY.md")
MODEL = os.environ.get("PLAN_MODEL") or "qwen3.5:4b-mlx"


def j(p, d=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return d or {}


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try: out.append(json.loads(line))
                except Exception: pass
    except OSError: pass
    return out


def ask(prompt):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "think": False, "stream": False, "keep_alive": "10m",
            "options": {"num_ctx": 8192, "num_predict": 400, "temperature": 0.3}}
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return ((json.loads(r.read()).get("message") or {}).get("content") or "").strip()


def main():
    q = rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    st = Counter(r.get("state") for r in q)
    cap = j(os.path.join(S, "capabilities.json"))
    board = j(os.path.join(S, "output-board.json"))
    sw = j(os.path.join(S, "selfwatch.json"))
    blocked = [r for r in q if r.get("state") == "BLOCKED"][:5]
    today = time.strftime("%Y-%m-%d")
    done_today = [r for r in q if str(r.get("finished_at") or "")[:10] == today]
    ctx = ("队列：%s\n今日完成：%d\n产出：产品 %s / 内部 %s / 缺失 %s\n在线：%s\n阻塞：%s\n自愈：%s"
           % (json.dumps(dict(st), ensure_ascii=False), len(done_today),
              board.get("product"), board.get("infra"), board.get("missing"),
              ",".join(n for n, e in cap.items() if isinstance(e, dict) and e.get("online")),
              [r.get("id") for r in blocked], sw.get("stale")))
    txt = ask("你是机队作战参谋。只依据下面事实，给出今天最该做的 5 件事。\n"
              "每条一行，格式：动作｜理由｜建议执行者（bm-a/bm-b/bm-c/bm-m）。\n"
              "优先产品产出与解除阻塞，不要客套，不要编造。\n\n" + ctx)
    open(OUT, "w", encoding="utf-8").write("# 今日计划 %s\n\n%s\n\n---\n\n事实来源：队列/能力台账/产出看板/自愈\n" % (today, txt))
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "text": txt, "facts": ctx},
              open(os.path.join(S, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("plan written:", OUT)
    print(txt[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

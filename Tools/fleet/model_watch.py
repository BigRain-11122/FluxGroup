#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_watch.py - 新模型到货就自动测：工具调用 / 预填 / 摘要，结果入账。

2026-11-10 CEO：本地模型要真正调好、持续可用。
本件每 30 分钟扫一次本地模型，没测过的跑三项基准，写 state/model-bench.json，
并在有模型明显优于当前主模型时给出"建议切换"（不自动改会话配置，避免打断在用会话）。
"""
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
OUT = os.path.join(STATE, "model-bench.json")
BASE = "http://127.0.0.1:11434"
TOOLS = [{"type": "function", "function": {"name": "read_file", "description": "read",
          "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                         "required": ["path"]}}}]
PRIMARY = "qwen3.5:4b-mlx"


def tags():
    try:
        d = json.loads(urllib.request.urlopen(BASE + "/api/tags", timeout=5).read())
        return [m["name"] for m in d.get("models") or []]
    except Exception:
        return []


def chat(model, messages, tools=None, think=False, num_predict=64, timeout=180, ctx=16384):
    body = {"model": model, "messages": messages, "think": think, "stream": False,
            "keep_alive": "5m", "options": {"num_ctx": ctx, "num_predict": num_predict}}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    return d, round(time.time() - t, 1)


def bench(model):
    r = {"model": model, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    try:
        d, sec = chat(model, [{"role": "user", "content": "读 /tmp/x"}], tools=TOOLS)
        m = d.get("message") or {}
        r["tool_calls"] = bool(m.get("tool_calls"))
        r["tool_sec"] = sec
    except Exception as e:
        r["tool_calls"] = False
        r["tool_err"] = str(e)[:80]
    try:
        big = "规则与事实。" * 800
        d, sec = chat(model, [{"role": "system", "content": big},
                              {"role": "user", "content": "回复OK"}], num_predict=8, timeout=300)
        r["prefill_sec"] = sec
        r["context_tokens"] = d.get("prompt_eval_count")
    except Exception as e:
        r["prefill_sec"] = None
        r["prefill_err"] = str(e)[:80]
    try:
        d, sec = chat(model, [{"role": "user", "content":
                               "用3条中文要点总结：机队完成12张卡，bm-c缺目录失败3次，发布包已生成。"}],
                      num_predict=160, timeout=300)
        text = ((d.get("message") or {}).get("content") or "").strip()
        r["summary_len"] = len(text)
        r["summary_sec"] = sec
    except Exception as e:
        r["summary_len"] = 0
        r["summary_err"] = str(e)[:80]
    r["verdict"] = "USABLE" if (r.get("tool_calls") and (r.get("summary_len") or 0) > 10) else "NOT-FOR-AGENT"
    return r


def main():
    os.makedirs(STATE, exist_ok=True)
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        old = {"models": {}}
    models = old.setdefault("models", {})
    names = [n for n in tags() if "embedding" not in n]
    for n in names:
        if n not in models:
            models[n] = bench(n)
            print("benched", n, models[n].get("verdict"))
    usable = [m for m, v in models.items() if v.get("verdict") == "USABLE"]
    fastest = min(usable, key=lambda m: models[m].get("tool_sec") or 99) if usable else None
    old["primary"] = PRIMARY
    old["usable"] = usable
    old["suggestion"] = fastest if fastest and fastest != PRIMARY else None
    old["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(old, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("usable", usable, "suggestion", old["suggestion"])
    return 0


if __name__ == "__main__":
    main()

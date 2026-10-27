#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""l1-client.py - minimal OpenAI-compatible client for the local 35B lane (bm-a :8090).

Phase 1-alpha L1 wiring (BLUEPRINT v2 G3): makes cheap local capacity consumable by any
window/batch, and logs every call into the SLI-4 counter ledger
(media/logs/l1-consumption-ledger.jsonl).

Usage:
  python Tools/l1-client.py --task <name> --prompt "<text>"
  python Tools/l1-client.py --task <name> --prompt-file <path> [--out <path>]
  python Tools/l1-client.py --task pool-triage --pool-file cph4/fleet/dispatcher/POOL.json [--out <path>]
Env: L1_ENDPOINT (default http://127.0.0.1:8090)
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = os.environ.get("L1_ENDPOINT", "http://127.0.0.1:8090")
LEDGER = os.path.join(ROOT, "media", "logs", "l1-consumption-ledger.jsonl")


def build_pool_prompt(path):
    with open(path, encoding="utf-8") as f:
        cards = json.load(f)
    lines = [
        "你是集团调度池的本地分类助手（L1 小脑）。对下面每张 open 任务卡输出一行，格式："
        "卡ID | 车道 | 优先级合理性（一句话：合理/建议升降级+理由）| 一句话执行要点。"
        "最后输出一行总结：各车道负载与补卡建议。不要客套与重复卡面文字。",
    ]
    n = 0
    for c in cards:
        if c.get("status") != "open":
            continue
        n += 1
        lines.append("- {id} | {prio} | lane={lane} | {title} | spec={spec}".format(
            id=c.get("id", "?"), prio=c.get("priority", "?"),
            lane=c.get("lane", "?"), title=c.get("title", "?"),
            spec=c.get("spec", "?")))
    lines.append("(共 %d 张 open 卡)" % n)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--pool-file")
    ap.add_argument("--out")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--temperature", type=float, default=0.3)
    a = ap.parse_args()

    if a.pool_file:
        prompt = build_pool_prompt(a.pool_file)
    elif a.prompt_file:
        with open(a.prompt_file, encoding="utf-8") as f:
            prompt = f.read()
    elif a.prompt:
        prompt = a.prompt
    else:
        print("need one of --prompt/--prompt-file/--pool-file", file=sys.stderr)
        sys.exit(2)

    body = {
        "model": "qwen3.6-35b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": a.max_tokens,
        "temperature": a.temperature,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        ENDPOINT + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read().decode("utf-8"))
    content = resp["choices"][0]["message"]["content"]
    usage = resp.get("usage", {}) or {}
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    line = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "task": a.task,
            "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens")}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

    if a.out:
        head = ("# L1 %s（SLI-4 计数器数据点）\n\n> 产出=本地 35B %s 经 Tools/l1-client.py（零云端 token·"
                "用量已入 media/logs/l1-consumption-ledger.jsonl）\n\n```\n" % (a.task, a.task))
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(head + content + "\n```\n")
        print("WROTE %s (tokens: prompt=%s completion=%s)" %
              (a.out, line["prompt_tokens"], line["completion_tokens"]))
    else:
        print(content)
    print("LEDGER-APPENDED: " + json.dumps(line, ensure_ascii=False))


if __name__ == "__main__":
    main()

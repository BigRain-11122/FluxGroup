# -*- coding: utf-8 -*-
"""local_judge.py - answer the smart-tier judgment queue with bm-m's local model.

CEO 2026-10-30: 云端额度要用完了 -- the cloud-smart seat is closed until he reopens it.
Every OPEN judgment gets answered locally instead (default qwen3:4b-instruct, no-think,
short lease; 2026-10-30 bench: 4B 8k=3.3GB/41.6 tok/s vs 35B-A3B 22.0GB/29-40 tok/s with
14-21s cold load, so the control plane judges with 4B and leaves 35B to on-demand use).
The answer carries model="local:<model>" so the audit trail shows exactly which
brain said it. D-20261030-01 lesson baked in: the prompt FORBIDS inventing tools/paths;
the judge may only cite evidence given to it, and must say "需要人工" when unsure.
"""
import json
from concurrent.futures import ThreadPoolExecutor
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_lane as fl

MAX_PER_CYCLE = 4   # 4B ~3.5s/judgment on the real queue -> fits the 60s tick with margin

JUDGE_MODEL = (fl.LANES.get("bm-m", {}).get("llm") or {}).get("model") or "qwen3:4b-instruct"

PROMPT = """你是机队主控的本地判断席（只依据给定证据回答，严禁编造不存在的工具、命令或路径；证据不足就回答"需要人工裁决+原因"）。
问题：{question}
背景证据：{evidence}
业务约束：算力分层=本地优先，云端已停用；公司生产力机 09-19 点让位 CEO 办公；主控机只做调度与文本。
请用不超过 80 字给出下一步动作（谁、做什么），格式："动作｜理由"。"""


def main():
    root = fl.ROOT_DEFAULT
    path = os.path.join(root, fl.JUDGMENT_REL.replace("/", os.sep))
    rows = fl.read_jsonl(path)
    todo = [r for r in rows if r.get("state") == "OPEN"][:MAX_PER_CYCLE]
    # Parallel on purpose: 2026-10-31 measured 3 concurrent 4B calls at ~41 tok/s each with
    # no extra memory, so serialising judgments burns wall-clock for nothing.
    with ThreadPoolExecutor(max_workers=MAX_PER_CYCLE) as ex:
        answers = list(ex.map(lambda r: fl.local_llm(
            PROMPT.format(question=r.get("question", ""),
                          evidence=json.dumps(r.get("evidence") or {}, ensure_ascii=False)[:1200]),
            node="bm-m", timeout=90), todo))
    n = 0
    for r, ans in zip(todo, answers):
        if not ans or not str(ans).strip():
            r["note"] = "local-judge failed this round (ollama down?)"
            continue
        r["state"] = "ANSWERED"
        r["answer"] = str(ans).strip()[:500]
        r["model"] = "local:" + JUDGE_MODEL
        r["answered_at"] = fl.now_iso()
        n += 1
    if n:
        fl.write_jsonl(path, rows)
    open_count = sum(1 for r in rows if r.get("state") == "OPEN")
    print("[local_judge] answered=%d still_open=%d (tier: local→shared→codely)" % (n, open_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""local_judge.py - answer the smart-tier judgment queue with bm-m's local 35B.

CEO 2026-10-30: 云端额度要用完了 -- the cloud-smart seat is closed until he reopens it.
Every OPEN judgment gets answered locally instead (qwen3.5:35b-a3b, no-think, resident).
The answer carries model="local:qwen3.5:35b-a3b" so the audit trail shows exactly which
brain said it. D-20261030-01 lesson baked in: the prompt FORBIDS inventing tools/paths;
the judge may only cite evidence given to it, and must say "需要人工" when unsure.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_lane as fl

MAX_PER_CYCLE = 3   # 35B ~30s/judgment -> fits inside the 60s tick with margin

PROMPT = """你是机队主控的本地判断席（只依据给定证据回答，严禁编造不存在的工具、命令或路径；证据不足就回答"需要人工裁决+原因"）。
问题：{question}
背景证据：{evidence}
业务约束：算力分层=本地优先，云端已停用；公司生产力机 09-19 点让位 CEO 办公；主控机只做调度与文本。
请用不超过 80 字给出下一步动作（谁、做什么），格式："动作｜理由"。"""


def main():
    root = fl.ROOT_DEFAULT
    path = os.path.join(root, fl.JUDGMENT_REL.replace("/", os.sep))
    rows = fl.read_jsonl(path)
    n = 0
    for r in rows:
        if r.get("state") != "OPEN" or n >= MAX_PER_CYCLE:
            continue
        ans = fl.local_llm(
            PROMPT.format(question=r.get("question", ""),
                          evidence=json.dumps(r.get("evidence") or {}, ensure_ascii=False)[:1200]),
            node="bm-m", timeout=40)
        if not ans or not str(ans).strip():
            r["note"] = "local-judge failed this round (ollama down?)"
            continue
        r["state"] = "ANSWERED"
        r["answer"] = str(ans).strip()[:500]
        r["model"] = "local:qwen3.5:35b-a3b"
        r["answered_at"] = fl.now_iso()
        n += 1
    if n:
        fl.write_jsonl(path, rows)
    open_count = sum(1 for r in rows if r.get("state") == "OPEN")
    print("[local_judge] answered=%d still_open=%d (tier: local→shared→codely)" % (n, open_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())

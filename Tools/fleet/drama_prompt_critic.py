#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_prompt_critic.py — 本地大模型审稿（CPU 模式，与 GPU 烧片并行）。

为什么（2026-11-20）：CEO 2026-11-08 令「表演禁字面化」——叹气/呼吸不许拍脸；10-25 判例
「HIM 名词块末的地板短语 + 动作分词」这类结构病；11-14 判例「双 ID 块 's 粘连」。
这些病在**提示词阶段就能查**，不该等到烧完再看片。

本工具用本机 ollama（num_gpu=0 → 纯 CPU，不抢 GPU）逐镜审稿，输出机器可读的 flags，
再由人复核。**它是初筛不是判决**——4B 会误判，别把它的结论当终审。

用法：
  python Tools/fleet/drama_prompt_critic.py --prompts cph4/fleet/out/drama/EP001/kf_prompts.json \
      --out cph4/fleet/out/drama/EP001/critic.json [--model qwen3.5:4b-q4_K_M] [--limit 0]
Exit: 0 已产出报告；2 输入缺；3 模型不可用
"""
import argparse
import json
import os
import re
import sys
import urllib.request

DEFAULT_HOST = os.environ.get("CRITIC_HOST", "http://127.0.0.1:11434")

RULES = """你是 MV/漫剧提示词审稿员。逐条判断下面这条英文画面提示词是否有以下缺陷，只输出 JSON。

缺陷代码：
L1 表演字面化：写了"叹气/大口呼吸/胸腔起伏/嘴唇微张/张嘴"这类直接拍脸的生理动作
L2 人物双动作：同一张脸同时做两件事（如边笑边哭、边说话边皱眉）
L3 名词块粘连：人物描述后直接跟 's（如 shoes's face）导致归属误读
L4 镜头越权：文字描述里命令了镜头运动（i2v 由运镜字段管，KF 提示词不该写 camera moves）
L5 伪文字风险：描述了招牌/屏幕/书本/碑文上的文字内容（模型会画成乱码）
L6 物理不可能：悬空物体、无源光源、镜像/倒影逻辑错
无缺陷则 output {"flags":[]}。

提示词：
---
%s
---
只输出 JSON，形如 {"flags":[{"code":"L1","why":"不超过20字"}],"score":8}
score 是这条提示词的可烧性 0-10（10=直接可烧）。"""


def llm(prompt, model, host, timeout=240):
    body = json.dumps({
        "model": model, "prompt": prompt, "stream": False, "think": False,
        "options": {"num_predict": 220, "temperature": 0.2, "num_gpu": 0},
    }).encode()
    req = urllib.request.Request(host + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode()).get("response", "")


def parse_json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="qwen3.5:4b-q4_K_M")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)

    if not os.path.isfile(a.prompts):
        print("CRITIC ABORT prompts missing: " + a.prompts)
        return 2
    rows = json.load(open(a.prompts, encoding="utf-8"))
    if a.limit:
        rows = rows[:a.limit]

    try:
        urllib.request.urlopen(a.host + "/api/tags", timeout=8).read()
    except Exception:
        print("CRITIC ABORT model host unreachable: " + a.host)
        return 3

    report, flagged = [], 0
    for i, r in enumerate(rows, 1):
        txt = llm(RULES % (r.get("prompt", "")[:1400]), a.model, a.host)
        obj = parse_json(txt) or {"flags": [], "score": None, "raw": txt[:200]}
        flags = obj.get("flags") or []
        if flags:
            flagged += 1
        report.append({"id": r.get("id"), "score": obj.get("score"), "flags": flags})
        mark = "!" if flags else "."
        print("[%d/%d] %s %s %s" % (i, len(rows), mark, r.get("id"),
                                    ",".join(f.get("code", "?") for f in flags)), flush=True)

    out = {"ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"), "model": a.model,
           "prompts": os.path.basename(a.prompts), "total": len(rows),
           "flagged": flagged, "rows": report}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("CRITIC DONE total=%d flagged=%d -> %s" % (len(rows), flagged, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

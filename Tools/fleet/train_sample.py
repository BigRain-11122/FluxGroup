#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_sample.py — 基座 vs LoRA 同题对拍，人眼判断"学没学到 B站语感"。

为什么不用自动分数：自动指标（ppl/相似度）在"风格像不像真人"这件事上全是自欺——
同一句话换个标点分数就变，但人一眼能看出是不是客服腔。所以这里只负责把两边摆在一起，
判断留给人（出口径化的盲评表在 train/RUNS/<ts>/AB.jsonl，可脱开工具打分）。

用法：
  python3 Tools/fleet/train_sample.py --adapter cph4/fleet/social/train/RUNS/<ts>/adapter
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODEL_DEFAULT = os.path.join(os.path.expanduser("~"), ".fluxgroup", "models", "qwen3.5-4b-4bit")

# 同题：都是"看完这条视频想留一句话"。题目里必须带视频标题——训练样本 100% 带上下文，
# 对拍时不给标题就是拿训练分布外的题去考它，结论会失真。
_TITLE = "原创青春暗恋短片《看不见她》- 用 iPhone 拍摄"
PROMPTS = [
    "视频《%s》。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。" % _TITLE,
    "用 B 站观众的口吻，给《%s》写一句真实评论，不超过 25 字。" % _TITLE,
    "刚看完《%s》，写一句你最想说的话。就像平时在评论区那样。" % _TITLE,
]


def gen(model, tok, prompt, max_tokens, temp, n):
    """mlx_lm 0.32 起 generate() 不再吃 temp/top_p，而是把 **kwargs 直接转给
    generate_step()，后者只认 sampler —— 传 temp 会报
    "generate_step() got an unexpected keyword argument"。采样器要自己造。

    另：Qwen3.5 是思考型模型，默认会先吐 <think>…</think> 思考块，直接生成拿到的是
    推理过程而不是评论。必须用 apply_chat_template(enable_thinking=False) 自己拼 ids，
    否则对拍看到的全是"我正在分析这个请求"。
    """
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler
    sampler = make_sampler(temp=temp)
    msgs = [{"role": "user", "content": prompt}]
    try:
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                      enable_thinking=False)
    except TypeError:
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True)
    outs = []
    for _ in range(n):
        try:
            outs.append(generate(model, tok, prompt=ids, max_tokens=max_tokens,
                                 sampler=sampler, verbose=False).strip())
        except Exception as e:
            outs.append("<生成失败 %s>" % str(e)[:50])
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--n", type=int, default=3, help="同一题生成几条")
    ap.add_argument("--max-tokens", type=int, default=60)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if not os.path.isdir(a.adapter):
        print("[sample] 找不到 adapter：%s" % a.adapter)
        return 2
    from mlx_lm import load

    out_path = a.out or os.path.join(a.adapter, "..", "AB.jsonl")
    rows = []
    print("[sample] 加载基座…", flush=True)
    base, tok = load(a.model)
    for p in PROMPTS:
        rows.append({"side": "base", "prompt": p, "outputs": gen(base, tok, p, a.max_tokens,
                                                                a.temp, a.n)})
    del base
    print("[sample] 加载基座+LoRA…", flush=True)
    tuned, tok2 = load(a.model, adapter_path=a.adapter)
    for p in PROMPTS:
        rows.append({"side": "lora", "prompt": p, "outputs": gen(tuned, tok2, p, a.max_tokens,
                                                                 a.temp, a.n)})

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "adapter": a.adapter,
                            "temp": a.temp, "n": a.n}, ensure_ascii=False) + "\n")
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 屏显：同题上下并排，方便一眼看差别
    print("\n===== 对拍（每题：基座 / LoRA） =====")
    for i, p in enumerate(PROMPTS):
        print("\n[题%d] %s" % (i + 1, p))
        for r in rows:
            if r["prompt"] != p:
                continue
            print("  %-4s | %s" % (r["side"], " / ".join(r["outputs"])))
    print("\n[sample] → %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

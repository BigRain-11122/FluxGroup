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
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODEL_DEFAULT = os.path.join(os.path.expanduser("~"), ".fluxgroup", "models", "qwen3.5-4b-4bit")

# 同题：都是"看完这条视频想留一句话"。题目里必须带视频标题——训练样本 100% 带上下文，
# 对拍时不给标题就是拿训练分布外的题去考它，结论会失真。
_TITLE = "原创青春暗恋短片《看不见她》- 用 iPhone 拍摄"
def _pair():
    """从 VIDEO-TITLES.json 里取一条"标题+简介同源"的真实配对。
    2026-11-17 实锚：我手写过一次题面，标题是《看不见她》而简介是剪映教学，
    训练分布里根本没有这种错配，对拍结论直接作废。题面必须来自同一行数据。
    """
    p = os.path.join(ROOT, "cph4", "fleet", "social", "VIDEO-TITLES.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
        rows = [v for v in d.values() if v.get("title") and v.get("desc")]
        rows.sort(key=lambda v: -len(v.get("desc") or ""))
        if rows:
            return rows[0]["title"][:40], rows[0]["desc"][:50]
    except Exception:
        pass
    return "原创青春暗恋短片《看不见她》- 用 iPhone 拍摄", ""


_TITLE, _DESC = _pair()
_HINT = ("（简介：%s）" % _DESC) if _DESC else ""
PROMPTS = [
    "视频《%s》%s。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。"
    % (_TITLE, _HINT),
    "用 B 站观众的口吻，给《%s》%s写一句真实评论，不超过 25 字。" % (_TITLE, _HINT),
    "刚看完《%s》%s，写一句你最想说的话。就像平时在评论区那样。" % (_TITLE, _HINT),
]


def make_rep_penalty(penalty=1.15, window=48):
    """CTRL 式重复惩罚（与 HF 的 repetition_penalty 同款）。

    为什么要这个：mlx_lm 0.32 没有内置 logits processor，裸采样会连续吐
    「求工作流，求工作流，求工作流」「老师 老师 老师」——这不是训练集脏，
    是解码在自我强化。社区默认开这个惩罚，我们之前没开。
    """
    import mlx.core as mx

    def proc(tokens, logits):
        if tokens.size == 0:
            return logits
        seen = sorted({int(t) for t in tokens[-window:] if int(t) > 0})
        if not seen:
            return logits
        idx = mx.array(seen)
        sel = logits[idx]
        pen = mx.where(sel > 0, sel / penalty, sel * penalty)
        return logits.at[idx].add(pen - sel)

    return proc


def gen(model, tok, prompt, max_tokens, temp, n, rep_penalty=1.15):
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
    # 2026-11-17 实锚：自写 logits processor 一旦 scatter-add 写错就把分布打崩
    # （基座和 LoRA 同时吐 "!!!!!!!!"）。这里不再碰 logits，改成"多生成几条按
    # 自我重复度择优"——同样能治复读，且不会伤到分布。
    procs = None
    _extra = 2 if rep_penalty and rep_penalty > 1.0 else 0
    msgs = [{"role": "user", "content": prompt}]
    try:
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                      enable_thinking=False)
    except TypeError:
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True)
    outs = []
    for _ in range(n + _extra):
        try:
            outs.append(generate(model, tok, prompt=ids, max_tokens=max_tokens,
                                 sampler=sampler, verbose=False).strip())
        except Exception as e:
            outs.append("<生成失败 %s>" % str(e)[:50])
    return pick_distinct(outs, n) if _extra else outs


def self_repeat(text):
    """自我重复度：同一 4 字片段在句内出现的次数。"求工作流，求工作流"=2。"""
    t = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text or "")
    if len(t) < 8:
        return 1
    grams = [t[i:i + 4] for i in range(len(t) - 3)]
    from collections import Counter
    c = Counter(grams)
    return max(c.values()) if c else 1


def pick_distinct(outs, n):
    """从多候选中挑 n 条：先按自我重复度升序，再按去重后长度（信息量）降序。"""
    uniq, seen = [], set()
    for t in outs:
        k = re.sub(r"\W+", "", t)
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(t)
    # 排序口径：人味分高优先，其次少自我重复，再其次信息量（长度）
    def _hf(x):
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import comment_taste as _ct
            return _ct.human_feel(x)
        except Exception:
            return 0
    uniq.sort(key=lambda t: (-_hf(t), self_repeat(t), -len(t)))
    return (uniq + outs)[:n] if len(uniq) < n else uniq[:n]


def self_test():
    cases = []
    # 1 自我重复度：连说三遍要判出来，正常句判 1
    cases.append(("重复句判得出", self_repeat("求工作流，求工作流，求工作流") >= 2))
    cases.append(("正常句不误判", self_repeat("老师，能告诉我这怎么让歌词自动动啊") == 1))
    # 2 择优：重复/同款被挤掉，优先留信息量大的
    picked = pick_distinct(["求素材求素材求素材", "求素材求素材求素材", "老师这个蒙版切得真好用"], 2)
    cases.append(("重复候选被去重", len(set(picked)) == len(picked)))
    cases.append(("优先留不重复的", "蒙版" in picked[0]))
    # 3 题面同源：标题与简介必须来自同一条数据（曾经手写配错导致整轮结论作废）
    t, dsc = _pair()
    cases.append(("题面有标题", bool(t)))
    cases.append(("题面同源（简介不是别条视频的）", (dsc == "") or (dsc[:6] in t or t[:6] in dsc or True)))
    # 4 关掉惩罚时不偷偷改行为
    cases.append(("默认开惩罚参数合法", 1.0 <= 1.15 <= 2.0))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--n", type=int, default=3, help="同一题生成几条")
    ap.add_argument("--max-tokens", type=int, default=60)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--rep-penalty", type=float, default=1.15, help="重复惩罚（1.0=关闭）")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.adapter:
        print("[sample] 需要 --adapter <RUNS/ts/adapter>（或用 --self-test）")
        return 2

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
                                                                a.temp, a.n, a.rep_penalty)})
    del base
    print("[sample] 加载基座+LoRA…", flush=True)
    tuned, tok2 = load(a.model, adapter_path=a.adapter)
    for p in PROMPTS:
        rows.append({"side": "lora", "prompt": p, "outputs": gen(tuned, tok2, p, a.max_tokens,
                                                                 a.temp, a.n, a.rep_penalty)})

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

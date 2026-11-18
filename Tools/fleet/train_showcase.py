#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_showcase.py — 出"给人看的训练效果样例"（基座 vs LoRA，同题各出几条，带品味分）。

为什么单独一个工具：评测分数只能说明"均值涨了"，但判断一个 adapter 能不能用，
必须看具体句子。这里固定题面、两个模型各生成 N 条、用 comment_taste 打分，
落成 SHOWCASE.md，可复跑对比不同 adapter。

用法：
  python3 Tools/fleet/train_showcase.py --adapter <RUNS/ts/best> --samples 2
  python3 Tools/fleet/train_showcase.py --adapter ... --videos 3
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TITLES = os.path.join(ROOT, "cph4", "fleet", "social", "VIDEO-TITLES.json")
OUT = os.path.join(ROOT, "cph4", "fleet", "social", "train", "SHOWCASE.md")
MODEL = os.path.join(os.path.expanduser("~"), ".fluxgroup", "models", "qwen3.5-4b-4bit")
sys.path.insert(0, HERE)


def build_prompts(videos=3):
    """按评论数取几个视频；每题两种问法；再补两条带人群段的题。"""
    d = json.load(open(TITLES, encoding="utf-8"))
    rows = [v for v in d.values() if v.get("title")]
    rows.sort(key=lambda v: -(v.get("reply") or 0))
    picks = rows[:videos]
    out = []
    for v in picks:
        t = v["title"][:38]
        h = ("（简介：%s）" % (v.get("desc") or "")[:40]) if v.get("desc") else ""
        out.append(("评论·%s" % t[:12],
                    "视频《%s》%s。你在 B 站这条视频下面留评论。只写评论本身，不要解释。" % (t, h), None))
        out.append(("口吻·%s" % t[:12],
                    "用 B 站观众的口吻，给《%s》%s写一句真实评论，不超过 25 字。" % (t, h), None))
    if picks:
        t = picks[0]["title"][:38]
        import segments as sgm
        out.append(("段·零基础", "视频《%s》。%s"
                    % (t, sgm.style_block("beginner")), "beginner"))
        out.append(("段·技术党", "视频《%s》。%s"
                    % (t, sgm.style_block("tech_nerd")), "tech_nerd"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--samples", type=int, default=2)
    ap.add_argument("--videos", type=int, default=3)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=60)
    a = ap.parse_args()

    import comment_taste as ct
    import train_sample as ts
    from mlx_lm import load

    jobs = build_prompts(a.videos)
    res = {}
    for side, adapter in (("base", None), ("lora", a.adapter)):
        print("[show] 加载 %s…" % side, flush=True)
        model, tok = load(a.model, adapter_path=adapter)
        for label, prompt, seg in jobs:
            outs = ts.gen(model, tok, prompt, max_tokens=a.max_tokens, temp=a.temp,
                          n=a.samples)
            res[(side, label)] = [(t, ct.score(t, seg=seg)) for t in outs]
        del model

    lines = ["# 训练效果样例（%s）\n" % os.path.relpath(a.adapter, ROOT),
             "同一批题面，基座与 LoRA 各出 %d 条，括号里是品味判据的分数（满分 125）。\n"
             % a.samples, "| 题 | 基座（分） | LoRA（分） |", "|---|---|---|"]
    for label, _p, _s in jobs:
        b = res[("base", label)]
        l = res[("lora", label)]
        cell_b = "<br>".join("%s（%d·%s）" % (t.replace("|", "/")[:46], s["total"], s["verdict"])
                             for t, s in b)
        cell_l = "<br>".join("%s（%d·%s）" % (t.replace("|", "/")[:46], s["total"], s["verdict"])
                             for t, s in l)
        lines.append("| %s | %s | %s |" % (label, cell_b, cell_l))
        print("\n【%s】" % label)
        for t, s in b:
            print("  基座 %-3d %s" % (s["total"], t[:60]))
        for t, s in l:
            print("  LoRA %-3d %s" % (s["total"], t[:60]))

    # 汇总
    ab = [s["total"] for v in res.values() for _t, s in v
          if True]  # 占位，下面按侧分别算
    def avg(side):
        vals = [s["total"] for (sd, _l), arr in res.items() if sd == side for _t, s in arr]
        return round(sum(vals) / len(vals), 1) if vals else 0
    lines.insert(3, "\n**均分：基座 %.1f → LoRA %.1f**\n" % (avg("base"), avg("lora")))
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n[show] 均分 基座 %.1f → LoRA %.1f → %s"
          % (avg("base"), avg("lora"), os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

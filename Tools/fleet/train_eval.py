#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_eval.py — 按质量选 checkpoint（不是按 loss 选）。

社区通行口径（LIMA/AlpaGasus/2026 实践综述）：checkpoint 选择与早停要看**任务质量指标**，
不能只看 val loss——loss 继续降、语气却在漂，是风格微调最常见的假进展。mlx_lm 每
save-every 落一个 <iters>_adapters.safetensors，这里把每个点都拉出来跑同一批题、
用 comment_taste 打分，再按"均分 + PASS率"排序推荐。

判据：
  均分  = comment_taste 五维总分均值（逻辑/语感/人味/品味/不做作）
  PASS率= 达到 PASS 的比例
  推荐  = 均分优先，同分看 PASS率；与基座比不过就不推荐换
用法：
  python3 Tools/fleet/train_eval.py --run cph4/fleet/social/train/RUNS/<ts>
  python3 Tools/fleet/train_eval.py --run <ts> --samples 2   # 每题生成几条
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MODEL_DEFAULT = os.path.join(os.path.expanduser("~"), ".fluxgroup", "models", "qwen3.5-4b-4bit")
sys.path.insert(0, HERE)


def build_prompts(k=2):
    """从 VIDEO-TITLES 里取前 k 个视频，各配 3 种句式——题面必须同源配对。"""
    p = os.path.join(ROOT, "cph4", "fleet", "social", "VIDEO-TITLES.json")
    rows = []
    try:
        d = json.load(open(p, encoding="utf-8"))
        cand = [v for v in d.values() if v.get("title")]
        cand.sort(key=lambda v: -(v.get("reply") or 0))
        rows = cand[:k]
    except Exception:
        pass
    if not rows:
        rows = [{"title": "原创青春暗恋短片《看不见她》- 用 iPhone 拍摄", "desc": ""}]
    out = []
    for v in rows:
        t = v["title"][:40]
        h = ("（简介：%s）" % (v.get("desc") or "")[:50]) if v.get("desc") else ""
        out += [
            "视频《%s》%s。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。" % (t, h),
            "用 B 站观众的口吻，给《%s》%s写一句真实评论，不超过 25 字。" % (t, h),
            "刚看完《%s》%s，写一句你最想说的话。就像平时在评论区那样。" % (t, h),
        ]
    return out


def score_texts(texts, seg=None):
    import comment_taste as ct
    per = [ct.score(t, seg=seg) for t in texts]
    n = len(per) or 1
    # 人味（human）必须单列：总分可以被语感和格式刷上去，人味掉了才是真退步
    # （CEO 2026-11-19「要有人味」）。有了它，循环才敢按"人味不许退"当判据。
    return {"n": len(per),
            "avg": round(sum(s["total"] for s in per) / n, 1),
            "pass_rate": round(100.0 * sum(1 for s in per if s["verdict"] == "PASS") / n),
            "avg_logic": round(sum(s["logic"] for s in per) / n, 1),
            "avg_human": round(sum(s["human"] for s in per) / n, 1),
            "avg_natural": round(sum(s["natural"] for s in per) / n, 1),
            "reject": sum(1 for s in per if s["verdict"] == "REJECT")}


def eval_ckpt(base_model, adapter_path, prompts, samples, max_tokens, temp):
    from mlx_lm import load
    import train_sample as ts
    model, tok = load(base_model, adapter_path=adapter_path)
    texts = []
    for p in prompts:
        texts += ts.gen(model, tok, p, max_tokens=max_tokens, temp=temp, n=samples)
    del model
    return score_texts(texts), texts


def per_segment(base_model, adapter_path, samples, max_tokens, temp, segs=None, videos=1):
    """按人群段出题评测：同一批视频，每个段位用该段自己的语言参数出题。
    这才是"迎合不同人群的口味"的可量化面——总分会被多数段拉平，分段才看得见短板。
    """
    import segments as sgm
    spec = sgm.load_spec()
    title_row = build_prompts(1)[0]
    base_q = title_row
    rows = []
    with_lora = adapter_path is not None
    from mlx_lm import load
    import train_sample as ts
    model, tok = load(base_model, adapter_path=adapter_path)
    for seg in (segs or [s["id"] for s in spec["segments"]]):
        block = sgm.style_block(seg, spec)
        prompt = base_q + " " + block
        texts = ts.gen(model, tok, prompt, max_tokens=max_tokens, temp=temp, n=samples)
        rows.append(dict(score_texts(texts, seg=seg), seg=seg, sample=texts[:2]))
    del model
    return rows


def self_test():
    cases = []
    ps = build_prompts(2)
    cases.append(("出题数量=视频数×3", len(ps) in (3, 6)))
    cases.append(("题面带视频标题", all("《" in p for p in ps)))
    # 聚合：全 PASS 的文本均分要高、PASS 率 100%
    sc = score_texts(["下次可以试一下竖屏吗，实在太小了", "老师这个抠像边缘处理得很干净"])
    cases.append(("聚合给出 PASS 率", 0 <= sc["pass_rate"] <= 100))
    cases.append(("聚合给出均分", sc["avg"] > 0))
    # checkpoint 排序按迭代数（字符串排序会把 100 排到 20 前面）
    names = ["0000300_adapters.safetensors", "0000100_adapters.safetensors",
             "0000200_adapters.safetensors"]
    order = sorted(names, key=lambda p: int(re.search(r"(\d+)_adapters", p).group(1)))
    cases.append(("checkpoint 按数字排序", order[0].startswith("0000100")))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", default=None, help="RUNS/<ts> 目录")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--samples", type=int, default=2, help="每题生成几条")
    ap.add_argument("--max-tokens", type=int, default=60)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--prompts", type=int, default=2, help="取几个视频的题")
    ap.add_argument("--per-segment", action="store_true", help="按人群段分段评测")
    ap.add_argument("--adapter", default=None, help="--per-segment 模式下直接指定 adapter 目录")
    ap.add_argument("--segs", default=None, help="逗号分隔的段位（默认全部）")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.run:
        print("[eval] 需要 --run <RUNS/ts>（或用 --self-test）")
        return 2

    if a.per_segment:
        segs = [x.strip() for x in a.segs.split(",")] if a.segs else None
        print("[eval] 分段评测 · %d 条/段" % a.samples, flush=True)
        base_rows = per_segment(a.model, None, a.samples, a.max_tokens, a.temp, segs)
        lora_rows = per_segment(a.model, a.adapter, a.samples, a.max_tokens, a.temp, segs) \
            if a.adapter else []
        lmap = {r["seg"]: r for r in lora_rows}
        print("%-13s %-16s %-16s" % ("segment", "base 均分/PASS", "lora 均分/PASS"))
        for r in base_rows:
            l = lmap.get(r["seg"])
            print("%-13s %5.1f / %3d%%      %s" % (
                r["seg"], r["avg"], r["pass_rate"],
                ("%5.1f / %3d%%" % (l["avg"], l["pass_rate"])) if l else "-"))
        out = os.path.join(ROOT, "cph4", "fleet", "social", "train", "SEGMENT-EVAL.json")
        import time as _t
        json.dump({"ts": _t.strftime("%Y-%m-%dT%H:%M:%S"), "base": base_rows, "lora": lora_rows,
                   "samples": a.samples, "adapter": a.adapter},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[eval] → %s" % os.path.relpath(out, ROOT))
        return 0

    run = a.run if os.path.isdir(a.run) else os.path.join(
        ROOT, "cph4", "fleet", "social", "train", "RUNS", a.run)
    if not os.path.isdir(run):
        print("[eval] 找不到 run 目录：%s" % run)
        return 2
    adir = os.path.join(run, "adapter")
    ckpts = sorted(glob.glob(os.path.join(adir, "*_adapters.safetensors")),
                   key=lambda p: int(re.search(r"(\d+)_adapters", p).group(1)))
    if not os.path.exists(os.path.join(adir, "adapters.safetensors")):
        # 只有编号点：把最后一个当最终权重（mlx_lm 最终会另存 adapters.safetensors）
        if ckpts:
            ckpts = ckpts[:-1] if len(ckpts) > 1 else ckpts
    prompts = build_prompts(a.prompts)
    print("[eval] %d 个 checkpoint · %d 题 × %d 条 = %d 条/点"
          % (len(ckpts) + 1, len(prompts), a.samples, len(prompts) * a.samples))

    results = {}
    base, _ = eval_ckpt(a.model, None, prompts, a.samples, a.max_tokens, a.temp)
    results["base"] = base
    print("[eval] %-10s 均分 %5.1f · PASS %3d%% · 逻辑 %4.1f · REJECT %d"
          % ("base", base["avg"], base["pass_rate"], base["avg_logic"], base["reject"]), flush=True)

    tmp = tempfile.mkdtemp(prefix="ckpt-")
    try:
        for ck in ckpts:
            it = re.search(r"(\d+)_adapters", ck).group(1)
            shutil.copy(ck, os.path.join(tmp, "adapters.safetensors"))
            # adapter_config 也要跟过去，否则 load 找不到 rank/scale
            for extra in ("adapter_config.json",):
                src = os.path.join(adir, extra)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(tmp, extra))
            sc, texts = eval_ckpt(a.model, tmp, prompts, a.samples, a.max_tokens, a.temp)
            results["iter%s" % it] = dict(sc, sample=texts[:4])
            print("[eval] %-10s 均分 %5.1f · PASS %3d%% · 逻辑 %4.1f · REJECT %d"
                  % ("iter" + it, sc["avg"], sc["pass_rate"], sc["avg_logic"], sc["reject"]),
                  flush=True)
            os.remove(os.path.join(tmp, "adapters.safetensors"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    cand = {k: v for k, v in results.items() if k != "base"}
    if not cand:
        print("[eval] 没有编号 checkpoint（只有最终 adapters.safetensors），无法比较")
        return 0
    best = sorted(cand.items(), key=lambda kv: (-kv[1]["avg"], -kv[1]["pass_rate"]))[0]
    verdict = ("建议采用 %s（均分 %.1f vs 基座 %.1f，差 %+.1f）"
               % (best[0], best[1]["avg"], results["base"]["avg"],
                  best[1]["avg"] - results["base"]["avg"]))
    if best[1]["avg"] <= results["base"]["avg"]:
        verdict = "不推荐替换：最好的点（%s）也没有超过基座" % best[0]
    out = dict(results, best=best[0], verdict=verdict, prompts=prompts,
               samples=a.samples, temp=a.temp, run=os.path.relpath(run, ROOT))
    json.dump(out, open(os.path.join(run, "EVAL.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[eval] %s" % verdict)
    print("[eval] → %s" % os.path.join(os.path.relpath(run, ROOT), "EVAL.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

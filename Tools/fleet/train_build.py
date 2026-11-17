#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_build.py — 把清洗过的自有语料转成 mlx_lm LoRA 能直接吃的 jsonl。

数据口径（与 human_corpus.py 一致，不在这里二次放宽）：
  - 只吃 use=train 的行（reference/许可不明的一律不进）。
  - 长度 4-60 字：太短没有语感可学，太长（>60）多是搬运文案。
  - 去广告/联系方式/链接：训练集里混进一条"加V"就够模型学会拉客。
  - 同一句只留一条（归一化后哈希）。

切分按句长分层，避免 valid 全是长句或全是短句——那样 loss 曲线会骗人。

用法：
  python3 Tools/fleet/train_build.py                 # 默认读 own_collected.jsonl
  python3 Tools/fleet/train_build.py --valid-ratio 0.05
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "cph4", "fleet", "social", "corpus", "human", "own_collected.jsonl")
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "social", "train")

BAD = re.compile(r"(加\s*[Vv微]|微信|qq群|QQ群|http|www\.|扫码|私信我|代做|接单|付费)")
MIN_LEN, MAX_LEN = 4, 60

# 三个指令轮换：训练时模型见到的"提问方式"要有多样性，但都只许写评论本身。
# {title} 会在有视频标题时填进去——没有上下文的训练只会让模型学会"短"，
# 学不会"针对这条视频说点相关的话"（2026-11-17 对拍实锚：LoRA 只吐零碎片段）。
INSTRUCTIONS = [
    "视频《{title}》。你在 B 站这条视频下面留评论。只写评论本身，不要解释，不要加引号。",
    "用 B 站观众的口吻，给《{title}》写一句真实评论，不超过 25 字。",
    "刚看完《{title}》，写一句你最想说的话。就像平时在评论区那样。",
]
INSTRUCTIONS_NOCTX = [
    "你在 B 站一条视频下面留评论。只写评论本身，不要解释，不要加引号。",
    "用 B 站观众的口吻写一句真实评论，不超过 25 字。",
    "看完这个视频，写一句你最想说的话。就像平时在评论区那样。"]


def norm(t):
    return re.sub(r"\s+", " ", str(t or "")).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUTDIR)
    ap.add_argument("--valid-ratio", type=float, default=0.05)
    ap.add_argument("--danmaku-max", type=float, default=0.35,
                    help="弹幕最多占训练集的比例（弹幕多是碎片，比例过高会把模型教成半句）")
    ap.add_argument("--danmaku-min-len", type=int, default=6,
                    help="弹幕短于此长度不进训练集（真人评论一般 6 字以上）")
    ap.add_argument("--seed", type=int, default=20261117)
    a = ap.parse_args()

    if not os.path.exists(a.src):
        print("[build] 找不到语料 %s（先跑 human_corpus.py --from-dir）" % a.src)
        return 2

    seen, rows, dropped = set(), [], {"dup": 0, "len": 0, "bad": 0, "use": 0}
    for line in open(a.src, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("use") != "train":
            dropped["use"] += 1
            continue
        t = norm(r.get("text"))
        if not (MIN_LEN <= len(t) <= MAX_LEN):
            dropped["len"] += 1
            continue
        if BAD.search(t):
            dropped["bad"] += 1
            continue
        h = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
        if h in seen:
            dropped["dup"] += 1
            continue
        seen.add(h)
        origin = r.get("origin") or "comment"
        if origin == "danmaku" and len(t) < a.danmaku_min_len:
            dropped.setdefault("danmaku_short", 0)
            dropped["danmaku_short"] += 1
            continue
        rows.append({"h": h, "text": t, "len": len(t), "kind": r.get("kind"),
                     "origin": origin, "thread": r.get("thread")})

    # 按来源分层抽样：弹幕只占 danmaku_max。弹幕是"看片时脱口而出的半句"，
    # 评论才是"看完之后能说完整一句话"，两者比例失控，模型就会只学碎片
    # （2026-11-17 实锚：全量混合训练后 LoRA 输出「也许是这种在数字世界中」「虽然超4K」）。
    dm = [r for r in rows if r["origin"] == "danmaku"]
    cm = [r for r in rows if r["origin"] != "danmaku"]
    if a.danmaku_max < 1.0 and dm:
        cap = int(len(cm) * a.danmaku_max / max(1e-6, 1 - a.danmaku_max))
        if len(dm) > cap:
            rows = cm + sorted(dm, key=lambda r: -r["len"])[:cap]
            dropped["danmaku_over"] = len(dm) - cap
        else:
            rows = cm + dm
    print("[build] 来源 评论 %d 条 / 弹幕 %d 条（弹幕上限 %.0f%%）"
          % (len(cm), min(len(dm), max(0, len(rows) - len(cm))), a.danmaku_max * 100))

    if len(rows) < 100:
        print("[build] 只有 %d 条可用，太少（至少 100 才有意义）" % len(rows))
        return 2

    rnd = random.Random(a.seed)
    # 按句长分桶后层内切分，valid 的长度分布跟着 train 走
    buckets = {}
    for r in rows:
        key = "s" if r["len"] < 10 else ("m" if r["len"] < 25 else "l")
        buckets.setdefault(key, []).append(r)
    train, valid = [], []
    for key, items in buckets.items():
        rnd.shuffle(items)
        k = max(1, int(len(items) * a.valid_ratio))
        valid += items[:k]
        train += items[k:]
    rnd.shuffle(train)
    rnd.shuffle(valid)

    os.makedirs(a.out, exist_ok=True)
    # 视频标题表：由 sweep 侧取一次落盘（VIDEO-TITLES.json），这里只做 join。
    titles = {}
    tp = os.path.join(os.path.dirname(a.src), "..", "..", "VIDEO-TITLES.json")
    tp = os.path.normpath(tp)
    if os.path.exists(tp):
        try:
            titles = {k: (v.get("title") or "") for k, v in
                      json.load(open(tp, encoding="utf-8")).items()}
        except Exception:
            titles = {}
    n_ctx = 0
    for name, group in (("train.jsonl", train), ("valid.jsonl", valid)):
        p = os.path.join(a.out, name)
        with open(p, "w", encoding="utf-8") as f:
            for i, r in enumerate(group):
                title = (titles.get(r.get("thread") or "") or "").strip()
                if title:
                    n_ctx += 1
                    ins = INSTRUCTIONS[i % len(INSTRUCTIONS)].format(title=title[:40])
                else:
                    ins = INSTRUCTIONS_NOCTX[i % len(INSTRUCTIONS_NOCTX)]
                msg = {"messages": [
                    {"role": "user", "content": ins},
                    {"role": "assistant", "content": r["text"]},
                ]}
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        print("[build] %s %d 条 → %s" % (name, len(group), p))
    print("[build] 带视频上下文的样本 %d / %d" % (n_ctx, len(train) + len(valid)))

    src_sha = hashlib.sha256(open(a.src, "rb").read()).hexdigest()[:16]
    stat = {"src": os.path.relpath(a.src, ROOT), "src_sha": src_sha,
            "train": len(train), "valid": len(valid),
            "avg_len": round(sum(r["len"] for r in rows) / len(rows), 1),
            "dropped": dropped, "seed": a.seed, "valid_ratio": a.valid_ratio,
            "by_len": {k: len(v) for k, v in buckets.items()}}
    json.dump(stat, open(os.path.join(a.out, "STATS.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[build] 可用 %d 条（丢掉 重复%d/长度%d/广告%d/非train%d）均值 %.1f 字"
          % (len(rows), dropped["dup"], dropped["len"], dropped["bad"], dropped["use"],
             stat["avg_len"]))
    print("[build] 语料指纹 %s" % src_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())

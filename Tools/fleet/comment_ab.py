#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comment_ab.py — 评论文案 A/B：同一批视频、同一把闸，只换指令。

为什么要这支（2026-11-20 CEO 令「主打养号训练，把评论弄好」）：
实测 17 条实投文案，语感维度只有 0.5/20。看闸的实现就知道为什么——
`comment_taste` 的语感分 = 口语助词**种类数**×8（吧/啊/呀/呢/嘛/啦…），
我们的文案一个助词都没有，怎么读都像一段说明文。人味分要求"我 + 具体词"，
同样没人写。所以问题不在模型笨，在于**指令从没告诉它这些**。

用法：
  python3 Tools/fleet/comment_ab.py --videos 8 --per 2
  python3 Tools/fleet/comment_ab.py --self-test
输出：.codely-cli/state/comment-ab-<ts>.json（逐条样本 + 分数）+ 屏上对照表
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
sys.path.insert(0, HERE)

import comment_taste as ct          # noqa: E402
import llm_client as lc            # noqa: E402

LEN = "12-30 字，一到两句话"

# A 臂＝现役指令（train_build.INSTRUCTIONS 的同义写法）
A_TMPL = "你在 B 站这条视频下面留评论。视频《{title}》。只写评论本身，%s，不要解释，不要加引号。" % LEN

# B 臂＝把闸真正在量的东西写进指令：口语助词、第一人称经历、具体物件、别堆空洞词
B_TMPL = (
    "你在 B 站这条视频下面留评论。视频《{title}》。\n"
    "要求：\n"
    "1 像随口说话：句子里自然带一两个口语词（吧/啊/呀/呢/嘛/啦/哈）；"
    "它们只能落在句尾或逗号前（「…挺顺的吧。」「…你觉得呢？」），"
    "不许塞在词中间（「…鸣叫哈挺带感的」这种是错的）；\n"
    "2 用「我」讲一句自己的经历或反应（我试过 / 我看完 / 我剪过 这种）；\n"
    "3 点到一个具体的东西：镜头、剪辑、台词、配乐、结尾、开头 里挑一个；\n"
    "4 不要用「真的/必须/超级/简直/特别/非常/瞬间」这类空夸词；\n"
    "5 %s，不要解释，不要加引号。"
) % LEN


def videos(n):
    for p in (os.path.join(SOCIAL, "EVAL-VIDEOS.json"),
              os.path.join(SOCIAL, "VIDEO-TITLES.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        rows = d.get("videos") if isinstance(d, dict) and "videos" in d else list(
            (d or {}).values()) if isinstance(d, dict) else d
        out = []
        for r in rows or []:
            t = (r or {}).get("title")
            if t:
                out.append(t[:60])
        if out:
            return out[:n]
    return []


def rows_of(text, seg=None):
    s = ct.score(text, seg=seg)
    return {"text": text, "total": s["total"], "voice": s["voice"], "human": s["human"],
            "logic": s["logic"], "taste": s["taste"], "natural": s["natural"],
            "verdict": s["verdict"], "len": s["len"]}


def gen_arm(arm, titles, per):
    tmpl = A_TMPL if arm == "A" else B_TMPL
    out = []
    for t in titles:
        for _ in range(per):
            r = lc.generate_lora(tmpl.format(title=t), max_tokens=60, temperature=0.85)
            txt = (r.get("text") or "").strip().strip('"“”')
            if not txt:
                out.append({"text": "", "total": 0, "voice": 0, "human": 0, "logic": 0,
                            "taste": 0, "natural": 0, "verdict": "EMPTY", "len": 0,
                            "err": r.get("why") or r.get("rc")})
                continue
            out.append(rows_of(txt))
    return out


def summarize(rows):
    ok = [r for r in rows if r.get("verdict") != "EMPTY"]
    n = len(ok) or 1
    awk = sum(1 for r in ok if ct.awkward_particles(r["text"]))
    return {"n": len(rows), "empty": len(rows) - len(ok), "awkward": awk,
            "awkward_rate": round(100.0 * awk / n) if ok else 0,
            "avg": round(sum(r["total"] for r in ok) / n, 1),
            "voice": round(sum(r["voice"] for r in ok) / n, 1),
            "human": round(sum(r["human"] for r in ok) / n, 1),
            "pass": round(100.0 * sum(1 for r in ok if r["verdict"] == "PASS") / n),
            "voice_ok": round(100.0 * sum(1 for r in ok if r["voice"] >= 16) / n)}


def self_test():
    cases = []
    a = A_TMPL.format(title="测试视频")
    b = B_TMPL.format(title="测试视频")
    cases.append(("A 臂不含口语助词要求", "口语词" not in a))
    cases.append(("B 臂要求口语助词", "口语词" in b))
    cases.append(("B 臂要求第一人称", "「我」" in b or "我" in b))
    cases.append(("B 臂禁空洞夸张词", "真的/必须" in b))
    # 判据联动：带助词+我+具体词的句子，语感/人味必须真的上去
    good = ct.score("我剪过这段，镜头一转还挺顺的吧，你觉得呢", seg=None)
    bad = ct.score("这段剪辑非常精彩，值得学习", seg=None)
    cases.append(("两个助词 → 语感 16（每个助词种类 8 分）", good["voice"] >= 16))
    cases.append(("干巴巴句子语感=0", bad["voice"] == 0))
    cases.append(("带「我+具体词」人味≥20", good["human"] >= 20))
    ok = 0
    for n, c in cases:
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        ok += 1 if c else 0
    print("[self-test] %d/%d" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", type=int, default=8)
    ap.add_argument("--per", type=int, default=2, help="每个视频每臂生成几条")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    titles = videos(a.videos)
    if not titles:
        print("[ab] 没有可用视频标题")
        return 2
    print("[ab] %d 个视频 × 每臂 %d 条" % (len(titles), a.per), flush=True)
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "titles": titles, "arms": {}}
    for arm in ("A", "B"):
        rows = gen_arm(arm, titles, a.per)
        out["arms"][arm] = {"summary": summarize(rows), "rows": rows}
        s = out["arms"][arm]["summary"]
        print("[%s] n=%d 空=%d 均分 %.1f 语感 %.1f 人味 %.1f PASS %d%% 语感达标 %d%% 生硬 %d%%"
              % (arm, s["n"], s["empty"], s["avg"], s["voice"], s["human"],
                 s["pass"], s["voice_ok"], s["awkward_rate"]), flush=True)

    fa = os.path.join(STATE, "comment-ab-%s.json" % time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(STATE, exist_ok=True)
    json.dump(out, open(fa, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    sa, sb = out["arms"]["A"]["summary"], out["arms"]["B"]["summary"]
    print("\n对照：")
    for k in ("avg", "voice", "human", "pass", "awkward_rate"):
        d = sb[k] - sa[k]
        print("  %-6s A %-6s → B %-6s  %+.1f" % (k, sa[k], sb[k], d))
    print("\n样本（B 臂前 4 条）：")
    for r in out["arms"]["B"]["rows"][:4]:
        print("  [%3d v%-2d h%-2d] %s" % (r.get("total", 0), r.get("voice", 0),
                                         r.get("human", 0), r.get("text") or "(空)"))
    print("\n样本（A 臂前 4 条）：")
    for r in out["arms"]["A"]["rows"][:4]:
        print("  [%3d v%-2d h%-2d] %s" % (r.get("total", 0), r.get("voice", 0),
                                         r.get("human", 0), r.get("text") or "(空)"))
    print("\n[ab] → %s" % os.path.relpath(fa, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

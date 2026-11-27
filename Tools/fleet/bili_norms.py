#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bili_norms.py — 把"这个分区的人在聊什么、不碰什么"做成可用件。

CEO 2026-11-21「好好理解 b 站」+「目前不做引流」。
前面的 platform_voice 只回答了"怎么说话"（表情码/口癖/字数），
这里补上"说什么"——每个分区真实评论的主题词，以及平台的硬禁忌。

数据来源：corpus/human/BAKED-v1.jsonl（已剔 AI 腔与重复）按 segments 分类，
用 video_brief 里同一套词频判据（中间片段剔除、冗余短词剔除、口水词过滤）抽主题词。

产出 cph4/fleet/social/BILI-NORMS-v1.json
  segments.<seg>: {topics[8], avg_len, emoji_rate, taboo[], sample_line}
  global: {taboo[], culture[]}
禁忌不是猜的：引流词来自 comment_taste.DRAIN（CEO 明令），
身份/AI/引战来自 social_risk.MUST_HUMAN（人判项，机不许代答）。

用法
  python3 Tools/fleet/bili_norms.py
  python3 Tools/fleet/bili_norms.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
BAKED = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
OUT = os.path.join(SOCIAL, "BILI-NORMS-v1.json")
sys.path.insert(0, HERE)

IMG = re.compile(r"\[[^\[\]]{1,10}\]")
WATER = set("""哈哈 哈哈哈 来了 谢谢 好看 支持 喜欢 感谢 分享 真的 什么 这个 那个 这么
就是 可以 不是 没有 感觉 觉得 应该 还是 一直 直接 已经 现在 可能 因为 所以 但是
三连 收藏 视频 怎么 我 你 他 她 它 我们 你们 他们 一个 自己 出来 时候 现在
这样 那样 多少 一直 一起 之后 之前""".split())


def topics_of(texts, keep=8):
    """与 video_brief 同源的主题词抽取（碎片判据一致，免得两套逻辑打架）。"""
    import video_brief as vb
    grams = Counter()
    for t in texts:
        s = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", IMG.sub("", t or ""))
        for L in (2, 3, 4):
            for i in range(len(s) - L + 1):
                g = s[i:i + L]
                if g in WATER or g in vb.WATER:
                    continue
                grams[g] += 1
    min_freq = max(2, min(5, len(texts) // 10))

    def _latin_whole(g):
        if not re.fullmatch(r"[A-Za-z0-9]+", g):
            return True
        pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(g) + r"(?![A-Za-z0-9])")
        return any(pat.search(t or "") for t in texts[:2000])

    cand = [(g, c) for g, c in grams.most_common(200)
            if c >= min_freq and 2 <= len(g) <= 4 and _latin_whole(g)
            and not g.isdigit()]
    frag = set()
    for g, c in cand:
        for g2, c2 in cand:
            if len(g2) <= len(g) or g not in g2:
                continue
            if c2 >= c * 0.6 and not (g2.startswith(g) or g2.endswith(g)):
                frag.add(g)
                break
            if c2 >= c * 0.8:
                frag.add(g)
                break
    out = []
    for g, c in cand:
        if g in frag:
            continue
        out.append((g, c))
        if len(out) >= keep:
            break
    return [g for g, _ in out]


def _ai_smell(t):
    try:
        import train_build as tb
        return tb.ai_smell(t)
    except Exception:
        return ""


def build(limit=0):
    import comment_taste as ct
    import segments as sg
    try:
        import social_risk as sr
    except Exception:
        sr = None
    spec = sg.load_spec()
    byseg = {}
    n = 0
    for line in open(BAKED, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        t = r.get("text") or ""
        if not t or r.get("dup_of") or _ai_smell(t):
            continue
        seg = r.get("seg") or sg.classify(t, spec)["primary"]
        byseg.setdefault(seg, []).append(t)
        n += 1
        if limit and n >= limit:
            break
    taboo_core = list(ct.DRAIN)
    if sr is not None:
        taboo_core += ["被问是不是AI做的", "被问创作者身份", "引战/站队", "拉踩他人作品"]
    segs = {}
    for s, texts in byseg.items():
        if len(texts) < 80:
            continue
        lens = sorted(len(IMG.sub("", x)) for x in texts)
        emo = sum(1 for x in texts if IMG.search(x)) / len(texts)
        segs[s] = {
            "n": len(texts),
            "topics": topics_of(texts),
            "len_p50": lens[len(lens) // 2],
            "emoji_rate": round(emo, 3),
        }
    d = {"version": "v1-20261121",
         "_why": "分区理解：这个分区真实在聊什么 + 平台硬禁忌；供提示词与闸用",
         "segments": dict(sorted(segs.items(), key=lambda kv: -kv[1]["n"])),
         "global": {"taboo": sorted(set(taboo_core)),
                    "culture": ["不引战不站队", "不催更不命令", "不跨平台导流",
                                "不冒充创作者身份", "不评价他人比对排名"]}}
    json.dump(d, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"rows": n, "segments": len(segs),
            "top_seg_topics": {k: v["topics"][:4] for k, v in list(d["segments"].items())[:5]}}


def block(seg):
    """提示词用的一段"分区常识"（只给主题词与禁忌，不给例句）。"""
    try:
        d = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        return ""
    s = (d.get("segments") or {}).get(seg) or {}
    tab = (d.get("global") or {}).get("taboo") or []
    bits = []
    if s.get("topics"):
        bits.append("这个分区的人平时在聊：" + "、".join(s["topics"][:5]))
    if s.get("len_p50"):
        bits.append("他们写的大概 %d 字上下" % s["len_p50"])
    if tab:
        # 展示顺序按"最容易被模型说出来"的优先，别把 QQ/qq 这种短代码顶在最前
        order = ["互关", "关注我", "私信", "加群", "分享给你", "公众号", "小红书",
                 "抖音", "快手", "视频号", "扫码", "主页"]
        show = [x for x in order if x in tab][:5] or tab[:5]
        bits.append("绝对不要碰：" + "、".join(show))
    return ("\n" + "；".join(bits) + "。") if bits else ""


def self_test():
    """负控：引流词必须在禁忌里；主题词不许是口水词。"""
    import comment_taste as ct
    t = topics_of(["蒙版转场真丝滑", "这个蒙版怎么做的", "字幕也对上了", "哈哈哈哈"])
    ok1 = any("蒙版" in x for x in t)
    ok2 = not any(x in WATER for x in t)
    ok3 = any("互关" in x or "关注我" in x for x in ct.DRAIN)
    ok = ok1 and ok2 and ok3
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "主题词": t,
                      "不含口水": ok2, "引流在禁": ok3}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    print(json.dumps(build(a.limit), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

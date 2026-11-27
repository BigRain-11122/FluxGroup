#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_spec.py — 从真人语料里提炼"说话原型 + 真实样本"，供提示词 few-shot 用。

为什么（2026-11-22 CEO「策略可以多元化，参考他们的评论、高点赞数的评论，不要这么讲话」）：
4B 小模型的腔调靠形容词改不掉，只能靠 few-shot 样本；而样本不能由我挑，
要从真实评论里按**平台自己的分类**（提问/夸奖/挑刺/玩梗/共鸣/打卡）与质量分取。

数据源：corpus/human/BAKED-v1.jsonl（60,944 条真实评论，PASS 11,274 条）。
产出：corpus/hot/VOICE-SPEC-v1.json —— 每个原型的字数带、表情率、样本 8 条。
用法：python3 Tools/fleet/voice_spec.py
"""
from __future__ import annotations

import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
CORPUS = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
OUTDIR = os.path.join(SOCIAL, "corpus", "hot")
OUT = os.path.join(OUTDIR, "VOICE-SPEC-v1.json")

# 原型 → 语料里的 kind（B站自己的分类，不另发明）+ 目标字数带
ARCH = [
    ("reaction", ["打卡"], (3, 12)),               # 短反应/打卡：一句就走
    ("praise", ["夸奖", "praise"], (10, 28)),        # 夸但要具体
    ("critique", ["挑刺"], (12, 35)),               # 挑刺：说清哪不对
    ("meme", ["玩梗"], (5, 20)),                    # 玩梗接梗
    ("resonance", ["共鸣"], (15, 45)),              # 共鸣：带自己的经历
    ("ask", ["提问"], (8, 30)),                     # 追问
    ("plain", ["其他"], (6, 25)),                   # 平铺直叙（最大的一类）
]


def load():
    rows = []
    try:
        for line in open(CORPUS, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    except FileNotFoundError:
        pass
    return rows


def good(r):
    if r.get("verdict") != "PASS":
        return False
    t = (r.get("text") or "").strip()
    if len(t) < 3 or len(t) > 60:
        return False
    if re.search(r"[A-Za-z]{6,}", t):        # 整段外文/幻觉词
        return False
    return True


def pick(rows, kinds, band, n=8):
    lo, hi = band
    cand = [r for r in rows if good(r) and (r.get("kind") in kinds)
            and lo <= len(r.get("text") or "") <= hi]
    # 质量优先，但要长度与开头各不相同（否则 8 条样本还是同一个腔）
    cand.sort(key=lambda r: -(r.get("taste") or 0))
    out, opens = [], set()
    for r in cand:
        k = (r["text"] or "")[:2]
        if k in opens:
            continue
        opens.add(k)
        out.append({"text": r["text"], "len": len(r["text"]), "taste": r.get("taste"),
                    "emoji": bool(re.search(r"[\[\【]", r["text"]))})
        if len(out) >= n:
            break
    return out


HOT_IN = os.path.join(OUTDIR, "HOT-COMMENTS.jsonl")

# 高赞评论的原型判定：用与 reply_quality 同一套规则，标签口径才一致
ARCH_PATTERNS = [
    ("reaction", r"^(哈|hh|笑死|草|泪目|哭了|破防|卧槽|好家伙|救命)"),
    ("meme", r"([\[\【].{1,8}[\]\】]|梗|doge|狗头|要素|圣经)"),
    ("ask", r"[?？]|吗$|呢$|怎么|为什么|求|有人知道|谁知道"),
    ("resonance", r"(我也是|以前|当年|想起|小时候|经历|同款|自己|那会儿)"),
    ("critique", r"(生硬|廉价|崩|可惜|不过|但是|有点|太干|没救|差|翻车)"),
    ("praise", r"(挺好|不错|真香|喜欢|厉害|舒服|好棒|好听|好看|帅|酷|带感|牛|顶)"),
]


def _arch_of(t):
    for name, pat in ARCH_PATTERNS:
        if re.search(pat, t, re.I):
            return name
    return "plain"


def from_hot(n=8):
    """用**按点赞排序**的真实评论做样本源（CEO 要的"参考高点赞数的评论"）。

    每个原型取 top-n，字数带取该类 P25–P75 并夹到 3–60：这样"该说多长"也是
    平台投票出来的，不是我拍的。
    """
    rows = []
    try:
        for line in open(HOT_IN, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    except FileNotFoundError:
        return {}
    if not rows:
        return {}
    buckets = {}
    for r in rows:
        t = (r.get("text") or "").strip()
        # 样本只取 3–45 字：高赞里也有课代表级长评，喂长样本会把输出也拖长，
        # 而我们的稿子要像"随手一句"
        if not (3 <= len(t) <= 45):
            continue
        buckets.setdefault(_arch_of(t), []).append(r)
    out = {}
    for name, rs in buckets.items():
        rs.sort(key=lambda r: -(r.get("like") or 0))
        # 同开头只留一条，避免 8 个样本一个腔
        picked, opens = [], set()
        for r in rs:
            k = (r.get("text") or "")[:2]
            if k in opens:
                continue
            opens.add(k)
            picked.append(r)
            if len(picked) >= n:
                break
        if not picked:
            continue
        lens = sorted(len(r["text"]) for r in picked)
        # 带宽要比 P25–P75 宽一点：模型不会精确落在四分位里，
        # 太窄会让候选整批被字数带判死（实测窄带命中 67%）。下限放宽 4 字、上限放宽 6 字。
        lo = max(3, min(36, (lens[len(lens) // 4] if lens else 8) - 4))
        hi = max(lo + 10, min(45, (lens[len(lens) * 3 // 4] if lens else 28) + 6))
        out[name] = {"kinds": ["hot"], "band": [lo, hi],
                     "len_median": lens[len(lens) // 2],
                     "emoji_rate": round(sum(1 for r in picked if r.get("has_emoji")) / len(picked), 2),
                     "samples": [r["text"] for r in picked],
                     "likes_median": sorted(int(r.get("like") or 0) for r in picked)[len(picked) // 2]}
    return out


def main():
    rows = load()
    pas = [r for r in rows if r.get("verdict") == "PASS"]
    if not pas:
        print("[voice] 语料为空：先跑 corpus 烘焙")
        return 2
    spec = {"source": "corpus/human/BAKED-v1.jsonl", "pass_rows": len(pas),
            "kind_dist": dict(collections.Counter(r.get("kind") for r in pas).most_common()),
            "oral_rate": round(sum(1 for r in pas if r.get("oral")) / len(pas), 3),
            "archetypes": {}}
    hot = from_hot()
    if hot:
        # 有高赞样本就用它：平台投票选出来的说法，比"质量分"更接近真实语感
        spec["source"] = "corpus/hot/HOT-COMMENTS.jsonl（按点赞排序）"
        spec["archetypes"] = hot
    for name, kinds, band in ARCH:
        if name in spec["archetypes"]:
            continue
        samples = pick(rows, kinds, band)
        if not samples:
            continue
        lens = sorted(s["len"] for s in samples)
        spec["archetypes"][name] = {
            "kinds": kinds, "band": list(band),
            "len_median": lens[len(lens) // 2],
            "emoji_rate": round(sum(1 for s in samples if s["emoji"]) / len(samples), 2),
            "samples": [s["text"] for s in samples],
        }
    os.makedirs(OUTDIR, exist_ok=True)
    # 弹幕池：从真实短评论里取"通用、不指名具体对象"的短句。
    # 弹幕的共同特征就是通用（"这段我看了两遍""哈哈哈哈哈"），
    # 指名道姓的句子放进弹幕会显得串场，所以把含专有名词风险的一律筛掉。
    dm, seen = [], set()
    for r in sorted(pas, key=lambda r: -(r.get("taste") or 0)):
        t = (r.get("text") or "").strip()
        if not (3 <= len(t) <= 14):
            continue
        if r.get("kind") not in ("打卡", "玩梗", "夸奖", "praise", "其他"):
            continue
        if re.search(r"[A-Za-z]{3,}|[?？]|http", t):
            continue
        # 弹幕要能放进任何一条视频：含"老师/助教/UP主/你们"的句子跨视频会串场
        if re.search(r"老师|助教|up主|UP主|up|你们|你|作者", t):
            continue
        # 弹幕池只收"脱离上下文也成立"的情绪/认同句：带领域名词的句子跨视频就串场
        # （2026-11-22 实测："屏幕里的游戏画面有点模糊啊" 被发到剪辑教程下）
        if re.search(r"游戏|软件|画面|剪辑|调色|镜头|视频|画质|素材|转场|配乐|音效|字幕", t):
            continue
        if not re.search(r"哈哈|笑|绝|好家伙|泪|哭|破防|学到|谢谢|舒服|牛|顶|妙|爱了|喜欢|支持|好听|好看|厉害|真香|救命|太|不错|可以", t):
            continue
        if t in seen:
            continue
        seen.add(t)
        dm.append(t)
        if len(dm) >= 60:
            break
    spec["danmaku"] = dm
    json.dump(spec, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[voice] 原型 %d 个 → %s" % (len(spec["archetypes"]), os.path.relpath(OUT, ROOT)))
    for k, v in spec["archetypes"].items():
        print("  %-9s 字数带 %s 中位 %d｜表情 %.0f%%｜样本 %d"
              % (k, v["band"], v["len_median"], 100 * v["emoji_rate"], len(v["samples"])))
        print("      例：%s" % v["samples"][0][:40])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""persona_mine.py — 从真人评论原文算出可执行的人设，而不是写一段形容词。

输入：cph4/fleet/social/corpus/mine/COMMENTS-MINE.jsonl（comment_harvest.py 落的盘）
      + SPLIT-v1.json（用实践台账把"我们 AI 写过的那几条"剔除后的结果）

只算本地能算的东西：字数分布、标点习惯、表情使用、语气词、问句比例、高频词。
不叫大模型——分布必须可复算，模型说的"温柔风趣"没法验收。

产出：
  HUMAN-PERSONA-v1.json   机读（给 prompt / 闸 / 自检用）
  HUMAN-PERSONA.md        人读（一眼看这人怎么说话）
  BAN-PHRASES-v1.json     我们自己发过、被判定"AI 味"的句子与词表

用法：
  python3 Tools/fleet/persona_mine.py            # 生成
  python3 Tools/fleet/persona_mine.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOC = os.path.join(ROOT, "cph4", "fleet", "social")
MINE = os.path.join(SOC, "corpus", "mine", "COMMENTS-MINE.jsonl")
SPLIT = os.path.join(SOC, "corpus", "mine", "SPLIT-v1.json")
OUT_JSON = os.path.join(SOC, "HUMAN-PERSONA-v1.json")
OUT_MD = os.path.join(SOC, "HUMAN-PERSONA.md")
OUT_BAN = os.path.join(SOC, "BAN-PHRASES-v1.json")

# 我们自己发出去、被 CEO 判"AI 味"的原句（来自 practice-log 的 post 记录）。
# 这张表是"实锚"，不是想象：每一条都是真发出去过的。
AI_SENT = [
    "教程太干货了，必须三连支持！",
    "教程干货满满，新手必看！",
    "保姆级教程太实用了，已收藏！",
    "剪辑太久了，别累着自己！",
    "你这教程比付费课还强十倍，我跟着学了一周，终于搞懂了才是真。",
    "学剪辑的，你的拉片干货太实用了。",
    "这教程干货满满，照着剪肯定有氛围感。",
    "新手别怕剪辑烂，跟着教程拍剪都能变大盘！",
    "期待看到从零开始的拍摄实战教程，三段式思维对营造氛围感真的太重要啦。",
    "重复意象与拆镜头，让剪辑更有故事感。",
    "阴天的情绪剪辑有质感，光影处理很到位。",
    "开头镜头晃得脚疼，这剪辑没必要啊。",
    "你真本末倒置，剪辑本该是为内容服务，而非炫技，这样教学算哪门手艺。",
    "别光理论，先从提升单节剪辑效率开始。",
    "镜头没给到那个转身的表情呢，配乐突然卡顿了吧，花絮剪辑里这场高光总得补全嘛。",
    "发烧时剪辑真帅，字体藏在黑屏里。",
    "S5 拍夜新街口真不错，求更多教程！",
]

# AI 腔词表：按"为什么像 AI"分组，写清判据，方便以后加。
BAN_WORDS = {
    "空夸词": ["干货满满", "干货", "保姆级", "三连", "已收藏", "太实用了", "必须", "真不错",
              "氛围感", "质感", "很到位", "绝了", "yyds", "宝藏", "封神"],
    "作文词": ["不仅", "而且", "从而", "综上", "总的来说", "值得一提", "令人", "极大地",
              "充分", "展现了", "体现了", "可谓", "堪称", "无疑", "赋予", "传递了"],
    "营销词": ["赋能", "维度", "层面", "闭环", "抓手", "打法", "干货分享", "强烈推荐"],
    "客服腔": ["宝子", "亲", "同学", "小可爱", "感谢支持", "感谢留言", "欢迎", "祝你",
              "希望可以帮到你", "有问题随时"],
}

PARTICLES = "呀啦呢吧哈哦嘛呗啊咯嘿噢"


def norm(t: str) -> str:
    return re.sub(r"\s+", "", t or "")


def clean(t: str) -> str:
    """去掉"回复 @某人 :"前缀——那是接口带的壳，不是他说话的方式。"""
    t = re.sub(r"^回复\s*@[^：:]{1,24}[：:]\s*", "", (t or "").strip())
    return t.strip()


def load_human():
    if os.path.exists(SPLIT):
        d = json.load(open(SPLIT, encoding="utf-8"))
        return [clean(r["text"]) for r in d.get("human") or [] if r.get("text")]
    rows = [json.loads(l) for l in open(MINE, encoding="utf-8") if l.strip()]
    ai = {norm(t) for t in AI_SENT}
    return [clean(r["text"]) for r in rows
            if r.get("text") and norm(r["text"]) not in ai]


IMG = re.compile(r"\[[^\[\]]{1,10}\]")


def analyze(texts):
    texts = [t for t in texts if t]
    lens = [len(IMG.sub("", t)) for t in texts]     # 字数不含表情
    n = len(texts)
    has_img = [bool(IMG.search(t)) for t in texts]
    end_period = sum(1 for t in texts if t.rstrip().endswith("。"))
    end_none = sum(1 for t in texts if not re.search(r"[。！？!?~～…]$", t.strip()))
    has_q = sum(1 for t in texts if re.search(r"[？?]", t))
    has_excl = sum(1 for t in texts if re.search(r"[！!]", t))
    multi = sum(1 for t in texts if "\n" in t)
    first_person = sum(1 for t in texts if "我" in t)
    second_person = sum(1 for t in texts if "你" in t)
    part_hit = sum(1 for t in texts if any(c in t for c in PARTICLES))
    imgs = Counter(m for t in texts for m in IMG.findall(t))
    # 高频 2-3 字词（去掉表情与标点）
    grams = Counter()
    for t in texts:
        s = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", IMG.sub("", t))
        for L in (2, 3):
            for i in range(len(s) - L + 1):
                grams[s[i:i + L]] += 1
    words = [(w, c) for w, c in grams.most_common(80) if c >= 2 and len(w) >= 2]

    q = statistics.quantiles(lens, n=4) if len(lens) >= 4 else [min(lens), statistics.median(lens), max(lens)]
    return {
        "n": n,
        "len": {"min": min(lens), "p25": round(q[0]), "median": round(statistics.median(lens)),
                "p75": round(q[2]), "max": max(lens)},
        "rate": {
            "emoji": round(sum(has_img) / n, 3),
            "end_period": round(end_period / n, 3),
            "no_end_punct": round(end_none / n, 3),
            "question": round(has_q / n, 3),
            "exclaim": round(has_excl / n, 3),
            "multiline": round(multi / n, 3),
            "first_person": round(first_person / n, 3),
            "second_person": round(second_person / n, 3),
            "particle": round(part_hit / n, 3),
        },
        "top_emoji": imgs.most_common(10),
        "top_words": words[:20],
        "examples": texts,
    }


def build_fewshot(a, k=6):
    """挑"最能代表他"的句子进 prompt：短、有具体对象、带他的口气。

    不用最长也不用最新——只用规则挑：含表情 / 含语气词 / 5-25 字 / 无问句。
    """
    scored = []
    for t in a["examples"]:
        body = IMG.sub("", t)
        L = len(body)
        if not (4 <= L <= 30) or "\n" in t:
            continue
        sc = 0
        sc += 2 if IMG.search(t) else 0
        sc += 2 if any(c in t for c in PARTICLES) else 0
        sc += 1 if re.search(r"[我你]", t) else 0
        sc -= 1 if re.search(r"[？?]", t) else 0
        scored.append((sc, -L, t))
    scored.sort(reverse=True)
    out = []
    seen = set()
    for sc, _, t in scored:
        if sc <= 0:
            continue
        k2 = norm(t)
        if k2 in seen:
            continue
        seen.add(k2)
        out.append(t)
        if len(out) >= k:
            break
    return out


def self_test():
    """负控：给定 3 句（1 句带表情短句、1 句长句、1 句问句），字数与比率必须算对。"""
    a = analyze(["很喜欢这首[星星眼]", "这是一句特别特别长的话用来把分布拉长一点看看中位数会不会跑偏掉", "封面是范伟老师是吧"])
    # 期望值是手数的：5 / 31 / 中位 9，不拿函数自己的输出当答案
    ok = (a["n"] == 3 and a["rate"]["emoji"] == 0.333 and a["len"]["min"] == 5
          and a["len"]["max"] == 31 and a["len"]["median"] == 9)
    # ban 闸负控：AI 句子必须被打中
    hit = [w for w in BAN_WORDS["空夸词"] if w in AI_SENT[0]]
    ok = ok and bool(hit)
    print(json.dumps({"self_test": "PASS" if ok else "FAIL", "stats": a["len"],
                      "ban_hit": hit}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    texts = load_human()
    st = analyze(texts)
    few = build_fewshot(st)
    persona = {
        "_why": "从真人原文算出的可执行人设。字数/标点/表情/语气词全是实测比例，不是形容词。",
        "version": "v1-20261120",
        "account": "acct1 大喵没鱼吃（CEO 本人手写）",
        "source": "cph4/fleet/social/corpus/mine/COMMENTS-MINE.jsonl（消息中心可回捞部分）",
        "bias": "只含被回复过的评论；无回复的短评不在内，故覆盖率不可用、风格可用",
        "n": st["n"],
        "len": st["len"],
        "rate": st["rate"],
        "top_emoji": st["top_emoji"],
        "top_words": st["top_words"],
        "write_rules": [
            "字数按 p25–p75 走（%d–%d 字），不要写满 35" % (st["len"]["p25"], st["len"]["p75"]),
            "句子常常不写句号（%.0f%% 无结束标点），别每句都收得整整齐齐" % (st["rate"]["no_end_punct"] * 100),
            "表情是常用件（%.0f%% 带 [xxx]），一条最多一个" % (st["rate"]["emoji"] * 100),
            "带具体对象：歌名/镜头/字幕/人物/机型，不写抽象的『质感/氛围』",
            "允许一句只有 2-4 个字（如『梯田』『又能白嫖了』），不要每条都完整句",
        ],
        "fewshot": few,
    }
    ban = {"_why": "真发出去过、被 CEO 判 AI 味的原句 + 按原因分组的词表", "version": "v1-20261120",
           "sentences": AI_SENT, "words": BAN_WORDS}

    os.makedirs(SOC, exist_ok=True)
    json.dump(persona, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(ban, open(OUT_BAN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# 老号真人评论人设（从 %d 条亲笔评论算出）" % st["n"], "",
          "> 来源：消息中心能回捞到的、被回复过的评论。无回复的短评拿不到，所以这是"
          "「风格可用、覆盖率不可用」的样本。", "",
          "## 一、字数", "",
          "| min | p25 | 中位 | p75 | max |", "|---|---|---|---|---|",
          "| %d | %d | %d | %d | %d |" % (st["len"]["min"], st["len"]["p25"],
                                          st["len"]["median"], st["len"]["p75"], st["len"]["max"]), "",
          "## 二、习惯（都是比例，可复算）", "",
          "| 习惯 | 比例 |", "|---|---|"]
    names = {"emoji": "带表情 [xxx]", "end_period": "以句号收尾", "no_end_punct": "完全不加结束标点",
             "question": "含问句", "exclaim": "含感叹号", "multiline": "多行", "first_person": "出现「我」",
             "second_person": "出现「你」", "particle": "带语气词（%s）" % PARTICLES}
    for k, v in st["rate"].items():
        md.append("| %s | %.0f%% |" % (names.get(k, k), v * 100))
    md += ["", "## 三、常用表情", "",
           "、".join("%s×%d" % (e, c) for e, c in st["top_emoji"]) or "（无）", "",
           "## 四、高频词", "",
           "、".join("%s(%d)" % (w, c) for w, c in st["top_words"][:15]) or "（样本不足）", "",
           "## 五、写稿规则（直接进 prompt / 闸）", ""]
    md += ["- " + r for r in persona["write_rules"]]
    md += ["", "## 六、进 prompt 的样句", ""] + ["- " + f for f in few]
    md += ["", "## 七、禁句（我们自己发过、被判 AI 味的）", ""] + ["- " + s for s in AI_SENT[:6]]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md) + "\n")

    print(json.dumps({"n": st["n"], "len": st["len"], "rate": st["rate"],
                      "fewshot": few, "out": [os.path.relpath(OUT_JSON, ROOT),
                                              os.path.relpath(OUT_MD, ROOT),
                                              os.path.relpath(OUT_BAN, ROOT)]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

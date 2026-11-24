#!/usr/bin/env python3
"""标题工坊：按 42 号 9 篇实测给标题打分，并做机械变形出备选。

为什么不做「智能生成」：标题的创意部分要模型或人来做，机造只会产出模板腔
（正是 CEO 反复否掉的「草率 / 太俗」）。所以这个工具只管两件事——
**卡形式**（把长度超了、没点名对象、用了标题党词这类硬伤先拦住）
和**给诊断**（逐维说明为什么不行），剩下的交给人挑。

三个硬闸（不过即判 FAIL）：
  H1 长度 16-32 字         实测中位 26，见 STYLE-42HAO-v1.md
  H2 点名 >=1 个可搜对象    沿用选题闸判据；真实标题平均只点名 1 个
  H3 不含禁词               AI 腔开头 / 标题党 / 禁承诺 / 抽象词

三个加分项（是分布，不是铁律）：
  B1 含数字或型号           9 篇里 6 篇有
  B2 落在三种真实句式之一    动作+现场物 / 数字规格+悬念 / 断言+对比收口
  B3 长度落在 20-28         最接近中位 26 的甜区

一个减分项：
  M1 以问号结尾             9 篇里只有 2 篇

用法：
  gzh_title.py --title "标题文字"
  gzh_title.py --in article.md          # 读第一个 H1
  gzh_title.py --topic A01              # 打分 + 出机械变体
  gzh_title.py --topic A01 --json
  gzh_title.py --self-test
退出码：0 硬闸全过 / 1 硬闸不过 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOPICS = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "TOPICS-v4.json")

LEN_RANGE = (16, 32)
LEN_SWEET = (20, 28)

AI_OPEN = ("随着", "在当今", "近年来", "众所周知", "在…的背景")
CLICKBAIT = ("震惊", "必看", "干货", "建议收藏", "太可怕", "竟然", "万万没想到",
             "不看后悔", "速看", "惊呆", "必读", "太卷了")
ABSTRACT = ("很多", "各种", "众多", "随着", "不断发展", "越来越", "一定程度上",
            "某种意义上", "等方面", "诸多", "一系列")
FALLBACK_PROMISES = ("我实测", "我跑了", "我拆了")

# 句式信号（从 42 号真实标题归纳，见 STYLE-42HAO-v1.md §二）
ACT_VERB = ("探访", "拆", "叠", "摆", "打开", "翻", "量", "画", "按", "点", "装", "跑")
CONTRAST = ("不只有", "应该怎么", "凭什么", "差在哪", "在哪", "为什么", "不在")

# 单位必须**紧跟数字**才算规格（否则「V8」「L3」这种型号名会被误判成带单位）
UNITS = ("TOPS", "nits", "kWh", "km/h", "kW", "Ah", "mm", "cm", "ms", "km", "Hz",
         "kg", "%", "元", "万", "亿", "公里", "度", "英寸", "寸", "层", "项", "倍")


def _num_unit_pattern():
    return r"(?<![\d.])\d[\d,]*(?:\.\d+)?\s*(?:" + "|".join(
        re.escape(u) for u in sorted(UNITS, key=len, reverse=True)) + r")"


def _load_promises():
    """禁承诺从选题库读，保持单一事实源；读不到才用兜底。"""
    try:
        doc = json.load(open(TOPICS, encoding="utf-8"))
        p = doc.get("forbidden_promises") or []
        return tuple(p) if p else FALLBACK_PROMISES
    except Exception:  # noqa: BLE001
        return FALLBACK_PROMISES


def _subjects(topic):
    """把 topic['subject'] 拆成可匹配的片段（长度 >=2）。"""
    out = []
    for s in (topic or {}).get("subject") or []:
        for p in re.split(r"[\s/、（）()]+", str(s)):
            p = p.strip()
            if len(p) >= 2:
                out.append(p)
                # 「新势力」这种复合词，再去掉末尾虚字做一次宽松匹配
                if len(p) >= 4:
                    out.append(p[: len(p) - 1])
    return out


def sentence_type(title):
    """判句式，返回 (类型, 说明) 或 (None, 原因)。"""
    has_num = bool(re.search(r"\d", title))
    has_unit = bool(re.search(_num_unit_pattern(), title))
    if has_num and has_unit:
        return "B", "数字规格+悬念"
    if re.search(r"[？?]\s*$", title) or any(w in title for w in CONTRAST):
        return "C", "断言+对比收口"
    if any(w in title for w in ACT_VERB):
        return "A", "具体动作+现场物"
    if has_num:
        return "B", "型号/数字+悬念（无单位）"
    return None, "三种句式都不像"


def score(title, topic=None):
    """返回 dict：title/len/hard{}/bonus{}/minus{}/ok/verdict。"""
    title = (title or "").strip()
    n = len(title)
    hard, bonus, minus = {}, {}, {}

    # --- 硬闸 ---
    lo, hi = LEN_RANGE
    hard["H1 长度"] = (lo <= n <= hi, f"{n} 字，要求 {lo}-{hi}（实测中位 26）")

    subs = _subjects(topic)
    if subs:
        hit = [s for s in subs if s.lower() in title.lower()]
        hard["H2 点名对象"] = (bool(hit),
                            f"命中 {hit[:2]}" if hit else f"未点名任何对象，候选：{subs[:4]}")
    else:
        hard["H2 点名对象"] = (None, "未给选题，跳过（只判形式）")

    promises = _load_promises()
    bad = []
    for w in AI_OPEN:
        if title.startswith(w) or w in title:
            bad.append(f"AI腔:{w}")
    for w in CLICKBAIT:
        if w in title:
            bad.append(f"标题党:{w}")
    for w in promises:
        if w in title:
            bad.append(f"禁承诺:{w}")
    for w in ABSTRACT:
        if w in title:
            bad.append(f"抽象词:{w}")
    hard["H3 无禁词"] = (not bad, "干净" if not bad else " ".join(bad))

    # --- 加分 ---
    bonus["B1 含数字/型号"] = (bool(re.search(r"\d", title)), "有" if re.search(r"\d", title) else "无（9 篇里 6 篇有）")
    st, why = sentence_type(title)
    bonus["B2 三种句式"] = (st is not None, f"{st} {why}" if st else why)
    slo, shi = LEN_SWEET
    bonus["B3 甜区长度"] = (slo <= n <= shi, f"{n} 字{'在' if slo <= n <= shi else '不在'} {slo}-{shi}")

    # --- 减分 ---
    q = bool(re.search(r"[？?]\s*$", title))
    minus["M1 问号结尾"] = (not q, "问号结尾（9 篇里只有 2 篇）" if q else "无")

    passed = [v[0] for v in hard.values() if v[0] is not None]
    ok = all(passed) if passed else True
    n_bonus = sum(1 for v in bonus.values() if v[0])
    n_minus = sum(1 for v in minus.values() if not v[0])
    return {
        "title": title, "len": n, "hard": hard, "bonus": bonus, "minus": minus,
        "ok": ok, "bonus_count": n_bonus, "minus_count": n_minus,
        "verdict": ("可用" if ok and n_bonus >= 2 else
                    "勉强" if ok else "不可用"),
    }


def variants(title, topic=None):
    """机械变形：只改形式不改判断，结果必须再打分。

    只做可逆、不编造内容的四种变形；填不满就跳过，不硬凑数量。
    """
    title = (title or "").strip()
    out = [("V1 原题", title)]

    # V2 数字前置：把标题里/场景里的数字短句提到最前
    num = None
    m = re.search(_num_unit_pattern(), title)
    if m:
        num = m.group(0).strip()
    elif topic:
        m2 = re.search(_num_unit_pattern(),
                       (topic.get("scene") or "") + " " + (topic.get("promise") or ""))
        if m2:
            num = m2.group(0).strip()
    if num and not title.startswith(num):
        rest = title.replace(num, "", 1).strip(" ，、：")
        cand = f"{num}，{rest}"
        if len(cand) <= LEN_RANGE[1] and rest:
            out.append(("V2 数字前置", cand))

    # V3 冒号化：前半变主题，后半变问题
    parts = re.split(r"[，,]", title, maxsplit=1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        cand = f"{parts[0].strip()}：{parts[1].strip()}"
        if len(cand) <= LEN_RANGE[1]:
            out.append(("V3 冒号化", cand))

    # V4 去问号：问句改陈述（不改字词，只删问号）
    if re.search(r"[？?]\s*$", title):
        cand = re.sub(r"[？?]\s*$", "", title).strip()
        if cand:
            out.append(("V4 去问号", cand))

    # 去重（同文字只留第一条，标注更具体的那个）
    seen, uniq = set(), []
    for tag, t in out:
        if t in seen:
            continue
        seen.add(t)
        uniq.append((tag, t))
    return uniq


def _fmt(r):
    lines = [f"标题: {r['title']}  ({r['len']} 字)"]
    for name, (ok, why) in r["hard"].items():
        mark = "PASS" if ok else ("SKIP" if ok is None else "FAIL")
        lines.append(f"  {name:14} {mark:4} {why}")
    for name, (ok, why) in r["bonus"].items():
        lines.append(f"  {name:14} {'+' if ok else '-'}    {why}")
    for name, (ok, why) in r["minus"].items():
        lines.append(f"  {name:14} {'OK' if ok else 'X'}    {why}")
    lines.append(f"→ 硬闸 {'全过' if r['ok'] else '不过'}"
                 f" · 加分 {r['bonus_count']}/3 · 减分 {r['minus_count']}"
                 f" → {r['verdict']}")
    return "\n".join(lines)


def _load_topic(tid):
    doc = json.load(open(TOPICS, encoding="utf-8"))
    for t in doc.get("topics") or []:
        if t.get("id") == tid:
            return t
    raise SystemExit(f"选题库里没有 {tid}")


def self_test():
    fails = []
    topic = {
        "subject": ["小米 YU7"],
        "scene": "把常用的三个功能藏进二层菜单，指尖在屏幕上找了三圈",
        "promise": "三个功能的位置 + 各自代价",
    }

    # 正控：真实标题（42 号原文）必须判可用
    good = "探访小米龙甲电池诞生地，这里有一座「影子工厂」"
    r = score(good)
    if not r["ok"]:
        fails.append(f"正控[真实标题] 被判不可用: {[k for k,v in r['hard'].items() if v[0] is False]}")

    # 负控 1：超长
    if score("这是一条特别特别长的标题" * 3)["hard"]["H1 长度"][0] is not False:
        fails.append("负控[超长] 未判红")

    # 负控 2：太短
    if score("小米 YU7")["hard"]["H1 长度"][0] is not False:
        fails.append("负控[太短] 未判红")

    # 负控 3：含给定选题却未点名对象
    if score("同一块屏，为什么有人点三下有人点五下", topic)["hard"]["H2 点名对象"][0] is not False:
        fails.append("负控[未点名对象] 未判红")

    # 负控 4：标题党
    if score("震惊！小米 YU7 中控屏竟然这样设计", topic)["hard"]["H3 无禁词"][0] is not False:
        fails.append("负控[标题党] 未判红")

    # 负控 5：禁承诺
    if score("我实测把小米 YU7 中控屏点了三百次", topic)["hard"]["H3 无禁词"][0] is not False:
        fails.append("负控[禁承诺] 未判红")

    # 负控 6：AI 腔开头
    if score("随着智能座舱不断发展，中控屏设计越来越重要", topic)["hard"]["H3 无禁词"][0] is not False:
        fails.append("负控[AI腔] 未判红")

    # 正控：点名对象能命中
    if score("小米 YU7 的中控屏：三个常用功能藏在第几层", topic)["hard"]["H2 点名对象"][0] is not True:
        fails.append("正控[点名对象] 未命中")

    # 句式识别（三种真实句式各一条）
    if sentence_type("3,000 TOPS 算力智驾芯片明年见")[0] != "B":
        fails.append("句式[B] 识别错误")
    if sentence_type("享界 V8 不只有第二排？家用 MPV 应该怎么造")[0] != "C":
        fails.append("句式[C] 识别错误")
    if sentence_type("把两页配置表叠在一起，红笔圈出七个差别")[0] != "A":
        fails.append("句式[A] 识别错误")

    # 变体：必须有原题，且都过得了长度
    vs = variants("小米 YU7 的中控屏，把最常用的三个功能藏到哪了", topic)
    if not vs or vs[0][0] != "V1 原题":
        fails.append("变体缺原题")
    if any(len(t) > LEN_RANGE[1] for _, t in vs):
        fails.append("变体产出超长标题")
    if len({t for _, t in vs}) != len(vs):
        fails.append("变体未去重")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 12/12  (2 正控 + 6 负控 + 3 句式 + 变体去重)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title")
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--topic")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    topic = _load_topic(a.topic) if a.topic else None

    title = a.title
    if not title and a.inp:
        md = open(a.inp, encoding="utf-8").read()
        m = re.search(r"^#\s+(.+)$", md, re.M)
        title = m.group(1).strip() if m else ""
    if not title and topic:
        title = topic.get("title", "")
    if not title:
        ap.print_help()
        return 1

    cands = variants(title, topic) if topic or a.title or a.inp else [("V1 原题", title)]
    scored = [(tag, score(t, topic)) for tag, t in cands]
    # 排序：硬闸过 > 加分多 > 减分少 > 长度更接近 26
    scored.sort(key=lambda x: (not x[1]["ok"], -x[1]["bonus_count"],
                               x[1]["minus_count"], abs(x[1]["len"] - 26)))

    if a.json:
        print(json.dumps([{"tag": tag, **r} for tag, r in scored],
                         ensure_ascii=False, indent=1))
        return 0 if scored[0][1]["ok"] else 1

    print(f"候选 {len(scored)} 条（机造变体只改形式，判断仍需人/模型给）\n")
    for tag, r in scored:
        print(f"[{tag}]")
        print(_fmt(r))
        print()
    best = scored[0][1]
    print(f"首选: {best['title']}")
    return 0 if best["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

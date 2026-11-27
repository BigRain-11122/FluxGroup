#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh_authority_check.py — 拦「编标准」与「编履历」。

为什么单独一道闸（2026-11-27 实测）：9B 出一篇深色模式稿，凭空写了
  ISO 15008:2017「车机必须维持高对比度」
  SAE J3016「L2+ 要求信息呈现清晰无误」
  NHTSA「触控目标不小于屏宽 1.5%，外扩 8px」
  韦伯对比度「>60% 安全区间」
四条全是编的；而 AI 指纹闸给它 12/100（阈值 45）判"像人写的"。
另外它写了「我曾参与某项目的视觉迭代」「我的团队在重构某旗舰车型」——
人设明确禁止编项目经历。

两件分开判，因为它们伤的是不同的东西：
  编标准 → 打假风险（发出去被人贴原文）
  编履历 → 人设崩塌（作者本人是正职设计师，一问就露）

判据：
  1 标准编号必须在 AUTHORITY-WHITELIST.json 里，否则 FAIL（不是 WARN）
  2 履历句式一律 FAIL，无论真假——要写就人来写，模型不许替你回忆
  3 三处以上 FAIL 视为整篇不可用（rc=2）

用法：
  python3 Tools/fleet/gzh_authority_check.py --in article.md
  python3 Tools/fleet/gzh_authority_check.py --in article.md --json
  python3 Tools/fleet/gzh_authority_check.py --self-test
退出码：0 通过 / 1 有问题 / 4 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GZH = os.path.join(ROOT, "cph4", "fleet", "social", "gzh")
WHITELIST = os.path.join(GZH, "AUTHORITY-WHITELIST.json")

# 标准/法规编号：ISO 15008:2017 / SAE J3016 / GB/T 1234 / UN R155 / FMVSS 111 ...
STD = re.compile(
    r"\b(ISO|IEC|SAE|JIS|DIN|NHTSA|FMVSS|UN\s?R|ECE|GB/T|GB|QC/T|JJF|EN)\s*[- ]?\s*"
    r"([A-Z]?\d[\w.:/\-]*)", re.I)

# 履历编造：模型最爱用的第一人称权威句
RESUME = re.compile(
    r"我曾(?:经)?参与|我曾经参与|我的团队|我们团队|我司|我所在的公司|"
    r"我在某(?:个)?项目|我主导|我负责过|我带队|我的项目|我手上(?:的)?项目|"
    r"我做过(?:某|一)?(?:个)?(?:旗舰|量产|主机厂)")

# 假精度阈值：感知/安全语境里的小数阈值，最容易张口就来
FAKE_PRECISION = re.compile(
    r"\d+\.\d{2,}\s*(?:秒|s|%|倍|px|nits|cd/m2|坎德拉)")


def _norm(s):
    return re.sub(r"\s+", " ", s).strip().upper()


def load_whitelist(path=None):
    try:
        d = json.load(open(path or WHITELIST, encoding="utf-8"))
        return {_norm(e["id"]) for e in d.get("entries") or []}
    except Exception:
        return set()


def _sentence_at(text, pos, span=40):
    a = max(0, text.rfind("。", 0, pos) + 1)
    b = text.find("。", pos)
    b = len(text) if b < 0 else b + 1
    s = text[a:b].strip()
    return (s[:span] + "…") if len(s) > span else s


def check(md, wl=None):
    """返回 (fails, warns)。纯函数，自检可直接喂文本。"""
    wl = load_whitelist() if wl is None else wl
    fails, warns = [], []

    seen = set()
    for m in STD.finditer(md):
        key = _norm("%s %s" % (m.group(1), m.group(2)))
        # 白名单按前缀匹配：ISO 15008:2017 与 ISO 15008 视为同一条
        base = re.sub(r"[:：].*$", "", key).strip()
        if any(base == w or base.startswith(w + " ") or w.startswith(base + " ") for w in wl):
            continue
        if base in seen:
            continue
        seen.add(base)
        fails.append("未核验的标准编号 %s｜%s" % (key, _sentence_at(md, m.start())))

    for m in RESUME.finditer(md):
        fails.append("编造履历「%s」｜%s" % (m.group(0), _sentence_at(md, m.start())))

    for m in FAKE_PRECISION.finditer(md):
        warns.append("两位以上小数的阈值 %s（要么标明出处，要么降精度）｜%s"
                     % (m.group(0), _sentence_at(md, m.start())))

    return fails, warns


def self_test():
    fails = []
    wl = load_whitelist()

    good = ("# 测题\n\n正文提到 WCAG 2.1 的 4.5:1，这是有出处的。\n"
            "我在自己的项目里改过一版色阶，代价是多花了两周。\n")
    f, w = check(good, wl)
    if f:
        fails.append("正样被判红：%s" % f[:2])

    bad_std = "根据 ISO 15008:2017 标准，车机必须维持高对比度。\n"
    f, _ = check(bad_std, wl)
    if not any("ISO" in x for x in f):
        fails.append("负控失效：编造标准 ISO 15008 没被抓到")

    bad_res = "我曾参与某项目的视觉迭代，最终重做了整块板。\n"
    f, _ = check(bad_res, wl)
    if not any("履历" in x for x in f):
        fails.append("负控失效：编造履历没被抓到")

    # 白名单本身要能过：WCAG 2.1 不该被判
    f, _ = check("对比度按 WCAG 2.1 取 4.5:1。\n", wl)
    if f:
        fails.append("白名单条目 WCAG 2.1 被误杀")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for x in fails:
            print("  -", x, file=sys.stderr)
        return 4
    print("SELF-TEST OK 4/4（正样通过/编标准能红/编履历能红/白名单不误杀）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=False)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.inp:
        ap.error("--in 必填")

    md = open(a.inp, encoding="utf-8").read()
    fails, warns = check(md)
    if a.json:
        print(json.dumps({"fails": fails, "warns": warns}, ensure_ascii=False, indent=1))
        return 1 if fails else 0

    print("权威闸：FAIL %d / WARN %d" % (len(fails), len(warns)))
    for x in fails:
        print("  FAIL %s" % x)
    for x in warns:
        print("  WARN %s" % x)
    if fails:
        print("\n处置：编造的标准与履历没有「补源」这条路——删掉，或者由人工换成真事再写。")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

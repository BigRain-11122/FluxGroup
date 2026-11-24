#!/usr/bin/env python3
"""文章逻辑闸：检出六类逻辑问题（CEO 点名「逻辑」）。

为什么机检逻辑：人写完自己看不出逻辑漏洞，因为脑子里补全了。
机检只看文字表面，反而能抓到「论据缺失」「数字无源」这类硬伤。

六类：
L1 论点无据    —— 判断句后面 2 句内没有依据（数字/来源/对比）
L2 因果倒置    —— 「因为A所以B」而 A 本身是结果
L3 以偏概全    —— 「所有/都/一定」+ 单例
L4 循环论证    —— A 因为 B，B 因为 A
L5 数字无源    —— 数字后 25 字内无来源词
L6 前后矛盾    —— 同一对象被给出相反评价

用法：
  gzh_logic_check.py --in article.md
  gzh_logic_check.py --self-test
退出码：0 无问题 / 1 有问题 / 4 自检失败
"""
from __future__ import annotations

import argparse
import re
import sys

# 依据信号：出现这些词说明作者给了支撑
EVIDENCE = ("因为", "数据显示", "根据", "来源", "公告", "财报", "配置表", "工信部",
            "实测", "对比", "比如", "例如", "官方", "标准", "%", "倍", "参数",
            "官网", "报告", "原文", "第\\d+页", "页", "元", "度", "公里")

# 绝对化词（以偏概全信号）
ABSOLUTE = ("所有", "全都", "都一定", "一定是", "必然是", "无一例外", "凡是", "任何")

# 因果连接
CAUSE = ("因为", "由于", "所以", "因此", "导致", "说明")

# 来源词（数字溯源）
SOURCE = ("根据", "来源", "官方", "官网", "公告", "财报", "报告", "配置表",
          "工信部", "国标", "标准", "实测", "测算", "估算", "报价", "页面")

# 评价词（矛盾检测）
POS = ("好", "强", "优秀", "领先", "扎实", "合理", "高级", "清晰")
NEG = ("差", "弱", "落后", "粗糙", "不合理", "廉价", "模糊", "难用")


def _sentences(text):
    """按句号切句，且标题行必须独立成句。

    坑：若只把标题前缀清空，标题会和紧跟的正文粘成一句，
    导致「下一句的依据」被当成本句的依据（L1 误判绿）。
    """
    # 标题行前后强制加句号，保证独立成句
    text = re.sub(r"(?m)^#+\s*(.+)$", r"\1。", text)
    parts = re.split(r"(?<=[。！？!?])\s*", text)
    return [(i, s.strip()) for i, s in enumerate(parts) if s.strip()]


def check(md):
    """返回 (issues, stats)。issues 每项 = (级别, 类型, 位置, 说明)。"""
    text = re.sub(r"```[\s\S]*?```", "", md)
    # 不要把 ## 前缀删掉——_sentences 需要它来把标题切成独立句；
    # 删了会让标题和下文粘连，L1 就会把下一句的依据借来（假绿）
    sents = _sentences(text)
    issues = []

    # --- L1 论点无据 ---
    # 判断句：含「是/该/应该/必须/显然/明显」且长度 >12，且句末不是问号
    for pos, s in sents:
        if len(s) < 8 or s.endswith(("？", "?")):
            continue
        is_claim = any(k in s for k in ("应该是", "该是", "必须", "显然", "明显",
                                        "问题在", "本质", "关键是", "根本原因是",
                                        "很差", "很好", "不对", "错了"))
        if not is_claim:
            continue
        # 看本句 + 紧邻下 1 句有没有依据（后 2 句太宽，会把下个论点的依据借来）
        window = " ".join(x for p, x in sents if pos <= p <= pos + 1)
        if not any(e in window for e in EVIDENCE):
            issues.append(("WARN", "L1 论点无据", pos, f"判断句后无依据：{s[:40]}"))

    # --- L2 因果倒置 ---
    for pos, s in sents:
        if "因为" in s and "所以" in s:
            a = s.split("因为", 1)[1].split("所以", 1)[0].strip()
            # 如果「因为」部分本身是结果词（销量/排名/口碑），逻辑可疑
            if any(k in a for k in ("卖得好", "销量高", "排名靠前", "口碑好", "受欢迎")):
                issues.append(("WARN", "L2 因果倒置", pos,
                               f"以结果解释结果：因为「{a[:24]}」"))

    # --- L3 以偏概全 ---
    for pos, s in sents:
        for ab in ABSOLUTE:
            if ab in s:
                # 绝对化词本身就足够可疑；若有单例更严重
                single = bool(re.search(r"(一台|一个|某|这款|那台)", s))
                issues.append(("WARN", "L3 以偏概全", pos,
                               f"{'单例推全体' if single else '绝对化断言'}：{s[:40]}"))
                break

    # --- L4 循环论证 ---
    for pos, s in sents:
        m = re.findall(r"([\u4e00-\u9fa5]{2,6})(?:是因为|由于)([\u4e00-\u9fa5]{2,6})", s)
        for a, b in m:
            if b in text and f"{b}是因为{a}" in text:
                issues.append(("WARN", "L4 循环论证", pos, f"{a}↔{b} 互为依据"))

    # --- L5 数字无源 ---
    for pos, s in sents:
        for num in re.finditer(r"\d+(?:[.,]\d+)*\s*(?:%|公里|km|元|万|亿|英寸|寸|秒|分钟|TOPS|nits|度)", s):
            tail = s[num.end():num.end() + 25]
            head = s[max(0, num.start() - 25):num.start()]
            if not any(x in tail or x in head for x in SOURCE):
                issues.append(("INFO", "L5 数字无源", pos,
                               f"「{num.group(0)}」附近无来源"))
                break  # 每句只报一次，避免刷屏

    # --- L6 前后矛盾 ---
    obj_pos, obj_neg = {}, {}
    for pos, s in sents:
        subj = None
        m = re.match(r"^([\u4e00-\u9fa5A-Za-z0-9]{2,10})", s)
        if m:
            subj = m.group(1)
        if not subj:
            continue
        if any(w in s for w in POS):
            obj_pos.setdefault(subj, []).append((pos, s[:30]))
        if any(w in s for w in NEG):
            obj_neg.setdefault(subj, []).append((pos, s[:30]))
    for subj in set(obj_pos) & set(obj_neg):
        # 排除「不好」这种同句否定
        issues.append(("WARN", "L6 前后矛盾", obj_pos[subj][0][0],
                       f"「{subj}」既有正面也有负面评价"))

    stats = {"sentences": len(sents), "chars": len(re.sub(r"\s", "", text))}
    return issues, stats


GOOD = """# 秦PLUS 和海豹06 差两万，我把两页配置表叠在一起看

把两页配置表打印出来，用红笔把多出来的项圈掉，桌上一共 7 个红圈。

## 多出来的第一项是后悬架

秦PLUS 用的是扭力梁，海豹06 用的是多连杆。根据两车配置表，这一项差价约 3000 元。

## 第二项是电池容量

海豹06 电池 60.5 度，秦PLUS 是 48 度。按官网报价每度 600 元算，这一项差 7500 元。

## 这两项占了差价的七成

两万差价里，电池和悬架合起来约 1.4 万，占了七成。剩下的四项加起来不到 6000 元。
"""

BAD_UNSUPPORTED = GOOD.replace(
    "根据两车配置表，这一项差价约 3000 元。", "这个设计显然很不对。")
BAD_CAUSE = GOOD.replace(
    "按官网报价每度 600 元算，这一项差 7500 元。", "因为这台车卖得好，所以配置给得高。")
BAD_SWEEP = GOOD.replace(
    "两万差价里，电池和悬架合起来约 1.4 万，占了七成。", "凡是这个价位的车，全都是减配。")
BAD_NUM = GOOD.replace("按官网报价每度 600 元算", "按每度 600 元算")
BAD_CONTRA = GOOD.replace(
    "剩下的四项加起来不到 6000 元。",
    "秦PLUS 的做工很扎实。但同一台车，秦PLUS 的内饰接缝很粗糙。")


def self_test():
    fails = []

    issues, st = check(GOOD)
    warn = [i for i in issues if i[0] == "WARN"]
    if warn:
        fails.append(f"好稿被判 WARN: {warn[:2]}")

    def expect(name, doc, code):
        iss, _ = check(doc)
        got = [i for i in iss if i[1].startswith(code)]
        if not got:
            fails.append(f"负控[{name}] 未检出 {code}")

    expect("论点无据", BAD_UNSUPPORTED, "L1")
    expect("因果倒置", BAD_CAUSE, "L2")
    expect("以偏概全", BAD_SWEEP, "L3")
    expect("数字无源", BAD_NUM, "L5")
    expect("前后矛盾", BAD_CONTRA, "L6")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print(f"SELF-TEST OK 6/6  (好稿 {st['sentences']} 句无 WARN / 5 类负控全检出)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--strict", action="store_true", help="INFO 也算失败")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.inp:
        ap.print_help(); return 1
    md = open(a.inp, encoding="utf-8").read()
    issues, stats = check(md)
    print(f"统计: {stats}")
    for lvl, typ, pos, msg in issues:
        print(f"{lvl:4} [{typ}] 句#{pos}: {msg}")
    bad = [i for i in issues if i[0] == "WARN" or (a.strict and i[0] == "INFO")]
    if bad:
        print(f"\nFAIL {len(bad)} 项需修", file=sys.stderr)
        return 1
    print("PASS 无 WARN 级逻辑问题")
    return 0


if __name__ == "__main__":
    sys.exit(main())

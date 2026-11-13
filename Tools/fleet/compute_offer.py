#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compute_offer.py - 算力产品线的三段产物：商品定义 / 报价 / 对外物料。

Why（2026-11-12/13）：PROD-BIGCOMPUTE-OFFER 的三道工序一直是 TOOL-PENDING，但它的
原料早就在盘上（MODEL-COMPUTE 的端点阶梯、STATIONS 的硬件、BRAIN-STRESS 的实测吞吐）。
缺的不是数据，是一个把它变成可验收产物的工序。

三条硬边界（CEO 2026-10-2x 对外口径）：
  * **不擅自定价**：只给成本项与毛利公式；价格空着等 CEO 拍板，机器不填数字。
  * **不对外承诺**：全文 DRAFT；不写 SLA/时效保证；不写"最快/保证/包过"这类词。
  * **缺数据就说缺**：电费、折旧、带宽没有口径就写"待财务口径"，绝不填 0 冒充。

用法：
  python3 Tools/fleet/compute_offer.py --stage all
  python3 Tools/fleet/compute_offer.py --stage quote
  python3 Tools/fleet/compute_offer.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(FLEET, "out", "bigcompute")

# 对外承诺词：命中就不许落盘（负控见 self_test）。
PROMISE_WORDS = ("保证", "承诺", "包过", "最快", "准时交付", "SLA 保障", "100%", "绝不")


def _j(name):
    try:
        with open(os.path.join(FLEET, name), encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def tiers():
    """三档服务：只描述能力边界，不写价格与承诺。"""
    return [
        {"id": "T1", "name": "文本处理（分类/抽取/摘要/写卡）",
         "model_tier": "本机轻模型 4B–8B",
         "can": ["按固定类别归类", "从长文里抽字段", "压成一句摘要", "给产出打完成度"],
         "cannot": ["不做长篇创作", "不做多轮辩论", "不替代人做判断（结论仍归人）"],
         "where": "每台机器本地（断网可用）",
         "deliver": "JSON 结果 + 规则复核记录"},
        {"id": "T2", "name": "批量生成（文案/剧本/评审稿）",
         "model_tier": "算力大脑 32B 档",
         "can": ["按模板批量写文案", "剧本/分镜草稿", "多席评审的初评文字"],
         "cannot": ["不直接对外发布（发布权在 CEO）", "不保证事实准确性（需规则复核）",
                    "不做图像/视频生成"],
         "where": "算力大脑（未入网前在具备显存的机器上跑）",
         "deliver": "草稿文件 + 生成参数 + 自检报告"},
        {"id": "T3", "name": "评测与质检（多席打分/闸判定）",
         "model_tier": "14B 档，多席并行",
         "can": ["按 rubric 打分", "找出违规/风险点", "同一产物多次评审求一致率"],
         "cannot": ["不替代法务结论", "不对最终上线负责（闸是辅助）"],
         "where": "算力大脑或显存足够的工位",
         "deliver": "评分表 + 否决项 + 一致性记录"},
    ]


def cost_items():
    """成本项：有口径的给式子，没口径的明确写缺。"""
    return [
        {"item": "机器折旧", "basis": "按各机购入价与折旧年限摊到小时",
         "status": "待财务口径", "why": "STATIONS 只有硬件型号，没有购入价"},
        {"item": "电费", "basis": "功率 × 运行小时 × 电价",
         "status": "待财务口径", "why": "无电表读数，不按经验值填"},
        {"item": "模型算力占用", "basis": "单次推理时长 × 占卡比例",
         "status": "可测", "why": "BRAIN-STRESS 有实测吞吐，可按任务量折算"},
        {"item": "人力复核", "basis": "人判件数量 × 单件分钟",
         "status": "可估", "why": "回执里 judge=manual 的件数可直接数"},
    ]


def build_offer(mc=None, stations=None):
    mc = mc or {}
    gw = {g.get("id"): g for g in (mc.get("gateways") or [])}
    L = ["# 算力服务 · 商品定义（DRAFT · 需 CEO 确认）", ""]
    L.append("> 本文是机器生成的草稿：只写能力与边界，不含价格、不含对外承诺。")
    L.append("> 价格见 `quote.md`；对外物料见 `assets/`。")
    L += ["", "## 一、三档服务", ""]
    for t in tiers():
        L += ["### %s %s" % (t["id"], t["name"]), "",
              "- 模型档位：%s" % t["model_tier"],
              "- 跑在哪：%s" % t["where"],
              "- 交付形态：%s" % t["deliver"],
              "- 能做什么："]
        L += ["  - " + x for x in t["can"]]
        L += ["- **不做什么（边界）**："]
        L += ["  - " + x for x in t["cannot"]]
        L.append("")
    L += ["## 二、依赖与前提", ""]
    brain = gw.get("brain") or {}
    if brain.get("url"):
        L.append("- 算力大脑已入网：`%s`（order=%s）" % (brain.get("url"), brain.get("order")))
    else:
        L.append("- 算力大脑**未入网**：`%s` —— T2/T3 目前只能在具备显存的工位上跑，"
                 "产能受限是事实，不写成「即将可用」。" % (brain.get("pending") or "url 为空"))
    L.append("- 本机档（T1）在每台机器独立完成，断网可用。")
    L.append("- 全部产出默认落盘为草稿，对外发布权在 CEO。")
    L += ["", "## 三、交付边界（写清，避免误解）", "",
          "1. 不承诺时效：任务按队列与机器状态排，不接「几小时必出」。",
          "2. 不承诺结果正确：机器产出必须过规则复核与人判，闸只做初筛。",
          "3. 不做数据托管：产出落各自工位磁盘，主控只存清单与哈希。",
          "4. 涉法务、涉肖像、涉平台规则的内容，一律人判后才可对外。"]
    _assert_no_promise("\n".join(L))
    return "\n".join(L) + "\n"


def build_quote(mc=None):
    mc = mc or {}
    L = ["# 算力服务 · 报价（DRAFT · 价格留空，等 CEO 拍板）", ""]
    L.append("> 机器不填价格。本文只给成本项、毛利公式与建议区间的方法；"
             "具体数字由 CEO 决定后回填。")
    L += ["", "## 一、成本项", "", "| 项 | 口径 | 状态 | 说明 |", "|---|---|---|---|"]
    for c in cost_items():
        L.append("| %s | %s | %s | %s |" % (c["item"], c["basis"], c["status"], c["why"]))
    L += ["", "## 二、毛利口径（唯一算法）", "",
          "```",
          "单件成本 = 机器折旧 + 电费 + 算力占用 + 人力复核",
          "毛利率   = (单价 - 单件成本) / 单价",
          "```",
          "",
          "口径只此一处：报价单、物料、对外话术都引用这条公式，不许各写一份。",
          "",
          "## 三、定价（留空，人不填机器不猜）", "",
          "| 档 | 建议区间依据 | 单价（CEO 填） |",
          "|---|---|---|",
          "| T1 文本处理 | 按千次调用折算（算力占用可测） |  |",
          "| T2 批量生成 | 按千字产出折算（大脑未入网前成本偏高） |  |",
          "| T3 评测质检 | 按席位×产物折算（多席并行，占用翻倍） |  |",
          "",
          "## 四、缺什么（不填 0 冒充）", ""]
    miss = [c for c in cost_items() if c["status"].startswith("待")]
    for c in miss:
        L.append("- %s：%s" % (c["item"], c["why"]))
    if not miss:
        L.append("- （无）")
    _assert_no_promise("\n".join(L))
    return "\n".join(L) + "\n"


def build_assets():
    L = ["# 算力服务 · 一页纸（DRAFT）", "",
         "## 我们做什么", "",
         "- 文本处理：分类、抽取、摘要、写卡（本机跑，断网可用）",
         "- 批量生成：文案、剧本、评审初稿（按模板，可复核）",
         "- 评测质检：按 rubric 打分、找风险点、算一致性",
         "",
         "## 我们不做什么", "",
         "- 不承诺时效、不承诺结果正确（闸是初筛，人判才算数）",
         "- 不做图像/视频生成（那走视觉工位）",
         "- 不代替法务与平台规则判断",
         "",
         "## 交付", "",
         "- 产物 + 生成参数 + 自检报告 + 复核记录",
         "- 默认草稿，对外发布权在 CEO",
         "", "## 价格", "", "- 见 `quote.md`（由 CEO 定，机器不填）"]
    _assert_no_promise("\n".join(L))
    return "\n".join(L) + "\n"


NEG_CONTEXT = ("不", "无", "禁止", "杜绝", "避免", "零", "没有", "不得", "勿")


def _assert_no_promise(text):
    """对外承诺词命中即拒绝落盘——这是闸，不是文案建议。

    必须做否定语境识别：本文自己写的「不承诺时效」「不保证准确」里含"承诺/保证"，
    一刀切会把正确表述判成违规（2026-11-13 实测：首版直接拒绝了自己的产物）。
    判据=命中词前 6 字里出现否定词即跳过。
    """
    hit = []
    for w in PROMISE_WORDS:
        for m in re.finditer(re.escape(w), text):
            pre = text[max(0, m.start() - 6):m.start()]
            if any(n in pre for n in NEG_CONTEXT):
                continue
            hit.append(w)
            break
    if hit:
        raise SystemExit("拒绝落盘：出现对外承诺词 %s（只写边界，不写保证）" % hit)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["all", "offer", "quote", "assets"])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    mc, st = _j("MODEL-COMPUTE.json"), _j("STATIONS.json")
    made = []
    if a.stage in ("all", "offer"):
        p = os.path.join(OUT, "offer.md")
        write(p, build_offer(mc, st))
        made.append(p)
    if a.stage in ("all", "quote"):
        p = os.path.join(OUT, "quote.md")
        write(p, build_quote(mc))
        made.append(p)
    if a.stage in ("all", "assets"):
        p = os.path.join(OUT, "assets", "onepager.md")
        write(p, build_assets())
        made.append(p)
    print("已生成：%s" % "、".join(os.path.relpath(x, ROOT) for x in made))
    return 0


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    o, q, s = build_offer(), build_quote(), build_assets()
    chk("三档都在商品定义里", all(t["id"] in o for t in tiers()))
    chk("每档都写了「不做什么」", o.count("不做什么") >= 3, o.count("不做什么"))
    chk("报价里价格列留空（机器不填）", "|  |" in q)
    chk("报价写明缺什么（不填 0 冒充）", "待财务口径" in q)
    chk("毛利公式只有一条", q.count("毛利率   =") == 1)
    chk("全文标 DRAFT", all("DRAFT" in x for x in (o, q, s)))
    try:
        _assert_no_promise(o + q + s)
        clean = True
    except SystemExit:
        clean = False
    chk("产物本身不含对外承诺（否定语境不算）", clean)
    # 负控：塞一句"我们保证 100% 准时交付"必须被闸拦下
    try:
        _assert_no_promise(o + "我们保证 100% 准时交付")
        chk("负控：承诺词必须被拦", False)
    except SystemExit:
        chk("负控：承诺词必须被拦", True)
    _old = os.environ.get("MODEL_COMPUTE_FAKE")
    chk("大脑未入网时明说受限（不写成即将可用）",
        "未入网" in build_offer({"gateways": [{"id": "brain", "url": None,
                                               "pending": "未入网：tailnet IP 未分配"}]}))
    chk("大脑已入网时写出 url",
        "http://x:11434" in build_offer({"gateways": [{"id": "brain", "url": "http://x:11434",
                                                      "order": 1}]}))
    print("\n[compute_offer] %d/%d" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())

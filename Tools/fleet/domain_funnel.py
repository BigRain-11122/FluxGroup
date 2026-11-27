#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""domain_funnel.py - BigDomain 的漏斗表（每一步填盘上真数，没有就写 null）。

为什么（2026-11-03 · COMPANY-DESIGN-PLAN 第 8 位）：
BigDomain 卡在"上游没东西可卖"，很容易退化成一句"等上游"。但漏斗本身就能算：
谁能卖、卖到哪一步、卡在哪一环。全部取盘上事实，缺数据写 null 并标注来源缺口——
0 和 null 都是结论，"进行中"不是。

来源：queue（成片/包/结论卡）、asset 索引、compute 台账、issue 数据（无 → null）。

用法：python3 Tools/fleet/domain_funnel.py [--json] [--out PATH]
Exit: 0 正常。
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
DEFAULT_OUT = os.path.join(FLEET, "company", "bigdomain", "FUNNEL-v1.json")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def jlines(p):
    out = []
    try:
        for line in open(p, encoding="utf-8-sig"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)

    q = jlines(os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl"))
    asset = jload(os.path.join(FLEET, "lib", "ASSET-INDEX.json"), {}) or {}
    ledger = jload(os.path.join(FLEET, "company", "bigcompute", "CAPACITY-LEDGER-v1.json"), {}) or {}
    org = jload(os.path.join(FLEET, "company", "ORG-REGISTRY.json"), {}) or {}
    ob = {o.get("id"): o for o in (org.get("orgs") or [])}

    def done_of(line):
        return len([c for c in q if c.get("line") == line and c.get("state") == "DONE"])

    # 上游可卖物：只认"盘上有、能对外"的判据字段，不认"在推进"
    upstream = [
        {"source": "BigStream 成片", "line": "bigstream-mv", "done_cards": done_of("bigstream-mv"),
         "gate": "交付闸 v721 真判 FAIL（重复上屏/近静止/死镜），未过",
         "sellable": False,
         "why": "有母版但闸未过，且发布位在 CEO 手上"},
        {"source": "Biggame 可玩包", "line": "biggame", "done_cards": done_of("biggame"),
         "gate": "产品四闸（真包实跑/首启30秒/性能档/盲评）全空白",
         "sellable": False, "why": "包不在本机，四闸未跑"},
        {"source": "BigMoney 结论+信号", "line": "bigmoney", "done_cards": done_of("bigmoney"),
         "gate": "conclusion/quote/quality 回执各 0 份；signal CSV 从未生成",
         "sellable": False, "why": "可复算结论未出，卖点（四件齐）无法自证"},
        {"source": "FluxVerse 城市", "line": "fluxverse",
         "done_cards": done_of("fluxverse"), "gate": "四仓不在本机，无投影件",
         "sellable": False, "why": "对外形态未定"},
    ]
    slots = (ledger.get("totals") or {}).get("sellable_slots_now")
    funnel = [
        {"step": "1 内容触达（粉丝/播放）", "value": None,
         "source": "缺：无任何平台账号数据接入（账号在 CEO 手上）",
         "why_null": "未接数据源，不能写 0 冒充事实"},
        {"step": "2 私域承接（咨询/群）", "value": None,
         "source": "缺：无私域工具与记录",
         "why_null": "同上"},
        {"step": "3 可卖物（成片/包/结论/城市）", "value": 0,
         "source": "上游四家逐个见 upstream[]，判据都未过",
         "why_null": None},
        {"step": "4 付费转化（算力包 19.9）", "value": 0,
         "source": "无定价分母之外的成交；台账见 CAPACITY-LEDGER-v1.json",
         "why_null": None},
        {"step": "5 复购", "value": 0, "source": "无首购即无复购", "why_null": None},
    ]
    res = {
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "company": "bigdomain",
        "thesis": ("漏斗第 3 环为 0：四家上游的可卖物一个都没过闸。故本司当前唯一真产物是"
                   "「哪一环断了」的机读结论，不是商业模型。"),
        "funnel": funnel,
        "upstream": upstream,
        "capacity": {"sellable_slots_now": slots,
                     "note": "算力包是唯一有分母的候选，但需 BigCompute 定价与需求验证"},
        "kill_criteria_hit": None,
        "next_actions": [
            "把第 1/2 环的数据源补上（或明确写「不做私域」，二选一，不留空）",
            "上游任一家过闸后，本司再出报价草稿；未过闸不出价",
        ],
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    print("BigDomain 漏斗（盘上事实）")
    for f_ in funnel:
        v = "null" if f_["value"] is None else f_["value"]
        print("  %-28s %-6s %s" % (f_["step"], v, f_["source"]))
    print("  上游可卖物：%d 家 / 过闸 %d 家"
          % (len(upstream), len([u for u in upstream if u["sellable"]])))
    print("-> %s" % os.path.relpath(a.out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
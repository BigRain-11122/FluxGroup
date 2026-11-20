#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单位经济计算器：售价/折扣/分成/税/退款 → 每份净收入与目标所需份数。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cph4" / "fleet" / "game-v2" / "market"

# 默认值必须逐项等于宪法 C-12，否则算出来的门槛会比法低。改动先改宪法再改这里。
PRICE = 14.99
FX = 7.15
REGIONAL = 0.75          # C-12 区域系数
STEAM_CUT = 0.30
TAX = 0.20               # C-12 税基线
REFUND = 0.15            # C-12 退款基线
COST = 11_000            # C-12 单款成本上限
TARGET_GROSS = 30_000
TARGET_NET = 30_000


def calc(discount: float):
    gross_usd = PRICE * (1 - discount) * REGIONAL
    gross_cny = gross_usd * FX
    net = gross_cny * (1 - STEAM_CUT) * (1 - TAX) * (1 - REFUND)
    return {
        "discount": discount,
        "avg_price_usd": round(gross_usd, 2),
        "gross_cny_per_copy": round(gross_cny, 2),
        "net_cny_per_copy": round(net, 2),
        "copies_for_gross_30k": int(-(-TARGET_GROSS // gross_cny)),
        "copies_for_net_30k": int(-(-TARGET_NET // net)),
        "copies_to_recover_cost": int(-(-COST // net)),
    }


def main():
    rows = [calc(d) for d in (0.0, 0.10, 0.15, 0.30)]

    # 组合情景：每款 1,800 份终身，4/6/8 款每年
    portfolio = []
    base = calc(0.15)
    for n in (4, 6, 8):
        copies_year = 1800 * n
        net_year = copies_year * base["net_cny_per_copy"]
        portfolio.append({
            "titles_per_year": n,
            "lifetime_copies_each": 1800,
            "copies_per_year": copies_year,
            "net_year_cny": int(net_year),
            "net_month_cny": int(net_year / 12),
            "gross_year_cny": int(copies_year * base["gross_cny_per_copy"]),
            "cost_year_cny": COST * n,
            "net_margin": round((net_year - COST * n) / net_year, 3),
        })

    result = {
        "assumptions": {
            "price_usd": PRICE, "fx": FX, "regional_factor": REGIONAL,
            "steam_cut": STEAM_CUT, "tax": TAX, "refund": REFUND,
            "cost_per_title_cny": COST,
        },
        "scenarios": rows,
        "portfolio": portfolio,
        "note": (f"gross=流水；net=扣 Steam {STEAM_CUT:.0%}、税 {TAX:.0%}、退款 {REFUND:.0%} 后；"
                 "未计本地化/外包/音乐采购。默认值对齐宪法 C-12。"),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "UNIT-ECONOMICS-20261120.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys

    if "--self-test" in sys.argv:
        # 宪法 C-12 公布的两个数就是标定值；算不出来说明默认假设漂了。
        r = calc(0.15)
        fails = []
        if abs(r["net_cny_per_copy"] - 32.52) > 0.01:
            fails.append(f"net={r['net_cny_per_copy']}，C-12 为 32.52")
        if r["copies_for_net_30k"] != 923:
            fails.append(f"copies={r['copies_for_net_30k']}，C-12 为 923")
        if abs(REGIONAL - 0.75) > 1e-9 or abs(TAX - 0.20) > 1e-9 or abs(REFUND - 0.15) > 1e-9:
            fails.append(f"默认假设 {REGIONAL}/{TAX}/{REFUND} 不等于 C-12 的 0.75/0.20/0.15")
        print(json.dumps({"self_test": "PASS" if not fails else "FAIL",
                          "net_cny_per_copy": r["net_cny_per_copy"],
                          "copies_for_net_30k": r["copies_for_net_30k"],
                          "fails": fails}, ensure_ascii=False))
        raise SystemExit(0 if not fails else 1)

    raise SystemExit(main())

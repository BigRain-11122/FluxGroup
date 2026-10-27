# 散户级成本与可行性核算（100 万级 · A 股 ETF＋股票 · 2026-09-30 外审出件）
# 目的：把"我这个规模、这个换手，成本吃掉多少"算成一个数，作为策略设计的第一约束。
# 用法：python retail_feasibility.py
# 依赖：docs/audits/cost_model_cn.py（同目录）

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

CAPITAL = 1_000_000.0
POSITIONS = 15          # 百万级散户典型分散度
PER_POSITION = CAPITAL / POSITIONS

ETF = "510300"
STOCK = "600519"
ADV_ETF = 2_000_000_000.0    # 宽基 ETF 日成交额量级
ADV_STOCK = 3_000_000_000.0  # 大盘股日成交额量级


def drag_bp_per_year(code, adv, turns_per_year):
    """Annual cost drag in bp of capital for a given turnover."""
    px = 4.5 if code == ETF else 100.0
    qty = int(PER_POSITION / px / 100) * 100
    if qty <= 0:
        return None
    rt = cn.round_trip_cost_bp(code, px, qty, adv)
    return rt * turns_per_year, rt


def main():
    print(f"资金 {CAPITAL:,.0f} 元 · 分 {POSITIONS} 仓 · 单仓 {PER_POSITION:,.0f} 元")
    print()
    print("=== 一、最小佣金是否咬到你？（你的实际单笔规模） ===")
    print(f"{'单笔金额':>12}{'有效佣金bp/边':>16}{'是否受 5 元底影响':>20}")
    for n in (PER_POSITION, 50_000, 100_000, 200_000):
        bp = cn.effective_commission_bp(n)
        print(f"{n:>12,.0f}{bp:>16.2f}{'否（按万2.5）' if bp <= 2.51 else '是':>20}")
    print("  → 结论：百万级分 15 仓，单笔 ~6.7 万，佣金率就是万2.5，5 元底几乎不咬。")
    print()

    print("=== 二、往返成本（你的单仓规模） ===")
    for name, code, adv in (("ETF", ETF, ADV_ETF), ("大盘股", STOCK, ADV_STOCK)):
        px = 4.5 if code == ETF else 100.0
        qty = int(PER_POSITION / px / 100) * 100
        rt = cn.round_trip_cost_bp(code, px, qty, adv)
        print(f"  {name:<8} 仓位 {qty*px:>10,.0f} 元 → 往返 {rt:>6.2f} bp")
    print()

    print("=== 三、年成本拖累（关键约束） ===")
    print(f"{'年换手次数':>10}{'ETF拖累':>12}{'股票拖累':>12}{'股票-ETF':>12}")
    for turns in (4, 6, 12, 24, 48, 120):
        de, rte = drag_bp_per_year(ETF, ADV_ETF, turns)
        ds, rts = drag_bp_per_year(STOCK, ADV_STOCK, turns)
        print(f"{turns:>10}{de:>12.0f}{ds:>12.0f}{ds-de:>12.0f}")
    print("  单位：bp/年（1bp = 0.01%）。作为对照：")
    print("    · 沪深300 长期年化约 6-8%，被动+0.10 的判线 ≈ 10bp")
    print("    · 因此年换手 >12 次，单是成本就吃掉判线的一大块")
    print()

    print("=== 四、可承受换手上限（成本 ≤ 年化目标 10% 的口径） ===")
    for name, code, adv in (("ETF", ETF, ADV_ETF), ("股票", STOCK, ADV_STOCK)):
        px = 4.5 if code == ETF else 100.0
        qty = int(PER_POSITION / px / 100) * 100
        rt = cn.round_trip_cost_bp(code, px, qty, adv)
        for budget_bp in (30, 60):
            print(f"  {name:<6} 欲把年成本压在 {budget_bp}bp 内 → 年换手 ≤ {budget_bp/rt:>5.1f} 次")
    print()

    print("=== 五、个人 vs 机构的税收差（你的合法优势） ===")
    print("  个人买卖 A 股价差：免征个人所得税")
    print("  机构买卖 A 股价差：计入企业所得税（25%）")
    print(f"  → 若年化价差收益 8%（80,000 元），个人省税约 {80_000*0.25:,.0f} 元/年")
    print("  注意：ETF 与股票在印花税上差异见上；分红红利税按持股期限另计。")


if __name__ == "__main__":
    main()

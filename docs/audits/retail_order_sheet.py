# retail_order_sheet.py —— 每周操作单生成器（百万散户定制策略 V1）
# 用途：按 retail_strategy_v1.md 的规则，用最新数据算出「当前区间 + 目标权重 + 应买卖清单」。
# 用法：python retail_order_sheet.py            （用本地日线最新数据）
#       python retail_order_sheet.py --capital 1000000 --hold 510300:1200,511010:800
import os, sys, csv, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
BROAD, BOND, GOLD, OVERSEAS = "510300", "511010", "518880", "513500"
NAMES = {BROAD: "沪深300ETF", BOND: "国债ETF", GOLD: "黄金ETF", OVERSEAS: "标普500ETF"}
ADV = 500_000_000.0

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return []
    rows = []
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 5:
                continue
            try:
                rows.append((row[0], float(row[4])))
            except ValueError:
                continue
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=1_000_000.0)
    ap.add_argument("--hold", type=str, default="",
                    help="当前持仓 code:qty,code:qty（留空=空仓起步）")
    a = ap.parse_args()

    series = {c: load(c) for c in (BROAD, BOND, GOLD, OVERSEAS)}
    if not series[BROAD]:
        print("缺数据"); return
    px = {c: series[c][-1][1] for c in series if series[c]}
    date_now = series[BROAD][-1][0]

    closes_b = [v for _, v in series[BROAD]]
    ma200 = sum(closes_b[-200:]) / 200
    hi250 = max(closes_b[-250:])
    cur = closes_b[-1]
    dd250 = (cur - hi250) / hi250

    if cur > ma200:
        reg = "PEAK"
    elif dd250 <= -0.10:
        reg = "VALLEY"
    else:
        reg = "NEUTRAL"

    W = {"VALLEY":   {BROAD: .25, GOLD: .25, OVERSEAS: .25, BOND: .25},
         "NEUTRAL":  {BROAD: .17, GOLD: .17, OVERSEAS: .17, BOND: .49},
         "PEAK":     {BROAD: .15, GOLD: .15, OVERSEAS: .15, BOND: .55}}[reg]
    FREQ = {"VALLEY": "每周", "NEUTRAL": "每两周", "PEAK": "每季度"}[reg]

    hold = {}
    if a.hold:
        for part in a.hold.split(","):
            if ":" in part:
                c, q = part.split(":")
                hold[c.strip()] = int(float(q))

    port = a.capital + sum(q * px.get(c, 0) for c, q in hold.items())
    print(f"数据日期 {date_now}｜510300 现价 {cur:.3f}｜MA200 {ma200:.3f}｜250日高点 {hi250:.3f}｜距高点 {dd250*100:.1f}%")
    print(f"→ 当前区间：【{reg}】｜再平衡频率：{FREQ}")
    print(f"→ 组合总值 {port:,.0f} 元")
    print()
    print(f"{'标的':<12}{'现价':>8}{'目标权重':>10}{'目标市值':>12}{'现市值':>12}{'动作':>10}{'数量':>10}{'预估成本':>10}")
    total_cost = 0.0
    for c in (BROAD, GOLD, OVERSEAS, BOND):
        p = px.get(c)
        if not p:
            continue
        want = port * W[c]
        have = hold.get(c, 0) * p
        delta = want - have
        action, qty, cost = "持有", 0, 0.0
        if abs(delta) / port < 0.15:
            action = "不动（带内）"
        elif delta > 0:
            qty = int(delta / p / 100) * 100
            if qty > 0:
                cost = cn.buy_cost(p, qty, c, ADV) - p * qty
                action = "买入"
        else:
            qty = int(-delta / p / 100) * 100
            qty = min(qty, hold.get(c, 0))
            if qty > 0:
                cost = p * qty - cn.sell_proceeds(p, qty, c, ADV)
                action = "卖出"
            else:
                action = "无仓位可卖"
        total_cost += cost
        print(f"{NAMES[c]:<12}{p:>8.3f}{W[c]*100:>9.0f}%{want:>12,.0f}{have:>12,.0f}{action:>10}{qty:>10,}{cost:>10,.0f}")
    print()
    print(f"预估交易成本合计 {total_cost:,.0f} 元（{total_cost/port*10000:.1f} bp）")
    print("执行：次日开盘价附近挂单；成交后回写本单数量，作为下周的 --hold 输入。")

if __name__ == "__main__":
    main()

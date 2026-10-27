# worst_entry_dd.py —— 任意日建仓后的最坏回撤（回答"今天满仓最坏会怎样"）
# 方法：对每个交易日 t 作为建仓日，用策略规则跑到 t+252 交易日，记录该窗内的最大回撤。
#       统计：最坏、p5、p50（中位）、p95，以及在"低谷区"建仓时的分布。
# 这是原版回测缺失的那一块：起点风险。
import os, sys, csv, math, statistics
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
CAPITAL = 1_000_000.0
BROAD, BOND, GOLD, OVERSEAS = "510300", "511010", "518880", "513500"
ALL = [BROAD, BOND, GOLD, OVERSEAS]
ADV = 500_000_000.0
W = {"VALLEY": {BROAD: .25, GOLD: .25, OVERSEAS: .25, BOND: .25},
     "NEUTRAL": {BROAD: .17, GOLD: .17, OVERSEAS: .17, BOND: .49},
     "PEAK": {BROAD: .15, GOLD: .15, OVERSEAS: .15, BOND: .55}}

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    out = {}
    if not os.path.exists(p):
        return out
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            if len(row) < 6: continue
            try: out[row[0]] = (float(row[1]), float(row[4]))
            except ValueError: continue
    return out

def main():
    data = {c: load(c) for c in ALL}
    dates = sorted(set(data[BROAD]) & set(data[BOND]) & set(data[GOLD]) & set(data[OVERSEAS]))
    closes = {c: [data[c].get(d, (None, None))[1] for d in dates] for c in ALL}

    def ma(c, i, n):
        v = [closes[c][j] for j in range(max(0, i-n+1), i+1)]
        v = [x for x in v if x is not None]
        return sum(v)/len(v) if len(v) >= n*0.8 else None

    def regime(i):
        m = ma(BROAD, i, 200); c = closes[BROAD][i]
        if not m or not c: return "NEUTRAL"
        hi = max([x for x in closes[BROAD][max(0, i-250):i+1] if x] or [0])
        dd = (c-hi)/hi if hi else 0
        if c < m and dd <= -0.10: return "VALLEY"
        if c > m: return "PEAK"
        return "NEUTRAL"

    HORIZON = 252
    res = []
    valley_res = []
    for t in range(200, len(dates) - HORIZON):
        reg0 = regime(t)
        # 建仓：t+1 开盘按目标权重买入
        eq = CAPITAL; peak = CAPITAL; mdd = 0.0
        hold = {}
        for c, w in W[reg0].items():
            px = data[c].get(dates[t+1], (None, None))[0]
            if not px: continue
            qty = int(CAPITAL * w / px / 100) * 100
            if qty > 0:
                cost = cn.buy_cost(px, qty, c, ADV)
                if cost <= eq:
                    eq -= cost; hold[c] = qty
        # 持有到期（不再调仓，测的是"建仓后不动"的纯粹起点风险）
        for k in range(t+1, t+1+HORIZON):
            v = 0.0
            for c, q in hold.items():
                px = closes[c][k]
                if px: v += q*px
            e = eq + v
            if e > peak: peak = e
            d = (e-peak)/peak
            if d < mdd: mdd = d
        res.append((dates[t], reg0, mdd))
        if reg0 == "VALLEY":
            valley_res.append(mdd)

    res.sort(key=lambda x: x[2])
    mdd_all = [r[2] for r in res]
    mdd_all.sort()
    n = len(mdd_all)
    print(f"样本：{n} 个建仓日（每个持有 252 交易日）")
    print()
    print("=== 全部建仓日：持有 1 年的最大回撤分布 ===")
    for lab, q in (("最坏", 0.0), ("p5", 0.05), ("p25", 0.25), ("中位", 0.5), ("p75", 0.75), ("最轻", 0.999)):
        print(f"  {lab:<6}{mdd_all[int(q*(n-1))]*100:>8.1f}%")
    print()
    if valley_res:
        v = sorted(valley_res)
        print(f"=== 仅在【低谷】建仓的{len(v)}个样本 ===")
        for lab, q in (("最坏", 0.0), ("p5", 0.05), ("中位", 0.5), ("最轻", 0.999)):
            print(f"  {lab:<6}{v[int(q*(len(v)-1))]*100:>8.1f}%")
        print(f"  低谷建仓后亏超 20% 的比例: {sum(1 for x in v if x < -0.20)/len(v)*100:.0f}%")
    print()
    print("=== 最坏的 5 个建仓日 ===")
    for d, r, m in res[:5]:
        print(f"  {d}  建仓区间={r}  持有1年最大回撤 {m*100:.1f}%")

if __name__ == "__main__":
    main()

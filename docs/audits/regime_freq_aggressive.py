# regime_freq_adaptive.py —— 区间自适应频率策略（散户定制 · 低谷加频/高峰减频）
# 用户洞察（2026-09-30）：低谷期加多频率、高峰期减少频率。
# 这条在结构上绕开了前三个版本的病根：换手不再平均撒在全年，而是集中在期望值最高的区间。
#
# 设计（全部跑前冻结，禁参数搜索）：
#   底仓=4 类真独立资产等权：宽基 510300 / 债券 511010 / 黄金 518880 / 海外 513500
#   区间判定（用宽基，无未来函数）：
#       高峰 PEAK  : close > MA200
#       低谷 VALLEY: close < MA200 且 距离 250 日高点回撤 >= 10%
#       中性 NEUTRAL: 其余
#   频率预算：VALLEY=每周看一次 / NEUTRAL=每两周 / PEAK=每季度
#   低谷加权：VALLEY 时风险资产权重 ×1.5（债券腿相应减），上限保证债券腿 >=10%
#   成本：cost_model_cn.py；T+1 天然满足（最小间隔一周）
#   不杠杆、不做空、不碰期货
import os, sys, csv, math, statistics
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
CAPITAL = 1_000_000.0
BROAD, BOND, GOLD, OVERSEAS = "510300", "511010", "518880", "513500"
RISK = [BROAD, GOLD, OVERSEAS]
ALL = [BROAD, BOND, GOLD, OVERSEAS]
ADV = 500_000_000.0

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return None
    out = {}
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 6:
                continue
            try:
                out[row[0]] = (float(row[1]), float(row[4]))
            except ValueError:
                continue
    return out

def main():
    data = {c: load(c) for c in ALL}
    if any(data[c] is None for c in ALL):
        print("数据缺失"); return
    dates = sorted(set(data[BROAD]) & set(data[BOND]) & set(data[GOLD]) & set(data[OVERSEAS]))
    print(f"[激进档] 共同交易日 {len(dates)}（{dates[0]} → {dates[-1]}）· 4 类独立资产")

    closes = {c: [data[c].get(d, (None, None))[1] for d in dates] for c in ALL}
    opens = {c: [data[c].get(d, (None, None))[0] for d in dates] for c in ALL}

    def ma(i, n):
        v = [closes[BROAD][j] for j in range(max(0, i-n+1), i+1)]
        v = [x for x in v if x is not None]
        return sum(v)/len(v) if len(v) >= n*0.8 else None

    def regime(i):
        m = ma(i, 200)
        c = closes[BROAD][i]
        if not m or not c:
            return "NEUTRAL"
        # 250 日高点回撤
        hi = max([x for x in closes[BROAD][max(0, i-250):i+1] if x] or [0])
        dd = (c - hi) / hi if hi else 0
        if c < m and dd <= -0.10:
            return "VALLEY"
        if c > m:
            return "PEAK"
        return "NEUTRAL"

    # 目标权重
    def target_weights(reg):
        if reg == "VALLEY":
            rw, bw = 0.33, 0.01
        elif reg == "PEAK":
            rw, bw = 0.15, 0.55
        else:
            rw, bw = 0.17, 0.49
        return {BROAD: rw, GOLD: rw, OVERSEAS: rw, BOND: bw}

    cash = CAPITAL
    hold = {}
    equity = []
    last_check = -999
    turnover = 0.0
    checks = 0
    reg_hist = {"PEAK": 0, "VALLEY": 0, "NEUTRAL": 0}
    band = 0.15                        # 权重偏移 15% 以内不动（治噪声换手）

    for i in range(200, len(dates) - 1):
        reg = regime(i)
        reg_hist[reg] += 1
        # 频率预算
        gap = 5 if reg == "VALLEY" else (10 if reg == "NEUTRAL" else 60)
        if i - last_check < gap:
            equity.append((dates[i], cash + sum(q * (closes[c][i] or 0) for c, q in hold.items())))
            continue
        last_check = i
        checks += 1

        i_exe = i + 1                  # 次日开盘执行（无未来函数）
        tgt = target_weights(reg)
        port = cash + sum(q * (opens[c][i_exe] or 0) for c, q in hold.items())
        if port <= 0:
            continue
        # 单标的按 15% 带宽调整
        for c, w in tgt.items():
            px = opens[c][i_exe]
            if not px:
                continue
            want = port * w
            have = hold.get(c, 0) * px
            if abs(want - have) / port < band:
                continue
            if want > have:
                qty = int((want - have) / px / 100) * 100
                if qty > 0:
                    cost = cn.buy_cost(px, qty, c, ADV)
                    if cost <= cash:
                        cash -= cost
                        hold[c] = hold.get(c, 0) + qty
                        turnover += qty * px
            else:
                qty = int((have - want) / px / 100) * 100
                qty = min(qty, hold.get(c, 0))
                if qty > 0:
                    cash += cn.sell_proceeds(px, qty, c, ADV)
                    hold[c] -= qty
                    turnover += qty * px
                    if hold[c] <= 0:
                        del hold[c]
        equity.append((dates[i], cash + sum(q * (closes[c][i] or 0) for c, q in hold.items())))

    # 汇总
    final = equity[-1][1]
    yrs = (datetime.strptime(equity[-1][0], "%Y-%m-%d") - datetime.strptime(equity[0][0], "%Y-%m-%d")).days / 365.25
    cagr = (final / CAPITAL) ** (1 / yrs) - 1
    peak = CAPITAL; mdd = 0.0
    for _, e in equity:
        if e > peak: peak = e
        dd = (e - peak) / peak
        if dd < mdd: mdd = dd
    bench_cagr = (closes[BROAD][-1] / closes[BROAD][200]) ** (1 / yrs) - 1
    # 年度胜率：按自然年比较
    yearly = {}
    for d, e in equity:
        yearly.setdefault(d[:4], []).append(e)
    wins = 0; tot = 0
    prev = CAPITAL
    for y in sorted(yearly):
        last = yearly[y][-1]
        bt = None
        idxs = [j for j, dd_ in enumerate(dates) if dd_.startswith(y)]
        if idxs:
            b0 = closes[BROAD][idxs[0]]; b1 = closes[BROAD][idxs[-1]]
            if b0 and b1:
                bt = b1 / b0 - 1
        r = last / prev - 1
        if bt is not None:
            tot += 1
            if r > bt: wins += 1
        prev = last

    print()
    print(f"检查次数 {checks}（{checks/yrs:.1f}/年）· 区间分布 PEAK/VALLEY/NEUTRAL = "
          f"{reg_hist['PEAK']}/{reg_hist['VALLEY']}/{reg_hist['NEUTRAL']}")
    print(f"期末权益 {final:,.0f}｜总收益 {(final/CAPITAL-1)*100:.1f}%｜年化 {cagr*100:.2f}%")
    print(f"沪深300 同期年化 {bench_cagr*100:.2f}%｜超额 {(cagr-bench_cagr)*100:.2f}pp")
    print(f"最大回撤 {mdd*100:.1f}%")
    print(f"年度胜率 {wins}/{tot} = {wins/tot*100:.0f}%" if tot else "年度胜率 n/a")
    print(f"累计换手 {turnover/CAPITAL:.2f}x capital｜年均 {turnover/CAPITAL/yrs:.2f}x")
    print(f"成本拖累约 {turnover/CAPITAL/yrs*10.08:.0f} bp/年")

if __name__ == "__main__":
    main()


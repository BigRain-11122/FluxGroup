# research_round2.py —— 自主研究第二轮：H1 反转频率假设 + H2 极端度择时假设
# 设计纪律：一次性扫有限网格并全量公布（含失败），不做"挑最好"的二次搜索。
import os, csv, math, statistics
from datetime import datetime
DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
BROAD = "510300"

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p): return None
    out = {}
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            if len(row) < 6: continue
            try: out[row[0]] = (float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]))
            except ValueError: continue
    return out

def main():
    codes = sorted(f[:-4] for f in os.listdir(DAILY) if f.endswith(".csv") and f[:-4].isdigit())
    excl = {"511880", "511990"}
    data = {}
    for c in codes:
        if c in excl: continue
        d = load(c)
        if d and len(d) > 1200 and min(d) <= "2020-01-10":
            data[c] = d
    names = sorted(data.keys())
    # 交易日轴用最长的标的
    base = max(names, key=lambda c: len(data[c]))
    dates = sorted(data[base].keys())
    closes = {c: [data[c].get(d, (None,)*5)[3] for d in dates] for c in names}
    print(f"宇宙 {len(names)} 只｜交易日 {len(dates)}（{dates[0]} → {dates[-1]}）")

    # ================= H1: 反转 / 动量 频率扫描 =================
    print()
    print("=== H1: 单标的时序信号（非横截面）—— 反转 vs 动量 × 持有期 ===")
    print("  口径：信号日收盘算 N 日收益 -> 次日开盘进场 -> 持有 H 日 -> 次日开盘出场；含成本 10.08bp 往返")
    RT = 10.08 / 10000.0
    print(f"  {'信号':<16}{'持有H':>6}{'笔数':>7}{'胜率':>8}{'均值':>9}{'盈亏比':>8}{'期望':>9}{'年化≈':>9}")
    for sig_n in (5, 10, 20):
        for H in (5, 10, 20):
            for mode in ("reversal", "momentum"):
                rets = []
                for c in names:
                    cl = closes[c]
                    i = 200
                    while i + H + 1 < len(cl):
                        a, b = cl[i - sig_n], cl[i]
                        if not a or not b: i += 1; continue
                        s = b / a - 1
                        # 门槛：仅当信号幅度超过 2% 才出手（治噪声）
                        if abs(s) < 0.02: i += 1; continue
                        entry = data[c][dates[i+1]][0] if data[c].get(dates[i+1]) else None
                        exitp = data[c][dates[i+1+H]][0] if data[c].get(dates[i+1+H]) else None
                        if not entry or not exitp: i += 1; continue
                        if mode == "reversal":
                            ok = (s < 0)
                        else:
                            ok = (s > 0)
                        if not ok: i += 1; continue
                        r = exitp / entry - 1 - RT
                        rets.append(r)
                        i += H            # 不重叠
                if len(rets) < 30: continue
                w = sum(1 for r in rets if r > 0)
                wr = w / len(rets)
                mean = statistics.fmean(rets)
                g = [r for r in rets if r > 0]; l = [-r for r in rets if r <= 0]
                plr = (statistics.fmean(g)/statistics.fmean(l)) if g and l and statistics.fmean(l) > 0 else float('inf')
                exp = mean
                yrs = (datetime.strptime(dates[-1], "%Y-%m-%d") - datetime.strptime(dates[0], "%Y-%m-%d")).days/365.25
                # 年化近似：每笔占用 H 天，串行可做 252/H 次，但机会由门槛决定
                turns = len(rets) / len(names) / yrs
                ann = exp * turns
                print(f"  {mode:<16}{H:>6}{len(rets):>7}{wr*100:>7.1f}%{mean*100:>8.2f}%{plr:>8.2f}{exp*100:>8.2f}%{ann*100:>8.1f}%")

    # ================= H2: 极端度指标 vs 未来收益 =================
    print()
    print("=== H2: 极端度择时（宽基 510300）—— 各指标分位 vs 未来 20/60 日收益 ===")
    cl = closes[BROAD]
    # 可用指标
    def ma(i, n):
        v = cl[max(0, i-n+1):i+1]
        v = [x for x in v if x]
        return sum(v)/len(v) if len(v) >= n*0.8 else None

    inds = {}
    # 1) 距 MA200 偏离度
    inds["偏离MA200"] = [((cl[i]/ma(i,200)-1) if (cl[i] and ma(i,200)) else None) for i in range(len(cl))]
    # 2) 距 250 日高点回撤
    hi = []
    for i in range(len(cl)):
        w = [x for x in cl[max(0,i-250):i+1] if x]
        hi.append((cl[i]/max(w)-1) if w and cl[i] else None)
    inds["距250日高点"] = hi
    # 3) 20 日实现波动（年化）
    vol = []
    for i in range(len(cl)):
        if i < 21 or not cl[i-20] : vol.append(None); continue
        rs = [cl[j]/cl[j-1]-1 for j in range(i-19, i+1) if cl[j] and cl[j-1]]
        vol.append(statistics.pstdev(rs)*math.sqrt(252) if len(rs) > 5 else None)
    inds["20日波动"] = vol
    # 4) 20 日均量 / 250 日均量（成交额地量，用成交额列 4）
    amt = {}
    # 重新取成交额
    amt = {c: [data[c].get(d, (None,)*5)[4] if data[c].get(d) else None for d in dates] for c in names}
    a_b = amt[BROAD]
    vr = []
    for i in range(len(a_b)):
        if i < 250: vr.append(None); continue
        v20 = [x for x in a_b[i-19:i+1] if x]
        v250 = [x for x in a_b[i-249:i+1] if x]
        vr.append((statistics.fmean(v20)/statistics.fmean(v250)) if v20 and v250 and statistics.fmean(v250) > 0 else None)
    inds["20/250量比"] = vr

    for name, arr in inds.items():
        pairs = []
        for i in range(250, len(dates)-60):
            v = arr[i]
            if v is None or not cl[i]: continue
            for H in (20, 60):
                if i+H >= len(cl) or not cl[i+H]: continue
                pairs.append((v, cl[i+H]/cl[i]-1, H))
        for H in (20, 60):
            ps = [(v, r) for v, r, h in pairs if h == H]
            if len(ps) < 100: continue
            ps.sort(key=lambda x: x[0])
            n = len(ps); q = n//4
            lows = [r for _, r in ps[:q]]
            highs = [r for _, r in ps[-q:]]
            print(f"  {name:<12} H={H:<3} 最低四分位 均值 {statistics.fmean(lows)*100:>6.2f}% 正收益 {sum(1 for x in lows if x>0)/len(lows)*100:>5.1f}%"
                  f"  |  最高四分位 均值 {statistics.fmean(highs)*100:>6.2f}% 正收益 {sum(1 for x in highs if x>0)/len(highs)*100:>5.1f}%")

if __name__ == "__main__":
    main()

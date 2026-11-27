# 散户级可行域验证（100万 · 接受浮亏 · 追求年化+胜率）
# 用其自有数据回答一个决定性问题：48 只 ETF 之间有没有可轮动的分化度？
# 若绝大多数是宽基（高相关），"精选 ETF"就是幻觉，策略必须走 择时+杠杆化暴露+现金腿。
import os, sys, csv, math, statistics
from datetime import datetime

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return None
    out = []
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 5:
                continue
            try:
                out.append((row[0], float(row[4])))
            except ValueError:
                continue
    return out

def monthly_returns(series):
    """last close of each month -> monthly return series"""
    bym = {}
    for d, c in series:
        bym[d[:7]] = c
    months = sorted(bym.keys())
    rets = {}
    for i in range(1, len(months)):
        p0, p1 = bym[months[i-1]], bym[months[i]]
        if p0 > 0:
            rets[months[i]] = p1 / p0 - 1.0
    return rets

def corr(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 12:
        return None
    x = [a[k] for k in keys]; y = [b[k] for k in keys]
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sx = math.sqrt(sum((v-mx)**2 for v in x)); sy = math.sqrt(sum((v-my)**2 for v in y))
    if sx == 0 or sy == 0:
        return None
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x))) / (sx*sy)

def main():
    codes = sorted(f[:-4] for f in os.listdir(DAILY) if f.endswith(".csv") and f[:-4].isdigit())
    data = {}
    for c in codes:
        s = load(c)
        if s and len(s) > 250:
            data[c] = monthly_returns(s)
    print(f"样本：{len(data)} 只 ETF（各有 >250 交易日）")
    if len(data) < 5:
        print("样本不足"); return

    # 年度收益分布（看分化度）
    print("\n=== 一、年度收益分布（分化度 = 可轮动空间） ===")
    years = sorted({k[:4] for r in data.values() for k in r})
    print(f"{'年份':>6}{'只数':>6}{'最好':>10}{'最差':>10}{'中位':>10}{'极差(最好-最差)':>18}")
    for y in years[-6:]:
        vals = []
        for r in data.values():
            acc = 1.0
            for k, v in r.items():
                if k.startswith(y):
                    acc *= (1+v)
            if any(k.startswith(y) for k in r):
                vals.append(acc-1)
        if len(vals) >= 5:
            vals.sort()
            print(f"{y:>6}{len(vals):>6}{vals[-1]*100:>9.1f}%{vals[0]*100:>9.1f}%{statistics.median(vals)*100:>9.1f}%{(vals[-1]-vals[0])*100:>17.1f}%")

    # 相关性分布
    print("\n=== 二、两两月度相关分布（判'精选ETF'是否幻觉） ===")
    ks = sorted(data.keys())
    cs = []
    for i in range(len(ks)):
        for j in range(i+1, len(ks)):
            v = corr(data[ks[i]], data[ks[j]])
            if v is not None:
                cs.append(v)
    if cs:
        cs.sort()
        n = len(cs)
        print(f"  配对数 {n}｜中位 {statistics.median(cs):.3f}｜均值 {statistics.fmean(cs):.3f}")
        for q, lab in ((0.05,'p5'), (0.25,'p25'), (0.5,'p50'), (0.75,'p75'), (0.95,'p95')):
            print(f"  {lab}: {cs[int(q*(n-1))]:.3f}")
        low = sum(1 for v in cs if v < 0.5)
        print(f"  corr<0.5 的对数占比: {low/n*100:.1f}%  ← 这才是真可轮动空间")

    # 各标的与基准的相关（谁是宽基）
    base = "510300" if "510300" in data else ks[0]
    print(f"\n=== 三、与基准 {base} 的相关（>0.9 = 宽基替身，无轮动价值） ===")
    rows = []
    for c in ks:
        v = corr(data[base], data[c])
        if v is not None:
            rows.append((v, c))
    rows.sort(reverse=True)
    for v, c in rows[:8]:
        print(f"  {c}  corr={v:.3f}  {'← 宽基替身' if v > 0.9 else ''}")
    print("  ...")
    for v, c in rows[-8:]:
        print(f"  {c}  corr={v:.3f}  {'← 独立度高' if v < 0.5 else ''}")

if __name__ == "__main__":
    main()

# layer12_regime_style.py —— 第一层（大势）+ 第二层（风格）有效性实测
# 目的：先回答"大势能不能判断""风格有没有持续"，再谈选股与仓位。
# 方法：用 48 ETF 代理不同风格；逐年统计风格分化与延续性；测试大势判据的过滤效果。
import os, csv, math, statistics
from datetime import datetime

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
BROAD = "510300"

# 风格代理（按其池内可用标的）
STYLE = {
    "大盘价值/红利": ["510050", "510300", "512880"],
    "小盘成长":      ["159915", "159949", "159901"],
    "科技/信息":     ["515000", "512480", "159939"],
    "医药消费":      ["512010", "159928", "512690"],
    "周期资源":      ["512400", "515220", "512800"],
    "债券":          ["511010", "511260"],
    "黄金":          ["518880"],
    "海外":          ["513500", "513100"],
}

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return None
    out = {}
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            if len(row) < 5: continue
            try: out[row[0]] = float(row[4])
            except ValueError: continue
    return out

def main():
    codes = sorted(set(c for v in STYLE.values() for c in v))
    data = {}
    for c in codes:
        d = load(c)
        if d and min(d) <= "2020-02-01":
            data[c] = d
    print(f"风格代理可用：{len(data)}/{len(codes)} 只")
    avail = {k: [c for c in v if c in data] for k, v in STYLE.items()}
    for k, v in avail.items():
        print(f"  {k:<14} {len(v)} 只 {v}")

    dates = sorted(data[BROAD].keys())
    # 逐年：各风格收益
    print("\n=== 第二层：风格年度分化（代理等权年化收益） ===")
    years = sorted({d[:4] for d in dates})
    hdr = "风格".ljust(14) + "".join(f"{y:>10}" for y in years[-7:])
    print(hdr)
    style_year = {}
    for k, cs in avail.items():
        if not cs: continue
        row = []
        for y in years[-7:]:
            rs = []
            for c in cs:
                ser = data[c]
                ds = [d for d in dates if d.startswith(y) and d in ser]
                if len(ds) < 20: continue
                a, b = ser[ds[0]], ser[ds[-1]]
                if a > 0: rs.append(b/a - 1)
            row.append(statistics.fmean(rs) if rs else None)
        style_year[k] = row
        cells = "".join(f"{v*100:>9.1f}%" if v is not None else f"{'--':>10}" for v in row)
        print(k.ljust(14) + cells)

    # 风格延续性：上年最强 vs 次年表现
    print("\n=== 第二层：风格延续性（'上年最强' 是否 '次年仍强'） ===")
    wins = 0; tot = 0
    for i in range(len(years[-7:]) - 1):
        yr, nx = years[-7:][i], years[-7:][i+1]
        vals = {k: style_year[k][i] for k in style_year if style_year[k][i] is not None}
        vals2 = {k: style_year[k][i+1] for k in style_year if style_year[k][i+1] is not None}
        if not vals or not vals2: continue
        best = max(vals, key=vals.get)
        rank_next = sorted(vals2.values(), reverse=True)
        if best not in vals2: continue
        pos = sorted(vals2, key=lambda k: vals2[k], reverse=True).index(best) + 1
        tot += 1
        if pos <= 4: wins += 1
        print(f"  {yr} 最强={best:<14} → {nx} 排名 {pos}/{len(vals2)}")

    # 第一层：大势判据过滤效果
    print("\n=== 第一层：大势判据 vs 后续 60 日宽基收益 ===")
    cl = [data[BROAD][d] for d in dates]
    def ma(i, n):
        v = cl[max(0, i-n+1):i+1]
        return sum(v)/len(v) if len(v) == n else None
    buckets = {"MA200上方": [], "MA200下方": []}
    mom = {"20/60同向正": [], "20/60不满足": []}
    for i in range(200, len(dates)-60):
        m = ma(i, 200)
        if not m: continue
        fwd = cl[i+60]/cl[i] - 1
        buckets["MA200上方" if cl[i] > m else "MA200下方"].append(fwd)
        r20, r60 = cl[i]/cl[i-20]-1, cl[i]/cl[i-60]-1
        mom["20/60同向正" if (r20 > 0 and r60 > 0) else "20/60不满足"].append(fwd)
    for k, v in buckets.items():
        if v:
            pos = sum(1 for x in v if x > 0)/len(v)
            print(f"  {k:<12} n={len(v):<5} 未来60日均值 {statistics.fmean(v)*100:>6.2f}%  正收益比例 {pos*100:>5.1f}%")
    for k, v in mom.items():
        if v:
            pos = sum(1 for x in v if x > 0)/len(v)
            print(f"  {k:<12} n={len(v):<5} 未来60日均值 {statistics.fmean(v)*100:>6.2f}%  正收益比例 {pos*100:>5.1f}%")

if __name__ == "__main__":
    main()

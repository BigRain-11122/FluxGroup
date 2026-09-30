# cross_start_validation.py —— 跨起点 + 滚动窗口稳健性检验（外审自查·按 D-20260941 §1.3 自缚）
#
# 方法：对每一个可能的起点 t，跑窗口 W（1/3/5 年）的策略，记录结果；输出全分布。
#   判据（跑前写死）：
#     ① 滚动 3 年为正的比例
#     ② 滚动 3 年最差结果
#     ③ 起点敏感度：p5 与 p95 之差
#     ④ 对照：同窗口"买入持有沪深300"的分布
#   **若把最好的单点结果报告为发现 = §1.3 违规（本件即为纠错）**
import os, glob, sys
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
DAILY = os.path.join(BM, "data", "daily")
BARS = os.path.join(BM, "Money02", "data", "bars")
CAP = 1_000_000.0
WINDOWS = {"1年": 252, "3年": 756, "5年": 1260}

# ============================== 策略一：四资产 ==============================
BROAD, BOND, GOLD, OVER = "510300", "511010", "518880", "513500"
WEI = {"VALLEY": {BROAD: .25, GOLD: .25, OVER: .25, BOND: .25},
       "NEUTRAL": {BROAD: .17, GOLD: .17, OVER: .17, BOND: .49},
       "PEAK": {BROAD: .15, GOLD: .15, OVER: .15, BOND: .55}}

def load_etf(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, parse_dates=["date"]).set_index("date")
    return df

def four_asset_path():
    """返回逐日权重目标序列（用 510300 判区间），供任意起点使用。"""
    ds = {}
    for c in (BROAD, BOND, GOLD, OVER):
        d = load_etf(c)
        if d is None:
            return None, None
        ds[c] = d
    dates = sorted(set(ds[BROAD].index) & set(ds[BOND].index) & set(ds[GOLD].index) & set(ds[OVER].index))
    px = {c: ds[c]["close"].reindex(dates).ffill() for c in ds}
    ma200 = px[BROAD].rolling(200).mean()
    hi250 = px[BROAD].rolling(250).max()
    reg = []
    for i in range(len(dates)):
        m, c, h = ma200.iloc[i], px[BROAD].iloc[i], hi250.iloc[i]
        if pd.isna(m) or pd.isna(h):
            reg.append(None)
        elif c > m:
            reg.append("PEAK")
        elif (c - h) / h <= -0.10:
            reg.append("VALLEY")
        else:
            reg.append("NEUTRAL")
    return dates, (px, reg)

def four_asset_run(dates, ctx, t0, n):
    """从 t0 起跑 n 日：按区间调权重，15% 带宽，低谷每5日/中性每10日/高峰每60日检查。"""
    px, reg = ctx
    codes = [BROAD, GOLD, OVER, BOND]
    i = t0 + 200                      # 需要 MA200 预热
    if i + n >= len(dates):
        return None
    hold = {c: 0.0 for c in codes}
    cash = CAP
    last = -999
    peak = CAP
    mdd = 0.0
    curve = []
    while i < t0 + 200 + n and i < len(dates) - 1:
        r = reg[i]
        if r is None:
            i += 1
            continue
        gap = 5 if r == "VALLEY" else (10 if r == "NEUTRAL" else 60)
        if i - last >= gap:
            last = i
            w = WEI[r]
            port = cash + sum(hold[c] * px[c].iloc[i] for c in codes)
            for c in codes:
                p = px[c].iloc[i]
                if pd.isna(p) or p <= 0:
                    continue
                want = port * w[c]
                have = hold[c] * p
                if port > 0 and abs(want - have) / port < 0.15:
                    continue
                if want > have:
                    q = int((want - have) / p / 100) * 100
                    if q > 0:
                        cost = cn.buy_cost(p, q, c, 5e8)
                        if cost <= cash:
                            cash -= cost
                            hold[c] += q
                else:
                    q = min(int((have - want) / p / 100) * 100, int(hold[c]))
                    if q > 0:
                        cash += cn.sell_proceeds(p, q, c, 5e8)
                        hold[c] -= q
        e = cash + sum(hold[c] * px[c].iloc[i] for c in codes)
        if e > peak:
            peak = e
        dd = (e - peak) / peak
        if dd < mdd:
            mdd = dd
        curve.append(e)
        i += 1
    final = curve[-1]
    yrs = n / 252.0
    return dict(cagr=(final / CAP) ** (1 / yrs) - 1, mdd=mdd)

def bench_run(dates, ctx, t0, n, code=BROAD):
    px, _ = ctx
    i = t0 + 200
    if i + n >= len(dates):
        return None
    p0, p1 = px[code].iloc[i], px[code].iloc[i + n]
    if pd.isna(p0) or pd.isna(p1) or p0 <= 0:
        return None
    return (p1 / p0) ** (252.0 / n) - 1

# ============================== 策略二：低量选股 ==============================
def lowamt_path():
    m = pd.read_csv(os.path.join(BM, "data", "fundamental", "b_layer_mask.csv"), dtype={"code": str})
    ok = set(m[m["ok_static"] == True]["code"].str.zfill(6))
    panel = {}
    for f in sorted(glob.glob(os.path.join(BARS, "*.parquet"))):
        c = os.path.basename(f)[:-8]
        if not c.isdigit() or c not in ok:
            continue
        try:
            df = pd.read_parquet(f, columns=["date", "close", "amount", "pct_chg"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= "2016-01-01"]
        if len(df) < 250:
            continue
        panel[c] = df.set_index("date")
    return panel

def lowamt_run(panel, dates, t0, n, rebal=20, topn=20):
    """简化版：每 20 日选 TOP20 低量股等权，只在集合变化时交易（持仓用比例表示）。"""
    eq = CAP
    hold = {}          # code -> 市值权重
    peak = CAP
    mdd = 0.0
    i = max(t0, 250)
    end = t0 + 200 + n
    if end >= len(dates):
        return None
    # 预取需要的数据面
    close = {}
    for c in panel:
        close[c] = panel[c]["close"]
    Cm = pd.DataFrame(close).reindex(dates)
    Am = pd.DataFrame({c: panel[c]["amount"] for c in panel}).reindex(dates)
    Pm = pd.DataFrame({c: panel[c]["pct_chg"] for c in panel}).reindex(dates)
    vr = Am.rolling(20).mean() / Am.rolling(120).mean()
    shares = {}
    cash = CAP
    j = i
    while j < end:
        if (j - i) % rebal == 0:
            s = vr.iloc[j].dropna()
            idx = s.index
            a = Am.iloc[j].reindex(idx); p = Cm.iloc[j].reindex(idx); pc = Pm.iloc[j].reindex(idx)
            keep = ((a > 5e7).fillna(False).values & (p > 2.0).fillna(False).values
                    & (pc.abs() < 9.0).fillna(False).values)
            s = s[keep]
            if len(s) >= topn:
                pick = list(s.nsmallest(topn).index)
                port = cash + sum(shares[c] * (Cm.iloc[j].get(c) if not pd.isna(Cm.iloc[j].get(c, np.nan)) else 0) for c in list(shares))
                for c in list(shares.keys()):
                    if c not in pick:
                        p2 = Cm.iloc[j].get(c)
                        if p2 and not pd.isna(p2):
                            cash += cn.sell_proceeds(p2, shares[c], c, 5e8)
                        del shares[c]
                per = port / len(pick)
                for c in pick:
                    p2 = Cm.iloc[j].get(c)
                    if p2 is None or pd.isna(p2) or p2 <= 0:
                        continue
                    have = shares.get(c, 0) * p2
                    if per - have > p2 * 100:
                        q = int((per - have) / p2 / 100) * 100
                        if q > 0:
                            cost = cn.buy_cost(p2, q, c, 5e8)
                            if cost <= cash:
                                cash -= cost
                                shares[c] = shares.get(c, 0) + q
        e = cash + sum(sh * (Cm.iloc[j].get(c) if not pd.isna(Cm.iloc[j].get(c, np.nan)) else 0) for c, sh in shares.items())
        if e > peak:
            peak = e
        dd = (e - peak) / peak
        if dd < mdd:
            mdd = dd
        j += 1
    final = cash + sum(sh * (Cm.iloc[end].get(c) if not pd.isna(Cm.iloc[end].get(c, np.nan)) else 0) for c, sh in shares.items())
    yrs = n / 252.0
    return dict(cagr=(final / CAP) ** (1 / yrs) - 1, mdd=mdd)

def report(name, vals, bench=None):
    v = sorted(vals)
    n = len(v)
    if n < 10:
        print(f"{name}: 样本不足 ({n})"); return
    def q(f):
        return v[int(f * (n - 1))]
    pos = sum(1 for x in v if x > 0) / n * 100
    print(f"  {name:<22} n={n:<5} 最差 {v[0]*100:>7.1f}%  p25 {q(.25)*100:>7.1f}%  "
          f"中位 {q(.5)*100:>7.1f}%  p75 {q(.75)*100:>7.1f}%  最好 {v[-1]*100:>7.1f}%  "
          f"正比例 {pos:>5.1f}%  离散 {q(.95)-q(.05):>6.1f}pp")
    if bench is not None:
        b = sorted(bench)
        beat = sum(1 for i in range(n) if v[i] > b[i]) / n * 100
        print(f"  {'':<22} 跑赢基准比例 {beat:.1f}%")

def main():
    print("=" * 100)
    print("跨起点 / 滚动窗口稳健性检验（外审自查·按 D-20260941 §1.3）")
    print("=" * 100)
    dates, ctx = four_asset_path()
    if dates is None:
        print("ETF 数据缺失"); return
    print(f"\n策略一 四资产：交易日 {len(dates)}（{dates[0].date()} → {dates[-1].date()}）")
    for wname, n in WINDOWS.items():
        vals, bvals = [], []
        for t0 in range(0, len(dates) - 200 - n - 2):
            r = four_asset_run(dates, ctx, t0, n)
            b = bench_run(dates, ctx, t0, n)
            if r and b is not None:
                vals.append(r["cagr"]); bvals.append(b)
        if vals:
            print(f"\n [窗口 {wname}]")
            report("四资产 年化", vals, bvals)

    print("\n" + "-" * 100)
    print("策略二 低量选股（5,222 面板·已过第一铁律）")
    panel = lowamt_path()
    if not panel:
        print("面板缺失"); return
    # 用面板自身日期轴
    dts = sorted(set().union(*[set(d.index) for d in panel.values()]))
    dts = [d for d in dts if d >= pd.Timestamp("2016-01-01")]
    print(f"  交易日 {len(dts)}（{dts[0].date()} → {dts[-1].date()}）")
    for wname, n in (("3年", 756),):
        vals = []
        for t0 in range(0, len(dts) - 200 - n - 2, 20):     # 每 20 日取一个起点，控算力
            r = lowamt_run(panel, dts, t0, n)
            if r:
                vals.append(r["cagr"])
        if vals:
            print(f"\n [窗口 {wname}]（起点采样步长 20 日）")
            report("低量选股 年化", vals)

if __name__ == "__main__":
    main()

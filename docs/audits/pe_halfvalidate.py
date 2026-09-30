# pe_halfvalidate.py —— 低PE 半验证：缩小未来函数窗口
#
# 未来函数来源：np_ttm 是【当前】净利润。窗口越长，偏差越大。
# 做法：只跑最近 N 年（N=1/3/5），再用【截面内标准化】而非绝对值排序，
#       并输出逐年结果，看收益是否集中在某些年份（集中 = 疑似偏差驱动）。
import os, glob, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
BARS = os.path.join(BM, "Money02", "data", "bars")
CAP = 1_000_000.0
TOPN = 20
REBAL = 20
ADV = 5e8

def load():
    m = pd.read_csv(os.path.join(BM, "data", "fundamental", "b_layer_mask.csv"), dtype={"code": str})
    ok = set(m[m["ok_static"] == True]["code"].str.zfill(6))
    el = pd.read_csv(os.path.join(BM, "data", "fundamental", "eligibility.csv"), dtype={"code": str})
    el["code"] = el["code"].str.zfill(6)
    el = el.drop_duplicates("code").set_index("code")
    panel = {}
    for f in sorted(glob.glob(os.path.join(BARS, "*.parquet"))):
        c = os.path.basename(f)[:-8]
        if not c.isdigit() or c not in ok or c not in el.index:
            continue
        try:
            df = pd.read_parquet(f, columns=["date","close","amount","pct_chg","outstanding_share"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        if len(df) < 260:
            continue
        df = df.set_index("date")
        df["np_ttm"] = el.at[c, "np_ttm"]
        panel[c] = df
    return panel

def run(panel, start):
    dates = sorted(set().union(*[set(d.index) for d in panel.values()]))
    C = pd.DataFrame({c: panel[c]["close"] for c in panel}).reindex(dates)
    A = pd.DataFrame({c: panel[c]["amount"] for c in panel}).reindex(dates)
    P = pd.DataFrame({c: panel[c]["pct_chg"] for c in panel}).reindex(dates)
    S = pd.DataFrame({c: panel[c]["outstanding_share"] for c in panel}).reindex(dates)
    NP = pd.Series({c: panel[c]["np_ttm"].iloc[0] for c in panel})
    pe = (C.mul(S, axis=1)).div(NP, axis=1)
    pe = pe.where(pe > 0)

    lo = max(250, next((i for i, d in enumerate(dates) if d >= pd.Timestamp(start)), 250))
    eq = CAP; hold = {}; curve = []
    i = lo
    while i < len(dates) - REBAL - 1:
        a = A.iloc[i]; px = C.iloc[i]; pc = P.iloc[i]
        tradable = ((a > ADV).fillna(False).values & (px > 2.0).fillna(False).values
                    & (pc.abs() < 9.0).fillna(False).values)
        cols = [c for c, k in zip(C.columns, tradable) if k]
        s = pe.iloc[i].reindex(cols).dropna()
        if len(s) < TOPN:
            i += REBAL; continue
        pick = list(s.nsmallest(TOPN).index)
        ex = i + 1
        port = eq + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
        for c in list(hold.keys()):
            if c not in pick:
                p = C.iloc[ex].get(c)
                if p and not pd.isna(p):
                    q = hold[c]; eq += cn.sell_proceeds(p, q, c, ADV); del hold[c]
        per = port / len(pick)
        for c in pick:
            p = C.iloc[ex].get(c)
            if p is None or pd.isna(p) or p <= 0:
                continue
            have = hold.get(c, 0) * p
            if per - have > p * 100:
                q = int((per - have) / p / 100) * 100
                if q > 0:
                    cost = cn.buy_cost(p, q, c, ADV)
                    if cost <= eq:
                        eq -= cost; hold[c] = hold.get(c, 0) + q
        val = eq + sum(q * C.iloc[i + REBAL].get(c, 0) for c, q in hold.items() if q)
        curve.append((dates[i + REBAL], val)); i += REBAL
    final = curve[-1][1]; yrs = (curve[-1][0] - curve[0][0]).days / 365.25
    cagr = (final / CAP) ** (1 / yrs) - 1
    peak = CAP; mdd = 0.0
    for _, v in curve:
        if v > peak: peak = v
        dd = (v - peak) / peak
        if dd < mdd: mdd = dd
    yr = {}
    for d, v in curve: yr.setdefault(d.year, []).append(v)
    prev = CAP; ywin = 0; yearly = []
    for y in sorted(yr):
        r = yr[y][-1] / prev - 1
        yearly.append(f"{y}:{r*100:+.1f}%")
        if r > 0: ywin += 1
        prev = yr[y][-1]
    return dict(cagr=cagr, mdd=mdd, ywin=f"{ywin}/{len(yr)}", yearly=" ".join(yearly))

def main():
    panel = load()
    print(f"面板 {len(panel)} 只｜低PE TOP{TOPN}｜调仓 {REBAL} 日｜成交额>{ADV/1e8:.0f}亿")
    print("未来函数窗口越短，偏差越小\n")
    print(f"{'窗口':<14}{'年化':>9}{'最大回撤':>10}{'年度胜':>8}   逐年")
    for lab, start in (("近1年", "2025-09-30"), ("近3年", "2023-09-30"), ("近5年", "2021-09-30"), ("全期10年", "2016-09-30")):
        r = run(panel, start)
        print(f"{lab:<14}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['ywin']:>8}   {r['yearly']}")
    print("\n[判读] 若收益高度集中在个别年份 -> 疑似偏差或单一风格驱动，不可信。")

if __name__ == "__main__":
    main()

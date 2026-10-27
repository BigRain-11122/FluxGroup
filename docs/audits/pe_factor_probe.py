# pe_factor_probe.py —— 低估值因子方向性探测（PE 由价格×股本÷净利润导出）
#
# 重要偏差声明：np_ttm 取自 eligibility.csv 的【当前】净利润，套用于全历史 = 未来函数。
# 因此本件只做【方向性探测】，不作验证结论；要验证须有【点位时点】历史净利润
# （这正是 D-20260930-41 §3 第 1 项所索取的）。
#
# 对照设计：同一宇宙、同一调仓、同一成本，只换排序键。
import os, glob, sys
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
BARS = os.path.join(BM, "Money02", "data", "bars")
CAP = 1_000_000.0
TOPN = 20
REBAL = 60                      # 低频：估值因子宜低频
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
            df = pd.read_parquet(f, columns=["date", "close", "amount", "pct_chg", "outstanding_share"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= "2016-01-01"]
        if len(df) < 250:
            continue
        df = df.set_index("date")
        np_ttm = el.at[c, "np_ttm"]
        df["np_ttm"] = np_ttm if pd.notna(np_ttm) else np.nan
        panel[c] = df
    return panel


def run(panel, mode, ls):
    dates = sorted(set().union(*[set(d.index) for d in panel.values()]))
    C = pd.DataFrame({c: panel[c]["close"] for c in panel}).reindex(dates)
    A = pd.DataFrame({c: panel[c]["amount"] for c in panel}).reindex(dates)
    P = pd.DataFrame({c: panel[c]["pct_chg"] for c in panel}).reindex(dates)
    S = pd.DataFrame({c: panel[c]["outstanding_share"] for c in panel}).reindex(dates)
    NP = pd.Series({c: panel[c]["np_ttm"].iloc[0] for c in panel})
    mcap = C.mul(S, axis=1)                       # 市值
    pe = mcap.div(NP, axis=1)                     # PE
    pe = pe.where(pe > 0)                         # 亏损/异常 -> 剔除
    vr = A.rolling(20).mean() / A.rolling(120).mean()

    eq = CAP
    hold = {}
    curve = []
    turns = 0.0
    i = 250
    while i < len(dates) - REBAL - 1:
        a = A.iloc[i]; px = C.iloc[i]; pc = P.iloc[i]
        tradable = ((a > ADV).fillna(False).values & (px > 2.0).fillna(False).values
                    & (pc.abs() < 9.0).fillna(False).values)
        cols = [c for c, k in zip(C.columns, tradable) if k]
        if len(cols) < TOPN * 3:
            i += REBAL; continue
        if mode == "lowPE":
            s = pe.iloc[i].reindex(cols).dropna()
            pick = list(s.nsmallest(TOPN).index) if len(s) >= TOPN else None
        elif mode == "highPE":
            s = pe.iloc[i].reindex(cols).dropna()
            pick = list(s.nlargest(TOPN).index) if len(s) >= TOPN else None
        elif mode == "lowPE_lowamt":
            s1 = pe.iloc[i].reindex(cols).dropna()
            s2 = vr.iloc[i].reindex(s1.index).dropna()
            if len(s2) < TOPN:
                pick = None
            else:
                z1 = -(s1.reindex(s2.index) - s1.mean()) / (s1.std() + 1e-12)
                z2 = -(s2 - s2.mean()) / (s2.std() + 1e-12)
                z = z1 + z2
                pick = list(z.nlargest(TOPN).index)
        elif mode == "lowamt":
            s = vr.iloc[i].reindex(cols).dropna()
            pick = list(s.nsmallest(TOPN).index) if len(s) >= TOPN else None
        else:
            pick = None
        if pick is None:
            i += REBAL; continue
        ex = i + 1
        port = eq + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
        for c in list(hold.keys()):
            if c not in pick:
                p = C.iloc[ex].get(c)
                if p and not pd.isna(p):
                    q = hold[c]; eq += cn.sell_proceeds(p, q, c, ADV); turns += q * p; del hold[c]
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
                        eq -= cost; hold[c] = hold.get(c, 0) + q; turns += q * p
        val = eq + sum(q * C.iloc[i + REBAL].get(c, 0) for c, q in hold.items() if q)
        curve.append((dates[i + REBAL], val)); i += REBAL
    final = curve[-1][1]
    yrs = (curve[-1][0] - curve[0][0]).days / 365.25
    cagr = (final / CAP) ** (1 / yrs) - 1
    peak = CAP; mdd = 0.0
    for _, v in curve:
        if v > peak: peak = v
        dd = (v - peak) / peak
        if dd < mdd: mdd = dd
    yr = {}
    for d, v in curve: yr.setdefault(d.year, []).append(v)
    prev = CAP; ywin = 0
    for y in sorted(yr):
        if yr[y][-1] > prev: ywin += 1
        prev = yr[y][-1]
    return dict(cagr=cagr, mdd=mdd, turns=turns / CAP / yrs, ywin=f"{ywin}/{len(yr)}", n=len(curve))


def main():
    print("加载面板…")
    panel = load()
    print(f"{len(panel)} 只（过铁律 + 有 np_ttm）｜调仓 {REBAL} 日｜TOP{TOPN}｜成交额>{ADV/1e8:.0f}亿")
    print(f"\n{'策略':<22}{'年化':>9}{'最大回撤':>10}{'换手/年':>9}{'年度胜':>8}")
    for mode, lab in (("lowPE", "低PE"), ("highPE", "高PE"), ("lowamt", "低量(对照)"),
                      ("lowPE_lowamt", "低PE+低量")):
        r = run(panel, mode, None)
        print(f"{lab:<22}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['turns']:>9.2f}x{r['ywin']:>8}")
    print("\n[偏差警示] np_ttm = 当前净利润套全历史 = 未来函数；本件仅方向性探测，非验证结论。")


if __name__ == "__main__":
    main()

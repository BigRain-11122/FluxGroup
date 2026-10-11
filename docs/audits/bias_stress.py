# bias_stress.py —— 偏差压力测试 + 真实浪费额（本地跑·输出≤14行）
# 问题一：低 PE 的 +25.65% 里，有多少来自"面板零退市"（低价股会跌到退市，面板里没有）？
#   做法：压力档（剔除过去 120 日内出现 ≤-50% 者）+ 对风险股施加退市清算（×0.3 / ×0.0）
# 问题二：账本 entries/cells_ledger_delta 求和 → 真实已烧格数
import os, glob, sys, json
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
BARS = os.path.join(BM, "Money02", "data", "bars")
CAP = 1_000_000.0
TOPN = 20
REBAL = 60
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
        df = df[df["date"] >= "2016-01-01"]
        if len(df) < 250:
            continue
        df = df.set_index("date")
        df["np_ttm"] = el.at[c, "np_ttm"]
        panel[c] = df
    return panel

def run(panel, haircut=None, drop_distress=False):
    dates = sorted(set().union(*[set(d.index) for d in panel.values()]))
    C = pd.DataFrame({c: panel[c]["close"] for c in panel}).reindex(dates)
    A = pd.DataFrame({c: panel[c]["amount"] for c in panel}).reindex(dates)
    P = pd.DataFrame({c: panel[c]["pct_chg"] for c in panel}).reindex(dates)
    S = pd.DataFrame({c: panel[c]["outstanding_share"] for c in panel}).reindex(dates)
    NP = pd.Series({c: panel[c]["np_ttm"].iloc[0] for c in panel})
    pe = (C.mul(S, axis=1)).div(NP, axis=1)
    pe = pe.where(pe > 0)
    r20 = C / C.shift(20) - 1.0
    distress = (r20 <= -0.50)

    eq = CAP; hold = {}; curve = []
    i = 250
    while i < len(dates) - REBAL - 1:
        a = A.iloc[i]; px = C.iloc[i]; pc = P.iloc[i]
        tradable = ((a > ADV).fillna(False).values & (px > 2.0).fillna(False).values
                    & (pc.abs() < 9.0).fillna(False).values)
        cols = [c for c, k in zip(C.columns, tradable) if k]
        if drop_distress:
            cols = [c for c in cols if not bool(distress.iloc[i].get(c, False))]
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
                    mult = 1.0
                    if haircut is not None and bool(distress.iloc[i].get(c, False)):
                        mult = haircut
                    q = hold[c]; eq += cn.sell_proceeds(p * mult, q, c, ADV); del hold[c]
        per = port / len(pick)
        for c in pick:
            p = C.iloc[ex].get(c)
            if p is None or pd.isna(p) or p <= 0:
                continue
            mult = 1.0
            if haircut is not None and bool(distress.iloc[i].get(c, False)):
                mult = haircut
            p2 = p * mult
            have = hold.get(c, 0) * p
            if per - have > p * 100:
                q = int((per - have) / p / 100) * 100
                if q > 0:
                    cost = cn.buy_cost(p2, q, c, ADV)
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
    prev = CAP; ywin = 0
    for y in sorted(yr):
        if yr[y][-1] > prev: ywin += 1
        prev = yr[y][-1]
    return dict(cagr=cagr, mdd=mdd, ywin=f"{ywin}/{len(yr)}")

def main():
    panel = load()
    print(f"面板 {len(panel)} 只（过铁律+有np_ttm）｜低PE TOP{TOPN}｜调仓 {REBAL} 日")
    print(f"\n{'压力档':<26}{'年化':>9}{'最大回撤':>10}{'年度胜':>8}")
    for lab, hc, dd in (("基准（零退市面板）", None, False),
                        ("退市风险股 ×0.3 清算", 0.3, False),
                        ("退市风险股 ×0.0 清零", 0.0, False),
                        ("剔除退市风险股", None, True),
                        ("×0.3 + 剔除（双压）", 0.3, True)):
        r = run(panel, hc, dd)
        print(f"{lab:<26}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['ywin']:>8}")

    print()
    p = os.path.join(BM, "results", "gate_attrition.json")
    d = json.load(open(p, encoding="utf-8"))
    e = d.get("entries") or []
    tot = sum(int(x.get("cells_ledger_delta") or 0) for x in e)
    last = max((int(x.get("ledger_total_after") or 0) for x in e), default=0)
    print(f"账本 entries={len(e)} cells_delta_sum={tot} ledger_total_after_last={last}")

if __name__ == "__main__":
    main()

import os, glob, sys
import pandas as pd
sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\docs\audits")
import cost_model_cn as cn

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
BARS = os.path.join(BM, "Money02", "data", "bars")
CAP = 1_000_000.0
TOPN = 20
REBAL = 20

m = pd.read_csv(os.path.join(BM, "data", "fundamental", "b_layer_mask.csv"), dtype={"code": str})
ok = set(m[m["ok_static"] == True]["code"].str.zfill(6))
panel = {}
for f in sorted(glob.glob(os.path.join(BARS, "*.parquet"))):
    c = os.path.basename(f)[:-8]
    if not c.isdigit() or c not in ok:
        continue
    try:
        df = pd.read_parquet(f, columns=["date", "open", "close", "amount", "pct_chg"])
    except Exception:
        continue
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= "2016-01-01"]
    if len(df) < 250:
        continue
    panel[c] = df.set_index("date")

C = pd.DataFrame({c: d["close"] for c, d in panel.items()}).sort_index()
O = pd.DataFrame({c: d["open"] for c, d in panel.items()}).reindex(C.index)
A = pd.DataFrame({c: d["amount"] for c, d in panel.items()}).reindex(C.index)
P = pd.DataFrame({c: d["pct_chg"] for c, d in panel.items()}).reindex(C.index)
dates = C.index
vr = A.rolling(20).mean() / A.rolling(120).mean()
ma20 = C.rolling(20).mean()
ma60 = C.rolling(60).mean()
low120 = C.rolling(120).min()
mktvr = A.sum(axis=1).rolling(20).mean() / A.sum(axis=1).rolling(120).mean()


def run(label, minamt=5e7, need_ma20=False, need_ma60=False, no_new_low=False,
        vr_q=None, mkt_filter=False, prior_up=False):
    eq = CAP
    hold = {}
    curve = []
    turns = 0.0
    segwins = []
    i = 250
    while i < len(dates) - REBAL - 1:
        if mkt_filter and mktvr.iloc[i] < 0.8:
            curve.append((dates[i + REBAL], eq + sum(q * C.iloc[i + REBAL].get(c, 0) for c, q in hold.items() if q)))
            i += REBAL
            continue
        s = vr.iloc[i].dropna()
        idx = s.index
        a = A.iloc[i].reindex(idx)
        px = C.iloc[i].reindex(idx)
        pc = P.iloc[i].reindex(idx)
        keep = ((a > minamt).fillna(False).values & (px > 2.0).fillna(False).values
                & (pc.abs() < 9.0).fillna(False).values)
        s = s[keep]
        idx = s.index
        if need_ma20:
            m20 = ma20.iloc[i].reindex(idx)
            s = s[(C.iloc[i].reindex(idx) > m20).fillna(False).values]
            idx = s.index
        if need_ma60:
            m60 = ma60.iloc[i].reindex(idx)
            s = s[(C.iloc[i].reindex(idx) > m60).fillna(False).values]
            idx = s.index
        if no_new_low:
            lw = low120.iloc[i].reindex(idx)
            s = s[(C.iloc[i].reindex(idx) > lw).fillna(False).values]
            idx = s.index
        if prior_up:
            r20 = (C.iloc[i].reindex(idx) / C.iloc[i - 20].reindex(idx) - 1)
            s = s[(r20 > 0).fillna(False).values]
            idx = s.index
        if vr_q is not None and len(s) > 50:
            s = s[s <= s.quantile(vr_q)]
        if len(s) < TOPN * 3:
            curve.append((dates[i + REBAL], eq + sum(q * C.iloc[i + REBAL].get(c, 0) for c, q in hold.items() if q)))
            i += REBAL
            continue
        pick = s.nsmallest(TOPN).index
        ex = i + 1
        port = eq + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
        for c in list(hold.keys()):
            if c not in pick:
                p = O.iloc[ex].get(c)
                if p and p == p:
                    q = hold[c]
                    eq += cn.sell_proceeds(p, q, c, 5e8)
                    turns += q * p
                    del hold[c]
        per = port / len(pick)
        for c in pick:
            p = O.iloc[ex].get(c)
            if not p or p != p:
                continue
            want = per
            have = hold.get(c, 0) * p
            if want - have > p * 100:
                qty = int((want - have) / p / 100) * 100
                if qty > 0:
                    cost = cn.buy_cost(p, qty, c, 5e8)
                    if cost <= eq:
                        eq -= cost
                        hold[c] = hold.get(c, 0) + qty
                        turns += qty * p
        val = eq + sum(q * C.iloc[i + REBAL].get(c, 0) for c, q in hold.items() if q)
        if curve:
            segwins.append(1 if val > curve[-1][1] else 0)
        curve.append((dates[i + REBAL], val))
        i += REBAL
    final = curve[-1][1]
    yrs = (curve[-1][0] - curve[0][0]).days / 365.25
    cagr = (final / CAP) ** (1 / yrs) - 1
    peak = CAP
    mdd = 0.0
    for _, v in curve:
        if v > peak:
            peak = v
        dd = (v - peak) / peak
        if dd < mdd:
            mdd = dd
    yr = {}
    for d, v in curve:
        yr.setdefault(d.year, []).append(v)
    prev = CAP
    ywin = 0
    for y in sorted(yr):
        if yr[y][-1] > prev:
            ywin += 1
        prev = yr[y][-1]
    sr = sum(segwins) / len(segwins) * 100 if segwins else 0
    print(f"{label:<32}{cagr*100:>8.2f}%{mdd*100:>9.1f}%{sr:>9.1f}%{ywin}/{len(yr):<5}{turns/CAP/yrs:>8.2f}x")


print(f"{'前置条件（个股级）':<32}{'年化':>9}{'最大回撤':>10}{'区间胜率':>10}{'年度胜':<7}{'换手/年':>9}")
run("基准 低量")
run("+ 站上MA20", need_ma20=True)
run("+ 站上MA60", need_ma60=True)
run("+ 未创新低(120日)", no_new_low=True)
run("+ 前20日为正", prior_up=True)
run("+ 站上MA20 且 未创新低", need_ma20=True, no_new_low=True)
run("+ 成交额>1亿", minamt=1e8)
run("+ 成交额>2亿", minamt=2e8)
run("+ 量比最低10%", vr_q=0.10)
run("+ 量比最低25%", vr_q=0.25)
run("+ 站上MA20 + 市场量比>0.8", need_ma20=True, mkt_filter=True)
run("+ 未创新低 + 市场量比>0.8", no_new_low=True, mkt_filter=True)
run("+ 成交额>1亿 + 未创新低", minamt=1e8, no_new_low=True)
run("+ 前20日为正 + 市场量比>0.8", prior_up=True, mkt_filter=True)

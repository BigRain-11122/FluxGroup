# factor_scan.py —— 随机基准 + 价格量能类因子扫描
# 目的：回答"低量 14.8% 到底算不算强"——需要同宇宙同调仓的随机基准做对照。
# 同时扫可算的因子（无估值数据，只能用价量面）：
#   lowamt(低量) / lowvol(低波动) / smallcap(小市值代理=低价) / illiq(低流动性)
#   / lowamt+lowvol / lowamt+smallcap / 及其组合
import os, glob, sys, random
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
BARS = os.path.join(BM, "Money02", "data", "bars")
CAP = 1_000_000.0
TOPN = 20
REBAL = 20

def load():
    m = pd.read_csv(os.path.join(BM, "data", "fundamental", "b_layer_mask.csv"), dtype={"code": str})
    ok = set(m[m["ok_static"] == True]["code"].str.zfill(6))
    panel = {}
    for f in sorted(glob.glob(os.path.join(BARS, "*.parquet"))):
        c = os.path.basename(f)[:-8]
        if not c.isdigit() or c not in ok:
            continue
        try:
            df = pd.read_parquet(f, columns=["date", "open", "close", "amount", "pct_chg", "turnover"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= "2016-01-01"]
        if len(df) < 250:
            continue
        panel[c] = df.set_index("date")
    return panel

def backtest(C, O, A, P, dates, picker, label):
    eq = CAP; hold = {}; curve = []; turns = 0.0
    i = 250
    while i < len(dates) - REBAL - 1:
        s = picker(i)
        if s is None or len(s) < TOPN:
            curve.append((dates[i + REBAL], eq + sum(q * C.iloc[i + REBAL].get(c, 0) for c, q in hold.items() if q)))
            i += REBAL; continue
        pick = s[:TOPN]
        ex = i + 1
        port = eq + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
        for c in list(hold.keys()):
            if c not in pick:
                p = O.iloc[ex].get(c)
                if p and p == p:
                    q = hold[c]; eq += cn.sell_proceeds(p, q, c, 5e8); turns += q * p; del hold[c]
        per = port / len(pick)
        for c in pick:
            p = O.iloc[ex].get(c)
            if not p or p != p: continue
            want = per; have = hold.get(c, 0) * p
            if want - have > p * 100:
                qty = int((want - have) / p / 100) * 100
                if qty > 0:
                    cost = cn.buy_cost(p, qty, c, 5e8)
                    if cost <= eq:
                        eq -= cost; hold[c] = hold.get(c, 0) + qty; turns += qty * p
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
    return dict(label=label, cagr=cagr, mdd=mdd, turns=turns / CAP / yrs, ywin=f"{ywin}/{len(yr)}")

def main():
    print("加载…")
    panel = load()
    print(f"{len(panel)} 只")
    C = pd.DataFrame({c: d["close"] for c, d in panel.items()}).sort_index()
    O = pd.DataFrame({c: d["open"] for c, d in panel.items()}).reindex(C.index)
    A = pd.DataFrame({c: d["amount"] for c, d in panel.items()}).reindex(C.index)
    P = pd.DataFrame({c: d["pct_chg"] for c, d in panel.items()}).reindex(C.index)
    dates = C.index
    vr = A.rolling(20).mean() / A.rolling(120).mean()
    ret = C.pct_change()
    vol60 = ret.rolling(60).std()
    adv20 = A.rolling(20).mean()

    def base_ok(i):
        """共同的可交易过滤：过铁律 + 成交额>5000万 + 价>2 + 非涨停跌停"""
        px = C.iloc[i]; a = A.iloc[i]; pc = P.iloc[i]
        return (a > 5e7).fillna(False).values & (px > 2.0).fillna(False).values & (pc.abs() < 9.0).fillna(False).values

    def mk(factor_df, ascending=True, second=None):
        def picker(i):
            f = factor_df.iloc[i]
            s = f.dropna()
            ok = base_ok(i)
            s = s[ok[:len(s)] if len(ok) == len(s) else [True] * len(s)]
            if second is not None:
                f2 = second[0].iloc[i].reindex(s.index)
                s = s[f2.notna()]
                # 组合：标准化后相加
                z1 = (s - s.mean()) / (s.std() + 1e-12)
                z2 = (f2 - f2.mean()) / (f2.std() + 1e-12)
                z = z1 + second[1] * z2
                return list(z.sort_values(ascending=ascending).index)
            return list(s.sort_values(ascending=ascending).index)
        return picker

    print()
    print(f"{'策略':<26}{'年化':>9}{'最大回撤':>10}{'换手/年':>9}{'年度胜':>8}")
    # 随机基准（5 个种子）
    import random as _r
    rs = []
    for seed in (1, 2, 3, 4, 5):
        def rnd_picker(i, seed=seed):
            ok = base_ok(i)
            cand = [c for c, k in zip(C.columns, ok) if k]
            if len(cand) < TOPN: return None
            _r.seed(seed * 10000 + i)
            return _r.sample(cand, TOPN)
        r = backtest(C, O, A, P, dates, rnd_picker, f"random-{seed}")
        rs.append(r)
    avg = {k: np.mean([x[k] for x in rs]) for k in ("cagr", "mdd", "turns")}
    print(f"{'① 随机20只（5种子均值）':<26}{avg['cagr']*100:>8.2f}%{avg['mdd']*100:>9.1f}%{avg['turns']:>9.2f}x{'--':>8}")

    tests = [
        ("② 低量 lowamt", mk(vr, True)),
        ("③ 低波动 lowvol", mk(vol60, True)),
        ("④ 低价 smallcap代理", mk(C, True)),
        ("⑤ 低流动性 illiq", mk(adv20, True)),
        ("⑥ 高流动性", mk(adv20, False)),
        ("⑦ 低量+低波动", mk(vr, True, (vol60, 1.0))),
        ("⑧ 低量+低价", mk(vr, True, (C, 1.0))),
    ]
    for lab, pk in tests:
        r = backtest(C, O, A, P, dates, pk, lab)
        print(f"{lab:<26}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['turns']:>9.2f}x{r['ywin']:>8}")

if __name__ == "__main__":
    main()

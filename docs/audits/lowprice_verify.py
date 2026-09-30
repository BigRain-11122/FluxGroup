# lowprice_verify.py —— 低价因子抗偏差验证
# 关键问题：低价 26.8% 有多少来自"小市值+幸存者偏差"？逐步提高流动性下限、加可交易性约束，看衰减。
import os, glob, sys
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
            df = pd.read_parquet(f, columns=["date", "open", "close", "amount", "pct_chg"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= "2016-01-01"]
        if len(df) < 250:
            continue
        panel[c] = df.set_index("date")
    return panel

def run(C, O, A, P, dates, label, minamt, use_amount_as_signal=False, random_seed=None):
    eq = CAP; hold = {}; curve = []; turns = 0.0; picks_amt = []
    i = 250
    while i < len(dates) - REBAL - 1:
        px = C.iloc[i]; a = A.iloc[i]; pc = P.iloc[i]
        ok = ((a > minamt).fillna(False).values & (px > 2.0).fillna(False).values
              & (pc.abs() < 9.0).fillna(False).values)
        cand = [c for c, k in zip(C.columns, ok) if k]
        if random_seed is not None:
            import random
            random.seed(random_seed * 7919 + i)
            pick = random.sample(cand, min(TOPN, len(cand))) if len(cand) >= TOPN else None
        else:
            if len(cand) < TOPN:
                pick = None
            else:
                s = (A.rolling(20).mean().iloc[i] if use_amount_as_signal else px).reindex(cand).dropna()
                if len(s) < TOPN:
                    pick = None
                else:
                    pick = list(s.nsmallest(TOPN).index)
                    picks_amt.append(s.loc[pick].median() if not use_amount_as_signal else 0)
        if pick is None:
            curve.append((dates[i + REBAL], eq + sum(q * C.iloc[i + REBAL].get(c, 0) for c, q in hold.items() if q)))
            i += REBAL; continue
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
    cagr = (final / CAP) ** (1 / yrs) - 1 if final > 0 else -1
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
    med_amt = np.median(picks_amt) / 1e8 if picks_amt else 0
    print(f"{label:<34}{cagr*100:>8.2f}%{mdd*100:>9.1f}%{turns/CAP/yrs:>8.2f}x{ywin}/{len(yr):<5}{med_amt:>8.2f}亿")

def main():
    print("加载…")
    panel = load()
    C = pd.DataFrame({c: d["close"] for c, d in panel.items()}).sort_index()
    O = pd.DataFrame({c: d["open"] for c, d in panel.items()}).reindex(C.index)
    A = pd.DataFrame({c: d["amount"] for c, d in panel.items()}).reindex(C.index)
    P = pd.DataFrame({c: d["pct_chg"] for c, d in panel.items()}).reindex(C.index)
    dates = C.index
    print(f"{len(panel)} 只\n")
    print(f"{'策略':<34}{'年化':>9}{'最大回撤':>10}{'换手/年':>9}{'年度胜':<7}{'选中额中位':>10}")
    # 随机基准
    for seed in (1, 2, 3):
        run(C, O, A, P, dates, f"随机20只 seed={seed}", 5e7, random_seed=seed)
    print()
    # 低价因子：逐步提高流动性下限
    for amt in (5e7, 1e8, 2e8, 5e8, 1e9, 2e9):
        run(C, O, A, P, dates, f"低价 成交额>{amt/1e8:.1f}亿", amt)
    print()
    # 低流动性因子对照
    for amt in (5e7, 2e8):
        run(C, O, A, P, dates, f"低流动性 成交额>{amt/1e8:.1f}亿", amt, use_amount_as_signal=True)

if __name__ == "__main__":
    main()

# surv_bias_impact.py —— 幸存者偏差对"低量"信号的影响量化
# 三种口径对比，同一信号（低量=近20日均额/近120日均额 最小）：
#   A 原始面板（零退市·偏差口径）
#   B 剔退市风险股（过去 120 日内出现过 ≤-50% 的 20 日跌幅者剔除）
#   C 对退市风险股施加违约式清算（最后有效价 × 0.3，模拟退市前暴跌残余）
# 目的：判断"低量"信号是真机制，还是偏差产物。
import os, glob, sys, math
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BARS = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\Money02\data\bars"
START = "2016-01-01"
CAPITAL = 1_000_000.0
TOPN = 20
REBAL = 60

def load():
    out = {}
    for f in sorted(glob.glob(os.path.join(BARS, "*.parquet"))):
        code = os.path.basename(f)[:-8]
        if not code.isdigit(): continue
        try:
            df = pd.read_parquet(f, columns=["date","open","close","amount"])
        except Exception: continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= START]
        if len(df) < 250: continue
        out[code] = df.set_index("date")
    return out

def run(C, O, A, mode, distress=None):
    dates = C.index
    A20 = A.rolling(20).mean(); A120 = A.rolling(120).mean()
    vr = A20 / A120
    ret20 = C / C.shift(20) - 1.0
    equity = CAPITAL; hold = {}; curve = []; turns = 0.0
    i = 250
    while i < len(dates) - REBAL - 1:
        s = vr.iloc[i].dropna()
        a = A.iloc[i]; px = C.iloc[i]
        s = s[s.index.isin(a.dropna().index)]
        ok = (a.reindex(s.index) > 5e7).fillna(False).values & (px.reindex(s.index) > 2.0).fillna(False).values
        s = s[ok]
        if distress is not None:
            s = s[~s.index.isin(distress[i])]
        if len(s) < TOPN:
            i += REBAL; continue
        pick = s.nsmallest(TOPN).index
        ex = i + 1
        port = equity + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
        for c in list(hold.keys()):
            if c not in pick:
                p = O.iloc[ex].get(c)
                if p and p == p:
                    q = hold[c]
                    # 清算口径：若该股被标记退市风险，按 0.3 倍价清算
                    mult = 0.3 if (distress is not None and c in distress[i]) else 1.0
                    equity += cn.sell_proceeds(p * mult, q, c, 5e8)
                    turns += q * p
                    del hold[c]
        per = port / len(pick)
        for c in pick:
            p = O.iloc[ex].get(c)
            if not p or p != p: continue
            mult = 0.3 if (distress is not None and c in distress[i]) else 1.0
            p2 = p * mult
            want = per; have = hold.get(c, 0) * p
            if want - have > p * 100:
                qty = int((want - have) / p / 100) * 100
                if qty > 0:
                    cost = cn.buy_cost(p2, qty, c, 5e8)
                    if cost <= equity:
                        equity -= cost; hold[c] = hold.get(c, 0) + qty; turns += qty * p
        val = equity + sum(q * C.iloc[i+REBAL].get(c, 0) for c, q in hold.items() if q)
        curve.append((dates[i+REBAL], val)); i += REBAL
    if not curve: return None
    final = curve[-1][1]
    yrs = (curve[-1][0]-curve[0][0]).days/365.25
    cagr = (final/CAPITAL)**(1/yrs)-1 if final > 0 else -1
    peak = CAPITAL; mdd = 0.0
    for _, v in curve:
        if v > peak: peak = v
        dd = (v-peak)/peak
        if dd < mdd: mdd = dd
    return dict(cagr=cagr, mdd=mdd, turns=turns/CAPITAL/yrs, n=len(curve))

def main():
    print("加载面板…")
    panel = load()
    print(f"{len(panel)} 只")
    C = pd.DataFrame({c: d["close"] for c, d in panel.items()}).sort_index()
    O = pd.DataFrame({c: d["open"] for c, d in panel.items()}).reindex(C.index)
    A = pd.DataFrame({c: d["amount"] for c, d in panel.items()}).reindex(C.index)
    # 退市风险标记：过去 120 日内出现过 20 日跌幅 ≤ -50%
    ret20 = C / C.shift(20) - 1.0
    distress_flag = (ret20 <= -0.50)
    distress = {i: set(distress_flag.columns[distress_flag.iloc[i].fillna(False).values])
                for i in range(len(C.index))}
    n_flagged = sum(len(v) for v in distress.values())
    print(f"退市风险标记总数 {n_flagged}（过去120日内出现≤-50%的20日跌幅）\n")

    print(f"{'口径':<28}{'年化':>9}{'最大回撤':>10}{'换手/年':>9}")
    for lab, ds in (("A 原始面板（有偏差）", None),
                    ("B 剔退市风险股", distress),
                    ("C 风险股按0.3清算", distress)):
        r = run(C, O, A, "lowamt", ds)
        if r:
            print(f"{lab:<28}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['turns']:>9.2f}")

if __name__ == "__main__":
    main()

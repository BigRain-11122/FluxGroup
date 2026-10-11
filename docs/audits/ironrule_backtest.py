# ironrule_backtest.py —— 按第一铁律（不买亏损/ST/退市风险）筛选后的真实回测
# 筛选面：data/fundamental/b_layer_mask.csv 的 ok_static=True（eliminates r1_loss + r2_st）
#        外加：价格>2、成交额>5000万、剔除信号日涨停
# 目的：得出用户"现实中真能执行"的组合表现，而非纸面数字。
import os, glob, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
BARS = os.path.join(BM, "Money02", "data", "bars")
MASK = os.path.join(BM, "data", "fundamental", "b_layer_mask.csv")
START = "2016-01-01"
CAPITAL = 1_000_000.0
TOPN = 20

def load_mask():
    m = pd.read_csv(MASK, dtype={"code": str})
    ok = set(m[m["ok_static"] == True]["code"].str.zfill(6))
    return ok, len(m)

def load_panel(ok_codes):
    out = {}
    for f in sorted(glob.glob(os.path.join(BARS, "*.parquet"))):
        code = os.path.basename(f)[:-8]
        if not code.isdigit() or code not in ok_codes:
            continue
        try:
            df = pd.read_parquet(f, columns=["date", "open", "close", "amount", "pct_chg"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= START]
        if len(df) < 250:
            continue
        out[code] = df.set_index("date")
    return out

def main():
    ok, total = load_mask()
    print(f"b_layer_mask: 全体 {total} 只 → ok_static(过第一铁律) {len(ok)} 只")
    panel = load_panel(ok)
    print(f"面板加载 {len(panel)} 只（已过滤亏损/ST）· 区间 {START}+")
    C = pd.DataFrame({c: d["close"] for c, d in panel.items()}).sort_index()
    O = pd.DataFrame({c: d["open"] for c, d in panel.items()}).reindex(C.index)
    A = pd.DataFrame({c: d["amount"] for c, d in panel.items()}).reindex(C.index)
    P = pd.DataFrame({c: d["pct_chg"] for c, d in panel.items()}).reindex(C.index)
    dates = C.index
    print(f"矩阵 {C.shape[0]} × {C.shape[1]}\n")

    ret20 = C / C.shift(20) - 1.0
    ret60 = C / C.shift(60) - 1.0
    A20 = A.rolling(20).mean(); A120 = A.rolling(120).mean()
    vr = A20 / A120

    def run(mode, rebal, lb=20):
        equity = CAPITAL; hold = {}; curve = []; turns = 0.0; wins_detail = []
        i = 250
        while i < len(dates) - rebal - 1:
            if mode == "lowamt":
                s = vr.iloc[i].dropna()
            elif mode == "reversal":
                s = ret20.iloc[i].dropna() if lb == 20 else ret60.iloc[i].dropna()
            else:
                s = ret20.iloc[i].dropna()
            a = A.iloc[i].reindex(s.index); px = C.iloc[i].reindex(s.index); pc = P.iloc[i].reindex(s.index)
            keep = ((a > 5e7).fillna(False).values & (px > 2.0).fillna(False).values
                    & (pc.abs() < 9.0).fillna(False).values)
            s = s[keep]
            if len(s) < TOPN * 5:
                i += rebal; continue
            if mode == "lowamt":
                pick = s.nsmallest(TOPN).index
            else:
                pick = s.nsmallest(TOPN).index if mode == "reversal" else s.nlargest(TOPN).index
            ex = i + 1
            port = equity + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
            for c in list(hold.keys()):
                if c not in pick:
                    p = O.iloc[ex].get(c)
                    if p and p == p:
                        q = hold[c]
                        equity += cn.sell_proceeds(p, q, c, 5e8); turns += q * p
                        del hold[c]
            per = port / len(pick)
            for c in pick:
                p = O.iloc[ex].get(c)
                if not p or p != p: continue
                want = per; have = hold.get(c, 0) * p
                if want - have > p * 100:
                    qty = int((want - have) / p / 100) * 100
                    if qty > 0:
                        cost = cn.buy_cost(p, qty, c, 5e8)
                        if cost <= equity:
                            equity -= cost; hold[c] = hold.get(c, 0) + qty; turns += qty * p
            val = equity + sum(q * C.iloc[i+rebal].get(c, 0) for c, q in hold.items() if q)
            curve.append((dates[i+rebal], val))
            # 记录区间收益（用于胜率）
            if len(curve) > 1:
                wins_detail.append(1 if val > curve[-2][1] else 0)
            i += rebal
        if not curve: return None
        final = curve[-1][1]
        yrs = (curve[-1][0]-curve[0][0]).days/365.25
        cagr = (final/CAPITAL)**(1/yrs)-1 if final > 0 else -1
        peak = CAPITAL; mdd = 0.0
        for _, v in curve:
            if v > peak: peak = v
            dd = (v-peak)/peak
            if dd < mdd: mdd = dd
        pos_rate = sum(wins_detail)/len(wins_detail) if wins_detail else 0
        yr = {}
        for d, v in curve: yr.setdefault(d.year, []).append(v)
        prev = CAPITAL; ywin = 0; ytot = 0
        for y in sorted(yr):
            r = yr[y][-1]/prev - 1
            ytot += 1
            if r > 0: ywin += 1
            prev = yr[y][-1]
        return dict(cagr=cagr, mdd=mdd, turns=turns/CAPITAL/yrs,
                    pos_rate=pos_rate, ywin=f"{ywin}/{ytot}", n=len(curve))

    print(f"{'模式':<12}{'回看':>5}{'调仓':>6}{'年化':>9}{'最大回撤':>10}{'区间胜率':>10}{'年度胜':>8}{'换手/年':>9}")
    for mode, lb in (("lowamt", 0), ("reversal", 20), ("reversal", 60), ("momentum", 20)):
        for rebal in (20, 60):
            r = run(mode, rebal, lb)
            if not r:
                print(f"{mode:<12}{lb:>5}{rebal:>6}   无样本"); continue
            print(f"{mode:<12}{lb:>5}{rebal:>6}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%"
                  f"{r['pos_rate']*100:>9.1f}%{r['ywin']:>8}{r['turns']:>9.2f}")

if __name__ == "__main__":
    main()

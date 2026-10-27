# stock_xsection2.py —— 修正版：剔退市/仙股 + 排除涨停 + 基准对照
# 修正 1：反转 −100% 的根因=买入退市/长期停牌股（面板含已退市）。加双门：末次交易日须在样本末期 90 天内；价格>2 元。
# 修正 2：排除信号日涨停股（买不到）。
# 修正 3：加等权全市场与沪深300 对照，并输出年度胜率（用户要的高胜率指标）。
import os, glob, sys, math, statistics
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BARS = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\Money02\data\bars"
IDX = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily\510300.csv"
START = "2016-01-01"
CAPITAL = 1_000_000.0
TOPN = 20

def load_panel():
    fs = sorted(glob.glob(os.path.join(BARS, "*.parquet")))
    out = {}
    for f in fs:
        code = os.path.basename(f)[:-8]
        if not code.isdigit():
            continue
        try:
            df = pd.read_parquet(f, columns=["date", "open", "close", "amount", "preclose", "pct_chg"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= START]
        if len(df) < 250:
            continue
        out[code] = df.set_index("date")
    return out

def main():
    print("加载…")
    panel = load_panel()
    print(f"个股 {len(panel)} 只")
    closes = {c: df["close"] for c, df in panel.items()}
    opens = {c: df["open"] for c, df in panel.items()}
    amts = {c: df["amount"] for c, df in panel.items()}
    pcts = {c: df["pct_chg"] for c, df in panel.items()}
    C = pd.DataFrame(closes).sort_index()
    O = pd.DataFrame(opens).reindex(C.index)
    A = pd.DataFrame(amts).reindex(C.index)
    P = pd.DataFrame(pcts).reindex(C.index)
    dates = C.index
    last_valid = {c: df.index[-1] for c, df in panel.items()}
    end = dates[-1]
    alive = {c for c, d in last_valid.items() if (end - d).days <= 90}
    print(f"末次交易在末期 90 天内的存活标的 {len(alive)} 只（剔除 {len(panel)-len(alive)} 只退市/长停）")

    # 基准：沪深300
    idx = pd.read_csv(IDX, parse_dates=["date"]).set_index("date")["close"].reindex(dates).ffill()

    ret_l = C / C.shift(20) - 1.0
    A20 = A.rolling(20).mean(); A120 = A.rolling(120).mean()
    vr = A20 / A120

    def run(mode, rebal, hold_n=TOPN):
        equity = CAPITAL; hold = {}; curve = []; turnover = 0.0
        i = 250
        while i < len(dates) - rebal - 1:
            sig = ret_l.iloc[i].dropna()
            a = A.iloc[i].reindex(sig.index)
            px = C.iloc[i].reindex(sig.index)
            pc = P.iloc[i].reindex(sig.index)
            keep = (a > 5e7).fillna(False).values & (px > 2.0).fillna(False).values & (pc < 9.0).fillna(False).values
            keep = keep & pd.Index(sig.index).isin(alive)
            sig = sig[keep]
            if len(sig) < 300:
                i += rebal; continue
            if mode == "reversal":
                pick = sig.nsmallest(hold_n).index
            elif mode == "momentum":
                pick = sig.nlargest(hold_n).index
            elif mode == "lowamt":
                s = vr.iloc[i].dropna()
                s = s[s.index.isin(sig.index)]
                pick = s.nsmallest(hold_n).index if len(s) >= hold_n else sig.nsmallest(hold_n).index
            elif mode == "lowamt_highret":
                # 双重门：低量（缩量）+ 20日收益为正（不在下跌中接刀）
                s = vr.iloc[i].dropna(); s = s[s.index.isin(sig.index)]
                pos = sig[sig > 0]
                s2 = s[s.index.isin(pos.index)]
                pick = s2.nsmallest(hold_n).index if len(s2) >= hold_n else None
                if pick is None:
                    i += rebal; continue
            else:
                i += rebal; continue

            ex = i + 1
            port_val = equity + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
            for c in list(hold.keys()):
                if c not in pick:
                    p = O.iloc[ex].get(c)
                    if p and p == p:
                        q = hold[c]
                        equity += cn.sell_proceeds(p, q, c, 5e8); turnover += q * p
                        del hold[c]
            per = port_val / len(pick)
            for c in pick:
                p = O.iloc[ex].get(c)
                if not p or p != p: continue
                want = per; have = hold.get(c, 0) * p
                if want - have > p * 100:
                    qty = int((want - have) / p / 100) * 100
                    if qty > 0:
                        cost = cn.buy_cost(p, qty, c, 5e8)
                        if cost <= equity:
                            equity -= cost; hold[c] = hold.get(c, 0) + qty; turnover += qty * p
            val = equity + sum(q * C.iloc[i+rebal].get(c, 0) for c, q in hold.items() if q)
            curve.append((dates[i+rebal], val)); i += rebal
        if not curve: return None
        final = curve[-1][1]
        yrs = (curve[-1][0] - curve[0][0]).days / 365.25
        cagr = (final/CAPITAL)**(1/yrs)-1 if final > 0 else -1
        peak = CAPITAL; mdd = 0.0
        for _, v in curve:
            if v > peak: peak = v
            dd = (v-peak)/peak
            if dd < mdd: mdd = dd
        # 年度胜率（vs 沪深300）
        yr = {}
        for d, v in curve: yr.setdefault(d.year, []).append(v)
        wins = tot = 0; prev = CAPITAL
        for y in sorted(yr):
            seg = idx[idx.index.year == y]
            if len(seg) > 5:
                bt = seg.iloc[-1]/seg.iloc[0]-1
                r = yr[y][-1]/prev-1
                tot += 1
                if r > bt: wins += 1
            prev = yr[y][-1]
        return dict(cagr=cagr, mdd=mdd, turns=turnover/CAPITAL/yrs, win=f"{wins}/{tot}")

    print()
    print(f"{'模式':<18}{'调仓':>6}{'年化':>9}{'最大回撤':>10}{'换手/年':>9}{'年度胜':>8}")
    for rebal in (20, 60):
        for mode in ("reversal", "momentum", "lowamt", "lowamt_highret"):
            r = run(mode, rebal)
            if not r:
                print(f"{mode:<18}{rebal:>6}   无样本"); continue
            print(f"{mode:<18}{rebal:>6}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['turns']:>9.2f}{r['win']:>8}")

    # 基准同期
    b0, b1 = idx.iloc[250], idx.iloc[-1]
    yrs = (dates[-1]-dates[250]).days/365.25
    print(f"\n沪深300 同期年化 {((b1/b0)**(1/yrs)-1)*100:.2f}%")

if __name__ == "__main__":
    main()

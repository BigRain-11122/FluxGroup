# stock_xsection.py —— 股票池横截面反转实测（5,222 只 · 长期持有期）
# 目的：回答"宽截面 + 低频"是否就是有效组合（我此前用 31 只 ETF 测横截面→无效，
#       病因是宽度不足）。此处用全部个股 parquet 面板。
# 口径：每 N 日调仓；信号=过去 L 日收益（反转=取最小）/过去 L 日量比；
#       次一交易日开盘成交；成本用 cost_model_cn.py 股票口径（含印花税+过户费）。
import os, glob, sys, math, statistics
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

BARS = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\Money02\data\bars"
START = "2016-01-01"          # 面板在 2015 后更可靠；且有完整牛熊
CAPITAL = 1_000_000.0
TOPN = 20                     # 持有 20 只（百万级散户可执行）
RT_STOCK_BP = None            # 由 cost_model_cn 动态算

def load_panel():
    fs = sorted(glob.glob(os.path.join(BARS, "*.parquet")))
    out = {}
    for f in fs:
        code = os.path.basename(f)[:-8]
        if not code.isdigit():
            continue
        try:
            df = pd.read_parquet(f, columns=["date", "open", "close", "amount", "turnover"])
        except Exception:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= START]
        if len(df) < 300:
            continue
        out[code] = df.set_index("date")
    return out

def build_matrices(panel):
    close = {}
    open_ = {}
    amt = {}
    for c, df in panel.items():
        close[c] = df["close"]
        open_[c] = df["open"]
        amt[c] = df["amount"]
    C = pd.DataFrame(close).sort_index()
    O = pd.DataFrame(open_).reindex(C.index)
    A = pd.DataFrame(amt).reindex(C.index)
    return C, O, A

def backtest(C, O, A, lookback, rebal, mode):
    dates = C.index
    ret_l = C / C.shift(lookback) - 1.0
    # 量比：近 20 日均额 / 近 120 日均额
    A20 = A.rolling(20).mean()
    A120 = A.rolling(120).mean()
    vr = A20 / A120
    equity = CAPITAL
    curve = []
    turnover_notional = 0.0
    trades = 0
    hold = {}
    i = 250
    while i < len(dates) - rebal - 1:
        sig = ret_l.iloc[i].dropna()
        # 基本过滤：价格>1元、成交额>5000万（流动性）——按 sig.index 对齐，避免 pandas 索引错配
        a = A.iloc[i].reindex(sig.index)
        px = C.iloc[i].reindex(sig.index)
        ok = sig.index[(a > 5e7).fillna(False).values & (px > 1.0).fillna(False).values]
        sig = sig[ok]
        if len(sig) < 200:
            i += rebal
            continue
        if mode == "reversal":
            pick = sig.nsmallest(TOPN).index
        elif mode == "momentum":
            pick = sig.nlargest(TOPN).index
        elif mode == "lowvol_amt":
            s = vr.iloc[i].dropna()
            s = s[s.index.isin(ok)]
            pick = s.nsmallest(TOPN).index if len(s) >= TOPN else sig.nsmallest(TOPN).index
        else:
            i += rebal; continue

        # 执行：次一交易日开盘
        ex = i + 1
        entry = O.iloc[ex][pick]
        cur = {}
        # 估值
        port_val = equity + sum(q * C.iloc[i].get(c, 0) for c, q in hold.items())
        # 清掉不在新目标里的
        for c in list(hold.keys()):
            if c not in pick:
                p = O.iloc[ex].get(c)
                if p and p == p:
                    q = hold[c]
                    equity += cn.sell_proceeds(p, q, c, 5e8)
                    turnover_notional += q * p
                    del hold[c]
        # 等权买入
        per = port_val / TOPN
        for c in pick:
            p = entry.get(c)
            if not p or p != p:
                continue
            have = hold.get(c, 0) * p
            want = per
            if want - have > p * 100:
                qty = int((want - have) / p / 100) * 100
                if qty > 0:
                    cost = cn.buy_cost(p, qty, c, 5e8)
                    if cost <= equity:
                        equity -= cost
                        hold[c] = hold.get(c, 0) + qty
                        turnover_notional += qty * p
        trades += 1
        val = equity + sum(q * C.iloc[i + rebal].get(c, 0) for c, q in hold.items() if q)
        curve.append((dates[i + rebal], val))
        i += rebal
    if not curve:
        return None
    final = curve[-1][1]
    yrs = (curve[-1][0] - curve[0][0]).days / 365.25
    cagr = (final / CAPITAL) ** (1 / yrs) - 1 if final > 0 else -1
    peak = CAPITAL; mdd = 0.0
    for _, v in curve:
        if v > peak: peak = v
        dd = (v - peak) / peak
        if dd < mdd: mdd = dd
    # 年度胜率 vs 等权全市场
    return dict(final=final, cagr=cagr, mdd=mdd, turns=turnover_notional/CAPITAL/yrs, rebs=trades, yrs=yrs)

def main():
    print("加载个股面板…")
    panel = load_panel()
    print(f"可用个股 {len(panel)} 只")
    C, O, A = build_matrices(panel)
    print(f"矩阵 {C.shape[0]} 交易日 × {C.shape[1]} 只（{C.index[0].date()} → {C.index[-1].date()}）")
    print()
    print(f"{'模式':<16}{'回看':>6}{'调仓':>6}{'年化':>9}{'最大回撤':>10}{'换手/年':>9}{'调仓次数':>9}")
    for lookback in (20, 60, 120):
        for rebal in (20, 60):
            for mode in ("reversal", "momentum", "lowvol_amt"):
                r = backtest(C, O, A, lookback, rebal, mode)
                if not r:
                    print(f"{mode:<16}{lookback:>6}{rebal:>6}   无样本"); continue
                print(f"{mode:<16}{lookback:>6}{rebal:>6}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['turns']:>9.2f}{r['rebs']:>9}")

if __name__ == "__main__":
    main()

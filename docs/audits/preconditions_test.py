# preconditions_test.py —— 前置条件（大盘水温/广度）对"低量选股"的增益实测
# 基准：低量选股 TOP20 · 20 日调仓 · 第一铁律过滤（年化 14.80% / 回撤 -25.8% / 8-10 年胜）
# 逐个加前置条件，看是否"降回撤 + 提胜率"而不砍收益。
import os, glob, sys
import pandas as pd
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

def main():
    panel = load()
    print(f"面板 {len(panel)} 只（已过第一铁律）")
    C = pd.DataFrame({c: d["close"] for c, d in panel.items()}).sort_index()
    O = pd.DataFrame({c: d["open"] for c, d in panel.items()}).reindex(C.index)
    A = pd.DataFrame({c: d["amount"] for c, d in panel.items()}).reindex(C.index)
    P = pd.DataFrame({c: d["pct_chg"] for c, d in panel.items()}).reindex(C.index)
    dates = C.index
    vr = A.rolling(20).mean() / A.rolling(120).mean()

    # ---------- 大盘水温指标 ----------
    # 1) 广度：收盘价 > 自身 200 日均线的股票占比
    ma200 = C.rolling(200).mean()
    breadth = (C > ma200).sum(axis=1) / (C.notna() & ma200.notna()).sum(axis=1)
    breadth = breadth.replace([float('inf')], float('nan'))
    # 2) 全市场量能：20日总成交额 / 120日总成交额
    tot = A.sum(axis=1)
    mkt_vr = tot.rolling(20).mean() / tot.rolling(120).mean()
    # 3) 等权指数 vs 自身 MA200（广度版的趋势）
    eq_idx = (C / C.iloc[250]).mean(axis=1)
    eq_ma200 = eq_idx.rolling(200).mean()
    eq_above = (eq_idx > eq_ma200)
    # 4) 全市场 20 日收益（择时）
    mkt_r20 = eq_idx / eq_idx.shift(20) - 1

    def run(cond=None, label=""):
        eq = CAP; hold = {}; curve = []; turns = 0.0; idle = 0; total = 0
        i = 250
        while i < len(dates) - REBAL - 1:
            total += 1
            allow = True
            if cond is not None:
                allow = cond(i)
            if not allow:
                idle += 1
                # 空仓等待：不交易，仅估值
                val = eq + sum(q * C.iloc[i+REBAL].get(c, 0) for c, q in hold.items() if q)
                curve.append((dates[i+REBAL], val))
                i += REBAL
                continue
            s = vr.iloc[i].dropna()
            a = A.iloc[i].reindex(s.index); px = C.iloc[i].reindex(s.index); pc = P.iloc[i].reindex(s.index)
            keep = ((a > 5e7).fillna(False).values & (px > 2.0).fillna(False).values
                    & (pc.abs() < 9.0).fillna(False).values)
            s = s[keep]
            if len(s) < TOPN * 5:
                curve.append((dates[i+REBAL], eq + sum(q * C.iloc[i+REBAL].get(c, 0) for c, q in hold.items() if q)))
                i += REBAL; continue
            pick = s.nsmallest(TOPN).index
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
            val = eq + sum(q * C.iloc[i+REBAL].get(c, 0) for c, q in hold.items() if q)
            curve.append((dates[i+REBAL], val)); i += REBAL
        if not curve: return None
        final = curve[-1][1]; yrs = (curve[-1][0]-curve[0][0]).days/365.25
        cagr = (final/CAP)**(1/yrs)-1
        peak = CAP; mdd = 0.0
        for _, v in curve:
            if v > peak: peak = v
            dd = (v-peak)/peak
            if dd < mdd: mdd = dd
        yr = {}
        for d, v in curve: yr.setdefault(d.year, []).append(v)
        prev = CAP; ywin = 0
        for y in sorted(yr):
            if yr[y][-1] > prev: ywin += 1
            prev = yr[y][-1]
        return dict(cagr=cagr, mdd=mdd, turns=turns/CAP/yrs, ywin=f"{ywin}/{len(yr)}",
                    idle_pct=idle/total*100 if total else 0, final=final)

    conds = [
        ("无前置（基准）", None),
        ("广度>0.3", lambda i: breadth.iloc[i] > 0.3),
        ("广度>0.5", lambda i: breadth.iloc[i] > 0.5),
        ("市场量比>0.8", lambda i: mkt_vr.iloc[i] > 0.8),
        ("市场量比<0.8(地量)", lambda i: mkt_vr.iloc[i] < 0.8),
        ("等权指数>MA200", lambda i: bool(eq_above.iloc[i])),
        ("市场20日未深跌>-5%", lambda i: mkt_r20.iloc[i] > -0.05),
    ]
    print()
    print(f"{'前置条件':<24}{'年化':>9}{'最大回撤':>10}{'换手/年':>9}{'年度胜':<8}{'空仓占比':>9}")
    for lab, cond in conds:
        r = run(cond, lab)
        if not r:
            print(f"{lab:<24}  无样本"); continue
        print(f"{lab:<24}{r['cagr']*100:>8.2f}%{r['mdd']*100:>9.1f}%{r['turns']:>9.2f}x{r['ywin']:<8}{r['idle_pct']:>8.1f}%")

if __name__ == "__main__":
    main()

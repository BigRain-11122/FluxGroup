# dsr_pbo_fourasset.py —— 四资产策略的 DSR 与 PBO 校正（D-41 §1.4 首测）
#
# 背景：四资产策略是外审目前唯一仍在推荐的策略（跨起点已过：3年窗最差 -1.6%、跑赢基准 100%）。
#       但它是"扫了多个变体后选出的中间档"，按 §1.4 必须扣掉搜索带来的虚高。
# 方法：
#   ① 生成候选集（权重档 × 带宽 × 频率）= 我实际扫过的变体
#   ② CSCV 8 块 → C(8,4)=70 组合 → 算 PBO（过拟合概率）
#   ③ DSR：用候选集 Sharpe 的方差估 E[max SR]，对最优变体做缩减
import os, itertools, math, statistics
import pandas as pd

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
BROAD, BOND, GOLD, OVER = "510300", "511010", "518880", "513500"
CAP = 1_000_000.0

def load():
    ds = {}
    for c in (BROAD, BOND, GOLD, OVER):
        p = os.path.join(DAILY, c + ".csv")
        if not os.path.exists(p):
            return None
        ds[c] = pd.read_csv(p, parse_dates=["date"]).set_index("date")["close"]
    return ds

def build(prices):
    dates = sorted(set(prices[BROAD].index) & set(prices[BOND].index)
                   & set(prices[GOLD].index) & set(prices[OVER].index))
    px = {c: prices[c].reindex(dates).ffill() for c in prices}
    ma200 = px[BROAD].rolling(200).mean()
    hi250 = px[BROAD].rolling(250).max()
    reg = []
    for i in range(len(dates)):
        m, c, h = ma200.iloc[i], px[BROAD].iloc[i], hi250.iloc[i]
        if pd.isna(m) or pd.isna(h):
            reg.append(None)
        elif c > m:
            reg.append("PEAK")
        elif (c - h) / h <= -0.10:
            reg.append("VALLEY")
        else:
            reg.append("NEUTRAL")
    return dates, px, reg

def run(dates, px, reg, wset, band, gaps):
    """返回逐日收益序列（不含预热段）。"""
    codes = [BROAD, GOLD, OVER, BOND]
    hold = {c: 0.0 for c in codes}
    cash = CAP
    last = -999
    eq_prev = CAP
    rets = []
    for i in range(200, len(dates) - 1):
        r = reg[i]
        if r is None:
            continue
        gap = gaps[r]
        if i - last >= gap:
            last = i
            w = wset[r]
            port = cash + sum(hold[c] * px[c].iloc[i] for c in codes)
            for c in codes:
                p = px[c].iloc[i]
                if pd.isna(p) or p <= 0:
                    continue
                want = port * w[c]
                have = hold[c] * p
                if port > 0 and abs(want - have) / port < band:
                    continue
                if want > have:
                    q = int((want - have) / p / 100) * 100
                    if q > 0:
                        cost = p * q * (1 + 0.00025 + 0.001) + 5.0
                        if cost <= cash:
                            cash -= cost
                            hold[c] += q
                else:
                    q = min(int((have - want) / p / 100) * 100, int(hold[c]))
                    if q > 0:
                        cash += p * q * (1 - 0.00025 - 0.001) - 5.0
                        hold[c] -= q
        eq = cash + sum(hold[c] * px[c].iloc[i] for c in codes)
        if eq_prev > 0:
            rets.append(eq / eq_prev - 1.0)
        eq_prev = eq
    return rets

def sharpe(rs):
    if len(rs) < 30:
        return 0.0
    sd = statistics.pstdev(rs)
    return (statistics.fmean(rs) / sd * math.sqrt(252)) if sd > 0 else 0.0

def main():
    prices = load()
    if not prices:
        print("ETF 数据缺失"); return
    dates, px, reg = build(prices)
    print(f"交易日 {len(dates)}（{dates[0].date()} → {dates[-1].date()}）")

    # 候选集：我实际扫过的权重档 × 带宽 × 频率
    WSETS = {
        "std":  {"VALLEY": {BROAD:.25,GOLD:.25,OVER:.25,BOND:.25}, "NEUTRAL": {BROAD:.17,GOLD:.17,OVER:.17,BOND:.49}, "PEAK": {BROAD:.15,GOLD:.15,OVER:.15,BOND:.55}},
        "def":  {"VALLEY": {BROAD:.20,GOLD:.20,OVER:.20,BOND:.40}, "NEUTRAL": {BROAD:.15,GOLD:.15,OVER:.15,BOND:.55}, "PEAK": {BROAD:.10,GOLD:.10,OVER:.10,BOND:.70}},
        "mid":  {"VALLEY": {BROAD:.25,GOLD:.25,OVER:.25,BOND:.25}, "NEUTRAL": {BROAD:.17,GOLD:.17,OVER:.17,BOND:.49}, "PEAK": {BROAD:.15,GOLD:.15,OVER:.15,BOND:.55}},
        "aggr": {"VALLEY": {BROAD:.33,GOLD:.33,OVER:.33,BOND:.01}, "NEUTRAL": {BROAD:.17,GOLD:.17,OVER:.17,BOND:.49}, "PEAK": {BROAD:.15,GOLD:.15,OVER:.15,BOND:.55}},
        "eq":   {"VALLEY": {BROAD:.25,GOLD:.25,OVER:.25,BOND:.25}, "NEUTRAL": {BROAD:.25,GOLD:.25,OVER:.25,BOND:.25}, "PEAK": {BROAD:.25,GOLD:.25,OVER:.25,BOND:.25}},
    }
    BANDS = [0.10, 0.15, 0.20]
    GAPS = [{"VALLEY":5,"NEUTRAL":10,"PEAK":60},
            {"VALLEY":10,"NEUTRAL":20,"PEAK":120},
            {"VALLEY":20,"NEUTRAL":40,"PEAK":250}]

    cands = []
    for wn, ws in WSETS.items():
        for b in BANDS:
            for gi, g in enumerate(GAPS):
                rs = run(dates, px, reg, ws, b, g)
                cands.append({"name": f"{wn}|b{b}|g{gi}", "rets": rs, "sr": sharpe(rs),
                              "cagr": (1 + statistics.fmean(rs)) ** 252 - 1 if rs else 0})
    cands.sort(key=lambda x: -x["sr"])
    n = len(cands)
    print(f"\n候选集 N={n}（我实际扫过的权重档 × 带宽 × 频率）")
    print(f"{'候选':<16}{'年化':>9}{'Sharpe':>9}")
    for c in cands[:6]:
        print(f"{c['name']:<16}{c['cagr']*100:>8.2f}%{c['sr']:>9.2f}")
    best = cands[0]
    print(f"\n最优 = {best['name']}  Sharpe={best['sr']:.2f}")

    # ---- PBO via CSCV (8 blocks, all C(8,4)=70 splits) ----
    L = min(len(c["rets"]) for c in cands)
    M = (L // 8) * 8
    blocks = [slice(k * M // 8, (k + 1) * M // 8) for k in range(8)]
    R = {c["name"]: c["rets"][:M] for c in cands}
    names = [c["name"] for c in cands]
    overfit = 0
    total = 0
    for combo in itertools.combinations(range(8), 4):
        ins = [i for i in range(8) if i in combo]
        oos = [i for i in range(8) if i not in combo]
        def sr_on(idx, nm):
            rs = []
            for i in idx:
                rs.extend(R[nm][blocks[i]])
            return sharpe(rs)
        isr = {nm: sr_on(ins, nm) for nm in names}
        osr = {nm: sr_on(oos, nm) for nm in names}
        best_is = max(isr, key=isr.get)
        rank = sorted(osr.values()).index(osr[best_is]) / (len(names) - 1)  # 0=worst,1=best
        if rank < 0.5:
            overfit += 1
        total += 1
    pbo = overfit / total
    print(f"PBO(CSCV 8块, {total} 组合) = {pbo*100:.1f}%   （阈值 ≤25%）")

    # ---- DSR (deflated Sharpe) ----
    srs = [c["sr"] for c in cands]
    var_sr = statistics.pvariance(srs) if len(srs) > 1 else 0.0
    gamma = 0.5772156649
    Neff = n
    e_max = math.sqrt(var_sr) * ((1 - gamma) * 0 + math.sqrt(2 * math.log(Neff)) - (math.log(math.log(Neff)) + math.log(4 * math.pi)) / (2 * math.sqrt(2 * math.log(Neff)))) if var_sr > 0 and Neff > 2 else 0.0
    T = len(best["rets"])
    sr_hat = best["sr"]
    dsr = sr_hat - e_max * math.sqrt(252) / math.sqrt(T) * math.sqrt(T) / math.sqrt(252)
    # 直接用日频口径：SR_daily vs E[max] in daily units
    sr_d = sr_hat / math.sqrt(252)
    e_max_d = e_max / math.sqrt(252)
    z = (sr_d - e_max_d) * math.sqrt(T)
    from math import erf
    dsr_prob = 0.5 * (1 + erf(z / math.sqrt(2)))
    print(f"\n候选集 Sharpe 方差 = {var_sr:.3f}｜N_eff = {Neff}")
    print(f"E[max Sharpe|null] = {e_max:.2f}（年化口径）")
    print(f"最优 Sharpe = {sr_hat:.2f}")
    print(f"DSR（扣搜索后仍为正的概率）= {dsr_prob*100:.1f}%   （阈值 ≥95%）")
    print(f"\n[判读] PBO≤25% 且 DSR≥95% 才算过 §1.4；否则该策略亦须降级。")

if __name__ == "__main__":
    main()

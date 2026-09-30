# delist_correction.py —— 幸存者偏差修正量（不依赖缺失的退市行情）
#
# 思路：等权组合里，每年有 d 比例的成员"消失"（退市），而面板把它们整段剔除。
#       真值 ≈ 面板收益 − d × (典型退市损失)  （退市股在最后阶段平均跌 L）
#       再扣除"新上市股"的稀释（幸存者面板会把他们算进去，真实组合同样会，故可对冲）
# 参数：L 取保守/中性/激进三档（-50% / -70% / -90%），d 用实测退市数 / 当年宇宙规模
import os, glob, sys
import pandas as pd

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
BARS = os.path.join(BM, "Money02", "data", "bars")

# 实测退市数（akshare，本会话已取）
DELIST = {2016:2,2017:5,2018:6,2019:12,2020:20,2021:23,2022:46,2023:46,2024:55,2025:32,2026:19}

def main():
    m = pd.read_csv(os.path.join(BM, "data", "fundamental", "b_layer_mask.csv"), dtype={"code": str})
    ok = set(m[m["ok_static"] == True]["code"].str.zfill(6))
    closes = {}
    for f in sorted(glob.glob(os.path.join(BARS, "*.parquet"))):
        c = os.path.basename(f)[:-8]
        if not c.isdigit() or c not in ok:
            continue
        try:
            d = pd.read_parquet(f, columns=["date", "close"])
        except Exception:
            continue
        d["date"] = pd.to_datetime(d["date"])
        d = d[d["date"] >= "2016-01-01"]
        if len(d) < 250:
            continue
        closes[c] = d.set_index("date")["close"]
    C = pd.DataFrame(closes).sort_index()
    print(f"面板 {C.shape[1]} 只 × {C.shape[0]} 交易日")

    ew = C.pct_change().mean(axis=1)                 # 等权日收益
    alive = C.notna().sum(axis=1)                    # 每日在册数
    cum = (1 + ew.fillna(0)).cumprod()
    yrs = (C.index[-1] - C.index[0]).days / 365.25
    panel_cagr = cum.iloc[-1] ** (1 / yrs) - 1
    print(f"等权面板年化（幸存者口径） = {panel_cagr*100:.2f}%")

    print(f"\n{'年':>6}{'退市':>6}{'当年宇宙':>10}{'d(占比)':>10}{'L=-50%':>10}{'L=-70%':>10}{'L=-90%':>10}")
    total_drag = {0.5: 0.0, 0.7: 0.0, 0.9: 0.0}
    for y in sorted(DELIST):
        n = DELIST[y]
        idx = [i for i, d in enumerate(C.index) if d.year == y]
        if not idx:
            continue
        uni = float(alive.iloc[idx].mean())
        frac = n / uni if uni > 0 else 0
        row = []
        for L in (0.5, 0.7, 0.9):
            part = frac * L            # 该年一次性拖累
            total_drag[L] += part
            row.append(part * 100)
        print(f"{y:>6}{n:>6}{uni:>10.0f}{frac*100:>9.2f}%{row[0]:>9.2f}%{row[1]:>9.2f}%{row[2]:>9.2f}%")

    print(f"\n累计拖累（求和口径，近似）:")
    for L in (0.5, 0.7, 0.9):
        print(f"  L=-{L*100:.0f}%: 累计 {total_drag[L]*100:.2f}pp  →  修正后年化 ≈ "
              f"{(panel_cagr - total_drag[L]/yrs)*100:.2f}%")
    print(f"\n[解读] 这是【上界估计】：假设退市股在观测期内一次性损失 L，且未被提前剔除。")
    print(f"       真实拖累 ≤ 此值（因为等权组合在退市前就会因价格下跌而降低其权重）。")

if __name__ == "__main__":
    main()

# delist_bias_quant.py —— 退市偏差定量（用实测可取的退市名单）
# 目的：把"面板零退市"从定性变定量：2016-2026 退市多少只、占当时市场比例、退市前跌幅多大。
import os, sys, json
import pandas as pd

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"

def main():
    # 1) 退市名单（本会话已实测 akshare 可用）
    try:
        import akshare as ak
        sh = ak.stock_info_sh_delist()
        sz = ak.stock_info_sz_delist()
    except Exception as e:
        print("akshare 不可用:", str(e)[:60]); return

    sh["code"] = sh.iloc[:, 0].astype(str).str.zfill(6)
    sz["code"] = sz.iloc[:, 0].astype(str).str.zfill(6)
    sh["ddate"] = pd.to_datetime(sh.iloc[:, 3], errors="coerce")
    sz["ddate"] = pd.to_datetime(sz.iloc[:, 3], errors="coerce")
    delist = pd.concat([sh[["code", "ddate"]], sz[["code", "ddate"]]], ignore_index=True)
    delist = delist.dropna(subset=["ddate"])

    win = delist[(delist["ddate"] >= "2016-01-01") & (delist["ddate"] <= "2026-12-31")]
    print(f"退市清单合计 {len(delist)} 只｜2016-2026 区间内 {len(win)} 只")

    yr = win["ddate"].dt.year.value_counts().sort_index()
    print("逐年: " + " ".join(f"{y}:{c}" for y, c in yr.items()))

    # 2) 占当时 A 股数量的比例（用面板当前 5,222 只作分母的近似）
    panel_n = 5222
    per_year = {}
    for y, c in yr.items():
        per_year[int(y)] = round(c / panel_n * 100, 2)
    print("占当前面板比例(‰): " + " ".join(f"{y}:{v}" for y, v in per_year.items()))

    # 3) 面板覆盖率（应为 0）
    import glob
    have = set()
    for f in glob.glob(os.path.join(BM, "Money02", "data", "bars", "*.parquet")):
        c = os.path.basename(f)[:-8]
        if c.isdigit():
            have.add(c)
    inter = set(win["code"]) & have
    print(f"面板 ∩ 2016-2026退市 = {len(inter)} 只（应为 0）")

    # 4) 退市前跌幅（若能取到行情则算，否则如实标 DATA_GAP）
    print("\n退市前跌幅：需逐只行情 —— 取样 5 只尝试 akshare 历史行情")
    got = 0
    for code in list(win["code"])[:5]:
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20200101", adjust="")
            if df is None or df.empty:
                print(f"  {code}: 空"); continue
            c = df["收盘"].astype(float)
            if len(c) < 60:
                print(f"  {code}: 样本不足({len(c)})"); continue
            drop = c.iloc[-1] / c.iloc[-60] - 1
            print(f"  {code}: 退市前60日 {drop*100:+.1f}%  末价 {c.iloc[-1]:.2f}")
            got += 1
        except Exception as e:
            print(f"  {code}: 取数失败 {str(e)[:40]}")
    if got == 0:
        print("  => DATA_GAP：退市股行情未取得（须补数据面）")

if __name__ == "__main__":
    main()

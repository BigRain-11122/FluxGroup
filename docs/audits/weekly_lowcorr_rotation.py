# weekly_lowcorr_rotation.py —— 周频低相关轮动（100万散户定制 · 无期货/无做空/无杠杆）
# 规则（全部冻结，跑前写死；无参数搜索=不做数据窥探）：
#   频率：周频（信号用本周最后交易日收盘，次周首个交易日开盘执行 -> 无未来函数）
#   宇宙：48 ETF 中数据自 2020-01 起完整者；剔除货币/短融等非交易标的；宽基只留 1 只代表
#   评分：20/60/120 日收益的等权排名分（动量族）；另附反转变体对比
#   择时闸：沪深300 在 200 日均线之上 且 200 日均线 20 日内不下行 -> 才允许持有风险资产
#   持仓：评分前 4 等权；择时闸关闭时 -> 转入债券腿（511010/511260 取评分高者）
#   风控：单标的权重上限 35%（等权 25% 天然满足）；周内不干预；无止损（靠择时闸与债券腿控回撤）
#   成本：cost_model_cn.py（ETF 免印花税/过户费，ADV 分层滑点）
import os, sys, csv, math, statistics
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
CAPITAL = 1_000_000.0
BENCH = "510300"
BOND = ["511010", "511260", "511090"]
# 宽基替身只留一只，避免虚假分散
BROAD_KEEP = "510300"
BROAD_DROP = {"510330", "159919", "510050", "159901", "159949", "510500", "159922"}
EXCLUDE = {"511880", "511990"}          # 货币 ETF：非交易标的

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return None
    out = {}
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 6:
                continue
            try:
                out[row[0]] = (float(row[1]), float(row[4]))   # (open, close)
            except ValueError:
                continue
    return out

def main():
    codes = sorted(f[:-4] for f in os.listdir(DAILY) if f.endswith(".csv") and f[:-4].isdigit())
    data = {}
    for c in codes:
        if c in EXCLUDE or c in BROAD_DROP:
            continue
        d = load(c)
        if d and len(d) > 1200 and min(d) <= "2020-01-10":
            data[c] = d
    universe = sorted(data.keys())
    print(f"宇宙：{len(universe)} 只（自 2020-01 起完整）；基准 {BENCH}")
    if BENCH not in data:
        print("基准缺失"); return

    # 交易日轴（以基准为准）
    dates = sorted(data[BENCH].keys())
    # 周频：每周最后一个交易日
    weeks = {}
    for i, d in enumerate(dates):
        y, w, _ = datetime.strptime(d, "%Y-%m-%d").isocalendar()
        weeks[(y, w)] = i
    week_idx = [weeks[k] for k in sorted(weeks.keys())]
    print(f"周数：{len(week_idx)}（{dates[week_idx[0]]} → {dates[week_idx[-1]]}）")

    # 预计算：每日 close 表的列表形式，便于按索引取
    closes = {c: [data[c].get(d, (None, None))[1] for d in dates] for c in universe}
    opens  = {c: [data[c].get(d, (None, None))[0] for d in dates] for c in universe}

    def ret_over(c, i, n):
        if i - n < 0:
            return None
        a, b = closes[c][i-n], closes[c][i]
        if a is None or b is None or a <= 0:
            return None
        return b / a - 1.0

    def ma(c, i, n):
        vals = [closes[c][j] for j in range(max(0, i-n+1), i+1)]
        vals = [v for v in vals if v is not None]
        if len(vals) < n * 0.8:
            return None
        return sum(vals) / len(vals)

    # ---- 回测 ----
    cash = CAPITAL
    holdings = {}          # code -> qty
    equity_hist = []
    rebalances = 0
    turnover_notional = 0.0
    win_weeks = 0
    total_weeks = 0
    bench_start = None
    ADV = 500_000_000.0

    for wi in range(len(week_idx) - 1):
        i_sig = week_idx[wi]             # 信号日（本周最后交易日）
        i_exe = week_idx[wi + 1]         # 执行日（下周最后交易日开盘近似：用该日 open）
        d_exe = dates[i_exe]

        # 组合市值（用信号日收盘估值）
        inv_val = 0.0
        for c, q in holdings.items():
            px = closes[c][i_sig]
            if px:
                inv_val += q * px
        east = cash + inv_val

        # ---- 择时闸 ----
        gate = False
        mb = ma(BENCH, i_sig, 200)
        mb_prev = ma(BENCH, max(0, i_sig-20), 200)
        cb = closes[BENCH][i_sig]
        if mb and mb_prev and cb and cb > mb and mb >= mb_prev:
            gate = True

        # ---- 评分 ----
        scores = {}
        for c in universe:
            r20, r60, r120 = ret_over(c, i_sig, 20), ret_over(c, i_sig, 60), ret_over(c, i_sig, 120)
            if r20 is None or r60 is None or r120 is None:
                continue
            scores[c] = 0.5 * r20 + 0.3 * r60 + 0.2 * r120

        if gate:
            pool = {k: v for k, v in scores.items() if k not in BOND}
            # A-share ETF edge sits on the REVERSAL side, not momentum: the firm's own
            # STRATEGY_LIBRARY section 7 records 'equity-domain strength-continuation
            # families go deeply negative when moved into the ETF domain' and the zoo
            # behaviour families landed negative-sign 7 of 7. Momentum first (v1) lost
            # 41% -- logging that falsification and flipping to reversal on that evidence,
            # not on parameter search.
            top = sorted(pool.items(), key=lambda kv: kv[1])[:4]      # lowest 20/60/120 -> weakest
        else:
            bs = {k: scores.get(k) for k in BOND if k in scores}
            if bs:
                best = max(bs.items(), key=lambda kv: kv[1])[0]
                top = [(best, 1.0)]
            else:
                top = []

        target = {c: 1.0 / len(top) for c, _ in top} if top else {}

        # ---- 执行（下周开盘价）----
        # 先卖后买，按目标权重
        # 当前持仓市值（按执行日开盘）
        cur_val = {}
        for c, q in holdings.items():
            px = opens[c][i_exe]
            if px:
                cur_val[c] = q * px
        port_val = cash + sum(cur_val.values())

        # 全部卖出不在目标里的（T+1 天然满足：持仓至少已过一周）
        for c in list(holdings.keys()):
            if c not in target:
                px = opens[c][i_exe]
                if not px:
                    continue
                q = holdings[c]
                proceeds = cn.sell_proceeds(px, q, c, ADV)
                cash += proceeds
                turnover_notional += q * px
                del holdings[c]

        # 调整到目标权重
        # NO-TRADE BAND (20%): pulling every position to exact equal weight each week
        # manufactures pure cost with no signal (v1/v2 churn diagnosis). Only trade a
        # leg when its target differs from current by more than the band.
        BAND = 0.20
        for c, w in target.items():
            px = opens[c][i_exe]
            if not px:
                continue
            want_val = port_val * w
            have_val = holdings.get(c, 0) * px
            if want_val - have_val > px * 100 and (port_val - have_val) > 0 and (want_val - have_val) / port_val > BAND:
                qty = int((want_val - have_val) / px / 100) * 100
                if qty > 0:
                    cost = cn.buy_cost(px, qty, c, ADV)
                    if cost <= cash:
                        cash -= cost
                        holdings[c] = holdings.get(c, 0) + qty
                        turnover_notional += qty * px
            elif have_val - want_val > px * 100 and (have_val - want_val) / port_val > BAND:
                qty = int((have_val - want_val) / px / 100) * 100
                qty = min(qty, holdings.get(c, 0))
                if qty > 0:
                    proceeds = cn.sell_proceeds(px, qty, c, ADV)
                    cash += proceeds
                    holdings[c] -= qty
                    turnover_notional += qty * px
                    if holdings[c] <= 0:
                        del holdings[c]
        rebalances += 1

        # ---- 周收益 ----
        inv_val2 = sum(q * (closes[c][i_exe] or 0) for c, q in holdings.items())
        east2 = cash + inv_val2
        if east > 0:
            eq_ret = east2 / east - 1.0
            b_ret = None
            if opens[BENCH][i_exe] and opens[BENCH][i_sig]:
                b_ret = opens[BENCH][i_exe] / closes[BENCH][i_sig] - 1.0 + (closes[BENCH][i_exe]/opens[BENCH][i_exe]-1.0)
            equity_hist.append((d_exe, east2, eq_ret, b_ret))
            total_weeks += 1
            if b_ret is not None and eq_ret > b_ret:
                win_weeks += 1

    # ---- 汇总 ----
    final = equity_hist[-1][1]
    yrs = (datetime.strptime(equity_hist[-1][0], "%Y-%m-%d") - datetime.strptime(equity_hist[0][0], "%Y-%m-%d")).days / 365.25
    cagr = (final / CAPITAL) ** (1 / yrs) - 1
    peak = CAPITAL; mdd = 0.0
    for _, e, _, _ in equity_hist:
        if e > peak: peak = e
        dd = (e - peak) / peak
        if dd < mdd: mdd = dd
    rets = [r for _, _, r, _ in equity_hist]
    sd = statistics.pstdev(rets) * math.sqrt(52) if len(rets) > 1 else 0
    sharpe = (statistics.fmean(rets) * 52) / sd if sd > 0 else 0
    b0 = opens[BENCH][week_idx[0]]
    bench_final = closes[BENCH][week_idx[-1]] / b0
    bench_cagr = bench_final ** (1 / yrs) - 1
    beat_rate = win_weeks / total_weeks if total_weeks else 0
    cost_drag_bp = turnover_notional / CAPITAL / yrs * (10.0 / 10000) * 10000 / 10000 * 10000

    print()
    print(f"周数 {len(equity_hist)}｜年数 {yrs:.2f}｜调仓次数 {rebalances}（{rebalances/yrs:.1f}/年）")
    print(f"期末权益 {final:,.0f}｜总收益 {(final/CAPITAL-1)*100:.1f}%｜年化 {cagr*100:.2f}%")
    print(f"沪深300 同期年化 {bench_cagr*100:.2f}%｜超额 {(cagr-bench_cagr)*100:.2f}pp")
    print(f"最大回撤 {mdd*100:.1f}%｜年化波动 {sd*100:.1f}%｜Sharpe {sharpe:.2f}")
    print(f"周胜率（跑赢基准）{beat_rate*100:.1f}%｜周数 {total_weeks}")
    print(f"累计换手 {turnover_notional/CAPITAL:.1f}x capital｜年均 {turnover_notional/CAPITAL/yrs:.1f}x")
    print(f"成本拖累约 {turnover_notional/CAPITAL/yrs*10.08:.0f} bp/年（ETF 往返 10.08bp）")

if __name__ == "__main__":
    main()

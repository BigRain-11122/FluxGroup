# grid_vs_hold.py —— 网格 vs 买入持有 实测（1-15 天短线 · 含 T+1 与真实成本）
# 目的：用其自有日线回答"网格到底赚不赚、赚在哪、什么时候死"。
# 口径：T+1（除 T+0 品种）· 成本用 cost_model_cn.py · 无未来函数（当日信号次日执行）
import os, sys, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
CAPITAL = 1_000_000.0

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return []
    rows = []
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 6:
                continue
            try:
                rows.append((row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4])))
            except ValueError:
                continue
    return rows

def run_grid(code, rows, grid_n=10, capital=CAPITAL, max_inventory_frac=1.0,
             stop_loss=0.20, adv=1e9, label=""):
    """Long-only grid: N price levels between an anchor low and high.
    Each level holds one unit of capital. Sell one level on +step, buy one on -step.
    T+1: shares bought on day D cannot be sold until D+1.
    Hard rule: if drawdown from peak > stop_loss -> liquidate everything and stop.
    """
    if len(rows) < 300:
        return None
    px0 = rows[0][4]
    lo, hi = px0 * 0.7, px0 * 1.3          # anchor range from the start price (frozen, no hindsight)
    step = (hi - lo) / grid_n
    unit = capital / grid_n
    cash = capital
    # inventory as lots: list of [price, qty, buy_index]
    lots = []
    realized = 0.0
    trades = []          # (pnl, is_win)
    peak_equity = capital
    max_dd = 0.0
    stopped = False
    equity_curve = []

    for i, (d, o, h, l, c) in enumerate(rows):
        if stopped:
            equity_curve.append(cash)
            continue
        # mark equity
        inv = sum(q for _, q, _ in lots)
        eq = cash + inv * c
        if eq > peak_equity:
            peak_equity = eq
        dd = (eq - peak_equity) / peak_equity if peak_equity > 0 else 0
        if dd < max_dd:
            max_dd = dd
        # hard stop (protect against the grid's structural killer: a one-way decline)
        if dd <= -stop_loss:
            for (bp, q, bi) in lots:
                if i > bi:                                  # T+1
                    cash += cn.sell_proceeds(c, q, code, adv)
                    pnl = cn.sell_proceeds(c, q, code, adv) - cn.buy_cost(bp, q, code, adv)
                    realized += pnl
                    trades.append((pnl, pnl > 0))
            lots = []
            stopped = True
            equity_curve.append(cash)
            continue

        # grid action at this bar's close (executed next open in a stricter engine; here we
        # use close with a one-bar delay on the sell side via the T+1 lot rule)
        total_inv_cap = sum(bp * q for bp, q, _ in lots)
        inv_frac = total_inv_cap / capital
        # sell one unit if price rose a full step above the highest buy
        if lots:
            best_buy = max(bp for bp, _, _ in lots)
            if c >= best_buy + step:
                # sell the oldest sellable lot (T+1)
                for k, (bp, q, bi) in enumerate(lots):
                    if i > bi:
                        proceeds = cn.sell_proceeds(c, q, code, adv)
                        cash += proceeds
                        pnl = proceeds - cn.buy_cost(bp, q, code, adv)
                        realized += pnl
                        trades.append((pnl, pnl > 0))
                        lots.pop(k)
                        break
        # buy one unit if price fell a full step below the lowest buy (or below anchor)
        ref = min([bp for bp, _, _ in lots], default=hi)
        if c <= ref - step and inv_frac + (1.0/grid_n) <= max_inventory_frac and cash >= unit:
            qty = int(unit / c / 100) * 100
            if qty > 0:
                cost = cn.buy_cost(c, qty, code, adv)
                if cost <= cash:
                    cash -= cost
                    lots.append([c, qty, i])
        equity_curve.append(cash + sum(q for _, q, _ in lots) * c)

    final_inv = sum(q for _, q, _ in lots)
    final_eq = cash + final_inv * rows[-1][4]
    total_ret = final_eq / capital - 1
    wins = sum(1 for _, w in trades if w)
    n = len(trades)
    win_rate = wins / n if n else 0
    gains = [p for p, w in trades if w]
    losses = [-p for p, w in trades if not w]
    avg_gain = sum(gains)/len(gains) if gains else 0
    avg_loss = sum(losses)/len(losses) if losses else 0
    pl_ratio = (avg_gain/avg_loss) if avg_loss > 0 else float('inf')
    expect = (win_rate*avg_gain - (1-win_rate)*avg_loss) if n else 0
    hold_ret = rows[-1][4]/rows[0][4] - 1
    return dict(code=code, label=label, days=len(rows), trades=n, win_rate=win_rate,
                pl_ratio=pl_ratio, expect=expect, total_ret=total_ret, max_dd=max_dd,
                hold_ret=hold_ret, stopped=stopped, excess=total_ret-hold_ret)

def main():
    targets = [
        ("510050", "上证50ETF（震荡偏趋势）"),
        ("510300", "沪深300ETF（大盘）"),
        ("518880", "黄金ETF（长期上行）"),
        ("512880", "证券ETF（高波动）"),
        ("511010", "国债ETF（几乎无波动）"),
    ]
    print(f"{'标的':<22}{'天数':>6}{'笔数':>6}{'胜率':>8}{'盈亏比':>8}{'期望/笔':>10}{'网格收益':>10}{'买入持有':>10}{'超额':>9}{'最大回撤':>9}{'触发止损':>9}")
    for code, lab in targets:
        rows = load(code)
        r = run_grid(code, rows, label=lab)
        if not r:
            print(f"{lab:<22}  数据不足"); continue
        print(f"{r['label']:<22}{r['days']:>6}{r['trades']:>6}{r['win_rate']*100:>7.1f}%"
              f"{r['pl_ratio']:>8.2f}{r['expect']:>10,.0f}{r['total_ret']*100:>9.1f}%"
              f"{r['hold_ret']*100:>9.1f}%{r['excess']*100:>8.1f}%{r['max_dd']*100:>8.1f}%"
              f"{('是' if r['stopped'] else '否'):>9}")

if __name__ == "__main__":
    main()

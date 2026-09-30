# entry_pacing_test.py —— 建仓节奏与止跌确认 实测（修正"满仓即入"缺陷）
# 三个版本对比，同一段数据、同一成本口径、无未来函数：
#   A 立即满仓（原版·有缺陷）
#   B 确认闸：低谷中再要求 现价 > MA20 才建/加仓
#   C 确认闸 + 分批：进入低谷后分 4 周各 25% 到位
# 关键观察：建仓期的最大回撤 > 原版，才是"即时满仓"的真实风险
import os, sys, csv, math
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model_cn as cn

DAILY = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney\data\daily"
CAPITAL = 1_000_000.0
BROAD, BOND, GOLD, OVERSEAS = "510300", "511010", "518880", "513500"
ALL = [BROAD, BOND, GOLD, OVERSEAS]
NAMES = {BROAD: "沪深300", BOND: "国债", GOLD: "黄金", OVERSEAS: "标普500"}
ADV = 500_000_000.0

W = {"VALLEY": {BROAD: .25, GOLD: .25, OVERSEAS: .25, BOND: .25},
     "NEUTRAL": {BROAD: .17, GOLD: .17, OVERSEAS: .17, BOND: .49},
     "PEAK": {BROAD: .15, GOLD: .15, OVERSEAS: .15, BOND: .55}}

def load(code):
    p = os.path.join(DAILY, code + ".csv")
    if not os.path.exists(p):
        return {}
    out = {}
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 6:
                continue
            try:
                out[row[0]] = (float(row[1]), float(row[4]))
            except ValueError:
                continue
    return out

def run(confirm=False, phased=False, label=""):
    data = {c: load(c) for c in ALL}
    dates = sorted(set(data[BROAD]) & set(data[BOND]) & set(data[GOLD]) & set(data[OVERSEAS]))
    closes = {c: [data[c].get(d, (None, None))[1] for d in dates] for c in ALL}
    opens = {c: [data[c].get(d, (None, None))[0] for d in dates] for c in ALL}

    def ma(c, i, n):
        v = [closes[c][j] for j in range(max(0, i-n+1), i+1)]
        v = [x for x in v if x is not None]
        return sum(v)/len(v) if len(v) >= n*0.8 else None

    def regime(i):
        m200 = ma(BROAD, i, 200); c = closes[BROAD][i]
        if not m200 or not c:
            return "NEUTRAL"
        hi = max([x for x in closes[BROAD][max(0, i-250):i+1] if x] or [0])
        dd = (c - hi) / hi if hi else 0
        if c < m200 and dd <= -0.10:
            return "VALLEY"
        if c > m200:
            return "PEAK"
        return "NEUTRAL"

    cash = CAPITAL; hold = {}; equity = []; last_check = -999
    turnover = 0.0; checks = 0
    phase_left = 0; phase_target = None      # 分批状态

    for i in range(200, len(dates) - 1):
        reg = regime(i)
        gap = 5 if reg == "VALLEY" else (10 if reg == "NEUTRAL" else 60)
        if i - last_check < gap:
            equity.append(cash + sum(q * (closes[c][i] or 0) for c, q in hold.items()))
            continue
        last_check = i; checks += 1
        i_exe = i + 1

        # ---- 确认闸 ----
        if confirm and reg == "VALLEY":
            m20 = ma(BROAD, i, 20); c = closes[BROAD][i]
            if not (m20 and c and c > m20):
                equity.append(cash + sum(q * (closes[c][i] or 0) for c, q in hold.items()))
                continue

        tgt = W[reg]
        port = cash + sum(q * (opens[c][i_exe] or 0) for c, q in hold.items())

        # ---- 分批建仓 ----
        if phased:
            if phase_left == 0 and phase_target != reg:
                phase_target = reg; phase_left = 4      # 4 周到目标
            frac = 0.25 if phase_left > 0 else 1.0
            if phase_left > 0: phase_left -= 1
        else:
            frac = 1.0

        for c, w in tgt.items():
            px = opens[c][i_exe]
            if not px: continue
            want = port * w * frac
            have = hold.get(c, 0) * px
            if port > 0 and abs(want - have) / port < 0.15: continue
            if want > have:
                qty = int((want - have) / px / 100) * 100
                if qty > 0:
                    cost = cn.buy_cost(px, qty, c, ADV)
                    if cost <= cash:
                        cash -= cost; hold[c] = hold.get(c, 0) + qty; turnover += qty * px
            else:
                qty = min(int((have - want) / px / 100) * 100, hold.get(c, 0))
                if qty > 0:
                    cash += cn.sell_proceeds(px, qty, c, ADV); hold[c] -= qty; turnover += qty * px
                    if hold[c] <= 0: del hold[c]
        equity.append(cash + sum(q * (closes[c][i] or 0) for c, q in hold.items()))

    final = equity[-1]
    n_eq = len(equity)
    yrs = (datetime.strptime(dates[200 + n_eq - 1], "%Y-%m-%d") -
           datetime.strptime(dates[200], "%Y-%m-%d")).days / 365.25
    cagr = (final/CAPITAL) ** (1/yrs) - 1 if final > 0 else -1
    peak = CAPITAL; mdd = 0.0; dd_at_60d = 0.0
    for k, e in enumerate(equity):
        if e > peak: peak = e
        dd = (e - peak)/peak
        if dd < mdd: mdd = dd
        if k == 60: dd_at_60d = dd
    bench = (closes[BROAD][-1] / closes[BROAD][200]) ** (1/yrs) - 1
    yearly = {}
    for k, e in enumerate(equity):
        yearly.setdefault(dates[k+200][:4], []).append(e)
    wins = tot = 0; prev = CAPITAL
    for y in sorted(yearly):
        idxs = [j for j, d in enumerate(dates) if d.startswith(y)]
        if idxs and closes[BROAD][idxs[0]] and closes[BROAD][idxs[-1]]:
            bt = closes[BROAD][idxs[-1]]/closes[BROAD][idxs[0]] - 1
            r = yearly[y][-1]/prev - 1
            tot += 1
            if r > bt: wins += 1
        prev = yearly[y][-1]
    print(f"{label:<28}{cagr*100:>8.2f}%{mdd*100:>10.1f}%{(cagr-bench)*100:>9.2f}pp"
          f"{wins}/{tot:<5}{turnover/CAPITAL/yrs:>8.2f}x{turnover/CAPITAL/yrs*10.08:>7.0f}bp")
    return dict(cagr=cagr, mdd=mdd, excess=cagr-bench, win=f"{wins}/{tot}", to=turnover/CAPITAL/yrs)

def main():
    print(f"{'版本':<28}{'年化':>9}{'最大回撤':>10}{'超额':>11}{'年度胜':<7}{'换手/年':>9}{'成本':>8}")
    run(False, False, "A 立即满仓（原版）")
    run(True,  False, "B 确认闸（>MA20）")
    run(True,  True,  "C 确认闸 + 4周分批")

if __name__ == "__main__":
    main()

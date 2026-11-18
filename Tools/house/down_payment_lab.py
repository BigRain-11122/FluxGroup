# -*- coding: utf-8 -*-
"""
地产线 · 首付成数实验室（二手房口径，细到评估价与商贷消灭点）

为什么不能只按「总价 × 成数」算：
  1. 二手房按**银行评估价**放贷，评估价通常低于成交价 → 真实首付高于名义成数
  2. 公积金有**额度上限**，超过部分只能走商贷（3.0%），首付越高越可能"只欠公积金"（2.6%）
  3. 首付的选择本质是**杠杆定价**：借钱的成本 vs 自有资金的机会成本

输出：house/realestate/logs/down-payment-lab.md
用法：python Tools/house/down_payment_lab.py
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'house', 'realestate', 'logs', 'down-payment-lab.md')

UNITS = [
    {'k': 'A', 'name': '95㎡ 精装', 'price': 1_630_000, 'area': 95.0, 'fit_cost': 0},
    {'k': 'B', 'name': '136㎡ 毛坯', 'price': 2_060_000, 'area': 136.0, 'fit_cost': 200_000},
]

# ---- 政策与银行参数（★=必须柜台核实，未核实前不得据以签约） ----
APPRAISAL = 0.95      # ★银行评估价 ÷ 成交价（二手房常见 0.9–1.0）
POLICY_MIN = 0.15     # ★首套最低首付（政策底，各银行执行可能更高）
GJJ_CAP = 800_000     # ★公积金贷款上限（双人档；单人更低）
GJJ_RATE = 0.026      # ★公积金 5 年以上
COM_RATE = 0.030      # ★商贷首套
OPP = 0.025           # 自有资金机会成本（定存/理财）
YEARS = 30
PROP = 2.05           # 物业元/㎡/月
RENT_ANCHOR, ANCHOR_AREA, EXP_A = 33.7, 135.0, 0.18
RENT_GROWTH = 0.02
SELL_COST = 0.025
HOLD = 8


def pmt(p, r):
    if p <= 0:
        return 0.0
    i, n = r / 12, YEARS * 12
    return p * i * (1 + i) ** n / ((1 + i) ** n - 1)


def bal(p, r, months):
    if p <= 0:
        return 0.0
    i = r / 12
    m = pmt(p, r)
    return p * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def rent_net(area):
    r = area * RENT_ANCHOR * (ANCHOR_AREA / area) ** EXP_A
    return r, r - PROP * area - r / 12          # 毛租, 扣物业与 1 个月空置后的月净


def plan(u, down_nominal):
    """按评估价放贷：可贷 = 评估价 ×(1-成数)，但不超过 成交价×(1-成数) 的常见执行。
    保守取：贷款 = min(评估价×(1-成数), 成交价-首付现金)。"""
    price, area = u['price'], u['area']
    appraised = price * APPRAISAL
    loan_appr = appraised * (1 - down_nominal)
    down_cash = price - loan_appr                     # 成交价与放贷额的差额 = 真实首付
    gjj = min(loan_appr, GJJ_CAP)
    com = loan_appr - gjj
    monthly = pmt(gjj, GJJ_RATE) + pmt(com, COM_RATE)
    _, net_r = rent_net(area)
    cash_all = down_cash + u['fit_cost']              # 全部自出现金（不含税费中介）
    return dict(down_nominal=down_nominal, down_pct=down_cash / price,
                down_cash=down_cash, loan=loan_appr, gjj=gjj, com=com,
                monthly=monthly, gap=monthly - net_r, net_rent=net_r,
                cash_all=cash_all)


def outcome(u, p, years, g):
    """持有 years 年、房价年化 g，卖出后的净收益（元）"""
    price, area = u['price'], u['area']
    px = price * (1 + g) ** years
    balance = bal(p['gjj'], GJJ_RATE, years * 12) + bal(p['com'], COM_RATE, years * 12)
    rent_sum = sum(p['net_rent'] * 12 * (1 + RENT_GROWTH) ** t for t in range(years))
    paid = p['monthly'] * 12 * years
    return px * (1 - SELL_COST) - balance + rent_sum - paid - p['down_cash']


def need_g(u, p, years, target):
    """求解：使净收益 = target 的房价年化（二分）"""
    lo, hi = -0.20, 0.20
    for _ in range(80):
        mid = (lo + hi) / 2
        if outcome(u, p, years, mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def outcome_mult(u, p, years, mult):
    """持有 years 年、期末房价相对现在的累计倍数 mult，卖出净收益（元）"""
    price = u['price']
    px = price * mult
    balance = bal(p['gjj'], GJJ_RATE, years * 12) + bal(p['com'], COM_RATE, years * 12)
    rent_sum = sum(p['net_rent'] * 12 * (1 + RENT_GROWTH) ** t for t in range(years))
    paid = p['monthly'] * 12 * years
    return px * (1 - SELL_COST) - balance + rent_sum - paid - p['down_cash']


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    L = []
    w = L.append
    w('# 首付成数实验室（二手房口径）\n')
    w(f'> 评估价/成交价 = {APPRAISAL:.0%}★　政策底线首付 {POLICY_MIN:.0%}★　'
      f'公积金上限 {GJJ_CAP/1e4:.0f} 万★　公积金 {GJJ_RATE:.2%}★　商贷 {COM_RATE:.2%}★　'
      f'机会成本 {OPP:.1%}　持有 {HOLD} 年\n')

    for u in UNITS:
        w(f'\n## {u["k"]} · {u["name"]}　成交 {u["price"]/1e4:.0f} 万')
        if u['fit_cost']:
            w(f'（毛坯需另投装修 {u["fit_cost"]/1e4:.0f} 万，计入自出现金，但不进房价）')
        w('')
        w('| 名义成数 | 真实首付 | 真实首付额 | 贷款额 | 公积金 | 商贷 | 月供 | 月净租 | **月贴** | 自出现金 |')
        w('|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
        plans = []
        for d in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65):
            p = plan(u, d)
            plans.append(p)
            w(f'| {d:.0%} | **{p["down_pct"]:.1%}** | {p["down_cash"]/1e4:.0f} 万 | '
              f'{p["loan"]/1e4:.0f} 万 | {p["gjj"]/1e4:.0f} 万 | {p["com"]/1e4:.0f} 万 | '
              f'{p["monthly"]:,.0f} | {p["net_rent"]:,.0f} | **{p["gap"]:,.0f}** | '
              f'{p["cash_all"]/1e4:.0f} 万 |')

        # 商贷消灭点
        kill = None
        for p in plans:
            if p['com'] <= 1:
                kill = p
                break
        if kill:
            w(f'\n**商贷消灭点**：名义成数 {kill["down_nominal"]:.0%}（真实首付 '
              f'{kill["down_pct"]:.1%}、{kill["down_cash"]/1e4:.0f} 万）时贷款 '
              f'{kill["loan"]/1e4:.0f} 万全部走公积金，'
              f'月供降到 {kill["monthly"]:,.0f} 元、月贴 {kill["gap"]:,.0f} 元。')

        w(f'\n### 保本与跑赢定存：每档首付需要多高的房价年化（持有 {HOLD} 年）\n')
        w('| 名义成数 | 真实首付 | 月贴 | 保本所需年化 | 跑赢机会成本所需年化 | vs 基准 3% |')
        w('|---:|---:|---:|---:|---:|:---|')
        for p in plans:
            g0 = need_g(u, p, HOLD, 0.0)
            g1 = need_g(u, p, HOLD, p['down_cash'] * OPP * HOLD)
            flag = '✅ 有余量' if 0.03 >= g1 else ('⚠️ 贴着' if 0.03 >= g0 else '❌ 基准不够')
            w(f'| {p["down_nominal"]:.0%} | {p["down_pct"]:.1%} | {p["gap"]:,.0f} | '
              f'**{g0:+.2%}** | {g1:+.2%} | {flag} |')

    w('\n## 杠杆的风险敞口：8 年后卖出、不同首付 × 不同房价累计涨跌（万元）\n')
    w('> 累计口径：−20% = 8 年后房价比今天低 20%；+27% ≈ 年化 3% 复利 8 年。\n')
    for u in UNITS:
        w(f'\n**{u["k"]} · {u["name"]}**\n')
        w('| 名义成数 | 真实首付 | 自出现金 | 累计 −30% | 累计 −20% | 持平 | 累计 +27% | 最差档/自现金 |')
        w('|---:|---:|---:|---:|---:|---:|---:|---:|')
        for d in (0.15, 0.20, 0.30, 0.40, 0.50, 0.60):
            p = plan(u, d)
            m30 = outcome_mult(u, p, HOLD, 0.70) / 1e4
            m20 = outcome_mult(u, p, HOLD, 0.80) / 1e4
            m00 = outcome_mult(u, p, HOLD, 1.00) / 1e4
            m27 = outcome_mult(u, p, HOLD, 1.27) / 1e4
            ratio = m30 * 1e4 / p['cash_all'] * 100
            w(f'| {d:.0%} | {p["down_pct"]:.1%} | {p["cash_all"]/1e4:.0f} 万 | '
              f'{m30:+.1f} | {m20:+.1f} | {m00:+.1f} | {m27:+.1f} | {ratio:.0f}% |')

    w('\n## 参数敏感性（A 套 30% 名义首付）\n')
    u = UNITS[0]
    base = plan(u, 0.30)
    w('| 情形 | 月供 | 月供变化 | 自出现金 | 现金变化 |')
    w('|---|---:|---:|---:|---:|')
    w(f'| 基准（评估 95% / 商贷 3.0% / 公积金 2.6%） | {base["monthly"]:,.0f} | — | '
      f'{base["down_cash"]/1e4:.0f} 万 | — |')
    for label, appr, cr, gr in (('评估价降到 90%', 0.90, COM_RATE, GJJ_RATE),
                                ('商贷 +0.5pp', APPRAISAL, COM_RATE + 0.005, GJJ_RATE),
                                ('公积金 +0.5pp', APPRAISAL, COM_RATE, GJJ_RATE + 0.005)):
        globals()['APPRAISAL'] = appr
        globals()['COM_RATE'] = cr
        globals()['GJJ_RATE'] = gr
        p = plan(u, 0.30)
        w(f'| {label} | {p["monthly"]:,.0f} | {p["monthly"]-base["monthly"]:+,.0f} | '
          f'{p["down_cash"]/1e4:.0f} 万 | {(p["down_cash"]-base["down_cash"])/1e4:+.0f} 万 |')
    globals()['APPRAISAL'], globals()['COM_RATE'], globals()['GJJ_RATE'] = 0.95, 0.030, 0.026
    w('\n> 注意：评估价下调会让**月供变低但自出现金变多**——银行不接受成交价，差价要自己补。')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'written -> {OUT}  ({len(L)} lines)')


if __name__ == '__main__':
    main()

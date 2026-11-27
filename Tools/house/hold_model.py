# -*- coding: utf-8 -*-
"""
地产线 · 自持（买房出租）模型 v1
核心问题：租金 + 未来增值，扣掉月供与税费，年化到底多少？
最关键的一个数：**盈亏平衡的房价年涨幅 g***（低于它，持有就是亏的）
运行：python Tools/house/hold_model.py
"""
import json

VERSION = 'v1.0-20261116'

# ---------------- 输入 ----------------
AREA = 98
PRICE_PSM = 15800
DOWN = 0.15                 # 首付比例
RATE = 0.030                # 商贷年利率
YEARS_LOAN = 30
RENT = 3300                 # 整租月租
VAC_DAYS = 25               # 年空置天数
OPEX = 300                  # 运营（物业/维修/网）元/月
RENT_GROWTH = 0.02          # 租金年涨
BUY_TAX = 0.025             # 买入税费（契税 1% + 中介 1.5%）
SELL_TAX = 0.025            # 卖出税费（中介 1.5% + 个税 1%）
HOLD_YEARS = [5, 10, 15]
G_SCENARIOS = [-0.02, 0.0, 0.02, 0.03, 0.05]
OPPORTUNITY = 0.05          # 机会成本（理财/其他投资）


def monthly_payment(principal, rate, years):
    i = rate / 12
    n = years * 12
    if i == 0:
        return principal / n
    return principal * i * (1 + i) ** n / ((1 + i) ** n - 1)


def balance_after(principal, rate, years, months):
    i = rate / 12
    m = monthly_payment(principal, rate, years)
    return principal * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def npv(rate, flows):
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))


def irr(flows):
    lo, hi = -0.95, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid, flows) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def cash_flows(g, years, down=DOWN, rent=RENT, opex=OPEX):
    price = AREA * PRICE_PSM
    loan = price * (1 - down)
    pay = monthly_payment(loan, RATE, YEARS_LOAN)
    occ = (365 - VAC_DAYS) / 365
    flows = [-(price * down + price * BUY_TAX)]
    annual = []
    for y in range(years):
        r = rent * (1 + RENT_GROWTH) ** y
        net = (r * occ - opex - pay) * 12
        flows.append(net)
        annual.append(net)
    sell = price * (1 + g) ** years
    bal = balance_after(loan, RATE, YEARS_LOAN, years * 12)
    net_sale = sell - bal - sell * SELL_TAX
    flows[-1] += net_sale
    return flows, pay, annual[-1], net_sale, bal


def breakeven_g(years, target_irr, down=DOWN):
    lo, hi = -0.20, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        flows, *_ = cash_flows(mid, years, down=down)
        if irr(flows) < target_irr:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    price = AREA * PRICE_PSM
    loan = price * (1 - DOWN)
    pay = monthly_payment(loan, RATE, YEARS_LOAN)
    print(f'自持模型 {VERSION}')
    print(f'房源：{AREA}㎡ × {PRICE_PSM} 元/㎡ = {price/10000:.1f} 万｜首付 {DOWN:.0%}（{price*DOWN/10000:.1f} 万）'
          f'｜贷款 {loan/10000:.1f} 万｜{RATE:.1%} / {YEARS_LOAN} 年')
    print(f'月供 {pay:,.0f} 元｜整租 {RENT} 元/月｜空置 {VAC_DAYS} 天｜运营 {OPEX} 元/月\n')

    occ = (365 - VAC_DAYS) / 365
    rent_net = RENT * occ - OPEX
    print(f'租金净收入 {rent_net:,.0f} 元/月 → 月现金流 {rent_net - pay:+,.0f} 元'
          f'（年 {((rent_net - pay) * 12)/10000:+.2f} 万）')
    print(f'首年利息 {loan*RATE/10000:.2f} 万，首年本金 {(pay*12 - loan*RATE)/10000:.2f} 万\n')

    print('情景表（持有 n 年，房价年涨 g）：')
    print(f'{"g":>6}{"年限":>6}{"年现金流":>10}{"卖出净得":>10}{"总损益":>10}{"IRR":>8}')
    print('-' * 52)
    for g in G_SCENARIOS:
        for n in HOLD_YEARS:
            flows, pay_, annual, net_sale, bal = cash_flows(g, n)
            total = sum(flows)
            print(f'{g:>6.1%}{n:>6}{annual/10000:>9.2f}万{net_sale/10000:>9.1f}万{total/10000:>9.1f}万{irr(flows):>7.1%}')
    print()

    print('盈亏平衡的房价年涨幅 g*：')
    for n in HOLD_YEARS:
        g0 = breakeven_g(n, 0.0)
        g5 = breakeven_g(n, OPPORTUNITY)
        print(f'  持有 {n:>2} 年：不亏钱需 g ≥ {g0:>5.2%}；跑赢 {OPPORTUNITY:.0%} 机会成本需 g ≥ {g5:>5.2%}')
    print()

    print('首付比例的影响（持有 10 年，g=2%）：')
    for d in (0.15, 0.30, 0.50, 1.00):
        flows, pay_, annual, net_sale, bal = cash_flows(0.02, 10, down=d)
        print(f'  首付 {d:>5.0%}：月供 {monthly_payment(price*(1-d), RATE, YEARS_LOAN):>6,.0f}'
              f'｜年现金流 {annual/10000:>+6.2f} 万｜IRR {irr(flows):>6.1%}')
    print()

    # 改造场景：两套一室户（转租 6000，改造 20 万）
    print('改造后（两套一室户，转租 6000，改造 20 万，持有 10 年）：')
    price2 = price + 200000
    for g in (0.0, 0.02, 0.03):
        flows, pay_, annual, net_sale, bal = cash_flows(g, 10, rent=6000, opex=400)
        flows[0] -= 200000
        print(f'  g={g:>4.0%}：年现金流 {annual/10000:>+6.2f} 万｜IRR {irr(flows):>6.1%}')
    print()

    out = {'version': VERSION,
           'inputs': {'area': AREA, 'price_psm': PRICE_PSM, 'down': DOWN, 'rate': RATE,
                      'years_loan': YEARS_LOAN, 'rent': RENT, 'vac_days': VAC_DAYS,
                      'opex': OPEX, 'rent_growth': RENT_GROWTH,
                      'buy_tax': BUY_TAX, 'sell_tax': SELL_TAX},
           'breakeven': {str(n): {'irr0': breakeven_g(n, 0.0),
                                  'irr5': breakeven_g(n, OPPORTUNITY)} for n in HOLD_YEARS}}
    with open('house/realestate/hold-model-20261116.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('已写出 house/realestate/hold-model-20261116.json')


if __name__ == '__main__':
    main()

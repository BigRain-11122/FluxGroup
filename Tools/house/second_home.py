# -*- coding: utf-8 -*-
"""
地产线 · 二套房投资模型（改造租金 + 未来增值）
苏州口径：不限购 → "二套"只剩 ①利率（首套贷款未结清=3.3%）②契税（>140㎡=2%）
运行：python Tools/house/second_home.py
"""
import json

V = 'v1.0-20261116'

L = {
    'name': '尹山湖韵佳苑 135.15㎡ / 172万',
    'total': 1720000, 'area': 135.15,
    'down': 0.15, 'rate_second': 0.033, 'rate_first': 0.030, 'years': 30,
    'deed_tax': 0.01,          # ≤140㎡ 二套契税 1%
    'buy_other': 0.015,        # 中介等
    'sell_tax': 0.025,
    'rent_whole': 4600, 'vac': 30, 'opex': 400,
    'rent_growth': 0.02,
}
SCHEMES = {
    '不改（整租）': {'rent': 4600, 'cost': 30000, 'vac': 30, 'opex': 400},
    '改两套一室户': {'rent': 7400, 'cost': 220000, 'vac': 40, 'opex': 600},
    '改四间合租': {'rent': 7200, 'cost': 160000, 'vac': 45, 'opex': 750},
}


def pay(p, rate, years):
    i = rate / 12
    n = years * 12
    return p / n if i == 0 else p * i * (1 + i) ** n / ((1 + i) ** n - 1)


def bal(p, rate, years, months):
    i = rate / 12
    m = pay(p, rate, years)
    return p * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def npv(r, cf):
    return sum(c / (1 + r) ** t for t, c in enumerate(cf))


def irr(cf):
    lo, hi = -0.95, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid, cf) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def flows(g, years, rent, cost, vac, opex, rate=None, down=None):
    rate = rate or L['rate_second']
    down = L['down'] if down is None else down
    price = L['total']
    loan = price * (1 - down)
    m = pay(loan, rate, L['years'])
    occ = (365 - vac) / 365
    cf = [-(price * down + price * L['deed_tax'] + price * L['buy_other']) - cost]
    rents = []
    for y in range(years):
        r = rent * (1 + L['rent_growth']) ** y
        net = (r * occ - opex - m) * 12
        cf.append(net)
        rents.append(net)
    sell = price * (1 + g) ** years
    net_sale = sell - bal(loan, rate, L['years'], years * 12) - sell * L['sell_tax']
    cf[-1] += net_sale
    return cf, m, rents, net_sale, loan


def breakeven(years, target, rate=None, rent=None, cost=0, vac=30, opex=400):
    rent = rent or L['rent_whole']
    lo, hi = -0.2, 0.3
    for _ in range(200):
        mid = (lo + hi) / 2
        cf, *_ = flows(mid, years, rent, cost, vac, opex, rate=rate)
        if irr(cf) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    p = L['total']
    print(f'二套房投资模型 {V}\n{L["name"]}\n')
    print(f'苏州不限购 → "二套"实质影响：利率 {L["rate_second"]:.1%}（首套 {L["rate_first"]:.1%}）；'
          f'契税 {L["deed_tax"]:.0%}（135.15㎡ ≤140㎡）\n')

    m1 = pay(p * (1 - L['down']), L['rate_first'], L['years'])
    m2 = pay(p * (1 - L['down']), L['rate_second'], L['years'])
    print(f'首付 {L["down"]:.0%} = {p*L["down"]/10000:.1f} 万｜贷款 {(p*(1-L["down"]))/10000:.1f} 万')
    print(f'月供：首套 {m1:,.0f}｜二套 {m2:,.0f}｜差额 {m2-m1:+,.0f}/月（年 {(m2-m1)*12/10000:+.2f} 万）\n')

    print('一、三种方案的现金流（二套利率 3.3%）')
    print(f'{"方案":<14}{"月租":>7}{"年现金流":>11}{"改造回本":>9}{"10年IRR@g2":>11}')
    base = None
    for k, s in SCHEMES.items():
        cf0, m, rents, _, _ = flows(0.0, 10, s['rent'], s['cost'], s['vac'], s['opex'])
        cf2, *_ = flows(0.02, 10, s['rent'], s['cost'], s['vac'], s['opex'])
        annual = rents[0]
        if base is None:
            base = annual
        inc = annual - base
        pb = s['cost'] / inc if inc > 0 else float('inf')
        print(f'{k:<14}{s["rent"]:>7,}{annual/10000:>10.2f}万'
              f'{(f"{pb:.1f}年" if pb != float("inf") else "—"):>9}{irr(cf2):>10.1%}')
    print()

    print('二、情景表（不改，二套）')
    print(f'{"g":>6}{"年限":>5}{"年现金流":>11}{"卖出净得":>11}{"总损益":>10}{"IRR":>8}')
    for g in (-0.02, 0.0, 0.02, 0.03):
        for n in (5, 10, 15):
            cf, m, rents, ns, _ = flows(g, n, L['rent_whole'], 0, 30, 400)
            print(f'{g:>6.0%}{n:>5}{rents[-1]/10000:>10.2f}万{ns/10000:>10.1f}万'
                  f'{sum(cf)/10000:>9.1f}万{irr(cf):>7.1%}')
    print()

    print('三、盈亏平衡房价年涨幅（二套 3.3%）')
    for n in (5, 10, 15):
        print(f'  持有 {n:>2} 年：不亏 {breakeven(n, 0.0):>6.2%}｜跑赢5%理财 {breakeven(n, 0.05):>6.2%}')
    print()

    print('四、改造的增量（改两套 vs 不改，二套，10 年 g=2%）')
    cf_a, *_ = flows(0.02, 10, 4600, 30000, 30, 400)
    cf_b, *_ = flows(0.02, 10, 7400, 220000, 40, 600)
    print(f'  不改：IRR {irr(cf_a):.1%}｜总损益 {sum(cf_a)/10000:.1f} 万')
    print(f'  改两套：IRR {irr(cf_b):.1%}｜总损益 {sum(cf_b)/10000:.1f} 万')
    print(f'  改造增量总损益：{(sum(cf_b)-sum(cf_a))/10000:+.1f} 万'
          f'｜IRR 提升 {(irr(cf_b)-irr(cf_a))*100:+.1f}pp')
    print()

    print('五、二套 vs 首套（不改，10 年 g=2%）')
    cf1, *_ = flows(0.02, 10, 4600, 30000, 30, 400, rate=L['rate_first'])
    print(f'  首套 3.0%：IRR {irr(cf1):.1%}｜总损益 {sum(cf1)/10000:.1f} 万')
    print(f'  二套 3.3%：IRR {irr(cf_a):.1%}｜总损益 {sum(cf_a)/10000:.1f} 万')
    print(f'  资格成本：IRR {(irr(cf1)-irr(cf_a))*100:.1f}pp｜总损益 {(sum(cf1)-sum(cf_a))/10000:.1f} 万'
          f'（10 年，仅利率差）')

    out = {'version': V, 'inputs': L, 'schemes': SCHEMES,
           'monthly': {'first': round(m1), 'second': round(m2)},
           'breakeven': {str(n): {'irr0': breakeven(n, 0.0), 'irr5': breakeven(n, 0.05)} for n in (5, 10, 15)}}
    json.dump(out, open('house/realestate/second-home-20261116.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('\n已写出 house/realestate/second-home-20261116.json')


if __name__ == '__main__':
    main()

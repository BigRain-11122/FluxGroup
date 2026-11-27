# -*- coding: utf-8 -*-
"""
地产线 · 单套房源体检器 v1
输入一套挂牌，输出：价格分位、租售比、自持现金流、盈亏平衡涨幅、改造方案对比
运行：python Tools/house/analyze_listing.py
"""
import json

V = 'v1.0-20261116'

# ---------------- 房源（贝壳 107113244434） ----------------
L = {
    'name': '尹山湖韵佳苑 · 3室2厅 · 135.15㎡ · 南 · 14/28层 · 简装',
    'total': 1720000, 'area': 135.15, 'psm': 12727,
    'community_low': 15951, 'community_mid': 17359, 'community_high': 18367,
    'community_deal_low': 12953, 'community_deal_high': 16438,
    'district_mid': 16900,
    'rent_whole': 4600,          # 135㎡ 三房整租（保守）
    'vac_days': 30, 'opex': 400,
    'rent_growth': 0.02, 'rate': 0.030, 'years_loan': 30,
    'buy_tax': 0.025, 'sell_tax': 0.025,
    'build_year': 2016,
}
# 改造方案
SCHEMES = {
    '整租（简装刷新）': {'rent': 4600, 'cost': 30000, 'vac': 30, 'opex': 400},
    '改两套一室户': {'rent': 3700 * 2, 'cost': 220000, 'vac': 40, 'opex': 600},
    '改四间合租': {'rent': 1800 * 4, 'cost': 160000, 'vac': 45, 'opex': 750},
}


def pay(principal, rate, years):
    i = rate / 12
    n = years * 12
    return principal / n if i == 0 else principal * i * (1 + i) ** n / ((1 + i) ** n - 1)


def bal(principal, rate, years, months):
    i = rate / 12
    m = pay(principal, rate, years)
    return principal * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def npv(r, flows):
    return sum(cf / (1 + r) ** t for t, cf in enumerate(flows))


def irr(flows):
    lo, hi = -0.95, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid, flows) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def flows_for(g, years, down, rent, cost=0, vac=30, opex=400, price=None, area=None):
    price = price or L['total']
    loan = price * (1 - down)
    m = pay(loan, L['rate'], L['years_loan'])
    occ = (365 - vac) / 365
    cf = [-(price * down + price * L['buy_tax']) - cost]
    for y in range(years):
        r = rent * (1 + L['rent_growth']) ** y
        cf.append((r * occ - opex - m) * 12)
    sell = price * (1 + g) ** years
    net = sell - bal(loan, L['rate'], L['years_loan'], years * 12) - sell * L['sell_tax']
    cf[-1] += net
    return cf, m


def breakeven(years, target, down=0.15, rent=None):
    rent = rent or L['rent_whole']
    lo, hi = -0.2, 0.3
    for _ in range(200):
        mid = (lo + hi) / 2
        cf, _ = flows_for(mid, years, down, rent)
        if irr(cf) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    p = L['total']
    psm = L['psm']
    print(f'房源体检 {V}\n{L["name"]}\n总价 {p/10000:.0f} 万｜面积 {L["area"]}㎡｜单价 {psm:,} 元/㎡\n')

    # 1 价格分位
    print('【1】价格位置')
    print(f'  本套单价 {psm:,}')
    print(f'  小区挂牌 低 {L["community_low"]:,} / 中 {L["community_mid"]:,} / 高 {L["community_high"]:,}')
    print(f'  小区近一年成交 {L["community_deal_low"]:,} – {L["community_deal_high"]:,}')
    print(f'  板块中位 {L["district_mid"]:,}')
    print(f'  → 比小区挂牌中位低 {(1-psm/L["community_mid"])*100:.0f}%；'
          f'比成交下限{"还低" if psm < L["community_deal_low"] else "高"} '
          f'{abs(psm-L["community_deal_low"])/L["community_deal_low"]*100:.0f}%')
    if psm < L['community_deal_low']:
        print('  [注意] 低于近一年成交下限 → 必须查清"为什么便宜"（见风险清单）')

    # 2 租售比
    print('\n【2】租金与租售比')
    for k, s in SCHEMES.items():
        gross_y = s['rent'] * 12
        print(f'  {k:<12} 月租 {s["rent"]:>5,}｜年 {gross_y/10000:>5.2f} 万'
              f'｜毛租售比 {gross_y/p*100:>5.2f}%｜改造 {s["cost"]/10000:>5.1f} 万')

    # 3 自持现金流（不改）
    print('\n【3】自持现金流（不改，整租）')
    for d in (0.15, 0.30, 0.50, 1.00):
        cf, m = flows_for(0.0, 10, d, L['rent_whole'])
        annual = cf[1]
        print(f'  首付 {d:>5.0%}：月供 {m:>6,.0f}｜年现金流 {annual/10000:>+6.2f} 万｜'
              f'10年 IRR(g=0) {irr(cf):>6.1%}')

    # 4 盈亏平衡
    print('\n【4】盈亏平衡房价年涨幅')
    for n in (5, 10, 15):
        print(f'  持有 {n:>2} 年：不亏 {breakeven(n, 0.0):>6.2%}｜跑赢5% {breakeven(n, 0.05):>6.2%}')

    # 5 改造对比（自持，15% 首付，持有 10 年）
    print('\n【5】改造方案对比（首付 15%，持有 10 年）')
    base_cf, m = flows_for(0.0, 10, 0.15, L['rent_whole'])
    base_annual = base_cf[1]
    for k, s in SCHEMES.items():
        cf, _ = flows_for(0.02, 10, 0.15, s['rent'], cost=s['cost'], vac=s['vac'], opex=s['opex'])
        cf0, _ = flows_for(0.0, 10, 0.15, s['rent'], cost=s['cost'], vac=s['vac'], opex=s['opex'])
        annual = cf0[1]
        inc = annual - base_annual
        payback = s['cost'] / inc if inc > 0 else float('inf')
        print(f'  {k:<12} 月租 {s["rent"]:>5,}｜年现金流 {annual/10000:>+6.2f} 万'
              f'（增量 {inc/10000:>+5.2f}）｜改造回本 {payback:>5.1f} 年｜IRR(g=2%) {irr(cf):>6.1%}')

    print('\n【6】房龄与折旧')
    print(f'  建成 {L["build_year"]}，房龄 {2026-L["build_year"]} 年；贷款剩余年限按 30 年计，'
          f'出售时房龄 {2026-L["build_year"]+10} 年')

    out = {'version': V, 'listing': L,
           'breakeven': {str(n): {'irr0': breakeven(n, 0.0), 'irr5': breakeven(n, 0.05)} for n in (5, 10, 15)}}
    with open('house/realestate/listing-20261116-yunjiaoyuan.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('\n已写出 house/realestate/listing-20261116-yunjiaoyuan.json')


if __name__ == '__main__':
    main()

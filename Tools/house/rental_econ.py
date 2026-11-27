# -*- coding: utf-8 -*-
"""
地产线 · 二房东经营模型 v1.1（包租口径）
三个杠杆：拿房价 / 单元租金 / 出租率
核心区分：轻改（视觉翻新）vs 结构改（分隔/加卫）
输出：净现金流、回本、不同租期累计、最优定价、可行性边界
运行：python Tools/house/rental_econ.py
"""
import json

VERSION = 'v1.1-20261114'

# ---------------- 假设（改这里，全文重算） ----------------
MARKET_WHOLE = 3300        # 整租市场价（元/月）
RENT_IN_RATIO = 0.70       # 拿房价 = 市场价 × 70%
OPEX_BASE = 100            # 固定运营（元/月）
OPEX_PER_UNIT = 150        # 每单元运营（维修/保洁/网/耗材）
LEASE_YEARS = 6            # 租约年限
ELASTIC = 2.0              # 降价 1% → 空置天数减少 2%
VAC_FLOOR = 7              # 空置天数下限

# ---------------- 五个方案（同一套 98㎡） ----------------
SCHEMES = {
    '① 整租转租(仅刷新)':   {'units': [(3300, 25)], 'cost': 20000,  'kind': '轻改'},
    '② 轻改整租':           {'units': [(3300, 15)], 'cost': 30000,  'kind': '轻改'},
    '③ 轻改分间(共享卫)':    {'units': [(1700, 30), (1550, 40), (1000, 50)], 'cost': 50000, 'kind': '轻改'},
    '④ 三间合租(加1卫)':     {'units': [(1870, 30), (1760, 40), (1210, 50)], 'cost': 140000, 'kind': '结构改'},
    '⑤ 两套一室户(加卫+门)':  {'units': [(3000, 40), (3000, 40)], 'cost': 200000, 'kind': '结构改'},
}
HORIZONS = [5, 6, 8, 10]


def gross_rent(units, discount=0.0):
    total = 0.0
    for rent, vac in units:
        r = rent * (1 - discount)
        v = max(VAC_FLOOR, vac * (1 - ELASTIC * discount))
        total += r * (365 - v) / 365
    return total


def evaluate(name, sch, discount=0.0, ratio=RENT_IN_RATIO, vac_delta=0, rent_mul=1.0):
    units = [(r * rent_mul, max(VAC_FLOOR, v + vac_delta)) for r, v in sch['units']]
    gross = gross_rent(units, discount)
    rent_in = MARKET_WHOLE * ratio
    opex = OPEX_BASE + OPEX_PER_UNIT * len(units)
    net = gross - rent_in - opex
    annual = net * 12
    payback = sch['cost'] / annual if annual > 0 else float('inf')
    occ = sum((365 - max(VAC_FLOOR, v + vac_delta)) / 365 for _, v in units) / len(units)
    return dict(scheme=name, units=len(units), gross_month=gross, rent_in=rent_in, opex=opex,
                net_month=net, net_year=annual, occupancy=occ, payback_y=payback,
                cost=sch['cost'], kind=sch['kind'], discount=discount)


def best_discount(sch):
    best, d = None, 0.0
    while d <= 0.3001:
        net = evaluate('x', sch, discount=d)['net_month']
        if best is None or net > best[1]:
            best = (d, net)
        d += 0.005
    return best


def main():
    print(f'二房东经营模型 {VERSION}')
    print(f'假设：整租 {MARKET_WHOLE} 元/月｜拿房 {RENT_IN_RATIO:.0%}｜租约 {LEASE_YEARS} 年｜'
          f'运营 {OPEX_BASE}+{OPEX_PER_UNIT}/单元｜弹性 {ELASTIC}\n')

    base = evaluate('①', SCHEMES['① 整租转租(仅刷新)'])
    rows = []
    print(f'{"方案":<22}{"转租/月":>8}{"出租率":>7}{"净现金/月":>9}{"回本":>7}{"5年累计":>9}{"8年累计":>9}')
    print('-' * 76)
    for name, sch in SCHEMES.items():
        r = evaluate(name, sch)
        rows.append(r)
        h5 = r['net_year'] * 5 - sch['cost']
        h8 = r['net_year'] * 8 - sch['cost']
        print(f'{name:<22}{r["gross_month"]:>8.0f}{r["occupancy"]:>7.1%}'
              f'{r["net_month"]:>9.0f}{r["payback_y"]:>6.1f}年{h5/10000:>8.1f}万{h8/10000:>8.1f}万')

    print('\n最优定价（降价换出租率）：')
    for name, sch in SCHEMES.items():
        d, net = best_discount(sch)
        b = evaluate(name, sch)['net_month']
        print(f'  {name:<22} 最优降幅 {d:>5.1%}  净现金 {net:>6.0f}（基准 {b:.0f}，{net-b:+.0f}）')
    print('  规则：出租率 >67% 时降价不划算；<67% 才靠降价换量。')

    print('\n敏感性（净现金/月）：')
    print(f'{"方案":<22}{"租入65%":>9}{"75%":>8}{"空置-10天":>11}{"空置+10天":>11}{"租金-10%":>10}{"租金+10%":>10}')
    for name, sch in SCHEMES.items():
        cells = [evaluate(name, sch, ratio=0.65)['net_month'],
                 evaluate(name, sch, ratio=0.75)['net_month'],
                 evaluate(name, sch, vac_delta=-10)['net_month'],
                 evaluate(name, sch, vac_delta=10)['net_month'],
                 evaluate(name, sch, rent_mul=0.9)['net_month'],
                 evaluate(name, sch, rent_mul=1.1)['net_month']]
        print(f'{name:<22}' + ''.join(f'{c:>10.0f}' for c in cells))

    print('\n可行性边界（按 5 年回本倒推改造成本上限，含相对①的增量口径）：')
    for name, sch in SCHEMES.items():
        r = evaluate(name, sch)
        inc_month = r['net_month'] - base['net_month']
        inc_year = inc_month * 12
        max_cost = inc_year * 5 if inc_year > 0 else 0
        inc_cost = sch['cost'] - SCHEMES['① 整租转租(仅刷新)']['cost']
        verdict = '过' if max_cost >= inc_cost else '不过'
        print(f'  {name:<22} 增量 {inc_month:>6.0f}/月｜5 年可承受 {max_cost/10000:>5.1f} 万'
              f'（增量投入 {inc_cost/10000:>5.1f} 万）→ {verdict}')

    print('\n租期累计（净现金×年 - 改造成本）：')
    print(f'{"方案":<22}' + ''.join(f'{str(h)+"年":<9}' for h in HORIZONS))
    for name, sch in SCHEMES.items():
        r = evaluate(name, sch)
        print(f'{name:<22}' + ''.join(f'{((r["net_year"]*h - sch["cost"])/10000):<9.1f}' for h in HORIZONS))

    out = {'version': VERSION,
           'assumptions': {'market_whole': MARKET_WHOLE, 'rent_in_ratio': RENT_IN_RATIO,
                           'opex_base': OPEX_BASE, 'opex_per_unit': OPEX_PER_UNIT,
                           'lease_years': LEASE_YEARS, 'elastic': ELASTIC},
           'schemes': SCHEMES, 'results': rows}
    with open('house/realestate/rental-econ-20261114.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('\n已写出 house/realestate/rental-econ-20261114.json')


if __name__ == '__main__':
    main()

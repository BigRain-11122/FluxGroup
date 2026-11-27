# -*- coding: utf-8 -*-
"""
地产线 · 低价捡漏筛选 v2（小区级）
口径（2026-11-16 CEO 令：不看高价、低价捡漏为主、兼顾涨幅与租金）：

  1. 低价：75㎡ 两房（流通最好的面积段）公允总价 ≤ 150 万
  2. 捡漏：报价应低于「本小区公允区间下限」，出价线 = 下限 × 0.95
  3. 租金：净回报 ≥ 1.5%（毛回报另列；净口径扣物业/空置/维修/中介/税费）
  4. 涨幅：只碰「次新板块 + 主流面积」；老破小一律剔
     —— 机构共识（东吴/高盛/社科院）：L 型筑底，老破小与配套差加速贬值
     本机无建成年份数据（房天下小区详情页需验证），故用「板块分级 + 小区名标记」替代，
     并在结果里标明这是代理判据、需现场核年代。

数据：hot-sectors-<date>.csv（板块挂牌/在售）+ communities-cache.csv（小区挂牌）
标定：挂牌→成交 1.19（韵佳苑同小区同面积段实测），区间 1.10–1.29
"""
import argparse
import csv
import os
import re
import statistics
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RE = os.path.join(ROOT, 'house', 'realestate')

RENT_ANCHOR = 33.7      # 元/㎡/月，韵佳苑 135㎡ 整租 4550 实测
ANCHOR_AREA = 135.0
DISTRICT_RENT = {'相城': 0.90, '吴中': 0.95, '姑苏': 1.05, '高新': 1.00,
                 '园区': 1.20, '吴江': 0.85}

# 次新/有接盘板块（可涨可卖） vs 老城存量（租得动但难卖）
SECTOR_TIER = {
    '元和': 2, '高铁新城': 2, '郭巷': 2, '科技城': 2, '青剑湖': 2,
    '太湖新城': 2, '斜塘': 2, '狮山': 2,
    '城南': 0, '金阊': 0, '沧浪': 0, '平江': 0, '双塔': 0,
    '湖东': 1, '玲珑': 1, '双湖': 1, '独墅湖': 1,
}

EXCLUDE_KW = ('别墅', '大厦', '商业', '广场', '公寓', '写字楼', '酒店', '商铺',
              '市场', '科技园', '产业园', '工业', '商务', '综合服务楼', '员工楼')
OLD_RE = re.compile(r'(新村|一村|二村|三村|四村|五村|六村|七村|八村|九村|村$|老村)')


def latest(pattern):
    fs = [f for f in os.listdir(RE) if f.startswith(pattern) and f.endswith('.csv')]
    return os.path.join(RE, sorted(fs)[-1]) if fs else None


def load_sectors():
    p = latest('hot-sectors-')
    out = {}
    with open(p, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            try:
                out[r['sector']] = {'district': r['district'],
                                    'price': int(r['price']),
                                    'listings': int(r['listings'] or 0)}
            except (ValueError, KeyError):
                continue
    return out, os.path.basename(p)


def load_communities():
    rows = []
    with open(os.path.join(RE, 'communities-cache.csv'), encoding='utf-8-sig',
              newline='') as f:
        for r in csv.DictReader(f):
            try:
                psm = int(float(r['psm']))
            except (ValueError, KeyError):
                continue
            name = (r.get('community') or '').strip()
            if not name or any(k in name for k in EXCLUDE_KW):
                continue
            if not (4000 <= psm <= 45000):
                continue
            rows.append({'sector': r['sector'], 'district': r['district'],
                         'community': name, 'psm': psm,
                         'old_name': bool(OLD_RE.search(name))})
    return rows


def rent_for(area, district):
    f_area = (ANCHOR_AREA / area) ** 0.18
    return round(area * RENT_ANCHOR * f_area * DISTRICT_RENT.get(district, 1.0) / 50) * 50


def net_yield(rent, area, price):
    """净口径：扣空置 1 个月、物业 2.05 元/㎡、维修 3%、中介半月、税费 11.5%"""
    gross = rent * 12
    vacant = rent * 1
    prop = 2.05 * area * 12
    repair = gross * 0.03
    agent = rent * 0.5
    tax = gross * 0.115
    return (gross - vacant - prop - repair - agent - tax) / price * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--area', type=float, default=75)
    ap.add_argument('--max-total', type=float, default=150)
    ap.add_argument('--min-net-yield', type=float, default=1.5, dest='min_net')
    ap.add_argument('--r-min', type=float, default=0.72)
    ap.add_argument('--r-max', type=float, default=1.05)
    ap.add_argument('--keep-old-names', action='store_true')
    ap.add_argument('--top', type=int, default=18)
    args = ap.parse_args()

    sectors, sfile = load_sectors()
    comms = load_communities()
    print(f'数据：{sfile}（{len(sectors)} 板块）+ communities-cache（{len(comms)} 小区）')
    if not args.keep_old_names:
        old = sum(1 for c in comms if c['old_name'])
        comms = [c for c in comms if not c['old_name']]
        print(f'剔除"XX村/新村"命名老盘 {old} 个 → 余 {len(comms)}')

    rows = []
    for c in comms:
        s = sectors.get(c['sector'])
        if not s or not s['price']:
            continue
        r = c['psm'] / s['price']
        if not (args.r_min <= r <= args.r_max):
            continue
        fair = s['price'] / 1.19 * r
        low = s['price'] / 1.29 * r
        high = s['price'] / 1.10 * r
        total_mid = fair * args.area / 10000
        if total_mid > args.max_total:
            continue
        rent = rent_for(args.area, c['district'])
        gross = rent * 12 / (total_mid * 10000) * 100
        net = net_yield(rent, args.area, total_mid * 10000)
        if net < args.min_net:
            continue
        tier = SECTOR_TIER.get(c['sector'], 1)
        s_price = max(0.0, (args.max_total - total_mid) / args.max_total) * 22
        s_yield = min(1.0, (net - 1.0) / 1.5) * 26
        s_tier = tier / 2 * 22                      # 涨幅/退出面
        s_val = (1 - min(1.0, abs(r - 0.80) / 0.22)) * 15
        s_liq = (1 - min(1.0, abs(s['listings'] - 2000) / 4200)) * 15
        rows.append({
            'sector': c['sector'], 'district': c['district'], 'community': c['community'],
            'tier': tier,
            'list_psm': c['psm'], 'r_vs_sector': round(r, 3),
            'fair_low': int(low), 'fair_mid': int(fair), 'fair_high': int(high),
            'total_mid_wan': round(total_mid, 1),
            'bid_line_wan': round(low * 0.95 * args.area / 10000, 1),
            'rent_m': rent,
            'yield_gross': round(gross, 2), 'yield_net': round(net, 2),
            'sector_listings': s['listings'],
            'score': round(s_price + s_yield + s_tier + s_val + s_liq, 1),
        })

    rows.sort(key=lambda x: -x['score'])
    out = os.path.join(RE, f'bargain-low-{date.today():%Y%m%d}.csv')
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ['x'])
        w.writeheader()
        w.writerows(rows)

    print(f'\n达标小区 {len(rows)} 个（{args.area:.0f}㎡ 两房，总价≤{args.max_total:.0f}万，'
          f'净回报≥{args.min_net}%）\n')
    hdr = (f'{"板块":<7}{"档":>2}{"小区":<16}{"挂牌":>6}{"系数":>5}{"公允单价":>7}'
           f'{"中值总价":>7}{"出价线":>6}{"月租":>5}{"毛%":>5}{"净%":>5}{"分":>5}')
    print(hdr)
    for x in rows[:args.top]:
        print(f"{x['sector']:<7}{x['tier']:>2}{x['community'][:14]:<16}{x['list_psm']:>6}"
              f"{x['r_vs_sector']:>5.2f}{x['fair_mid']:>7}{x['total_mid_wan']:>7.0f}"
              f"{x['bid_line_wan']:>6.0f}{x['rent_m']:>5}{x['yield_gross']:>5.1f}"
              f"{x['yield_net']:>5.2f}{x['score']:>5.0f}")

    print('\n板块汇总（达标数 / 净回报中位 / 板块在售）：')
    agg = {}
    for x in rows:
        agg.setdefault(x['sector'], []).append(x)
    for k, v in sorted(agg.items(), key=lambda kv: -len(kv[1])):
        print(f"  {k:<7}{len(v):>3} 个  净 {statistics.median([y['yield_net'] for y in v]):.2f}%"
              f"  在售 {v[0]['sector_listings']:>5}  档 {v[0]['tier']}")
    print('\n→', out)


if __name__ == '__main__':
    main()

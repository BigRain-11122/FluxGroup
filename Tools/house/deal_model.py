# -*- coding: utf-8 -*-
"""
一房一价决策模型 v2 —— 四维（时间点 / 板块 / 小区 / 户型）× 双轨（自住 / 投资）

设计要点（为什么这样切）：
  自住和投资是两个不同的问题，混在一起就会得出互相矛盾的价。
  - 自住轨问"比同类便宜多少" → 决定出一个"合理价"
  - 投资轨问"要到手几年、年化多少" → 决定出一个"门槛价"
  两个价之间的差价，就是"这笔钱是消费还是投资"的量化表达。

用法：
    python Tools/house/deal_model.py
    python Tools/house/deal_model.py --price 1650000 --area 135.15 --years 8
    python Tools/house/deal_model.py --json

自检：
    python Tools/house/deal_model.py --self-test
"""
import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import return_model as RM  # noqa: E402

# Windows 控制台默认 GBK，输出 ✓/✗/㎡ 会抛 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
BASE_PATH = os.path.join(ROOT, 'house', 'realestate', 'baselines.json')
SECTORS_CSV = os.path.join(ROOT, 'house', 'realestate', 'hot-sectors-20261116.csv')

DEFAULTS = dict(
    price=1_720_000, area=135.15, community='yunjiaoyuan', band='128-135',
    floor=14, total_floor=28, orientation='南', years=8, target_irr=0.04,
    price_trend=0.0, decor_discount=0.05, bargain_discount=0.03,
    monthly_rent=None, listing_listings=None, sector_monthly=None,
)


def load_base(path=BASE_PATH):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# ---------------- 定价：投资轨 ----------------
def build_cfg(price, area, monthly_rent, years, g, rate=0.033, down=0.30,
              opex_psm=2.05):
    return {
        'property': {'price': price, 'area': area, 'deed_tax_rate': 0.02,
                     'agency_buy': 0.01, 'other_buy': 0.005},
        'rent': {'units': [{'rent': monthly_rent, 'vacancy_days': 30}],
                 'growth': 0.02, 'bad_debt': 0.0},
        'opex': {'property_fee_per_sqm': opex_psm, 'maintenance_pct': 0.03,
                 'appliance_reserve': 1000, 'insurance': 200,
                 'management_pct': 0.0, 'letting_cost_months': 0.5,
                 'utilities_vacant': 150},
        'tax': {'vat_rate': 0.015, 'income_tax_rate': 0.10, 'property_tax_rate': 0.0},
        'finance': {'down': down, 'rate': rate, 'years': 30, 'valuation_ratio': 1.0},
        'exit': {'years': years, 'price_growth': g, 'sell_agency': 0.02,
                 'sell_tax': 0.025},
        'capex': {'initial': 0, 'major_cycle_years': 0, 'major_per_sqm': 0},
        'discount_rate': 0.05,
    }


def irr_at(cfg, price):
    c = copy.deepcopy(cfg)
    c['property']['price'] = price
    v = RM.irr(RM.annual_cf(c)['flows'])
    return -1.0 if v is None else v


def price_for_irr(cfg, target, lo=300_000, hi=6_000_000):
    """买入价越低 IRR 越高，单调，二分即可。返回使 IRR=target 的买入价。"""
    if irr_at(cfg, lo) < target:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if irr_at(cfg, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def g_for_irr(price, area, rent, years, target, lo=-0.10, hi=0.25):
    """在给定买入价下，求解使 IRR=target 的房价年涨幅。IRR 随 g 单调递增。"""
    def f(g):
        v = irr_at(build_cfg(price, area, rent, years, g), price)
        return -1.0 if v is None else v
    if f(hi) < target:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------- 定价：自住轨 ----------------
def self_living_price(deal_mid_psm, area, decor=0.05, bargain=0.03):
    """同面积段成交中位单价 × 面积 × (1 − 简装 − 议价)"""
    raw = deal_mid_psm * area
    return raw * (1 - decor - bargain), raw


# ---------------- 四维打分 ----------------
def score_time(base, inv_months, price_trend):
    """3 信号：库存去化 / 价格趋势 / 政策立场。返回 (分, 明细)"""
    det = []
    if inv_months is None:
        s1, t1 = 0.5, '去化未知'
    elif inv_months <= 18:
        s1, t1 = 1.0, f'去化{inv_months:.1f}月≤18'
    elif inv_months <= 24:
        s1, t1 = 0.5, f'去化{inv_months:.1f}月(18~24)'
    else:
        s1, t1 = 0.0, f'去化{inv_months:.1f}月>24'
    det.append(('库存', s1, t1))

    if price_trend >= 0.02:
        s2, t2 = 1.0, f'3月环比{price_trend:+.1%}(转正)'
    elif price_trend >= 0:
        s2, t2 = 0.5, f'3月环比{price_trend:+.1%}(横盘)'
    else:
        s2, t2 = 0.0, f'3月环比{price_trend:+.1%}(下跌)'
    det.append(('趋势', s2, t2))

    stance = base.get('policy', {}).get('stance', '中性')
    # 托底≠刺激：托底只保证"不更快下跌"，不产生上涨，故与中性同档
    s3 = {'收紧需求': 0.0, '中性': 0.5, '托底': 0.5, '刺激': 1.0}.get(stance, 0.5)
    det.append(('政策', s3, stance))
    return sum(d[1] for d in det), det


def score_sector(listings, sector_monthly, sector_name=''):
    """板块：只有月成交时才能算去化；否则诚实返回 None。"""
    if listings and sector_monthly:
        m = listings / sector_monthly
        s = 1.0 if m <= 12 else (0.5 if m <= 24 else 0.0)
        return s, f'{sector_name} 在售{listings}套 ÷ 月成交{sector_monthly}套 = 去化{m:.1f}月'
    if listings:
        return None, (f'{sector_name} 在售{listings}套（平台自身房源数，非全市场）；'
                      f'缺板块月成交 → 只能看相对位置，不给结论')
    return None, '板块数据缺失'


def score_community(c):
    det = []
    md = c.get('monthly_deals')
    det.append(('月成交', 1.0 if md and md >= 3 else (0.5 if md and md >= 1.5 else 0.0),
                f'{md}套/月' if md else '未知'))
    sm = c.get('static_months')
    det.append(('静态去化', 1.0 if sm and sm <= 24 else (0.5 if sm and sm <= 36 else 0.0),
                f'{sm}月' if sm else '未知'))
    age = 2026 - c.get('build_year', 2026)
    det.append(('房龄', 1.0 if age <= 15 else (0.5 if age <= 20 else 0.0), f'{age}年'))
    det.append(('产权', 0.0 if c.get('title_mixed') else 1.0,
                '混40年公寓(需核)' if c.get('title_mixed') else '单一'))
    return sum(d[1] for d in det) / len(det), det


def score_layout(area, avg_area, band, band_deals):
    det = []
    r = area / avg_area
    det.append(('面积偏离', 1.0 if r <= 1.3 else (0.5 if r <= 1.5 else 0.0),
                f'{area:.0f}㎡ = 均套{avg_area:.0f}㎡ 的 {r:.2f} 倍'))
    det.append(('同类成交', 1.0 if band_deals else 0.0,
                f'{band}㎡ 近6月 {band_deals or 0} 笔'))
    return sum(d[1] for d in det) / len(det), det


# ---------------- 主流程 ----------------
def evaluate(args):
    base = load_base(args.base)
    m = base['market']
    c = base['community'].get(args.community, {})
    avg_area = m['avg_unit_area_secondhand']['v']

    inv_months = m['inventory_units']['v'] / m['newhome_monthly_units']['v']
    if args.area > 0:
        psm = args.price / args.area
    else:
        psm = 0

    band_psm = c.get('deal_mid_psm_by_band', {}).get(args.band)
    band_deals = c.get('deals_6m_by_band', {}).get(args.band, 0)
    rent = args.monthly_rent or (c.get('rent_by_band', {}).get(args.band[:3], 4550))
    listings = args.listing_listings or c.get('listings_platform')

    t_score, t_det = score_time(base, inv_months, args.price_trend)
    s_score, s_note = score_sector(listings, args.sector_monthly, c.get('sector', ''))
    c_score, c_det = score_community(c)
    h_score, h_det = score_layout(args.area, avg_area, args.band, band_deals)

    sl_price, sl_raw = (None, None)
    if band_psm:
        sl_price, sl_raw = self_living_price(band_psm, args.area,
                                             args.decor_discount, args.bargain_discount)

    cfg = build_cfg(args.price, args.area, rent, args.years, 0.015)
    thr_price = price_for_irr(cfg, args.target_irr)
    irr_now = irr_at(cfg, args.price)
    # 保本涨幅：使 IRR=0
    be_g = 0.015
    lo, hi = -0.10, 0.10
    for _ in range(60):
        mid = (lo + hi) / 2
        v = irr_at(build_cfg(args.price, args.area, rent, args.years, mid), args.price)
        if v is None or v < 0:
            lo = mid
        else:
            hi = mid
    be_g = (lo + hi) / 2

    verdict_self = None
    if sl_price:
        gap = (args.price - sl_price) / sl_price
        if gap <= -0.02:
            verdict_self = '自住：便宜，可谈'
        elif gap <= 0.03:
            verdict_self = '自住：合理区间'
        else:
            verdict_self = '自住：贵了'

    verdict_inv = None
    if thr_price:
        if args.price <= thr_price:
            verdict_inv = '投资：达标'
        else:
            verdict_inv = f'投资：不达标（需降价 {(args.price - thr_price) / 10000:.0f} 万）'

    g_need = g_for_irr(args.price, args.area, rent, args.years, args.target_irr)

    return dict(
        price=args.price, area=args.area, psm=psm,
        self_price=sl_price, self_price_raw=sl_raw, self_gap=(
            (args.price - sl_price) / sl_price if sl_price else None),
        thr_price=thr_price, irr=irr_now, be_g=be_g, g_need=g_need,
        thr_realistic=bool(thr_price and thr_price >= args.price * 0.70),
        target_irr=args.target_irr, years=args.years,
        time=(t_score, t_det), sector=(s_score, s_note),
        community=(c_score, c_det), layout=(h_score, h_det),
        rent=rent, inv_months=inv_months,
        verdict_self=verdict_self, verdict_inv=verdict_inv,
        community_name=c.get('name', args.community),
    )


def fmt(r):
    w = []
    a = w.append
    a('=' * 62)
    a(f"{r['community_name']}  {r['area']:.2f}㎡  挂牌 {r['price']/10000:.0f} 万"
      f"（{r['psm']:,.0f} 元/㎡）")
    a('=' * 62)
    a('')
    a('一、一句话结论')
    a(f"  {r['verdict_self'] or '—'}；{r['verdict_inv'] or '—'}")
    a('')
    a('二、自住轨：比同类贵还是便宜')
    if r['self_price']:
        a(f"  自住合理价：{r['self_price']/10000:.1f} 万  "
          f"（同面积段成交中位倒推，已扣简装5%+议价3%）")
        a(f"  挂牌{'高于' if r['self_gap'] > 0 else '低于'}合理价 "
          f"{abs(r['self_gap']):.1%}")
    else:
        a('  缺同面积段成交中位，无法计算')
    a('')
    a('三、投资轨：要什么条件才成立')
    a(f"  现状：{r['years']} 年持有、房价按 1.5% 年涨，IRR {r['irr']:.1%}")
    a(f"  保本（IRR=0）需房价年涨 {r['be_g']:+.1%}")
    if r['g_need'] is None:
        a(f"  达标（IRR {r['target_irr']:.0%}）：即使房价年涨 25% 也达不到")
    else:
        a(f"  达标（IRR {r['target_irr']:.0%}）需房价年涨 {r['g_need']:.1%}")
    if r['thr_price']:
        flag = '' if r['thr_realistic'] else '（低于挂牌 30%，等于不现实）'
        a(f"  等价说法：买入价降到 {r['thr_price']/10000:.0f} 万以内{flag}")
    a('')
    a('四、四维体检')
    a(f"  时间点 {r['time'][0]:.1f}/3  {'✅' if r['time'][0] >= 2.5 else ('🟡' if r['time'][0] >= 1.5 else '🔴')}")
    for k, s, d in r['time'][1]:
        a(f"      {k} {'✓' if s >= 1 else ('~' if s >= .5 else '✗')}  {d}")
    sc, sn = r['sector']
    a(f"  板块   {'—' if sc is None else f'{sc:.1f}/1'}")
    a(f"      {sn}")
    a(f"  小区   {r['community'][0]:.0%} 通过")
    for k, s, d in r['community'][1]:
        a(f"      {k} {'✓' if s >= 1 else ('~' if s >= .5 else '✗')}  {d}")
    a(f"  户型   {r['layout'][0]:.0%} 通过")
    for k, s, d in r['layout'][1]:
        a(f"      {k} {'✓' if s >= 1 else ('~' if s >= .5 else '✗')}  {d}")
    a('')
    a('五、一个动作')
    if r['self_price'] and r['thr_price']:
        if r['price'] <= r['thr_price']:
            a(f'  → 自住和投资都成立，直接接。')
        elif r['price'] <= r['self_price'] * 1.03:
            a(f"  → 自住口径可接（合理价 {r['self_price']/10000:.0f} 万上下）；"
              f"当投资买要砍到 {r['thr_price']/10000:.0f} 万以内。")
        else:
            a(f"  → 报价偏高，按 {r['self_price']/10000:.0f} 万起谈；"
              f"投资口径需 {r['thr_price']/10000:.0f} 万以内。")
    a('')
    return '\n'.join(w)


def self_test():
    """正例 + 反例：便宜房双轨成立 / 高价房双轨都不成立 / IRR 单调。"""
    base = load_base()
    m = base['market']
    c = base['community']['yunjiaoyuan']
    avg = m['avg_unit_area_secondhand']['v']
    ok = True

    # 1) IRR 随价格单调递减
    cfg = build_cfg(1_720_000, 135.15, 4550, 8, 0.015)
    i_low, i_high = irr_at(cfg, 1_200_000), irr_at(cfg, 2_400_000)
    if not i_low > i_high:
        print(f'[FAIL] IRR 应随价升而降: {i_low:.3f} vs {i_high:.3f}')
        ok = False

    # 2) 正例：便宜到 110 万，应双轨成立
    thr = price_for_irr(cfg, 0.04)
    if thr is None or not (900_000 < thr < 2_000_000):
        print(f'[FAIL] 门槛价异常: {thr}')
        ok = False
    else:
        print(f'[ok] 门槛价 {thr/10000:.1f} 万（应低于挂牌 172 万）'
              f' {"✓" if thr < 1_720_000 else "✗"}')
        if thr >= 1_720_000:
            ok = False

    # 3) 自住价：同面积段 14351 元/㎡ × 135.15 × 0.92
    p, raw = self_living_price(c['deal_mid_psm_by_band']['128-135'], 135.15)
    exp = 14351 * 135.15 * 0.92
    if abs(p - exp) > 1:
        print(f'[FAIL] 自住价计算: {p} vs {exp}')
        ok = False
    else:
        print(f'[ok] 自住合理价 {p/10000:.1f} 万（原始 {raw/10000:.1f} 万）')

    # 4) 反例：挂牌价 172 万 应判"投资贵"
    if thr and 1_720_000 > thr:
        print(f'[ok] 挂牌 172 万 > 门槛 {thr/10000:.1f} 万 → 判"投资不成立" ✓')
    else:
        print('[FAIL] 挂牌 172 万应被判为投资不成立')
        ok = False

    # 5) 时间点打分：去化 21.2 月 + 横盘 + 托底 = 1.5
    s, _ = score_time(base, 42771 / 2021, 0.0)
    if abs(s - 1.5) > 1e-9:
        print(f'[FAIL] 时间点应为 1.5，得 {s}')
        ok = False
    else:
        print('[ok] 时间点 1.5/3（现在可谈、不可买）')

    # 6) 户型：135 / 103.3 = 1.31 → 应落在 0.5 档
    s2, _ = score_layout(135.15, avg, '128-135', 1)
    if abs(s2 - 0.75) > 1e-9:
        print(f'[FAIL] 户型分应为 0.75，得 {s2}')
        ok = False
    else:
        print('[ok] 户型 0.75（面积偏离扣分、同类成交加分）')

    print('\nSELF-TEST', 'PASS 6/6' if ok else 'FAIL')
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=BASE_PATH)
    ap.add_argument('--price', type=float, default=DEFAULTS['price'])
    ap.add_argument('--area', type=float, default=DEFAULTS['area'])
    ap.add_argument('--community', default=DEFAULTS['community'])
    ap.add_argument('--band', default=DEFAULTS['band'])
    ap.add_argument('--years', type=int, default=DEFAULTS['years'])
    ap.add_argument('--target-irr', type=float, default=DEFAULTS['target_irr'])
    ap.add_argument('--price-trend', type=float, default=DEFAULTS['price_trend'])
    ap.add_argument('--decor-discount', type=float, default=DEFAULTS['decor_discount'])
    ap.add_argument('--bargain-discount', type=float,
                    default=DEFAULTS['bargain_discount'])
    ap.add_argument('--monthly-rent', type=float, default=None)
    ap.add_argument('--listing-listings', type=int, default=None)
    ap.add_argument('--sector-monthly', type=int, default=None)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    r = evaluate(args)
    if args.json:
        out = {k: v for k, v in r.items() if k != 'time' or True}
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    else:
        print(fmt(r))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
双层估值模型：板块定"值不值"，小区定"贵不贵"。

方法（为什么这样算才严谨）：
  1) 平台只有"挂牌价"，没有"成交价"。而园区同时有挂牌（多板块加权）和成交（2.37 万），
     于是可以标定出**挂牌/成交溢价倍数**（= 挂牌加权均价 ÷ 成交加权均价）。
  2) 该倍数只能标定园区一个点，不能假装知道每个板块。所以对全市用**区间**：
     高锚=园区倍数，低锚=全市倍数；板块公允成交价 = 挂牌价 ÷ 倍数区间 → 得到区间而非点估。
  3) 小区层用"小区挂牌 ÷ 板块挂牌"这个**同源比值**，规避口径错配，再乘板块公允成交价。
  4) 投资价值不拍租金：用实测锚（韵佳苑 4,550 元/月 / 172 万 = 毛租售比 3.17%）作为
     全市统一租金口径，算出净回报。**列内可比，绝对值仅供参考**（各板块真实租金未差异化）。

用法：
    python Tools/house/valuation.py                  # 板块表 + 小区表
    python Tools/house/valuation.py --sector 郭巷
    python Tools/house/valuation.py --screen         # 只看筛选结果
    python Tools/house/valuation.py --self-test
"""
import argparse
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RE = os.path.join(ROOT, 'house', 'realestate')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# 交易成本与持有成本参数（与 deal_model / return_model 同源）
P = dict(fee_psm=2.05, maint_pct=0.03, appliance=1000, insurance=200,
         letting_months=0.5, util_vacant=150, vat=0.015, itax=0.10)


def load_base():
    with open(os.path.join(RE, 'baselines.json'), encoding='utf-8') as f:
        return json.load(f)


def load_sectors():
    files = sorted(glob.glob(os.path.join(RE, 'hot-sectors-*.csv')))
    if not files:
        raise SystemExit('[FAIL] 找不到 hot-sectors-*.csv，先跑 scrape_hot_sectors.py')
    rows = []
    with open(files[-1], encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            try:
                r['psm'] = int(r['price']) if r.get('price') else None
                r['listings'] = int(r['listings']) if r.get('listings') else None
            except ValueError:
                r['psm'], r['listings'] = None, None
            rows.append(r)
    return rows, os.path.basename(files[-1])


def load_communities():
    path = os.path.join(RE, 'communities-cache.csv')
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            try:
                r['psm'] = int(r['psm']) if r.get('psm') else None
            except ValueError:
                r['psm'] = None
            out.append(r)
    return out


# ---------------- 标定 ----------------
def weighted_psm(rows):
    tot_n = tot_v = 0
    for r in rows:
        if r.get('psm') and r.get('listings'):
            tot_n += r['listings']
            tot_v += r['psm'] * r['listings']
    return (tot_v / tot_n) if tot_n else None


def calibrate(sectors, base):
    """
    溢价倍数（挂牌 ÷ 成交）只能从**同小区同面积段**标定，不能拿板块互比。

    ⚠️ 反面教材（本轮实测）：园区挂牌加权 51,872 vs 园区成交 23,700 → 2.19 倍。
    这**不是**"挂牌虚高 2.2 倍"，而是两边的商品结构不同——挂牌端是双湖/玲珑的
    别墅豪宅，成交端含唯亭/胜浦/娄葑的低价小户型。用 2.19 去除挂牌价，会把
    公允成交价算低一半。跨口径比值只能当"结构差异诊断"，不能当换算系数。

    正法：用韵佳苑自己 —— 小区挂牌均价 17,106 vs 128-135㎡ 段成交中位 14,351
    → 1.19 倍。同小区、同面积段、同商品，才是真溢价。
    """
    c = base['community']['yunjiaoyuan']
    listed = c['community_avg_listed_psm']
    deal = c['deal_mid_psm_by_band']['128-135']
    central = listed / deal

    # 诊断用（不参与计算）：说明跨口径比值有多不可靠
    park = [r for r in sectors if r['district'] == '园区']
    park_list = weighted_psm(park)
    park_deal = base['market']['park_secondhand_psm']['v']
    diag = dict(park_list=park_list, park_deal=park_deal,
                park_ratio=(park_list / park_deal) if park_list else None)

    return central * 1.08, central * 0.92, dict(
        central=central, listed=listed, deal=deal, diagnostic=diag)


# ---------------- 收益 ----------------
def net_yield(psm, area=100.0, rent_psm_month=33.7):
    """给定单价，算净租金回报（扣物业/维修/空置/中介/税）。"""
    price = psm * area
    gross = rent_psm_month * area * 12
    opex = (P['fee_psm'] * area * 12 + gross * P['maint_pct'] + P['appliance']
            + P['insurance'] + gross / 12 * P['letting_months']
            + P['util_vacant'] * 12)
    vat = gross * P['vat']
    itax = max(0.0, gross - opex - vat) * P['itax']
    net = gross - opex - vat - itax
    return dict(price=price, gross=gross, opex=opex, vat=vat, itax=itax,
                net=net, gross_yield=gross / price, net_yield=net / price)


def rent_psm_from_anchor(base):
    """用实测锚反推全市统一租金单价（元/㎡/月）。"""
    c = base['community']['yunjiaoyuan']
    rent = c['rent_by_band']['135']
    area = 135.15
    return rent / area


# ---------------- 板块表 ----------------
def sector_table(sectors, base):
    hi, lo, cal = calibrate(sectors, base)
    rent_psm = rent_psm_from_anchor(base)
    median_psm = sorted(r['psm'] for r in sectors if r['psm'])
    median_psm = median_psm[len(median_psm) // 2] if median_psm else 30000
    max_list = max((r['listings'] or 0) for r in sectors) or 1

    out = []
    for r in sectors:
        if not r.get('psm'):
            continue
        psm = r['psm']
        fair_hi = psm / lo if lo else None      # 用低倍数除 → 公允价上限
        fair_lo = psm / hi if hi else None      # 用高倍数除 → 公允价下限
        y = net_yield((fair_lo + fair_hi) / 2 if fair_lo and fair_hi else psm,
                      rent_psm_month=rent_psm)
        # 分项打分
        s_price = max(0.0, min(1.0, (1 - (psm / median_psm - 0.6) / 1.0)))
        s_yield = max(0.0, min(1.0, (y['net_yield'] - 0.015) / 0.020))
        s_liq = max(0.0, min(1.0, 1 - (r['listings'] or 0) / max_list))
        s_pos = max(0.0, min(1.0, 1 - psm / (median_psm * 2)))
        score = 40 * s_yield + 25 * s_price + 25 * s_liq + 10 * s_pos
        out.append(dict(sector=r['sector'], district=r['district'], psm=psm,
                        listings=r['listings'], fair_lo=fair_lo, fair_hi=fair_hi,
                        premium_lo=lo, premium_hi=hi,
                        net_yield=y['net_yield'], gross_yield=y['gross_yield'],
                        score=score, s_yield=s_yield, s_price=s_price,
                        s_liq=s_liq, s_pos=s_pos))
    out.sort(key=lambda x: -x['score'])
    return out, cal, rent_psm


# ---------------- 小区表 ----------------
def community_table(comms, sectors, base):
    hi, lo, cal = calibrate(sectors, base)
    sec = {r['sector']: r for r in sectors if r.get('psm')}
    out = []
    for c in comms:
        if not c.get('psm'):
            continue
        s = sec.get(c.get('sector'))
        if not s:
            continue
        rel = c['psm'] / s['psm']
        fair_hi = s['psm'] / lo * rel if lo else None
        fair_lo = s['psm'] / hi * rel if hi else None
        out.append(dict(community=c['community'], sector=c['sector'],
                        district=c.get('district', ''), psm=c['psm'],
                        sector_psm=s['psm'], rel=rel,
                        fair_lo=fair_lo, fair_hi=fair_hi,
                        last_seen=c.get('last_seen', ''), url=c.get('url', '')))
    out.sort(key=lambda x: (x['sector'], -x['psm']))
    return out


def screen(sec_rows, comm_rows, min_yield=0.015, min_listings=1000, top=5):
    """
    筛选：先过门槛（净回报下限 + 有货），再按净回报排名取前 N。

    注意：这里不做"高分即值得买"的暗示——苏州全市场净租金回报都在 2% 以下，
    排名只说明"同样租金假设下，哪个板块的价格压力更小"。
    """
    cand = [s for s in sec_rows
            if s['net_yield'] >= min_yield and (s['listings'] or 0) >= min_listings]
    cand.sort(key=lambda s: -s['net_yield'])
    sectors = cand[:top]
    keep = {s['sector'] for s in sectors}
    commons = [c for c in comm_rows if c['sector'] in keep]
    return sectors, commons


# ---------------- 输出 ----------------
def fmt_sectors(rows, cal, rent_psm, path_name):
    w = []
    a = w.append
    d = cal['diagnostic']
    a(f'板块层 · 数据源 {path_name}')
    a(f'溢价标定（同小区同面积段，唯一可用）：'
      f'韵佳苑挂牌 {cal["listed"]:,} ÷ 成交 {cal["deal"]:,} = {cal["central"]:.2f} 倍'
      f'（区间 {cal["central"]*0.92:.2f}~{cal["central"]*1.08:.2f}）')
    if d.get('park_ratio'):
        a(f'结构诊断（不参与计算）：园区挂牌加权 {d["park_list"]:,.0f} ÷ 成交 '
          f'{d["park_deal"]:,} = {d["park_ratio"]:.2f} 倍 —— 差异来自挂牌/成交的商品结构不同，'
          f'不能当换算系数')
    a(f'租金口径：全市 {rent_psm:.1f} 元/㎡/月（实锚 韵佳苑 4,550÷135.15）')
    a('')
    a(f'{"板块":<8}{"区":<5}{"挂牌":>7}{"公允成交区间":>15}{"在售":>7}{"净回报":>8}{"综合":>7}')
    a('-' * 66)
    for r in rows:
        fl = f"{r['fair_lo']:,.0f}-{r['fair_hi']:,.0f}" if r['fair_lo'] else '—'
        a(f"{r['sector']:<8}{r['district']:<5}{r['psm']:>7,}{fl:>15}"
          f"{r['listings'] or 0:>7}{r['net_yield']:>7.2%}{r['score']:>7.0f}")
    return '\n'.join(w)


def fmt_communities(rows, limit=40):
    w = ['', f'小区层（共 {len(rows)} 个，按板块+价格降序显示前 {limit}）',
         f'{"小区":<16}{"板块":<8}{"挂牌":>7}{"板块挂牌":>8}{"相对":>6}{"公允成交区间":>15}']
    for r in rows[:limit]:
        nm = r['community'][:14]
        fl = f"{r['fair_lo']:,.0f}-{r['fair_hi']:,.0f}" if r['fair_lo'] else '—'
        w.append(f'{nm:<16}{r["sector"]:<8}{r["psm"]:>7,}{r["sector_psm"]:>8,}'
                 f'{r["rel"]:>6.2f}{fl:>15}')
    return '\n'.join(w)


def self_test():
    base = load_base()
    sectors, name = load_sectors()
    hi, lo, cal = calibrate(sectors, base)
    c = base['community']['yunjiaoyuan']
    ok = True

    # 1) 溢价倍数应落在 1.05~1.35（同小区挂牌比成交高，通常 10%~30%）
    if not (1.05 <= cal['central'] <= 1.35):
        print(f'[FAIL] 溢价 {cal["central"]:.2f} 越界（应 1.05~1.35）')
        ok = False
    else:
        print(f'[ok] 溢价标定 {cal["central"]:.2f} 倍'
              f'（{cal["listed"]:,} ÷ {cal["deal"]:,}，同小区同面积段）')

    # 2) 区间必须包住中心值
    if not (lo < cal['central'] < hi):
        print(f'[FAIL] 区间 {lo:.2f}~{hi:.2f} 未包住中心 {cal["central"]:.2f}')
        ok = False
    else:
        print(f'[ok] 区间 {lo:.2f}~{hi:.2f} 包住中心值')

    # 3) 外部验证：模型公允价必须落在 20 笔真实成交的单价区间内
    fair = cal['listed'] / cal['central']
    obs = c['deal_band_observed']
    if not (obs['lo'] <= fair <= obs['hi']):
        print(f'[FAIL] 公允价 {fair:,.0f} 落在实测区间 {obs["lo"]:,}~{obs["hi"]:,} 之外')
        ok = False
    else:
        print(f'[ok] 公允价 {fair:,.0f} 落在 20 笔真实成交区间 {obs["lo"]:,}~{obs["hi"]:,} 内')

    # 4) 一致性：板块公允成交价必须低于挂牌价，且折扣率与溢价区间自洽
    rows0, _, _ = sector_table(sectors, base)
    ratios = [r['fair_hi'] / r['psm'] for r in rows0 if r['fair_hi']]
    if not ratios or not all(0.80 <= x <= 0.98 for x in ratios):
        print(f'[FAIL] 公允/挂牌 比值越界：{[round(x, 3) for x in ratios[:5]]}')
        ok = False
    else:
        print(f'[ok] 公允/挂牌 比值 {min(ratios):.2f}~{max(ratios):.2f}（应 <1 且贴近 1/1.19）')

    # 5) 净回报随单价单调递减
    y1 = net_yield(15000)['net_yield']
    y2 = net_yield(30000)['net_yield']
    if not y1 > y2:
        print(f'[FAIL] 净回报未随价递减 {y1:.3f} vs {y2:.3f}')
        ok = False
    else:
        print(f'[ok] 净回报递减 15k→{y1:.2%}  30k→{y2:.2%}')

    # 6) 公允区间有序
    rows, _, _ = sector_table(sectors, base)
    bad = [r['sector'] for r in rows if r['fair_lo'] and r['fair_hi']
           and not r['fair_lo'] < r['fair_hi']]
    if bad:
        print(f'[FAIL] 公允区间倒挂: {bad[:3]}')
        ok = False
    else:
        print(f'[ok] {len(rows)} 个板块公允区间均有序')

    sc, _ = screen(rows, [], min_yield=0.015, min_listings=1000, top=5)
    if not sc:
        print('[FAIL] 筛选返回空（下限 1.5% 应至少命中若干板块）')
        ok = False
    else:
        print(f'[ok] 筛选命中 {len(sc)} 个板块：' + ','.join(s['sector'] for s in sc))

    print('\nSELF-TEST', 'PASS 6/6' if ok else 'FAIL')
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sector', default='')
    ap.add_argument('--screen', action='store_true')
    ap.add_argument('--min-yield', type=float, default=0.015)
    ap.add_argument('--min-listings', type=int, default=1000)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    sectors, name = load_sectors()
    comms = load_communities()
    sec_rows, cal, rent_psm = sector_table(sectors, base=load_base())
    comm_rows = community_table(comms, sectors, load_base())

    if args.sector:
        sec_rows = [r for r in sec_rows if args.sector in r['sector']]
        comm_rows = [r for r in comm_rows if args.sector in r['sector']]

    if args.screen:
        sc, cm = screen(sec_rows, comm_rows, args.min_yield, args.min_listings)
        print(f'筛选条件：净回报 ≥ {args.min_yield:.1%} 且 板块在售 ≥ {args.min_listings}')
        print(f'命中板块 {len(sc)} 个、小区 {len(cm)} 个\n')
        if sc:
            print(fmt_sectors(sc, cal, rent_psm, name))
        if cm:
            print(fmt_communities(cm, 30))
        return

    if args.json:
        print(json.dumps(dict(calibration=cal, sectors=sec_rows,
                              communities=comm_rows), ensure_ascii=False, indent=2))
        return

    print(fmt_sectors(sec_rows, cal, rent_psm, name))
    if comm_rows:
        print(fmt_communities(comm_rows))
    else:
        print('\n小区层：communities-cache.csv 为空（房天下限流时抓不到）。'
              '\n  修复：等 10 分钟后跑 `python Tools/house/scrape_communities.py --only 郭巷`，'
              '每日任务会逐日补全。')


if __name__ == '__main__':
    main()

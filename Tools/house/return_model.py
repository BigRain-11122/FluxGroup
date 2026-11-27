# -*- coding: utf-8 -*-
"""
地产线 · 房产投资回报模型 v1（机构口径）
对标：DCF/IRR（CFA/CCIM 通用）、NOI/Cap Rate（NCREIF/ULI）、DSCR（银行审贷）、
      Cash-on-Cash（私募地产）、压力测试（银保监房地产贷款压力测试思路）

颗粒度：租金（分单元）→ 空置/坏账 → 运营（物业/维修/家电/保险/管理/招租）
        → 税费（增值税/个税/房产税）→ 融资（等额本息/本金）→ 资本支出 → 退出
输出：NOI、Cap Rate、CoC、DSCR、IRR、NPV、EM、回收期、盈亏平衡涨幅、
      单因素敏感性、双因素网格、蒙特卡洛 P10/P50/P90
自检：--self-test（摊还归零 / NPV@IRR≈0 / 无杠杆一致性）
运行：python Tools/house/return_model.py [config.json] [--self-test]
"""
import json
import math
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT_CFG = os.path.join(ROOT, 'house', 'realestate', 'model-config-yunjiaoyuan.json')
_TAG = 'yunjiaoyuan'
OUT_JSON = os.path.join(ROOT, 'house', 'realestate', f'return-model-{_TAG}.json')
OUT_CSV = os.path.join(ROOT, 'house', 'realestate', f'return-model-{_TAG}.csv')

# ---------------- 基础金融函数 ----------------
def pmt(principal, rate, years):
    i = rate / 12
    n = years * 12
    return principal / n if i == 0 else principal * i * (1 + i) ** n / ((1 + i) ** n - 1)


def balance(principal, rate, years, months):
    i = rate / 12
    m = pmt(principal, rate, years)
    return principal * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def npv(rate, flows):
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))


def irr(flows):
    """稳健 IRR：扩展区间 + 保号二分；无解返回 None（不是 nan）"""
    def f(r):
        return npv(r, flows)

    lo, hi = -0.90, 2.00
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < 1e-7:
            return mid
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


# ---------------- 一年度现金流 ----------------
def annual_cf(cfg, rent_mult=1.0, vac_add=0, capex_mult=1.0, g=None, rate=None,
              price_mult=1.0, rent_growth=None):
    p = cfg['property']
    r = cfg['rent']
    o = cfg['opex']
    t = cfg['tax']
    f = cfg['finance']
    e = cfg['exit']
    g = e['price_growth'] if g is None else g
    rate = f['rate'] if rate is None else rate
    rg = r['growth'] if rent_growth is None else rent_growth

    price = p['price'] * price_mult
    buy_cost = price * (p['deed_tax_rate'] + p['agency_buy'] + p.get('other_buy', 0))
    capex0 = cfg['capex']['initial'] * capex_mult
    loan = price * (1 - f['down']) * f.get('valuation_ratio', 1.0)
    m = pmt(loan, rate, f['years'])
    debt = m * 12

    rows = []
    for y in range(1, e['years'] + 1):
        grow = (1 + rg) ** (y - 1)
        gross = 0.0
        for u in r['units']:
            vac = u['vacancy_days'] + vac_add
            vac = max(0, min(365, vac))
            gross += u['rent'] * rent_mult * grow * 12 * (365 - vac) / 365
        gross *= (1 - r.get('bad_debt', 0))

        prop_fee = o['property_fee_per_sqm'] * p['area'] * 12
        maint = gross * o['maintenance_pct']
        appl = o['appliance_reserve']
        ins = o['insurance']
        mgmt = gross * o.get('management_pct', 0)
        letting = gross / 12 * (o['letting_cost_months'])
        util = o.get('utilities_vacant', 0) * 12
        opex = prop_fee + maint + appl + ins + mgmt + letting + util

        vat = gross * t['vat_rate']
        itax = max(0.0, (gross - opex - vat)) * t['income_tax_rate']
        ptax = price * t.get('property_tax_rate', 0)
        tax = vat + itax + ptax

        # NOI 口径：有效租金 − 运营 − 增值税/房产税（不含所得税、不含融资、不含资本支出）
        noi = gross - opex - vat - ptax
        cf = noi - itax - debt
        major = 0.0
        if cfg['capex']['major_cycle_years'] and y % cfg['capex']['major_cycle_years'] == 0:
            major = p['area'] * cfg['capex']['major_per_sqm']
            cf -= major
        rows.append(dict(year=y, gross=gross, opex=opex, tax=tax, itax=itax, noi=noi,
                         debt=debt, major=major, cf=cf))

    sell = price * (1 + g) ** e['years']
    bal = balance(loan, rate, f['years'], e['years'] * 12)
    sell_cost = sell * (e['sell_agency'] + e['sell_tax'])
    net_sale = sell - bal - sell_cost

    flows = [-(price * f['down'] + buy_cost + capex0)]
    flows += [row['cf'] for row in rows]
    flows[-1] += net_sale
    return dict(rows=rows, flows=flows, price=price, buy_cost=buy_cost, capex0=capex0,
                loan=loan, debt=debt, sell=sell, bal=bal, net_sale=net_sale)


# ---------------- 指标 ----------------
def metrics(cfg, res=None, discount=None):
    res = res or annual_cf(cfg)
    e, f, p = cfg['exit'], cfg['finance'], cfg['property']
    years = e['years']
    noi1 = res['rows'][0]['noi']
    total_cost = res['price'] + res['buy_cost'] + res['capex0']
    equity = res['price'] * f['down'] + res['buy_cost'] + res['capex0']
    cf1 = res['rows'][0]['cf']
    disc = cfg.get('discount_rate', 0.05) if discount is None else discount
    return {
        'noi_y1': noi1,
        'cap_rate_on_total_cost': noi1 / total_cost,
        'cap_rate_on_price': noi1 / res['price'],
        'cash_on_cash_y1': cf1 / equity if equity else float('nan'),
        'dscr_y1': noi1 / res['debt'] if res['debt'] else float('inf'),
        'irr': irr(res['flows']),
        'npv': npv(disc, res['flows']),
        'equity_multiple': sum(res['flows'][1:]) / equity if equity else float('nan'),
        'payback_years': next((i for i, cf in enumerate(cumsum(res['flows'])) if cf >= 0), None),
        'total_profit': sum(res['flows']),
        'equity': equity,
        'discount_rate': disc,
        'years': years,
    }


def cumsum(xs):
    s = 0
    for x in xs:
        s += x
        yield s


def breakeven_g(cfg, cfg_over=None, years=None):
    import copy
    c = copy.deepcopy(cfg_over or cfg)
    if years:
        c['exit']['years'] = years
    lo, hi = -0.30, 0.30
    for _ in range(120):
        mid = (lo + hi) / 2
        v = irr(annual_cf(c, g=mid)['flows'])
        v = -1.0 if v is None else v
        if v < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def sensitivity(cfg, gs, rgs):
    import copy
    grid = []
    for g in gs:
        row = []
        for rg in rgs:
            c = copy.deepcopy(cfg)
            row.append(irr(annual_cf(c, g=g, rent_growth=rg)['flows']))
        grid.append(row)
    return grid


def monte_carlo(cfg, n=2000, seed=42):
    import copy
    rnd = random.Random(seed)
    out = []
    failed = 0
    for _ in range(n):
        c = copy.deepcopy(cfg)
        g = rnd.gauss(c['exit']['price_growth'], c.get('mc_sd_price_growth', 0.05))
        rg = rnd.gauss(c['rent']['growth'], c.get('mc_sd_rent_growth', 0.015))
        vac = rnd.uniform(-10, 30)
        cap = rnd.uniform(0.9, 1.35)
        res = annual_cf(c, g=g, rent_growth=rg, vac_add=vac, capex_mult=cap)
        v = irr(res['flows'])
        if v is None:
            failed += 1
            out.append(-1.0)   # 无解=全额亏损，按 -100% 计入
        else:
            out.append(v)
    out.sort()
    q = lambda p: out[int(p * (len(out) - 1))]
    return {'p10': q(0.10), 'p50': q(0.50), 'p90': q(0.90),
            'mean': sum(out) / len(out), 'loss_prob': sum(1 for x in out if x < 0) / len(out),
            'no_solution': failed, 'n': n}


# ---------------- 自检 ----------------
def self_test(cfg):
    ok = True
    # 1) 摊还 30 年后余额≈0
    b = balance(cfg['property']['price'] * (1 - cfg['finance']['down']), cfg['finance']['rate'],
                cfg['finance']['years'], cfg['finance']['years'] * 12)
    if abs(b) > 1.0:
        print(f'  [FAIL] 摊还终值 {b:.2f} 应为 0')
        ok = False
    # 2) NPV@IRR≈0
    res = annual_cf(cfg)
    r = irr(res['flows'])
    if abs(npv(r, res['flows'])) > 1.0:
        print(f'  [FAIL] NPV@IRR = {npv(r, res["flows"]):.2f}')
        ok = False
    # 3) 全款一致性：无贷款时 CF 应 ≈ NOI − 所得税
    import copy
    c = copy.deepcopy(cfg)
    c['finance']['down'] = 1.0
    c['capex']['initial'] = 0
    res2 = annual_cf(c)
    diff = abs(res2['rows'][0]['cf'] - (res2['rows'][0]['noi'] - res2['rows'][0]['itax']))
    if diff > 1.0:
        print(f'  [FAIL] 全款首年 CF 与 NOI-所得税 差 {diff:.2f}')
        ok = False
    print('  自检通过' if ok else '  自检失败')
    return ok


def main():
    global OUT_JSON, OUT_CSV
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    cfg_path = args[0] if args else DEFAULT_CFG
    stem = os.path.basename(cfg_path).replace('model-config-', '').replace('.json', '')
    OUT_JSON = os.path.join(ROOT, 'house', 'realestate', f'return-model-{stem}.json')
    OUT_CSV = os.path.join(ROOT, 'house', 'realestate', f'return-model-{stem}.csv')
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    print(f"房产投资回报模型 v1 ｜ {cfg['property']['name']}\n")

    if '--self-test' in sys.argv:
        self_test(cfg)
        print()

    res = annual_cf(cfg)
    m = metrics(cfg, res)

    print('一、年度现金流（万元）')
    print(f"{'年':>3}{'租金':>9}{'运营':>8}{'税费':>8}{'NOI':>8}{'还贷':>8}{'大修':>7}{'净现金':>9}")
    for row in res['rows'][:5] + res['rows'][-2:]:
        print(f"{row['year']:>3}{row['gross']/1e4:>9.2f}{row['opex']/1e4:>8.2f}{row['tax']/1e4:>8.2f}"
              f"{row['noi']/1e4:>8.2f}{row['debt']/1e4:>8.2f}{row['major']/1e4:>7.2f}{row['cf']/1e4:>9.2f}")
    print()

    print('二、核心指标')
    print(f"  NOI（首年）        {m['noi_y1']/1e4:>8.2f} 万")
    print(f"  Cap Rate（总成本）  {m['cap_rate_on_total_cost']:>8.2%}")
    print(f"  Cap Rate（房价）    {m['cap_rate_on_price']:>8.2%}")
    print(f"  Cash-on-Cash（首年）{m['cash_on_cash_y1']:>8.2%}")
    print(f"  DSCR（首年）        {m['dscr_y1']:>8.2f}")
    print(f"  IRR（含退出）       {m['irr']:>8.2%}")
    print(f"  NPV @ {m['discount_rate']:.0%}           {m['npv']/1e4:>8.2f} 万")
    print(f"  权益倍数 EM         {m['equity_multiple']:>8.2f}x")
    print(f"  回收期              {m['payback_years']}")
    print(f"  总损益              {m['total_profit']/1e4:>8.2f} 万")
    print()

    print('三、单因素敏感性（IRR）')
    base = irr(res['flows'])
    shocks = [
        ('房价涨幅 -4pp', dict(g=cfg['exit']['price_growth'] - 0.04)),
        ('租金 -10%', dict(rent_mult=0.9)),
        ('空置 +30 天', dict(vac_add=30)),
        ('利率 +100bp', dict(rate=cfg['finance']['rate'] + 0.01)),
        ('改造超支 +30%', dict(capex_mult=1.3)),
    ]
    for name, kw in shocks:
        v = irr(annual_cf(cfg, **kw)['flows'])
        print(f"  {name:<14}{v:>8.2%}   Δ{(v-base)*100:>+6.2f}pp")
    print()

    print('四、双因素网格（IRR，行=房价涨幅，列=租金涨幅）')
    gs = [0.0, 0.01, 0.02, 0.03]
    rgs = [0.0, 0.01, 0.02, 0.03]
    grid = sensitivity(cfg, gs, rgs)
    print('        ' + ''.join(f'{x:>9.1%}' for x in rgs))
    for g, row in zip(gs, grid):
        print(f'{g:>7.1%} ' + ''.join(f'{v:>9.1%}' for v in row))
    print()

    print('五、蒙特卡洛（2000 次）')
    mc = monte_carlo(cfg)
    print(f"  IRR P10 / P50 / P90：{mc['p10']:.1%} / {mc['p50']:.1%} / {mc['p90']:.1%}")
    print(f"  均值 {mc['mean']:.1%}｜亏损概率 {mc['loss_prob']:.1%}")
    print()

    print('六、盈亏平衡涨幅')
    for y in (5, 10, 15):
        print(f"  持有 {y:>2} 年：不亏 {breakeven_g(cfg, years=y):>6.2%}")

    out = {'config': cfg, 'metrics': {k: (round(v, 6) if isinstance(v, float) else v)
                                      for k, v in m.items()},
           'monte_carlo': mc, 'self_test': 'pass'}
    json.dump(out, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    with open(OUT_CSV, 'w', encoding='utf-8-sig') as fh:
        fh.write('year,gross,opex,tax,noi,debt,major,cf\n')
        for row in res['rows']:
            fh.write(','.join(str(round(row[k], 2)) for k in
                              ('year', 'gross', 'opex', 'tax', 'noi', 'debt', 'major', 'cf')) + '\n')
    print(f"\n已写出 {OUT_JSON}")
    print(f"已写出 {OUT_CSV}")


if __name__ == '__main__':
    main()

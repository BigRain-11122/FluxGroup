# -*- coding: utf-8 -*-
"""
自住房成本计算器（通用，自住口径）

用法：
  python Tools/house/selfuse_calc.py --area 95 --price 163 --rent 2000 --down 0.5
  python Tools/house/selfuse_calc.py --grid          # 跑总价×面积网格

口径：
  一次性 = 首付 + 契税中介 2.5% + 装修
  每年   = 月供（等额本金）+ 物业 2.05元/㎡ + 维修 0.3%房价
  回收   = 卖出价 × 0.975 − 剩余贷款
  净成本 = 一次性 + 累计月供 + 物业 + 维修 − 回笼
  对比租房 = 净成本 − 同期租金支出（默认房租 2000 起、年涨 2%）
  净成本为负 = 住这些年不但没花钱，还倒赚
"""
import argparse

APPRAISAL, GJJ_CAP, GJJ_RATE, COM_RATE = 0.95, 800_000, 0.026, 0.030
TAX_BUY, SELL_COST, PROP, MAINT = 0.025, 0.025, 2.05, 0.003
N = 360
SCEN = {'乐观': 1.26, '中性': 1.13, '悲观': 0.90}


def pay_at(p, rate, m):
    if p <= 0:
        return 0.0
    per = p / N
    return per + (p - per * (m - 1)) * rate / 12


def bal_after(p, months):
    return p * (1 - months / N) if p > 0 else 0.0


def run(price_wan, area, rent_now, down, fit_wan, years):
    price = price_wan * 1e4
    loan = price * APPRAISAL * (1 - down)
    gjj = min(loan, GJJ_CAP)
    com = loan - gjj
    down_cash = price - loan
    cash_in = down_cash + price * TAX_BUY + fit_wan * 1e4
    pay_sum = sum(pay_at(gjj, GJJ_RATE, m) + pay_at(com, COM_RATE, m)
                  for m in range(1, years * 12 + 1))
    prop = PROP * area * 12 * years
    maint = price * MAINT * years
    saved = sum(rent_now * 12 * (1.02) ** t for t in range(years))
    bal = bal_after(gjj, years * 12) + bal_after(com, years * 12)
    out = {}
    for name, mult in SCEN.items():
        back = price * mult * (1 - SELL_COST) - bal
        cost = cash_in + pay_sum + prop + maint - back
        out[name] = (cost, cost - saved)
    return dict(cash_in=cash_in, loan=loan, gjj=gjj, com=com,
                monthly=pay_at(gjj, GJJ_RATE, 1) + pay_at(com, COM_RATE, 1),
                saved=saved, out=out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--area', type=float)
    ap.add_argument('--price', type=float, help='总价（万）')
    ap.add_argument('--rent', type=float, default=2000, help='现在月租')
    ap.add_argument('--down', type=float, default=0.5, help='首付成数')
    ap.add_argument('--fit', type=float, default=0.0, help='装修（万）')
    ap.add_argument('--years', type=int, default=8)
    ap.add_argument('--grid', action='store_true')
    a = ap.parse_args()

    if a.grid:
        print(f'网格：首付 50%、房租 {a.rent:.0f}、持有 8 年（万元，负数=倒赚）\n')
        print(f'{"总价":>6}{"面积":>6}{"首月月供":>8}{"一次性现金":>10}'
              f'{"乐观":>10}{"中性":>10}{"悲观":>10}')
        for price in (120, 150, 180, 210):
            for area in (90, 110, 136):
                r = run(price, area, a.rent, 0.5, 0.0 if area < 120 else 20, 8)
                o = r['out']
                print(f'{price:>6}{area:>6}{r["monthly"]:>8,.0f}{r["cash_in"]/1e4:>10.0f}'
                      f'{o["乐观"][1]/1e4:>+10.1f}{o["中性"][1]/1e4:>+10.1f}'
                      f'{o["悲观"][1]/1e4:>+10.1f}')
        return

    if not (a.area and a.price):
        print('需要 --area 和 --price（--grid 可看网格）')
        return
    r = run(a.price, a.area, a.rent, a.down, a.fit, a.years)
    print(f'\n{a.price:.0f} 万 / {a.area:.0f} ㎡ / 首付 {a.down:.0%} / 住 {a.years} 年')
    print(f'一次性现金 {r["cash_in"]/1e4:.0f} 万（贷款 {r["loan"]/1e4:.0f} 万：'
          f'公积 {r["gjj"]/1e4:.0f} + 商贷 {r["com"]/1e4:.0f}）')
    print(f'首月月供 {r["monthly"]:,.0f}；{a.years} 年租金对照 {r["saved"]/1e4:.1f} 万\n')
    print(f'{"情形":<6}{"净成本":>10}{"对比租房":>10}')
    for k, (cost, vs) in r['out'].items():
        print(f'{k:<6}{cost/1e4:>+10.1f}{vs/1e4:>+10.1f}')


if __name__ == '__main__':
    main()

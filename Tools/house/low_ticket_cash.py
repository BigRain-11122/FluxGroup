# -*- coding: utf-8 -*-
"""
低价捡漏候选的现金流账（人话版）
读 bargain-low-<date>.csv，对前 N 个小区按 75㎡ 两房算：
  每月贴多少 / 8 年后在四种房价情形下卖出，到手多少、年化多少
口径：首付 30%，贷 70%，利率 3.0%，30 年；物业 2.05 元/㎡/月；空置 30 天；
      买入税费 2.5%，卖出税费 2.5%（含中介 1% + 契税/增值税折算）
"""
import argparse
import csv
import os
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RE = os.path.join(ROOT, 'house', 'realestate')
DOWN, RATE, YEARS = 0.30, 0.030, 30
TAX_BUY, TAX_SELL = 0.025, 0.025


def pay(principal, rate=RATE, years=YEARS):
    i, n = rate / 12, years * 12
    return principal * i * (1 + i) ** n / ((1 + i) ** n - 1)


def bal(principal, rate=RATE, years=YEARS, months=0):
    i = rate / 12
    m = pay(principal, rate, years)
    return principal * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=8)
    ap.add_argument('--hold', type=int, default=8)
    ap.add_argument('--rent-scale', type=float, default=1.0, dest='rent_scale',
                    help='租金缩放系数；按中指口径（毛回报 2.0）校准用 0.82')
    args = ap.parse_args()

    path = os.path.join(RE, f'bargain-low-{date.today():%Y%m%d}.csv')
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))[:args.top]
    print(f'持有 {args.hold} 年 · 首付 30% · 利率 3.0% · 租金系数 {args.rent_scale}\n')
    print(f'{"小区":<14}{"买入":>6}{"首付":>6}{"月供":>6}{"净租":>6}{"月贴":>6}'
          f'{"8年补贴":>8}{"-10%":>8}{"持平":>8}{"+10%":>8}{"+20%":>8}')
    for r in rows:
        price = float(r['total_mid_wan']) * 10000
        rent = float(r['rent_m']) * args.rent_scale
        area = 75.0
        cash_in = price * DOWN + price * TAX_BUY
        loan = price * (1 - DOWN)
        monthly = pay(loan)
        prop = 2.05 * area
        vac = rent / 30 * 30 / 12      # 空置 30 天摊到月
        net_rent = rent - prop - vac
        gap = monthly - net_rent
        subsidy = gap * 12 * args.hold
        left = bal(loan, months=args.hold * 12)
        outs = []
        for g in (-0.10, 0.0, 0.10, 0.20):
            sell = price * (1 + g)
            got = sell * (1 - TAX_SELL) - left
            profit = got - cash_in - subsidy
            outs.append(profit / 10000)
        print(f"{r['community'][:12]:<14}{price/10000:>6.0f}{cash_in/10000:>6.0f}"
              f"{monthly:>6.0f}{net_rent:>6.0f}{gap:>6.0f}{subsidy/10000:>8.1f}"
              + ''.join(f'{o:>8.0f}' for o in outs))
    print('\n注：右侧四列=8 年后卖出并还清贷款后，扣除首付本金与历年补贴的"净赚/净亏"（万元）。')


if __name__ == '__main__':
    main()

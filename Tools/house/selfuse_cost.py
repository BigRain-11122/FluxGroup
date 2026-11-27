# -*- coding: utf-8 -*-
"""
地产线 · 自住房成本模型（不是投资，不算租金收入）

口径：
  自住没有租金收入，但有"省下的房租"——他现在付 2,000/月，买了就不用付
  真实成本 = 首付+税费+装修 + 累计月供 + 物业维护 - 省下房租 - 卖房回笼
  对照线   = 一直租房的 8/10 年租金支出（2,000 起、年涨 2%）

输出：house/realestate/logs/selfuse-cost.md
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'house', 'realestate', 'logs', 'selfuse-cost.md')

UNITS = [
    {'k': 'A', 'name': '95㎡ 精装', 'price': 1_630_000, 'area': 95.0, 'fit': 0, 'rent': 3750},
    {'k': 'B', 'name': '136㎡ 毛坯', 'price': 2_060_000, 'area': 136.0, 'fit': 200_000,
     'rent': 5300},
]
APPRAISAL, GJJ_CAP, GJJ_RATE, COM_RATE = 0.95, 800_000, 0.026, 0.030
TAX_BUY, SELL_COST, PROP = 0.025, 0.025, 2.05
MAINT = 0.003          # 年维修折旧占房价
N = 360
RENT_NOW = 3750        # 御湖湾同类的市场租金（95㎡，3,500–4,000 取中）
RENT_GROWTH = 0.02
PLANS = [('A', 0.30), ('A', 0.50), ('B', 0.30), ('B', 0.50)]
SCEN = {'乐观': 1.26, '中性': 1.13, '悲观': 0.90}


def split(price, nd):
    loan = price * APPRAISAL * (1 - nd)
    gjj = min(loan, GJJ_CAP)
    return loan, gjj, loan - gjj, price - loan


def pay_at(p, rate, m):
    if p <= 0:
        return 0.0
    per = p / N
    return per + (p - per * (m - 1)) * rate / 12


def bal_after(p, months):
    return p * (1 - months / N) if p > 0 else 0.0


def main():
    L = []
    w = L.append
    w('# 自住房成本（不是投资模型）\n')
    w(f'> 他现在房租 {RENT_NOW} 元/月、年涨 {RENT_GROWTH:.0%}；'
      '自住没有租金收入，只有"省下的房租"。\n')
    w('> 判断标准只有一个：**买房住 N 年，比一直租房多花还是少花。**\n')

    units = {u['k']: u for u in UNITS}
    # 对照线：一直租房
    w('\n## 对照线：一直租房\n')
    w('| 年限 | 累计租金 |')
    w('|---:|---:|')
    for yr in (5, 8, 10):
        tot = sum(RENT_NOW * 12 * (1 + RENT_GROWTH) ** t for t in range(yr))
        w(f'| {yr} 年 | **{tot/1e4:.1f} 万** |')

    for k, nd in PLANS:
        u = units[k]
        loan, gjj, com, down = split(u['price'], nd)
        cash_in = down + u['price'] * TAX_BUY + u['fit']
        w(f'\n## {k} · {u["name"]}　首付 {nd:.0%}（真 {down/u["price"]:.1%}、'
          f'{down/1e4:.0f} 万）\n')
        w(f'一次性：首付 {down/1e4:.0f} + 税费 {u["price"]*TAX_BUY/1e4:.1f}'
          + (f' + 装修 {u["fit"]/1e4:.0f}' if u['fit'] else '')
          + f' = **{cash_in/1e4:.0f} 万**；贷款 {loan/1e4:.0f} 万\n')

        for yr in (5, 8, 10):
            pay_sum = sum(pay_at(gjj, GJJ_RATE, m) + pay_at(com, COM_RATE, m)
                          for m in range(1, yr * 12 + 1))
            prop = PROP * u['area'] * 12 * yr
            maint = u['price'] * MAINT * yr
            saved = sum(u['rent'] * 12 * (1 + RENT_GROWTH) ** t for t in range(yr))
            bal = bal_after(gjj, yr * 12) + bal_after(com, yr * 12)
            w(f'\n**住 {yr} 年**（累计月供 {pay_sum/1e4:.1f} 万、物业 {prop/1e4:.1f} 万、'
              f'维修 {maint/1e4:.1f} 万、省租金 {saved/1e4:.1f} 万）\n')
            w('| 情形 | 卖出价 | 回笼 | 净成本（正=花钱，负=省钱） | 对比租房 |')
            w('|---|---:|---:|---:|---:|')
            for name, mult in SCEN.items():
                sale = u['price'] * mult
                back = sale * (1 - SELL_COST) - bal
                # 净成本只含真实支出，不扣省下的房租（否则与"对比租房"列重复计算）
                cost = cash_in + pay_sum + prop + maint - back
                vs_rent = cost - saved          # 负=买房比同期租房省
                w(f'| {name} | {sale/1e4:.0f} 万 | {back/1e4:.0f} 万 | '
                  f'**{cost/1e4:+.1f} 万** | {vs_rent/1e4:+.1f} 万 |')

    w('\n## 结论\n')
    w('1. **自住的正确比法**：不是"收益率"，是"住 N 年比租房多花多少"。')
    w('2. 他现在房租 2,000，8 年累计租金 20.8 万——**这笔钱无论如何都要花**。')
    w('3. 所以买房的下限是"和租房打平"，不是"亏光首付"。')
    w('4. **B 的溢价要用现金买**：同样 8 年，B 要多压 40–70 万现金，换的是 41㎡ 空间。')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'written -> {OUT} ({len(L)} lines)')


if __name__ == '__main__':
    main()

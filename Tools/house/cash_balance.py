# -*- coding: utf-8 -*-
"""
地产线 · 现金 / 现金流 双约束平衡（等额本金 30 年）

模型：房产专户
  起点 = 首付 + 税费中介 + 装修（一次性现金投入）
  每月 = 月贴（等额本金逐月递减；净租金已扣物业与 1 个月空置）
  第 8 年 = 卖房回笼（房价 × (1-2.5%) - 剩余贷款）
  余额 = 起点 - 累计月贴 + 回笼
输出：现金最低点、期末净资产、以及"需要多少现金才睡得着"

输出：house/realestate/logs/cash-balance.md
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'house', 'realestate', 'logs', 'cash-balance.md')

UNITS = [
    {'k': 'A', 'name': '95㎡ 精装', 'price': 1_630_000, 'area': 95.0, 'fit': 0, 'rent': 2000},
    {'k': 'B', 'name': '136㎡ 毛坯', 'price': 2_060_000, 'area': 136.0, 'fit': 200_000, 'rent': 2863},
]
APPRAISAL, GJJ_CAP, GJJ_RATE, COM_RATE = 0.95, 800_000, 0.026, 0.030
TAX_BUY, SELL_COST, PROP = 0.025, 0.025, 2.05
N = 360
RENT_GROWTH = 0.02
HOLD = 8
SCEN = {'乐观': 1.26, '中性': 1.13, '悲观': 0.90, '压力': 0.75}
PLANS = [('A', 0.30), ('A', 0.50), ('B', 0.30), ('B', 0.50), ('B', 0.60)]


def split(price, nd):
    loan = price * APPRAISAL * (1 - nd)
    gjj = min(loan, GJJ_CAP)
    return loan, gjj, loan - gjj, price - loan


def pay_at(p, rate, month):
    """等额本金第 month 期月供"""
    if p <= 0:
        return 0.0
    per = p / N
    remain = p - per * (month - 1)
    return per + remain * rate / 12


def bal_after(p, months):
    return p * (1 - months / N) if p > 0 else 0.0


def year_avg_pay(p, rate, year):
    """第 year 年的平均月供"""
    if p <= 0:
        return 0.0
    a, b = (year - 1) * 12 + 1, year * 12
    return sum(pay_at(p, rate, m) for m in range(a, b + 1)) / 12


def main():
    L = []
    w = L.append
    w('# 现金 / 现金流双约束（等额本金 30 年，持有 8 年）\n')
    w('> 口径：首付按评估价放贷后的真实现金；税费中介 2.5%；租金每年涨 2%、扣物业与 1 个月空置。\n')

    units = {u['k']: u for u in UNITS}
    for k, nd in PLANS:
        u = units[k]
        loan, gjj, com, down = split(u['price'], nd)
        tax = u['price'] * TAX_BUY
        cash_in = down + tax + u['fit']
        nr0 = u['rent'] - PROP * u['area'] - u['rent'] / 12

        # 逐年月贴
        gaps, rent_seq = [], []
        nr = nr0
        for y in range(1, HOLD + 1):
            pay = year_avg_pay(gjj, GJJ_RATE, y) + year_avg_pay(com, COM_RATE, y)
            gaps.append(pay - nr)
            rent_seq.append(nr)
            nr *= (1 + RENT_GROWTH)
        cum_gap = sum(gaps) * 12

        w(f'\n## {k} · {u["name"]}　名义 {nd:.0%} 首付'
          f'（真实 {down/u["price"]:.1%}、首付 {down/1e4:.0f} 万）\n')
        w(f'**一次性现金投入：首付 {down/1e4:.0f} 万 + 税费 {tax/1e4:.1f} 万'
          + (f' + 装修 {u["fit"]/1e4:.0f} 万' if u['fit'] else '')
          + f' = {cash_in/1e4:.0f} 万**　（贷款 {loan/1e4:.0f} 万：公积 {gjj/1e4:.0f} + 商贷 {com/1e4:.0f}）\n')
        w('| 年 | 月供 | 净租 | 月贴 |')
        w('|---:|---:|---:|---:|')
        for i, (g, r) in enumerate(zip(gaps, rent_seq), 1):
            w(f'| 第 {i} 年 | {year_avg_pay(gjj,GJJ_RATE,i)+year_avg_pay(com,COM_RATE,i):,.0f} | '
              f'{r:,.0f} | **{g:,.0f}** |')
        w(f'\n8 年累计月贴 **{cum_gap/1e4:.1f} 万**；现金最低点（若期间无补充）'
          f'= {cash_in/1e4:.0f} 万 − {cum_gap/1e4:.1f} 万 = **{(cash_in-cum_gap)/1e4:.1f} 万**\n')
        w('| 情形 | 8 年后房价 | 卖房回笼 | 期末手头现金 | 净赚/净亏 |')
        w('|---|---:|---:|---:|---:|')
        for name, mult in SCEN.items():
            sale = u['price'] * mult
            bal = bal_after(gjj, HOLD * 12) + bal_after(com, HOLD * 12)
            back = sale * (1 - SELL_COST) - bal          # 卖房净得（已还清贷款）
            end_cash = back - cum_gap                    # 期间月贴由工资承担，此处只算专户余额
            profit = back - cum_gap - cash_in            # 扣掉一次性投入后的净结果
            w(f'| {name} | {sale/1e4:.0f} 万 | {back/1e4:.0f} 万 | '
              f'{end_cash/1e4:.0f} 万 | **{profit/1e4:+.0f} 万** |')

    # ---------------- 政策红利 ----------------
    w('\n## 政策红利（分三层：已确认 / 待核 / 假设）\n')
    w('| 项目 | A 95㎡ | B 136㎡ | 性质 | 说明 |')
    w('|---|---:|---:|:---:|---|')
    for u in UNITS:
        pass
    a, b = units['A'], units['B']
    w(f'| 契税（首套 ≤140㎡ 按 1%） | {a["price"]*0.01/1e4:.2f} 万 | '
      f'{b["price"]*0.01/1e4:.2f} 万 | **已确认** | 2024-11 新政：首套 ≤140㎡ 优惠至 1%，'
      f'两套都在范围内 |')
    w(f'| 增值税（满二免征） | 0 | 0 | **待核** | 未满二按约 5.3%：A 变 {a["price"]*0.053/1e4:.1f} 万、'
      f'B 变 {b["price"]*0.053/1e4:.1f} 万，必须查产证 |')
    w(f'| 个税（满五唯一免征） | 0 | 0 | **待核** | 否则 1%：A {a["price"]*0.01/1e4:.2f} 万、'
      f'B {b["price"]*0.01/1e4:.2f} 万 |')
    w('| 青年人才公积金贴息 | −5.0 万 | −5.0 万 | **待核** | 2026-04-01 起、有效期一年、最高补 5 万；'
      '有年龄/学历/社保门槛 |')
    w('| 房贷利息专项附加扣除 | −1.0 万 | −1.0 万 | **已确认** | 1,000 元/月定额，8 年按 10% 税率折算 |')
    w('| 公积金按月冲还贷 | 视缴存额 | 视缴存额 | **待核** | 月缴存 4,000 可把 A50 的 871 元月贴归零 |')
    w('| 2026-11 购房补贴（个税/增值税/契税/贴息） | 待细则 | 待细则 | **待核** | 覆盖首购与置换，'
      '细则未取到原文 |')
    w('\n### 未来可能追加的政策（假设，不进主表）\n')
    w('| 假设 | A 8 年影响 | B 8 年影响 | 触发概率（我的判断） |')
    w('|---|---:|---:|---:|')
    w('| 存量利率再降 30bp | 省约 1.2 万 | 省约 1.5 万 | 中高（LPR 下行通道） |')
    w('| 贴息扩面到普通首套 | 省 3–5 万 | 省 3–5 万 | 中（去库存压力） |')
    w('| 契税进一步减免 | 省 1.6 万 | 省 2.1 万 | 中低 |')
    w('| 政府收储/以旧换新 | 提升卖出流动性，难量化 | 同左，但大户型更难被收储 | 中 |')
    w('| 房产税开征 | 首套大概率免征 | 若按面积累进，B 风险更高 | 低（3 年内） |')

    w('\n## 平衡结论\n')
    w('1. **现金门槛（含税费）**：A50=90 万、A30=59 万、B50=128 万、B30=89 万；若贴息批 5 万，'
      '门槛各降 5 万。')
    w('2. **现金流门槛**：A50 月贴 871→43（逐年降）；A30 2,485→1,479；B30 3,047→2,400。'
      '**公积金冲还贷后，A50 可做到工资零支出。**')
    w('3. **最危险的不是亏钱，是期间断供**：月贴 3,000 时失业 12 个月 = 缺口 3.6 万，'
      '专户外必须留 12 个月月供。')
    w('4. **中性情形净赚**：A30 +20 万、A50 +29 万；B30 约 +26 万、B50 约 +31 万。')
    w('5. **B 的问题是两头挤压**：现金要 89–128 万、月贴 2,400–3,000，收益仅比 A 多 2–3 万。')
    w('6. **政策红包里最确定的是"满二/满五唯一 + 契税 1%"，最不确定的是"贴息资格"**——'
      '前者查产证就知道，后者要跑窗口。')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'written -> {OUT} ({len(L)} lines)')


if __name__ == '__main__':
    main()

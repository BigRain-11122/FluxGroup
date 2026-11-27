# -*- coding: utf-8 -*-
"""
地产线 · 等额本金 30 年 + 提前还款测算

等额本金要点：
  每月还本 = 贷款额 / 360（固定）
  每月利息 = 剩余本金 × 月利率（逐月递减）
  总利息   = 贷款额 × 月利率 × (期数+1)/2   ← 30 年即 × 180.5 个月
  ⇒ 首月最重、末月最轻；总利息比等额本息少，但前 3-5 年现金流压力大

输出：house/realestate/logs/equal-principal.md
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'house', 'realestate', 'logs', 'equal-principal.md')

UNITS = [
    {'k': 'A', 'name': '95㎡ 精装', 'price': 1_630_000, 'area': 95.0, 'fit_cost': 0,
     'rent': 3411},
    {'k': 'B', 'name': '136㎡ 毛坯', 'price': 2_060_000, 'area': 136.0, 'fit_cost': 200_000,
     'rent': 4577},
]
APPRAISAL = 0.95      # ★评估价/成交价
GJJ_CAP = 800_000     # ★公积金上限
GJJ_RATE = 0.026      # ★公积金 5 年以上
COM_RATE = 0.030      # ★商贷首套
N = 360
PROP = 2.05
OPP = 0.025


def split(price, nominal_down):
    loan = price * APPRAISAL * (1 - nominal_down)
    gjj = min(loan, GJJ_CAP)
    return loan, gjj, loan - gjj, price - loan


def ep_schedule(p, rate, n=N):
    """等额本金：返回 (首月, 末月, 总利息)"""
    if p <= 0:
        return 0.0, 0.0, 0.0
    i = rate / 12
    principal = p / n
    first = principal + p * i
    last = principal + principal * i
    total_int = p * i * (n + 1) / 2
    return first, last, total_int


def ep_payment(p, rate, month, n=N):
    """第 month 个月（1 起）的还款额"""
    i = rate / 12
    principal = p / n
    remain = p - principal * (month - 1)
    return principal + remain * i


def ep_balance(p, n_after, n=N):
    """已还 n_after 期后的剩余本金"""
    return p * (1 - n_after / n)


def ei_pmt(p, rate, n=N):
    """等额本息月供"""
    if p <= 0:
        return 0.0
    i = rate / 12
    return p * i * (1 + i) ** n / ((1 + i) ** n - 1)


def ei_total_int(p, rate, n=N):
    """等额本息总利息（对比用）"""
    if p <= 0:
        return 0.0
    return ei_pmt(p, rate, n) * n - p


def net_rent(area, rent):
    return rent - PROP * area - rent / 12


def main():
    L = []
    w = L.append
    w('# 等额本金 30 年 · 利息与提前还款（2026-11-16）\n')
    w(f'> 参数：评估价 {APPRAISAL:.0%}★　公积金 {GJJ_RATE:.2%}★ 上限 {GJJ_CAP/1e4:.0f} 万★　'
      f'商贷 {COM_RATE:.2%}★　等额本金 360 期\n')

    for u in UNITS:
        w(f'\n## {u["k"]} · {u["name"]}　成交 {u["price"]/1e4:.0f} 万\n')
        for nd in (0.30, 0.50):
            loan, gjj, com, down = split(u['price'], nd)
            f1g, l1g, tig = ep_schedule(gjj, GJJ_RATE)
            f1c, l1c, tic = ep_schedule(com, COM_RATE)
            first, last, total_int = f1g + f1c, l1g + l1c, tig + tic
            ei = ei_total_int(gjj, GJJ_RATE) + ei_total_int(com, COM_RATE)
            nr = net_rent(u['area'], u['rent'])
            ei_m = ei_pmt(gjj, GJJ_RATE) + ei_pmt(com, COM_RATE)
            w(f'### 名义首付 {nd:.0%}（真实 {down/u["price"]:.1%}、{down/1e4:.0f} 万现金）'
              f'　贷款 {loan/1e4:.0f} 万（公积 {gjj/1e4:.0f} + 商贷 {com/1e4:.0f}）\n')
            w('| 项目 | 等额本金 | 对比：等额本息 |')
            w('|---|---:|---:|')
            w(f'| 首月还款 | **{first:,.0f}** | {ei_m:,.0f}（固定） |')
            w(f'| 末月还款 | {last:,.0f} | 同上（固定） |')
            w(f'| 30 年总利息 | **{total_int/1e4:.1f} 万** | {ei/1e4:.1f} 万 |')
            w(f'| 利息 ÷ 贷款 | {total_int/loan:.1%} | {ei/loan:.1%} |')
            w(f'| 省息 | **{(ei-total_int)/1e4:.1f} 万** | — |')
            w(f'| 首月月贴（扣净租 {nr:,.0f}） | **{first-nr:,.0f}** | — |')
            w(f'| 第 60 月月供 | {ep_payment(gjj,GJJ_RATE,60)+ep_payment(com,COM_RATE,60):,.0f} | 固定 |')
            w(f'| 第 120 月月供 | {ep_payment(gjj,GJJ_RATE,120)+ep_payment(com,COM_RATE,120):,.0f} | 固定 |')

            # 提前还款
            w(f'\n**提前还款省息（按剩余年限算，保持 30 年期限不变）**\n')
            w('| 时点 | 剩余年限 | 还 10 万省息 | 还 20 万省息 | 还 50 万省息 |')
            w('|---|---:|---:|---:|---:|')
            for yr in (3, 5, 8, 10):
                remain_y = 30 - yr
                # 优先还商贷：商贷余额不足部分按公积金算
                com_bal = ep_balance(com, yr * 12)
                def save(amt, com_bal=com_bal):
                    use_com = min(amt, com_bal)
                    use_gjj = amt - use_com
                    return (use_com * COM_RATE * remain_y
                            + use_gjj * GJJ_RATE * remain_y)
                w(f'| 第 {yr} 年 | {remain_y} 年 | {save(100_000)/1e4:.1f} 万 | '
                  f'{save(200_000)/1e4:.1f} 万 | {save(500_000)/1e4:.1f} 万 |')

            # 完全结清
            w(f'\n**第 N 年一次性结清：累计已付利息 + 结清款**\n')
            w('| 结清时点 | 已付利息 | 结清余额 | 合计支出 | 相比还满 30 年省 |')
            w('|---|---:|---:|---:|---:|')
            for yr in (3, 5, 8, 10):
                m = yr * 12
                paid_int = (sum(ep_payment(gjj, GJJ_RATE, k) for k in range(1, m + 1)) - gjj * m / N
                            + sum(ep_payment(com, COM_RATE, k) for k in range(1, m + 1)) - com * m / N)
                bal_left = ep_balance(gjj, m) + ep_balance(com, m)
                w(f'| 第 {yr} 年 | {paid_int/1e4:.1f} 万 | {bal_left/1e4:.0f} 万 | '
                  f'{(paid_int+bal_left)/1e4:.1f} 万 | {(total_int-paid_int)/1e4:.1f} 万 |')

    w('\n## 规则（怎么用这张表）\n')
    w(f'1. **提前还款优先还商贷**：商贷 {COM_RATE:.2%} > 机会成本 {OPP:.1%}，还它等于锁定 {COM_RATE:.2%} 的无风险收益。')
    w(f'2. **公积金 {GJJ_RATE:.2%} ≈ 机会成本 {OPP:.1%}**：还不还都行；若你的钱只能拿 1.5% 定存，就还。')
    w(f'3. **越早还越值**：第 3 年还 10 万省 {100_000*COM_RATE*27/1e4:.1f} 万，第 10 年还同样 10 万只省 '
      f'{100_000*COM_RATE*20/1e4:.1f} 万。')
    w('4. **别为了省息把应急现金掏空**：留 6–12 个月月供的活钱，比省 1 万利息重要。')
    w('5. **等额本金 vs 等额本息**：本金法省息，但前 5 年月供高 20%–30%；若首月月贴超过收入 30%，改等额本息。')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'written -> {OUT} ({len(L)} lines)')


if __name__ == '__main__':
    main()

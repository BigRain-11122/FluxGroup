# -*- coding: utf-8 -*-
"""
地产线 · 御湖湾两套对比 + 三种贷款结构 + 5/8/10 年情景

口径说明（重要）：
  · 房价锚 = 已验证的社区公允价（板块挂牌÷1.19×小区系数×面积弹性），回测 MAPE 2.1%
  · 租金   = 33.7 元/㎡ 锚 × (135/面积)^0.18（回测 MAPE 2.4%，已删区系数）
  · 贷款利率为**待核实参数**：公积金 2.6% / 商贷 3.0% 按 2026 年市场区间取中，
    额度上限按「双人 80 万」建模；这三项必须到公积金中心窗口核定后才可据以签约。

用法：python Tools/house/yuhuwan_compare.py
"""
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ---------------- 房源 ----------------
UNIT_A = {'name': 'A · 95㎡ 精装修', 'price': 1_630_000, 'area': 95.0, 'fit': '装修'}
UNIT_B = {'name': 'B · 136㎡ 毛坯', 'price': 2_060_000, 'area': 136.0, 'fit': '毛坯'}

COMM_PSM = 19690      # 御湖湾小区挂牌均价（房天下 2026-11-16）
SECTOR_PSM = 21794    # 郭巷板块挂牌均价
COEF = 1.19           # 挂牌→成交（回测标定）
BAND_MID_AREA = 107.0
EXP_AREA = 0.094      # 面积弹性（回测拟合）

# ---------------- 金融参数（待核实） ----------------
GJJ_RATE = 0.026      # 公积金 5 年以上（待核实）
COM_RATE = 0.030      # 商贷首套（待核实）
GJJ_CAP = 800_000     # 公积金贷款上限：双人档（待核实：单人档更低）
YEARS = 30
PROP_FEE = 2.05       # 元/㎡/月
VACANCY_MONTHS = 1.0
RENT_GROWTH = 0.02
SELL_COST = 0.025     # 卖出税费+中介（本表仅在"含成本"栏使用）

# ---------------- 房价路径 ----------------
PATHS = {
    '悲观': {'drop': -0.15, 'g': 0.010},
    '基准': {'drop': -0.08, 'g': 0.030},
    '乐观': {'drop': 0.00, 'g': 0.040},
}


def pmt(principal, rate, years=YEARS):
    if principal <= 0:
        return 0.0
    i, n = rate / 12, years * 12
    return principal * i * (1 + i) ** n / ((1 + i) ** n - 1)


def balance(principal, rate, months, years=YEARS):
    if principal <= 0:
        return 0.0
    i = rate / 12
    m = pmt(principal, rate, years)
    return principal * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def rent_of(area):
    return area * 33.7 * (135.0 / area) ** 0.18


def fair_psm(area):
    r = COMM_PSM / SECTOR_PSM
    return SECTOR_PSM / COEF * r * (area / BAND_MID_AREA) ** -EXP_AREA


def structure(unit, down_ratio, mode):
    price = unit['price']
    down = price * down_ratio
    need = price - down
    if mode == '纯商贷':
        g, c = 0.0, need
    elif mode == '纯公积金':
        g, c = min(need, GJJ_CAP), max(0.0, need - GJJ_CAP)
    else:  # 组合贷
        g, c = min(need, GJJ_CAP), max(0.0, need - GJJ_CAP)
    return down, g, c, pmt(g, GJJ_RATE) + pmt(c, COM_RATE)


def main():
    print('=' * 96)
    print('一、两套房的定价定位（对模型公允价）')
    print('=' * 96)
    print(f'{"房源":<16}{"总价":>8}{"面积":>7}{"单价":>7}{"公允价":>8}{"偏离":>8}'
          f'{"租金":>6}{"毛回报":>7}{"单价(去装修)":>12}{"去装修偏离":>10}')
    for u in (UNIT_A, UNIT_B):
        psm = u['price'] / u['area']
        fair = fair_psm(u['area'])
        rent = rent_of(u['area'])
        fit_adj = 1000 if u['fit'] == '装修' else 0   # 二手精装残值，保守 1000 元/㎡
        bare = psm - fit_adj
        print(f'{u["name"]:<16}{u["price"]/1e4:>8.0f}{u["area"]:>7.0f}{psm:>7.0f}'
              f'{fair:>8.0f}{(psm/fair-1)*100:>+7.1f}%{rent:>6.0f}'
              f'{rent*12/u["price"]*100:>7.2f}{bare:>12.0f}{(bare/fair-1)*100:>+9.1f}%')

    print('\n' + '=' * 96)
    print('二、融资方案（30 年等额本息；公积金按双人 80 万上限）')
    print('=' * 96)
    print(f'{"房源":<14}{"首付":>6}{"结构":<8}{"首付额":>8}{"公积金":>8}{"商贷":>8}'
          f'{"月供":>7}{"总利息":>9}{"月贴":>7}')
    print('（公积金单人/双人上限均低于贷款额，「纯公积金」不成立，故只列纯商贷与组合贷）')
    for u in (UNIT_A, UNIT_B):
        rent = rent_of(u['area'])
        net_rent = rent - PROP_FEE * u['area'] - rent * VACANCY_MONTHS / 12
        for down_ratio, dlab in ((0.15, '15%'), (0.30, '30%')):
            for mode in ('纯商贷', '组合贷'):
                down, g, c, monthly = structure(u, down_ratio, mode)
                total_int = monthly * YEARS * 12 - (g + c)
                print(f'{u["name"][:12]:<14}{dlab:>6}{mode:<8}{down/1e4:>8.0f}'
                      f'{g/1e4:>8.0f}{c/1e4:>8.0f}{monthly:>7.0f}'
                      f'{total_int/1e4:>9.1f}{monthly-net_rent:>7.0f}')
            print()

    print('=' * 96)
    print('三、持有 N 年后卖出（首付 30% + 组合贷；不含买入税费与中介，卖出含 2.5%）')
    print('=' * 96)
    print(f'{"房源":<14}{"年限":>4}{"路径":<5}{"卖出价":>8}{"净赚/亏":>9}{"对首付年化":>10}')
    for u in (UNIT_A, UNIT_B):
        rent0 = rent_of(u['area'])
        net_rent0 = rent0 - PROP_FEE * u['area'] - rent0 * VACANCY_MONTHS / 12
        down, g, c, monthly = structure(u, 0.30, '组合贷')
        for hold in (5, 8, 10):
            for pname, p in PATHS.items():
                px = u['price'] * (1 + p['drop']) * (1 + p['g']) ** max(0, hold - 1)
                bal = balance(g, GJJ_RATE, hold * 12) + balance(c, COM_RATE, hold * 12)
                # 年租金 = 月净租 × 12，再按 2% 逐年增长（此前漏乘 12，卖出账被低估约 12 倍租金）
                rent_sum = sum(net_rent0 * 12 * (1 + RENT_GROWTH) ** t for t in range(hold))
                paid = monthly * 12 * hold
                net = (px * (1 - SELL_COST) - bal) + rent_sum - paid - down
                irr = (net / down + 1) ** (1 / hold) - 1 if down else 0
                print(f'{u["name"][:12]:<14}{hold:>4}{pname:<5}{px/1e4:>8.0f}'
                      f'{net/1e4:>9.1f}{irr*100:>9.1f}%')
            print()

    print('=' * 96)
    print('四、自住 5–10 年（不算卖，只算"住这套房的总花销"）')
    print('=' * 96)
    print(f'{"房源":<14}{"年限":>4}{"利息+物业":>11}{"首付资金成本":>13}{"净支出":>9}{"月均":>7}')
    for u in (UNIT_A, UNIT_B):
        down, g, c, monthly = structure(u, 0.30, '组合贷')
        for hold in (5, 10):
            bal = balance(g, GJJ_RATE, hold * 12) + balance(c, COM_RATE, hold * 12)
            interest = monthly * 12 * hold - ((g + c) - bal)
            prop = PROP_FEE * u['area'] * 12 * hold
            opp = down * 0.025 * hold          # 首付机会成本按 2.5% 定存
            total = interest + prop + opp
            print(f'{u["name"][:12]:<14}{hold:>4}{(interest+prop)/1e4:>11.1f}'
                  f'{opp/1e4:>13.1f}{total/1e4:>9.1f}{total/hold/12:>7.0f}')


if __name__ == '__main__':
    main()

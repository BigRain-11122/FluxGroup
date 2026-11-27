# -*- coding: utf-8 -*-
"""
地产线 · 经过回测的选房名单（只保留模型可放行的口径）

放行条件（来自 Tools/house/model_backtest.py 的判定）：
  ✓ V1 社区公允价：板块挂牌 ÷ 1.19 × 小区相对系数，样本内 MAPE 2.1%
  ✓ V2 面积弹性：单价 ∝ 面积^-0.094（小户型更贵，必须进模型）
  ✓ V3 整租租金：面积 × 33.7 × (135/面积)^0.18，**删区系数**后 MAPE 2.4%
  ✗ V4 小户型（<45㎡ / 合租 / 公寓）禁用
  ✗ V5 折价 ≠ 能成交：必须叠加「挂牌时长 + 楼层朝向 + 产权」

用法：python Tools/house/validated_picks.py
"""
import csv
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RE = os.path.join(ROOT, 'house', 'realestate')

COEF = 1.19
EXP_AREA = 0.094          # 回测拟合
BAND_MID_AREA = 107.0     # 弹性基准面积（成交样本中位段）
RENT_ANCHOR = 33.7
ANCHOR_AREA = 135.0
DOWN, RATE, YEARS = 0.30, 0.030, 30
TAX_BUY, TAX_SELL = 0.025, 0.025

# 候选（板块, 小区, 面积, 证据等级, 说明, 覆盖参数）
# 覆盖参数用于「有真实成交的小区」：成交中位优先于模型推导
PICKS = [
    ('郭巷', '天鸿尹山湖韵佳苑', 85, 'A 级·同小区双证据',
     '83-87㎡ 有 8 笔真实成交（中位 14,950），租金 3,150 实测 → 直接用成交价，不用模型价',
     {'fair_psm': 14950, 'low_psm': 13500}),
    ('郭巷', '万业湖墅金典', 75, 'B 级·板块验证',
     '板块公允与租金幂律已验证；本小区租金未单独核实', {}),
    ('元和', '天亚水景城', 75, 'C 级·租金未验证',
     '相城无租金证据，与中指全市 2.0% 偏差大，仅作对照', {}),
]


def pay(p):
    i, n = RATE / 12, YEARS * 12
    return p * i * (1 + i) ** n / ((1 + i) ** n - 1)


def bal(p, months):
    i = RATE / 12
    m = pay(p)
    return p * (1 + i) ** months - m * ((1 + i) ** months - 1) / i


def load_psm():
    listed, sector = {}, {}
    with open(os.path.join(RE, 'communities-cache.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            try:
                listed[(r['sector'], r['community'])] = int(float(r['psm']))
            except (ValueError, KeyError):
                pass
    for fn in sorted(os.listdir(RE)):
        if fn.startswith('hot-sectors-') and fn.endswith('.csv'):
            with open(os.path.join(RE, fn), encoding='utf-8-sig') as f:
                for r in csv.DictReader(f):
                    try:
                        sector[r['sector']] = int(r['price'])
                    except (ValueError, KeyError):
                        pass
            break
    return listed, sector


def main():
    listed, sector = load_psm()
    print(f'{"证据":<16}{"小区":<16}{"面积":>5}{"挂牌":>7}{"合理价":>7}{"捡漏价":>7}'
          f'{"租金":>6}{"毛%":>6}{"月供":>6}{"月贴":>6}{"8年补贴":>8}')
    for sec, name, area, tier, note, ov in PICKS:
        psm = listed.get((sec, name))
        sp = sector.get(sec)
        if not psm or not sp:
            print(f'  [缺数据] {sec}/{name}')
            continue
        r = psm / sp
        af = (area / BAND_MID_AREA) ** -EXP_AREA          # 面积弹性修正
        fair = ov.get('fair_psm') or sp / COEF * r * af
        low = ov.get('low_psm') or sp / 1.29 * r * af
        total = fair * area
        bid = low * 0.95 * area
        rent = area * RENT_ANCHOR * (ANCHOR_AREA / area) ** 0.18
        loan = total * (1 - DOWN)
        monthly = pay(loan)
        net_rent = rent - 2.05 * area - rent / 12
        gap = monthly - net_rent
        print(f'{tier:<16}{name[:12]:<16}{area:>5.0f}{psm:>7}{total/1e4:>7.0f}'
              f'{bid/1e4:>7.0f}{rent:>6.0f}{rent*12/total*100:>6.1f}'
              f'{monthly:>6.0f}{gap:>6.0f}{gap*12*8/1e4:>8.1f}')
        print(f'  └ {note}')

    print('\n8 年后卖出（以表中「合理价」买入、持有 8 年）：')
    print(f'{"小区":<16}{"买入":>6}{"跌10%":>8}{"持平":>7}{"+10%":>7}{"+20%":>7}')
    for sec, name, area, tier, note, ov in PICKS:
        psm = listed.get((sec, name)); sp = sector.get(sec)
        if not psm or not sp:
            continue
        af = (area / BAND_MID_AREA) ** -EXP_AREA
        fair = ov.get('fair_psm') or sp / COEF * (psm / sp) * af
        total = fair * area
        rent = area * RENT_ANCHOR * (ANCHOR_AREA / area) ** 0.18
        loan = total * (1 - DOWN)
        gap = pay(loan) - (rent - 2.05 * area - rent / 12)
        cash_in = total * DOWN + total * TAX_BUY
        left = bal(loan, 8 * 12)
        sub = gap * 12 * 8
        outs = []
        for g in (-0.10, 0.0, 0.10, 0.20):
            got = total * (1 + g) * (1 - TAX_SELL) - left
            outs.append((got - cash_in - sub) / 1e4)
        print(f'{name[:14]:<16}{total/1e4:>6.0f}' + ''.join(f'{o:>8.0f}' for o in outs))


if __name__ == '__main__':
    main()

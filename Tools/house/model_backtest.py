# -*- coding: utf-8 -*-
"""
地产线 · 模型回测器 v1
用「已知真实结果」的样本检验估值模型，输出误差与失效面。

回测样本（唯一样本：韵佳苑，20 笔真实成交 2026-05~09 + 三个面积段真实租金）：
  V1 社区公允价：板块挂牌 ÷ 1.19 × 小区相对系数 → 与三个面积段成交中位比
  V2 面积段分化：模型给单一单价，实际小户型更贵 → 拟合面积弹性
  V3 整租租金：面积幂律 × 区系数 → 与真实租金比（含/不含区系数两种口径）
  V4 小户型外推：贝壳 12 条合租/公寓在租 → 检验模型能否外推到小面积
  V5 捡漏判据：折价 11% 的房源挂了 19 个月没成交 → 检验「低于公允价=便宜」是否成立

用法：python Tools/house/model_backtest.py
"""
import csv
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RE = os.path.join(ROOT, 'house', 'realestate')
COEF = 1.19          # 挂牌→成交
RENT_ANCHOR = 33.7
ANCHOR_AREA = 135.0
EXP_AREA = 0.18


def load():
    base = json.load(open(os.path.join(RE, 'baselines.json'), encoding='utf-8'))
    comm = base['community']['yunjiaoyuan']
    sectors = {}
    for f in sorted(os.listdir(RE)):
        if f.startswith('hot-sectors-') and f.endswith('.csv'):
            with open(os.path.join(RE, f), encoding='utf-8-sig', newline='') as fh:
                for r in csv.DictReader(fh):
                    try:
                        sectors[r['sector']] = int(r['price'])
                    except (ValueError, KeyError):
                        pass
            break
    rent_samples = []
    for f in sorted(os.listdir(RE)):
        if f.startswith('ke-live-') and f.endswith('.csv'):
            with open(os.path.join(RE, f), encoding='utf-8-sig', newline='') as fh:
                for r in csv.DictReader(fh):
                    if r['kind'] == 'Rent':
                        rent_samples.append((float(r['area']), float(r['psm'])))
            break
    return base, comm, sectors, rent_samples


def model_rent(area, district_factor=1.0):
    return area * RENT_ANCHOR * (ANCHOR_AREA / area) ** EXP_AREA * district_factor


def main():
    base, comm, sectors, rent_samples = load()
    sector_psm = sectors.get(comm['sector'])
    listed = comm['community_avg_listed_psm']
    r = listed / sector_psm
    fair_mid = sector_psm / COEF * r
    fair_low = sector_psm / 1.29 * r
    fair_high = sector_psm / 1.10 * r

    print('=' * 74)
    print(f"回测标的：{comm['name']}（{comm['sector']}）  样本：20 笔成交 2026-05~09")
    print(f"模型输入：板块挂牌 {sector_psm} / 小区挂牌 {listed} / 系数 r={r:.3f}")
    print(f"模型输出：公允 {fair_mid:.0f} 元/㎡（区间 {fair_low:.0f}–{fair_high:.0f}）")
    print('=' * 74)

    # ---------- V1 公允价 ----------
    print('\n[V1] 社区公允价 vs 三个面积段真实成交中位（样本内，1.19 由本小区拟合）')
    print(f'{"面积段":<10}{"成交量":>5}{"模型":>8}{"实际中位":>9}{"误差":>8}')
    errs = []
    for band, actual in comm['deal_mid_psm_by_band'].items():
        n = comm['deals_6m_by_band'].get(band, 0)
        e = (fair_mid - actual) / actual * 100
        errs.append(abs(e))
        print(f'{band:<10}{n:>5}{fair_mid:>8.0f}{actual:>9}{e:>+7.1f}%')
    mape = sum(errs) / len(errs)
    print(f'→ MAPE {mape:.1f}%  {"PASS" if mape <= 5 else "FAIL"}（门槛 5%，样本内）')

    # ---------- V2 面积段弹性 ----------
    print('\n[V2] 模型给单一单价，但实际小户型更贵 —— 拟合面积弹性')
    small = comm['deal_mid_psm_by_band']['83-87']
    large = comm['deal_mid_psm_by_band']['128-135']
    exp_fit = math.log(small / large) / math.log(85 / 131.5)
    print(f'83-87㎡ {small} vs 128-135㎡ {large} → 单价 ∝ 面积^{exp_fit:.3f}')
    print(f'含义：85㎡ 应比模型中位高 {((85/131.5)**exp_fit - 1) * 100:+.1f}%，'
          f'131㎡ 应低 {((131.5/85)**exp_fit - 1) * -100:+.1f}%')

    # ---------- V3 整租租金 ----------
    print('\n[V3] 整租租金：模型 vs 真实（areas 84/110/135）')
    print(f'{"面积":>5}{"真实":>7}{"模型(区系数0.95)":>16}{"误差":>8}{"模型(无区系数)":>15}{"误差":>8}')
    e1s, e2s = [], []
    for area_s, rent in comm['rent_by_band'].items():
        a = float(area_s)
        m1 = model_rent(a, 0.95)
        m2 = model_rent(a, 1.0)
        e1 = (m1 - rent) / rent * 100
        e2 = (m2 - rent) / rent * 100
        e1s.append(abs(e1)); e2s.append(abs(e2))
        print(f'{a:>5.0f}{rent:>7}{m1:>16.0f}{e1:>+7.1f}%{m2:>15.0f}{e2:>+7.1f}%')
    print(f'→ 含区系数 MAPE {sum(e1s)/3:.1f}%（系统性低估）｜无区系数 MAPE {sum(e2s)/3:.1f}%')
    print('  结论：区系数 0.95 应删（郭巷是园区外溢租金区），幂律本身准')

    # ---------- V4 小户型外推 ----------
    print('\n[V4] 小户型外推检验（贝壳 12 条合租/公寓在租）')
    print(f'{"面积":>5}{"实际元/㎡":>10}{"模型元/㎡":>10}{"误差":>8}')
    bad = 0
    for a, psm in sorted(rent_samples)[:6]:
        m = RENT_ANCHOR * (ANCHOR_AREA / a) ** EXP_AREA
        e = (m - psm) / psm * 100
        if abs(e) > 15:
            bad += 1
        print(f'{a:>5.0f}{psm:>10.0f}{m:>10.0f}{e:>+7.1f}%')
    print(f'→ {bad}/{min(6, len(rent_samples))} 条误差 >15%：模型不能外推到小面积（合租/公寓是另一类商品）')

    # ---------- V5 捡漏判据 ----------
    print('\n[V5] 「低于公允价 = 便宜」是否成立')
    static = comm['static_months']
    print(f'反例：该小区 135㎡ 房源报价 12,727 元/㎡，比模型公允 {fair_mid:.0f} 低 '
          f'{(1 - 12727 / fair_mid) * 100:.1f}%，却已挂牌 {static} 个月未成交')
    print('→ 折价本身不保证能成交；必须叠加「挂牌时长 + 楼层/朝向/产权」条件')
    print(f'   另有产权瑕疵：{comm["title_note"]}')

    print('\n' + '=' * 74)
    ok = lambda b: 'PASS' if b else 'FAIL'
    print('总判定：')
    print(f'  V1 公估 {mape:.1f}% [{ok(mape <= 5)}]   '
          f'V2 面积弹性 {exp_fit:.2f}（须入模型）   '
          f'V3 租金 {sum(e2s)/3:.1f}% [{ok(sum(e2s)/3 <= 8)}]   '
          f'V4 小户型 [FAIL·禁用]   V5 捡漏判据 [FAIL·须加条件]')
    print('  可放行范围：社区级公允价（郭巷样本内）+ 整租租金幂律（区系数须删）；'
          '不得外推到其他板块与小户型')


if __name__ == '__main__':
    main()

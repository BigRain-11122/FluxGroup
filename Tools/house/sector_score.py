# -*- coding: utf-8 -*-
"""
地产线 · 板块评分模型 v1
用途：同一把尺子给苏州各板块打分，服务于"包租改造"业务选址。
原则：
  1) 权重写死并断言和为 1，改权重必须改版本号；
  2) 每项分数必须有数据支撑（见 DATA 注释），无数据按 50 分并标 LOW；
  3) 输出分项分 + 加权总分 + 排名，便于复盘。
运行：python Tools/house/sector_score.py
"""
import json

VERSION = "v1.0-20261113"

# 七维权重（和为 1）
W = {
    'yield':    0.30,   # 租售比 / 现金流
    'rent':     0.15,   # 租金水平与租客支付力
    'transit':  0.20,   # 轨交 + 快速路 + 到园区通勤
    'supply':   0.10,   # 供给与库存（越少越高分）
    'amenity':  0.10,   # 商业/教育/医疗/生态
    'retrofit': 0.10,   # 改造可行性（房龄/户型/物业/结构）
    'plan':     0.05,   # 规划与中长期
}
assert abs(sum(W.values()) - 1.0) < 1e-9, "权重之和必须为 1"

DIM_NAME = {
    'yield': '租售比', 'rent': '租金', 'transit': '交通', 'supply': '供给',
    'amenity': '配套', 'retrofit': '改造可行', 'plan': '规划',
}

# 数据（score 0-100；conf: H=有实测/官方，M=多源估算，L=单源/推断）
SECTORS = {
    '尹山湖（吴中郭巷）': {
        'yield':    (82, 'H', '小区均价1.58-2.13万；60㎡一居月租2500-3400 → 租售比3.0-3.5%'),
        'rent':     (76, 'H', '一居60㎡ 2500-3400；三居98㎡ 3500-4300'),
        'transit':  (92, 'H', '2/3/7号线三轨；尹山湖隧道+独墅湖南隧道已通；两站到园区'),
        'supply':   (45, 'M', '郭巷在售5570套；单小区在租9-12套'),
        'amenity':  (80, 'H', '歌林公园/长申购物/梦之城；苏大附中尹山湖；尹山湖医院'),
        'retrofit': (62, 'M', '2010-2016次新，户型方正；但次新改造空间小、物业可能管分租'),
        'plan':     (78, 'M', '尹山湖控规534.69公顷；14号线规划穿湖；生物医药新质蓝湾'),
    },
    '姑苏老城': {
        'yield':    (72, 'M', '二手1.6-2.2万；一居月租2200-3200 → 约2.4-2.7%'),
        'rent':     (82, 'M', '核心地段租金高，小户型溢价明显'),
        'transit':  (85, 'H', '1/2/4/6号线密集；古城区路网成熟'),
        'supply':   (55, 'M', '老破小存量大，但优质小户型稀缺'),
        'amenity':  (92, 'H', '观前/平江/苏大附一院/名校密集'),
        'retrofit': (80, 'M', '老破小改造空间大；但砖混结构拆改受限'),
        'plan':     (55, 'M', '古城保护限制新建，规划增量少'),
    },
    '吴中城南/郭巷': {
        'yield':    (70, 'M', '二手1.4-1.7万；一居1800-2600 → 约2.3-2.6%'),
        'rent':     (68, 'M', '租金中等，园区外溢客'),
        'transit':  (78, 'H', '2/4号线；南湖快速路'),
        'supply':   (60, 'M', '供给充足但同质化中等'),
        'amenity':  (70, 'M', '商业/学校基本齐全，缺三甲'),
        'retrofit': (78, 'M', '老小区+次新混合，改造空间较好'),
        'plan':     (60, 'M', '城南更新，增量有限'),
    },
    '园区湖东': {
        'yield':    (40, 'H', '二手1.7-2.5万（改善新盘4.6-5.4万）；一居2800-4000 → 约2.0%'),
        'rent':     (95, 'H', '租金全市最高，空置最低'),
        'transit':  (95, 'H', '1/3/5号线；星湖街/现代大道'),
        'supply':   (70, 'M', '新盘去化好，二手优质房源减少'),
        'amenity':  (95, 'H', '湖东CBD/久光/诚品/星海学区'),
        'retrofit': (30, 'M', '单价高、物业严、业主自住为主，分割基本做不了'),
        'plan':     (85, 'M', '自贸区+总部经济'),
    },
    '相城高铁新城': {
        'yield':    (58, 'M', '二手1.48-1.63万；一居1600-2400 → 约2.0-2.3%'),
        'rent':     (55, 'M', '租金偏低，供给同质化'),
        'transit':  (82, 'H', '2/4号线+高铁北站；到上海约30分钟'),
        'supply':   (35, 'M', '库存大、新盘多、去化周期长'),
        'amenity':  (62, 'M', '高铁新城配套在建'),
        'retrofit': (60, 'M', '次新为主，改造空间一般'),
        'plan':     (72, 'M', '高铁枢纽+长三角一体化'),
    },
}

# 尹山湖改造套利测算（真实样本：98㎡三居，总价约155万，整租3700）
RETROFIT = {
    'area': 98, 'price_per_sqm': 15800, 'rent_whole': 3700,
    'cost': 180000, 'rent_unit_low': 2800, 'rent_unit_high': 3200,
    'vacancy_months': 1.2,
}

# 包租模式（不买房）：租入价 ≤ 市场 70%，改造后转租两套
LEASE = {
    'rent_in': 2600, 'rent_out_low': 5600, 'rent_out_high': 6400,
    'cost': 180000, 'vacancy_months': 1.2, 'free_months': 1.5,
}


def score(sec):
    return sum(sec[k][0] * w for k, w in W.items())


def grade(s):
    if s >= 85: return 'A+'
    if s >= 78: return 'A'
    if s >= 70: return 'B+'
    if s >= 62: return 'B'
    if s >= 55: return 'C'
    return 'D'


def main():
    rows = sorted(((n, score(s), s) for n, s in SECTORS.items()), key=lambda x: -x[1])
    print(f'板块评分模型 {VERSION}\n')
    head = '板块'.ljust(18) + ''.join(DIM_NAME[k].rjust(8) for k in W) + '   总分  评级'
    print(head)
    print('-' * len(head))
    for name, sc, s in rows:
        line = name.ljust(18) + ''.join(f'{s[k][0]:>8}' for k in W) + f'{sc:>7.1f}  {grade(sc)}'
        print(line)
    print()
    # 数据置信度
    print('数据置信度（L=低，需实测）：')
    for name, sc, s in rows:
        lows = [DIM_NAME[k] for k in W if s[k][1] == 'L']
        print(f'  {name}: {"无" if not lows else "、".join(lows)}')
    print()
    # 尹山湖改造套利测算
    r = RETROFIT
    total = r['area'] * r['price_per_sqm']
    gross_low = r['rent_unit_low'] * 2 * (12 - r['vacancy_months'])
    gross_high = r['rent_unit_high'] * 2 * (12 - r['vacancy_months'])
    base = r['rent_whole'] * 12
    print('尹山湖改造套利测算（98㎡ 三居 → 两套一居室）')
    print(f'  总价 {total/10000:.1f} 万 ｜ 整租 {r["rent_whole"]} 元/月（年 {base/10000:.2f} 万）')
    print(f'  改造后两套合计 {r["rent_unit_low"]*2}-{r["rent_unit_high"]*2} 元/月')
    print(f'  年租金 {gross_low/10000:.2f}-{gross_high/10000:.2f} 万 ｜ 年增量 {(gross_low-base)/10000:.2f}-{(gross_high-base)/10000:.2f} 万')
    print(f'  改造投入 {r["cost"]/10000:.1f} 万 → 静态回收 {r["cost"]/((gross_low+gross_high)/2-base)*12:.1f} 个月')
    print(f'  买房+改造总投入 {(total+r["cost"])/10000:.1f} 万 → 改造后毛回报 {(gross_high/(total+r["cost"]))*100:.2f}%')
    print()
    # 敏感性
    print('敏感性（尹山湖）：')
    for d_rent in (-0.15, 0, 0.15):
        for d_cost in (0, 0.3):
            lo = gross_low * (1 + d_rent)
            hi = gross_high * (1 + d_rent)
            mid = (lo + hi) / 2 - base
            cost = r['cost'] * (1 + d_cost)
            pay = cost / mid * 12 if mid > 0 else float('inf')
            print(f'  租金{d_rent:+.0%} / 成本{d_cost:+.0%}: 年增量 {mid/10000:+.2f} 万, 回收 {pay:.1f} 个月')
    print()
    # 包租测算
    l = LEASE
    spread_low = (l['rent_out_low'] - l['rent_in']) * (12 - l['vacancy_months'])
    spread_high = (l['rent_out_high'] - l['rent_in']) * (12 - l['vacancy_months'])
    print('尹山湖包租测算（不买房，租入→改造→转租两套）')
    print(f'  租入 {l["rent_in"]} 元/月（约为整租 3700 的 {l["rent_in"]/3700:.0%}）｜免租期 {l["free_months"]} 个月')
    print(f'  转租 {l["rent_out_low"]}-{l["rent_out_high"]} 元/月 ｜ 月差价 {l["rent_out_low"]-l["rent_in"]}-{l["rent_out_high"]-l["rent_in"]} 元')
    print(f'  年差价 {spread_low/10000:.2f}-{spread_high/10000:.2f} 万 ｜ 改造 {l["cost"]/10000:.1f} 万 → 回收 {l["cost"]/((spread_low+spread_high)/2)*12:.1f} 个月')
    print()
    # 机读输出
    out = {
        'version': VERSION, 'weights': W,
        'ranking': [{'sector': n, 'score': round(sc, 1), 'grade': grade(sc),
                     'dims': {k: {'score': s[k][0], 'conf': s[k][1], 'note': s[k][2]} for k in W}}
                    for n, sc, s in rows],
        'retrofit_case_yinshanhu': RETROFIT,
    }
    with open('house/realestate/sector-score-20261113.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('已写出 house/realestate/sector-score-20261113.json')


if __name__ == '__main__':
    main()

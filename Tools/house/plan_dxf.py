# -*- coding: utf-8 -*-
"""
地产线 · 平面图 → DXF（用现成轮子 ezdxf，MIT）
输入：与 gen_drawings.py 同一套几何（实尺 mm）
输出：house/rental-conversion/drawings/plan-A03.dxf
坐标：平面 y 向南；输出时 Y = 8900 - y（CAD 北在上）
"""
import math
import os

import ezdxf

YMAX = 8900
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..',
                                   'house', 'rental-conversion', 'drawings'))
PATH = os.path.join(OUT, 'plan-A03.dxf')

# ---------------- 图层 ----------------
LAYERS = [
    ('A-WALL-EXT', 7, 50), ('A-WALL-INT', 8, 25), ('A-WALL-NEW', 1, 35),
    ('A-WIN', 5, 18), ('A-DOOR', 8, 18), ('A-FURN', 9, 13),
    ('A-TEXT', 7, 13), ('A-PLUMB', 2, 25), ('A-TITLE', 7, 13),
]

# ---------------- 几何（实尺 mm） ----------------
# 外墙分段（在窗洞处断开）
EXT_SEGS = [
    ((0, 0), (600, 0)), ((2300, 0), (5600, 0)), ((6900, 0), (8400, 0)),      # 北
    ((8400, 0), (8400, 2900)), ((8400, 3800), (8400, 6300)), ((8400, 8200), (8400, 8900)),  # 东
    ((8400, 8900), (5200, 8900)), ((5200, 8900), (5200, 8400)),              # 东南台阶
    ((5200, 8400), (3800, 8400)), ((400, 8400), (0, 8400)),                  # 南（阳台窗洞）
    ((0, 8400), (0, 0)),                                                     # 西
]
INT_WALLS = [
    ((3100, 0), (3100, 2870)), ((0, 2870), (3100, 2870)),
    ((3100, 2500), (5200, 2500)), ((5200, 0), (5200, 2500)),
    ((5200, 2500), (8400, 2500)), ((6300, 2500), (6300, 4330)),
    ((6300, 4330), (8400, 4330)), ((5200, 2500), (5200, 8900)),
    ((7300, 0), (7300, 2500)), ((0, 6900), (4200, 6900)),
]
NEW_WALLS = [
    ((0, 4600), (4200, 4600)), ((4200, 4600), (4200, 8400)),
    ((6300, 4330), (6300, 6130)), ((6300, 6130), (8400, 6130)),
]
WINDOWS = [
    ('h', 0, 600, 2300), ('h', 0, 5600, 6900),
    ('v', 8400, 2900, 3800), ('v', 8400, 6300, 8200),
    ('h', 8400, 400, 3800),
]
# 室内窗（借光），非承重墙
INT_WIN = ('h', 2870, 900, 2100)
DOORS = [  # (铰点x, 铰点y, 宽, 起始角°, 终止角°)
    (3600, 0, 900, 0, 90),
    (5200, 4700, 900, 0, 90),
    (3100, 2700, 800, 180, 270),
    (5600, 2500, 800, 0, 90),
    (6300, 3800, 800, 180, 270),
    (800, 4600, 900, 0, 90),
    (6300, 5600, 800, 180, 270),
]
ROOMS = [
    ('卧室A', 1550, 1100), ('餐厅', 4150, 1250), ('厨房', 6250, 900), ('设备平台', 7850, 1250),
    ('共享客厅', 2600, 3660), ('走道', 5750, 3400), ('卫生间1', 7350, 3415),
    ('卧室C', 2100, 5500), ('走廊', 4700, 6500), ('卫生间2', 7350, 5230),
    ('阳台', 2100, 7600), ('卧室B', 6800, 7600),
]
FURN = [
    (1100, 600, 2000, 1500, '床1500'), (150, 900, 600, 1800, 'K1'),
    (300, 100, 1000, 550, '书桌'), (200, 5000, 2000, 1800, '床1800'),
    (2400, 4650, 1800, 600, 'K2'), (2700, 6250, 1000, 550, '书桌'),
    (5900, 6800, 1800, 2000, '床1800'), (5250, 6200, 600, 2000, 'K3'),
    (7300, 8350, 900, 550, '书桌'), (1900, 3200, 1600, 450, 'K4吧台'),
    (150, 2950, 1500, 750, '沙发'), (1900, 3200 - 0, 0, 0, ''),
    (5260, 60, 1980, 600, '橱柜'), (5280, 1780, 600, 650, '冰箱'),
    (7400, 3400, 900, 900, '淋浴'), (7500, 2600, 500, 700, '马桶'),
    (6400, 2600, 800, 450, '台盆'), (7500, 4400, 900, 900, '淋浴'),
    (6450, 4380, 800, 420, '马桶'), (6400, 5700, 800, 350, '台盆'),
    (5250, 2560, 600, 600, '家政柜'), (5250, 3620, 600, 600, '洗衣机'),
    (2900, 7700, 600, 600, '洗衣柜'),
]
STACKS = [(8050, 2760, '排污立管'), (7830, 2760, '给水立管')]


def P(x, y):
    """平面坐标 → DXF 坐标（北在上）"""
    return (float(x), float(YMAX - y))


def wall(msp, p1, p2, t, layer):
    """双线墙：沿中线两侧各偏移 t/2"""
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L == 0:
        return
    nx, ny = -dy / L * t / 2, dx / L * t / 2
    for sx, sy in ((nx, ny), (-nx, -ny)):
        msp.add_line(P(x1 + sx, y1 + sy), P(x2 + sx, y2 + sy), dxfattribs={'layer': layer})
    # 端头封口
    msp.add_line(P(x1 + nx, y1 + ny), P(x1 - nx, y1 - ny), dxfattribs={'layer': layer})
    msp.add_line(P(x2 + nx, y2 + ny), P(x2 - nx, y2 - ny), dxfattribs={'layer': layer})


def window(msp, orient, pos, a, b, t=240, layer='A-WIN'):
    offs = (-t * 0.32, 0, t * 0.32)
    if orient == 'h':
        for o in offs:
            msp.add_line(P(a, pos + o), P(b, pos + o), dxfattribs={'layer': layer})
    else:
        for o in offs:
            msp.add_line(P(pos + o, a), P(pos + o, b), dxfattribs={'layer': layer})


def door(msp, cx, cy, r, a0, a1, layer='A-DOOR'):
    # 门扇
    msp.add_line(P(cx, cy), P(cx + r * math.cos(math.radians(a0)),
                             cy + r * math.sin(math.radians(a0))), dxfattribs={'layer': layer})
    # 弧线（折线近似，避免角度换算）
    pts = []
    n = 16
    for i in range(n + 1):
        ang = math.radians(a0 + (a1 - a0) * i / n)
        pts.append(P(cx + r * math.cos(ang), cy + r * math.sin(ang)))
    msp.add_lwpolyline(pts, dxfattribs={'layer': layer})


def main():
    doc = ezdxf.new('R2010', setup=True)
    doc.header['$INSUNITS'] = 4  # 毫米
    doc.styles.add('CJK', font='simhei.ttf')

    for name, color, lw in LAYERS:
        lay = doc.layers.add(name)
        lay.color = color
        lay.dxf.lineweight = lw

    msp = doc.modelspace()

    for a, b in EXT_SEGS:
        wall(msp, a, b, 240, 'A-WALL-EXT')
    for a, b in INT_WALLS:
        wall(msp, a, b, 120, 'A-WALL-INT')
    for a, b in NEW_WALLS:
        wall(msp, a, b, 100, 'A-WALL-NEW')

    for o, p, a, b in WINDOWS:
        window(msp, o, p, a, b)
    o, p, a, b = INT_WIN
    window(msp, o, p, a, b, t=120, layer='A-WIN')

    for cx, cy, r, a0, a1 in DOORS:
        door(msp, cx, cy, r, a0, a1)

    for x, y, w, h, label in FURN:
        if w <= 0 or h <= 0:
            continue
        msp.add_lwpolyline([P(x, y), P(x + w, y), P(x + w, y + h), P(x, y + h)],
                           close=True, dxfattribs={'layer': 'A-FURN'})
        if label:
            msp.add_text(label, height=90, dxfattribs={'layer': 'A-FURN', 'style': 'CJK'}) \
               .set_placement(P(x + w / 2, y + h / 2), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    for x, y, label in STACKS:
        msp.add_circle(P(x, y), radius=110, dxfattribs={'layer': 'A-PLUMB'})
        msp.add_text(label, height=80, dxfattribs={'layer': 'A-PLUMB', 'style': 'CJK'}) \
           .set_placement(P(x, y - 260), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    for name, x, y in ROOMS:
        msp.add_text(name, height=160, dxfattribs={'layer': 'A-TEXT', 'style': 'CJK'}) \
           .set_placement(P(x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    # 标题
    msp.add_text('苏州 · 两室两厅改造（三居室方案）  1:50  单位 mm',
                 height=200, dxfattribs={'layer': 'A-TITLE', 'style': 'CJK'}) \
       .set_placement(P(0, -900), align=ezdxf.enums.TextEntityAlignment.LEFT)
    msp.add_text('方案深化图 · 依据挂牌户型图反推，未现场复尺，不得直接施工',
                 height=140, dxfattribs={'layer': 'A-TITLE', 'style': 'CJK'}) \
       .set_placement(P(0, -1250), align=ezdxf.enums.TextEntityAlignment.LEFT)

    os.makedirs(OUT, exist_ok=True)
    doc.saveas(PATH)

    # 统计
    from collections import Counter
    c = Counter(e.dxftype() for e in msp)
    print('DXF 已生成:', PATH)
    print('实体:', dict(c), '总计', sum(c.values()))
    print('图层:', [l.dxf.name for l in doc.layers])

    # 工程量（墙长）
    def seg_len(segs):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) / 1000.0

    ext_l = seg_len(EXT_SEGS)
    int_l = seg_len(INT_WALLS)
    new_l = seg_len(NEW_WALLS)
    print()
    print('工程量（米）:')
    print(f'  外墙 {ext_l:.2f} m（240 厚，含窗洞扣除）')
    print(f'  原内墙 {int_l:.2f} m（120 厚）')
    print(f'  新建轻钢龙骨墙 {new_l:.2f} m（100 厚）')
    print(f'  拆墙 0.00 m')
    print(f'  墙体展开面积 ≈ {ext_l*2.7 + int_l*2.7 + new_l*2.7:.1f} ㎡（按净高 2.7m 计，未扣门窗）')


if __name__ == '__main__':
    main()

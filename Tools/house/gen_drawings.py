# -*- coding: utf-8 -*-
"""
地产线 · 一套改多套 图纸集生成器
输出：house/rental-conversion/drawings/*.svg + index.html

说明：方案深化图。几何依据 2026-11-13 挂牌户型图（房间面积 + 尺寸链），
长宽为按面积/比例反推，未经现场复尺；承重墙、立管、门洞必须现场核实后方可施工。
"""
import os
import math

# ---------- 纸张 / 单位 ----------
MM = 3.0                      # 1 纸面 mm = 3 px
PW, PH = 420 * MM, 297 * MM   # A3 横向 1260 x 891

INK = '#1c1c1c'
MID = '#565656'
LT = '#9a9a9a'
NEW = '#c0392b'
DEMOL = '#d4a017'
WIN = '#1f6fb2'
DOOR = '#7a7a7a'
PIPE = '#e67e22'
WATER = '#2b7cd3'
DRAIN = '#2e8b57'
ELEC = '#8e44ad'

C_PLAN = '#fdfbf7'
C_ROOM = '#fbf7ef'
C_SHARE = '#eef5ff'
C_WET = '#e9f7f3'
C_WARM = '#fff6e6'
C_GREEN = '#f0f7e6'
C_GREY = '#f3f3f3'


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ---------- 图纸 ----------
class Sheet:
    def __init__(self, no, name, scale='1:50', subtitle=''):
        self.no = no
        self.name = name
        self.scale = scale
        self.subtitle = subtitle
        self.body = []

    def a(self, s):
        self.body.append(s)

    # 纸面 mm 坐标
    def L(self, x1, y1, x2, y2, color=INK, w=0.35, dash=None, cap='butt', op=1):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.a(f'<line x1="{x1*MM:.2f}" y1="{y1*MM:.2f}" x2="{x2*MM:.2f}" y2="{y2*MM:.2f}" '
               f'stroke="{color}" stroke-width="{w*MM:.2f}"{d} stroke-linecap="{cap}" opacity="{op}"/>')

    def R(self, x, y, w, h, fill='none', stroke=INK, sw=0.35, dash=None, op=1, rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.a(f'<rect x="{x*MM:.2f}" y="{y*MM:.2f}" width="{w*MM:.2f}" height="{h*MM:.2f}" '
               f'fill="{fill}" stroke="{stroke}" stroke-width="{sw*MM:.2f}"{d} opacity="{op}" rx="{rx*MM:.2f}"/>')

    def P(self, pts, fill='none', stroke=INK, sw=0.35, dash=None, op=1):
        s = ' '.join(f'{x*MM:.2f},{y*MM:.2f}' for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ''
        tag = 'polygon' if fill != 'none' else 'polyline'
        self.a(f'<{tag} points="{s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw*MM:.2f}"{d} opacity="{op}"/>')

    def C(self, cx, cy, r, fill='none', stroke=INK, sw=0.35, dash=None, op=1):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.a(f'<circle cx="{cx*MM:.2f}" cy="{cy*MM:.2f}" r="{r*MM:.2f}" fill="{fill}" '
               f'stroke="{stroke}" stroke-width="{sw*MM:.2f}"{d} opacity="{op}"/>')

    def T(self, x, y, s, size=3.0, color=INK, anchor='start', weight='normal', rot=None, op=1, ls=0, halo=False):
        tr = f' transform="rotate({rot} {x*MM:.2f} {y*MM:.2f})"' if rot else ''
        lsp = f' letter-spacing="{ls}px"' if ls else ''
        base = (f'x="{x*MM:.2f}" y="{y*MM:.2f}" font-size="{size*MM:.2f}" text-anchor="{anchor}" '
                f'font-weight="{weight}" opacity="{op}"{tr}{lsp}')
        if halo:
            self.a(f'<text {base} fill="#ffffff" stroke="#ffffff" stroke-width="{size*MM*0.75:.2f}" '
                   f'stroke-linejoin="round" paint-order="stroke">{esc(s)}</text>')
        self.a(f'<text {base} fill="{color}">{esc(s)}</text>')

    # 多行文本
    def TB(self, x, y, lines, size=2.8, lh=4.6, color=INK, weight='normal', anchor='start'):
        for i, ln in enumerate(lines):
            self.T(x, y + i * lh, ln, size=size, color=color, weight=weight, anchor=anchor)

    def frame(self):
        f = []
        f.append(f'<rect x="0" y="0" width="{PW:.1f}" height="{PH:.1f}" fill="#ffffff"/>')
        f.append(f'<rect x="{6*MM}" y="{6*MM}" width="{(420-12)*MM}" height="{(297-12)*MM}" fill="none" stroke="{INK}" stroke-width="{1.1*MM}"/>')
        f.append(f'<rect x="{10*MM}" y="{10*MM}" width="{(420-20)*MM}" height="{(297-20)*MM}" fill="none" stroke="{INK}" stroke-width="{0.3*MM}"/>')
        # 标题栏
        tx, ty = 420 - 10 - 182, 297 - 10 - 38
        f.append(f'<rect x="{tx*MM}" y="{ty*MM}" width="{182*MM}" height="{38*MM}" fill="#fbfbfb" stroke="{INK}" stroke-width="{0.5*MM}"/>')
        f.append(f'<line x1="{tx*MM}" y1="{(ty+24)*MM}" x2="{(tx+182)*MM}" y2="{(ty+24)*MM}" stroke="{INK}" stroke-width="{0.4*MM}"/>')
        f.append(f'<line x1="{(tx+92)*MM}" y1="{(ty+24)*MM}" x2="{(tx+92)*MM}" y2="{(ty+38)*MM}" stroke="{INK}" stroke-width="{0.3*MM}"/>')
        for i, xx in enumerate([38, 70, 100]):
            f.append(f'<line x1="{(tx+xx)*MM}" y1="{(ty+24)*MM}" x2="{(tx+xx)*MM}" y2="{(ty+38)*MM}" stroke="{INK}" stroke-width="{0.3*MM}"/>')
        f.append(f'<line x1="{(tx+130)*MM}" y1="{(ty+24)*MM}" x2="{(tx+130)*MM}" y2="{(ty+38)*MM}" stroke="{INK}" stroke-width="{0.3*MM}"/>')

        def t(x, y, s, sz=2.9, w='normal', c=INK):
            f.append(f'<text x="{x*MM:.2f}" y="{y*MM:.2f}" font-size="{sz*MM:.2f}" fill="{c}" '
                     f'font-weight="{w}" font-family="Microsoft YaHei, Noto Sans SC, sans-serif">'
                     f'{esc(s)}</text>')

        t(tx + 2, ty + 5.5, '项目：苏州 · 两室两厅 住宅改造（一改多）', 3.0, 'bold')
        t(tx + 2, ty + 10.5, '阶段：方案深化图（依据挂牌户型图，未现场复尺）', 2.6, c=MID)
        t(tx + 2, ty + 15.5, '子项：三居室合租 + 新增独卫（推荐案）', 2.6, c=MID)
        t(tx + 2, ty + 20.5, '注意：承重墙/立管/门洞须现场核实，本册不得直接用于施工', 2.5, c=NEW)
        t(tx + 96, ty + 8, '图名', 2.5, c=MID)
        t(tx + 96, ty + 15, self.name, 3.4, 'bold')
        t(tx + 96, ty + 21, self.subtitle, 2.5, c=MID)

        labels = [('图号', self.no), ('比例', self.scale), ('日期', '2026-11-13'), ('设计', '地产子公司'), ('版本', 'V1')]
        xs = [2, 40, 72, 102, 132]
        for (lb, val), xx in zip(labels, xs):
            t(tx + xx, ty + 28.5, lb, 2.4, c=MID)
            t(tx + xx, ty + 34.5, val, 2.9, 'bold')
        return ''.join(f)

    def save(self, path):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW:.0f}" height="{PH:.0f}" '
                f'viewBox="0 0 {PW:.0f} {PH:.0f}" font-family="Microsoft YaHei, Noto Sans SC, sans-serif">')
        defs = """<defs>
<pattern id="h45" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
  <line x1="0" y1="0" x2="0" y2="6" stroke="#b9b9b9" stroke-width="1"/></pattern>
<pattern id="tile" width="12" height="12" patternUnits="userSpaceOnUse">
  <path d="M0 0H12V12H0Z" fill="none" stroke="#c9c9c9" stroke-width="1"/></pattern>
<pattern id="wood" width="8" height="24" patternUnits="userSpaceOnUse">
  <line x1="0" y1="0" x2="0" y2="24" stroke="#d8cdbd" stroke-width="2"/></pattern>
<pattern id="grain" width="5" height="5" patternUnits="userSpaceOnUse">
  <circle cx="1" cy="1" r="0.6" fill="#c7c7c7"/></pattern>
</defs>"""
        out = head + defs + self.frame() + ''.join(self.body) + '</svg>'
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(out)


# ---------- 平面绘制器 ----------
class Plan:
    def __init__(self, sh, ox, oy, scale=50):
        self.sh = sh
        self.ox = ox
        self.oy = oy
        self.k = 1.0 / scale      # 纸面 mm / 实尺 mm

    def x(self, v):
        return self.ox + v * self.k

    def y(self, v):
        return self.oy + v * self.k

    def w(self, mm):
        return mm * self.k

    def line(self, x1, y1, x2, y2, color=INK, t=30, dash=None, cap='square', op=1):
        self.sh.L(self.x(x1), self.y(y1), self.x(x2), self.y(y2), color,
                  w=max(self.w(t), 0.22), dash=dash, cap=cap, op=op)

    def rect(self, x, y, w, h, fill='none', stroke=INK, sw=20, dash=None, op=1):
        self.sh.R(self.x(x), self.y(y), self.w(w), self.w(h), fill, stroke,
                  max(self.w(sw), 0.2), dash, op)

    def C(self, cx, cy, r, fill='none', stroke=INK, sw=25, dash=None):
        self.sh.C(self.x(cx), self.y(cy), self.w(r), fill=fill, stroke=stroke,
                  sw=max(self.w(sw), 0.2), dash=dash)

    def text(self, x, y, s, size=2.0, color=INK, anchor='start', weight='normal', rot=None, halo=False):
        self.sh.T(self.x(x), self.y(y), s, size=size, color=color, anchor=anchor,
                  weight=weight, rot=rot, halo=halo)

    # 窗：白底擦墙 + 三线
    def window(self, x1, y1, x2, y2, t=240, horiz=True):
        self.line(x1, y1, x2, y2, '#ffffff', t + 40)
        for off in (-t * 0.3, 0, t * 0.3):
            if horiz:
                self.line(x1, y1 + off, x2, y2 + off, WIN, 18, cap='butt')
            else:
                self.line(x1 + off, y1, x2 + off, y2, WIN, 18, cap='butt')

    # 门：门洞白底 + 门扇 + 90°弧
    def door(self, x, y, width, rot=0, swing='ccw', t=120):
        # 以 (x,y) 为铰点，门扇沿 rot 方向展开
        ang = math.radians(rot)
        ex = x + width * math.cos(ang)
        ey = y + width * math.sin(ang)
        self.line(x, y, ex, ey, DOOR, 40)
        arc_start = rot
        arc_end = rot - 90 if swing == 'ccw' else rot + 90
        r = width
        p1 = (x + r * math.cos(math.radians(arc_start)), y + r * math.sin(math.radians(arc_start)))
        p2 = (x + r * math.cos(math.radians(arc_end)), y + r * math.sin(math.radians(arc_end)))
        large = 0
        sweep = 0 if swing == 'ccw' else 1
        self.sh.a(f'<path d="M {self.x(p1[0])*MM:.2f} {self.y(p1[1])*MM:.2f} A {self.w(r)*MM:.2f} {self.w(r)*MM:.2f} 0 {large} {sweep} '
                  f'{self.x(p2[0])*MM:.2f} {self.y(p2[1])*MM:.2f}" fill="none" stroke="{DOOR}" '
                  f'stroke-width="{max(self.w(18)*MM,0.2):.2f}" stroke-dasharray="3,2"/>')
        self.C(x, y, 45, fill=INK)


def dim_h(sh, p, x1, x2, y, label, ext=0):
    ya, yb = p.y(y), p.y(y + ext)
    sh.L(p.x(x1), ya, p.x(x1), yb, MID, w=0.2)
    sh.L(p.x(x2), ya, p.x(x2), yb, MID, w=0.2)
    yy = p.y(y + ext)
    sh.L(p.x(x1), yy, p.x(x2), yy, MID, w=0.22)
    for xx in (p.x(x1), p.x(x2)):
        sh.L(xx, yy - 1.1, xx, yy + 1.1, MID, w=0.4)
    sh.T((p.x(x1) + p.x(x2)) / 2, yy - 0.8, label, size=2.15, color=MID, anchor='middle')


def dim_v(sh, p, y1, y2, x, label, ext=0):
    xa = p.x(x)
    xb = p.x(x + ext)
    sh.L(xa, p.y(y1), xb, p.y(y1), MID, w=0.2)
    sh.L(xa, p.y(y2), xb, p.y(y2), MID, w=0.2)
    sh.L(xb, p.y(y1), xb, p.y(y2), MID, w=0.22)
    for yy in (p.y(y1), p.y(y2)):
        sh.L(xb - 1.1, yy, xb + 1.1, yy, MID, w=0.4)
    sh.T(xb - 0.8, (p.y(y1) + p.y(y2)) / 2, label, size=2.15, color=MID,
         anchor='middle', rot=90)


# ---------- 几何（实尺 mm，原点 = 西北角内墙面，x 向东，y 向南） ----------
OW, OD = 8400, 8900

ROOMS = [
    ('卧室A', 0, 0, 3100, 2870, 8.9, '8.4㎡ · 北窗', C_ROOM),
    ('餐厅', 3100, 0, 5200, 2500, 5.3, '', C_SHARE),
    ('厨房', 5200, 0, 7300, 2500, 5.3, '5.1㎡ · 北窗', C_WARM),
    ('设备平台', 7300, 0, 8400, 2500, 2.8, '待核实', C_GREY),
    ('走道', 5200, 2500, 6300, 4330, 2.0, '', C_GREY),
    ('卫生间1', 6300, 2500, 8400, 4330, 3.9, '3.9㎡ · 东窗', C_WET),
    ('客厅', 0, 2870, 5200, 6900, 21.0, '23.6㎡', C_SHARE),
    ('阳台', 0, 6900, 4200, 8400, 6.3, '5.3㎡ · 南向', C_GREEN),
    ('卧室B', 5200, 4330, 8400, 8900, 14.6, '15.8㎡ · 东窗', C_ROOM),
]

NEW_ROOMS = [
    ('卧室C', 0, 4600, 4200, 6900, 9.7, '新隔断 · 借阳台采光', C_ROOM),
    ('走廊', 4200, 4600, 5200, 8400, 3.8, '', C_GREY),
    ('卫生间2', 6300, 4330, 8400, 6130, 3.8, '新建 · 背靠背借管', C_WET),
]

NEW_WALLS = [
    ('W1', 0, 4600, 4200, 4600),
    ('W2', 4200, 4600, 4200, 8400),
    ('W3', 6300, 4330, 6300, 6130),
    ('W4', 6300, 6130, 8400, 6130),
]

EX_WALLS = [
    (3100, 0, 3100, 2870),
    (0, 2870, 3100, 2870),
    (3100, 2500, 5200, 2500),
    (5200, 0, 5200, 2500),
    (5200, 2500, 8400, 2500),
    (6300, 2500, 6300, 4330),
    (6300, 4330, 8400, 4330),
    (5200, 2500, 5200, 8900),
    (7300, 0, 7300, 2500),
    (0, 6900, 3500, 6900),
]

OUTLINE = [(0, 0), (8400, 0), (8400, 8900), (5200, 8900), (5200, 8400), (0, 8400)]

STACK_DRAIN = (8050, 2760)
STACK_SUPPLY = (7830, 2760)
FLUE = (7050, 280)


TAG_POS = {
    '卧室A': (300, 1150),
    '餐厅': (250, 1450),
    '厨房': (180, 1150),
    '设备平台': (120, 330),
    '走道': None,
    '卫生间1': (150, 1300),
    '客厅': (2600, 750),
    '阳台': (180, 330),
    '卧室B': (180, 330),
    '卧室C': (180, 330),
    '卫生间2': (150, 1150),
}


def base(sh, p, *, tint=True, new=True, labels=True, dims=False, leaf=True, lbl='center'):
    # 轮廓
    p.sh.P([(p.x(x), p.y(y)) for x, y in OUTLINE], fill=C_PLAN, stroke='none')
    if tint:
        for name, x1, y1, x2, y2, area, sub, col in ROOMS:
            p.rect(x1, y1, x2 - x1, y2 - y1, fill=col, stroke='none', sw=0)
        if new:
            for name, x1, y1, x2, y2, area, sub, col in NEW_ROOMS:
                p.rect(x1, y1, x2 - x1, y2 - y1, fill=col, stroke='none', sw=0)
    # 外墙
    pts = OUTLINE + [OUTLINE[0]]
    for a, b in zip(pts, pts[1:]):
        p.line(a[0], a[1], b[0], b[1], INK, 240)
    # 原内墙
    for x1, y1, x2, y2 in EX_WALLS:
        p.line(x1, y1, x2, y2, INK, 120)
    # 新墙
    if new:
        for tag, x1, y1, x2, y2 in NEW_WALLS:
            p.line(x1, y1, x2, y2, NEW, 100)
    # 窗
    p.window(600, 0, 2300, 0, 240, True)
    p.window(5600, 0, 6900, 0, 240, True)
    p.window(8400, 2900, 8400, 3800, 240, False)
    p.window(8400, 6300, 8400, 8200, 240, False)
    p.window(400, 8400, 3200, 8400, 240, True)
    # 新增室内窗：共享客厅 ← 卧室A 北窗借光（非承重墙开设，待结构核实）
    if new:
        p.line(900, 2870, 2100, 2870, '#ffffff', 160)
        p.line(900, 2870, 2100, 2870, WIN, 45, dash='9,5')
        p.line(900, 2810, 900, 2930, WIN, 28)
        p.line(2100, 2810, 2100, 2930, WIN, 28)
    # 门
    if leaf:
        p.line(3600, 0, 4500, 0, '#ffffff', 260)
        p.door(3600, 0, 900, rot=0, swing='cw')
        p.line(5200, 4700, 5200, 5600, '#ffffff', 140)
        p.door(5200, 4700, 900, rot=0, swing='cw')
        p.line(3100, 1900, 3100, 2700, '#ffffff', 140)
        p.door(3100, 2700, 800, rot=-90, swing='ccw')
        p.line(5600, 2500, 6400, 2500, '#ffffff', 140)
        p.door(5600, 2500, 800, rot=0, swing='cw')
        p.line(6300, 3000, 6300, 3800, '#ffffff', 140)
        p.door(6300, 3800, 800, rot=-90, swing='ccw')
        if new:
            p.line(800, 4600, 1700, 4600, '#ffffff', 130)
            p.door(800, 4600, 900, rot=0, swing='cw')
            p.line(6300, 4800, 6300, 5600, '#ffffff', 130)
            p.door(6300, 5600, 800, rot=-90, swing='ccw')
        # 阳台推拉门
        p.line(600, 6900, 2600, 6900, '#ffffff', 200)
        p.line(600, 6890, 2600, 6890, WIN, 20, cap='butt')
        p.line(600, 6915, 2600, 6915, WIN, 20, cap='butt')
    # 立管 / 烟道
    p.C(*STACK_DRAIN, 110, fill='#f1c40f', stroke='#8a6d00', sw=25)
    p.C(*STACK_SUPPLY, 110, fill='#aed6f1', stroke='#1f6fb2', sw=25)
    p.rect(FLUE[0] - 130, FLUE[1] - 130, 260, 260, fill='#f5d6a8', stroke='#a97a2a', sw=25)
    # 标注
    if labels:
        for name, x1, y1, x2, y2, area, sub, col in ROOMS:
            if lbl == 'corner':
                off = TAG_POS.get(name)
                if off is None:
                    continue
                tx, ty = x1 + off[0], y1 + off[1]
                p.text(tx, ty, name, 2.15, anchor='start', weight='bold', halo=True)
                if sub:
                    p.text(tx, ty + 310, sub, 1.6, color=MID, anchor='start', halo=True)
            else:
                if new and name == '客厅':
                    p.text(2600, 3660, '共享客厅', 2.35, anchor='middle', weight='bold', halo=True)
                    continue
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                p.text(cx, cy - 120, name, 2.35, anchor='middle', weight='bold')
                if sub:
                    p.text(cx, cy + 380, sub, 1.85, color=MID, anchor='middle')
        if new:
            for name, x1, y1, x2, y2, area, sub, col in NEW_ROOMS:
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                if name == '走廊':
                    p.text(cx, cy, name, 1.75, color=MID, anchor='middle', rot=90, halo=True)
                elif lbl == 'corner':
                    off = TAG_POS.get(name)
                    if off is None:
                        continue
                    tx, ty = x1 + off[0], y1 + off[1]
                    p.text(tx, ty, name, 2.05, anchor='start', weight='bold', color=NEW, halo=True)
                    if sub:
                        p.text(tx, ty + 300, sub, 1.55, color=MID, anchor='start', halo=True)
                else:
                    p.text(cx, cy - 120, name, 2.25, anchor='middle', weight='bold', color=NEW)
                    if sub:
                        p.text(cx, cy + 380, sub, 1.7, color=MID, anchor='middle')
    if dims:
        dim_h(sh, p, 0, 3100, 0, '3100', ext=-700)
        dim_h(sh, p, 3100, 5200, 0, '2100', ext=-700)
        dim_h(sh, p, 5200, 7300, 0, '2100', ext=-700)
        dim_h(sh, p, 0, 8400, 0, '8400', ext=-1150)
        dim_v(sh, p, 0, 2870, 0, '2870', ext=-700)
        dim_v(sh, p, 2870, 6900, 0, '4030', ext=-700)
        dim_v(sh, p, 0, 8400, 0, '8400', ext=-1150)
        dim_v(sh, p, 0, 4330, 8400, '4330', ext=700)
        dim_v(sh, p, 4330, 8900, 8400, '4570', ext=700)
        dim_v(sh, p, 0, 8900, 8400, '8900', ext=1150)
        dim_h(sh, p, 6300, 8400, 8900, '2100', ext=480)
        dim_h(sh, p, 5200, 8400, 8900, '3200', ext=480)


def north(sh, x, y):
    sh.C(x, y, 7.5, fill='#fff', stroke=LT, sw=0.3)
    sh.P([(x, y - 6), (x + 2.8, y + 4), (x, y + 1.6), (x - 2.8, y + 4)], fill=NEW, stroke=NEW, sw=0.2)
    sh.T(x, y + 13, 'N', size=2.6, color=MID, anchor='middle')


def scalebar(sh, x, y, scale=50):
    total = 2000  # 2m
    L = total / scale
    sh.L(x, y, x + L, y, INK, w=0.6)
    sh.L(x, y - 1.4, x, y + 1.4, INK, w=0.4)
    sh.L(x + L, y - 1.4, x + L, y + 1.4, INK, w=0.4)
    sh.L(x + L / 2, y - 1.4, x + L / 2, y + 1.4, INK, w=0.4)
    sh.T(x, y + 4.6, '0', size=2.1, color=MID, anchor='middle')
    sh.T(x + L / 2, y + 4.6, '1m', size=2.1, color=MID, anchor='middle')
    sh.T(x + L, y + 4.6, '2m', size=2.1, color=MID, anchor='middle')
    sh.T(x + L + 4, y + 1, f'1:{scale}', size=2.3, color=MID)


def legend(sh, x, y, items, title='图例', lh=5.4):
    sh.T(x, y, title, size=2.9, weight='bold')
    for i, (kind, label) in enumerate(items):
        yy = y + 6 + i * lh
        if kind == 'wall':
            sh.L(x, yy, x + 8, yy, INK, w=1.5)
        elif kind == 'new':
            sh.L(x, yy, x + 8, yy, NEW, w=1.2)
        elif kind == 'exist':
            sh.L(x, yy, x + 8, yy, INK, w=0.8)
        elif kind == 'win':
            sh.L(x, yy, x + 8, yy, WIN, w=0.7)
            sh.L(x, yy - 0.8, x + 8, yy - 0.8, WIN, w=0.3)
        elif kind == 'door':
            sh.C(x + 2, yy + 1, 1.6, fill='none', stroke=DOOR, sw=0.3)
            sh.L(x, yy + 1, x, yy - 2.6, DOOR, w=0.3)
        elif kind == 'drain':
            sh.C(x + 4, yy, 1.9, fill='#f1c40f', stroke='#8a6d00', sw=0.35)
        elif kind == 'supply':
            sh.C(x + 4, yy, 1.9, fill='#aed6f1', stroke='#1f6fb2', sw=0.35)
        elif kind == 'flue':
            sh.R(x + 1, yy - 1.6, 6, 3.2, fill='#f5d6a8', stroke='#a97a2a', sw=0.35)
        elif kind == 'pipe':
            sh.L(x, yy, x + 8, yy, PIPE, w=0.8, dash='4,2')
        elif kind == 'water':
            sh.L(x, yy, x + 8, yy, WATER, w=0.7)
        elif kind == 'sewer':
            sh.L(x, yy, x + 8, yy, DRAIN, w=0.7, dash='5,2')
        elif kind == 'socket':
            sh.C(x + 4, yy, 1.9, fill='#fff', stroke=ELEC, sw=0.35)
            sh.L(x + 2.6, yy, x + 5.4, yy, ELEC, w=0.35)
        elif kind == 'switch':
            sh.C(x + 4, yy, 1.9, fill=ELEC, stroke=ELEC, sw=0.3)
        elif kind == 'light':
            sh.C(x + 4, yy, 2.1, fill='none', stroke='#d08b00', sw=0.35)
            sh.L(x + 1.9, yy, x + 6.1, yy, '#d08b00', w=0.3)
            sh.L(x + 4, yy - 2.1, x + 4, yy + 2.1, '#d08b00', w=0.3)
        elif kind == 'furn':
            sh.R(x + 0.5, yy - 1.7, 7, 3.4, fill='#fff', stroke=MID, sw=0.3)
        sh.T(x + 11, yy + 1.2, label, size=2.35, color=MID)


def note_block(sh, x, y, lines, title='说明', width=0):
    sh.T(x, y, title, size=2.9, weight='bold')
    sh.TB(x, y + 6, lines, size=2.3, lh=4.4, color=MID)


# ================= 图纸 =================
OUTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'house', 'rental-conversion', 'drawings'))


def sheet_cover():
    sh = Sheet('T-00', '图纸目录与设计说明', '—', '方案深化')
    x = 18
    y = 22
    sh.T(x, y, '一、项目概况', size=3.4, weight='bold')
    rows = [
        ('项目', '苏州 · 两室两厅住宅，套内约 68–70㎡（建面约 83–85㎡）'),
        ('原始格局', '卧室A 8.4 ｜ 厨房 5.1 ｜ 卫生间 3.9 ｜ 卧室B 15.8 ｜ 客厅 23.6 ｜ 阳台 5.3'),
        ('采光面', '北 2（卧室A、厨房）· 东 2（卫1、卧室B）· 南 1（阳台）· 西 0'),
        ('改造目标', '由"整租两室"升级为"三居室合租 + 新增独立卫生间"'),
        ('改造量', '新增轻钢龙骨隔墙 4 道（W1–W4）· 新增卫生间 1 间 · 室内窗 1 樘 · 不拆墙体'),
        ('不动作项', '承重墙、外墙立面、燃气管道与表具、公共烟道、排污立管、疏散通道'),
    ]
    for i, (k, v) in enumerate(rows):
        yy = y + 9 + i * 7.2
        sh.T(x, yy, k, size=2.6, color=MID)
        sh.T(x + 26, yy, v, size=2.6)
        sh.L(x, yy + 2.6, x + 190, yy + 2.6, '#e6e6e6', w=0.25)

    y2 = y + 9 + len(rows) * 7.2 + 10
    sh.T(x, y2, '二、图纸目录', size=3.4, weight='bold')
    sheets = [
        ('T-00', '图纸目录与设计说明', '—'),
        ('A-01', '原始结构图', '1:50'),
        ('A-02', '墙体拆改图', '1:50'),
        ('A-03', '平面布置图', '1:50'),
        ('A-04', '地面铺装图', '1:50'),
        ('A-05', '天花布置图', '1:50'),
        ('A-06', '强弱电点位图', '1:50'),
        ('A-07', '给排水点位图', '1:50'),
        ('A-08', '卫生间2 立面与大样', '1:25 / 1:10'),
        ('D-01', '软装布置图', '1:50'),
        ('D-02', '软装材料板与家具清单', '—'),
        ('D-03', '产品配置标准与成本卡', '—'),
    ]
    for i, (no, nm, sc) in enumerate(sheets):
        yy = y2 + 8 + i * 6.4
        sh.L(x, yy + 2.4, x + 120, yy + 2.4, '#eeeeee', w=0.25)
        sh.T(x, yy, no, size=2.7, weight='bold')
        sh.T(x + 16, yy, nm, size=2.7)
        sh.T(x + 92, yy, sc, size=2.6, color=MID)
    sh.T(x, y2 + 8 + len(sheets) * 6.4 + 5, '页签：本册共 12 张（含封面），图纸编号与文件名一一对应。', size=2.3, color=MID)

    # 右栏
    rx = 232
    sh.T(rx, 22, '三、设计依据', size=3.4, weight='bold')
    sh.TB(rx, 31, [
        '1. 《住房租赁条例》国令812号（2025-09-15 施行）',
        '2. 《苏州市出租房屋居住安全管理条例》§11–12',
        '3. GB 50096《住宅设计规范》',
        '4. GB 50015《建筑给水排水设计标准》',
        '5. JGJ 298《住宅室内防水工程技术规范》',
        '6. GB 50118《民用建筑隔声设计规范》',
        '7. GB 50016《建筑设计防火规范》',
        '8. GB 55009《燃气工程项目规范》',
    ], size=2.4, lh=4.8, color=MID)

    sh.T(rx, 78, '四、主要材料做法', size=3.4, weight='bold')
    mat = [
        ('隔墙', '75 系列轻钢龙骨 + 双面双层 12mm 纸面石膏板 + 50mm 岩棉(≥80kg/m³)，Rw≥45dB'),
        ('楼地面', '卧室/厅：8mm SPC 锁扣地板；厨卫：300×300 防滑地砖；阳台：防滑地砖'),
        ('墙面', '居室：耐水腻子 + 哑光乳胶漆（可擦洗）；厨卫：300×600 墙砖到顶'),
        ('顶面', '居室：原结构顶 + 局部吊顶；厨卫：300×300 铝扣板，H=2400'),
        ('门', '户门保留；室内门 800/900×2100 免漆复合门；卫2 门 800 铝镁合金'),
        ('五金', '壁挂马桶隐藏水箱、恒温花洒、静音地漏、防臭存水弯'),
    ]
    for i, (k, v) in enumerate(mat):
        yy = 86 + i * 12.5
        sh.T(rx, yy, k, size=2.45, weight='bold')
        # 手工折行
        lines = []
        cur = ''
        for ch in v:
            cur += ch
            if len(cur) >= 30:
                lines.append(cur)
                cur = ''
        if cur:
            lines.append(cur)
        sh.TB(rx + 14, yy, lines, size=2.25, lh=4.2, color=MID)

    sh.T(rx, 170, '五、施工注意事项', size=3.4, weight='bold')
    sh.TB(rx, 179, [
        '1. 拆改前取得竣工图与物业结构确认；粗黑实线一律按承重墙处理。',
        '2. 新增卫生间必须与原卫生间背靠背，横管≤1.5m，坡度 1.5%–2%。',
        '3. 不得新增排污立管、不得在梁下穿孔、不得改动燃气任何部件。',
        '4. 防水：地面 + 墙面 1.8m，两遍，闭水 48 小时并留存影像。',
        '5. 隔墙内预埋 40mm 线管；下水管包 2mm 隔音棉 + 阻尼片。',
        '6. 公共烟道不得封堵、不得改向；第二厨房不得接入。',
        '7. 疏散通道净宽≥1.1m，不得上锁堆物；每间配烟感与灭火器。',
        '8. 完工后按《住房租赁条例》实名签约并办理租赁备案。',
    ], size=2.3, lh=4.6, color=MID)

    sh.L(rx, 228, rx + 165, 228, '#e6e6e6', w=0.3)
    sh.T(rx, 235, '本册为方案深化图：几何依据挂牌户型图反推，未经现场复尺。', size=2.4, color=NEW)
    sh.T(rx, 241, '承重墙位置、立管管径、门洞尺寸、卧室B 南墙有无窗——四项核实后方可出施工图。', size=2.4, color=NEW)
    return sh


def sheet_orig():
    sh = Sheet('A-01', '原始结构图', '1:50', '改造前现状')
    p = Plan(sh, 44, 46, 50)
    base(sh, p, tint=True, new=False, labels=True, dims=True)
    legend(sh, 246, 40, [
        ('wall', '外墙 / 承重墙（不可动）'),
        ('exist', '原内隔墙'),
        ('win', '外窗'),
        ('door', '门 / 门洞'),
        ('drain', '排污立管 DN110'),
        ('supply', '给水立管 DN32'),
        ('flue', '公共烟道'),
    ])
    north(sh, 236, 92)
    scalebar(sh, 232, 118, 50)
    note_block(sh, 246, 152, [
        '现状要点：',
        '· 采光面 5 个：北2、东2、南1；西侧为共用山墙。',
        '· 入户门仅北墙中部一扇，东、南为外墙。',
        '· 排污立管 1 根（东侧卫1 内），烟道 1 个（厨房东北角）。',
        '· 卫生间1 与 卧室B 之间为原隔墙，厚度按 120 计。',
        '· 设备平台 2100×1100 段用途待核实（管井/设备平台）。',
        '',
        '实测复核项（必做）：',
        '1. 各房间净尺寸与图差 >5% 时，本册全部重排。',
        '2. 承重墙/剪力墙位置（物业结构图 + 敲击复核）。',
        '3. 排污立管管径、是否同层排水（抬头看顶有无横管）。',
        '4. 卧室B 南墙是否开窗（若有，可用于方案A 明卫）。',
    ], width=160)
    return sh


def sheet_demol():
    sh = Sheet('A-02', '墙体拆改图', '1:50', '拆除 0 · 新建 4 道')
    p = Plan(sh, 28, 34, 50)
    base(sh, p, tint=False, new=True, labels=True, dims=False, leaf=True)
    # 新墙加编号
    for tag, x1, y1, x2, y2 in NEW_WALLS:
        p.C((x1 + x2) / 2, (y1 + y2) / 2, 150, fill='#fff', stroke=NEW, sw=40)
        p.text((x1 + x2) / 2, (y1 + y2) / 2 + 60, tag, 2.1, color=NEW, anchor='middle', weight='bold')
    legend(sh, 246, 40, [
        ('wall', '保留墙体'),
        ('new', '新建墙体（W1–W4）'),
        ('door', '新增 / 保留门洞'),
        ('win', '保留窗'),
    ])
    north(sh, 236, 84)
    scalebar(sh, 232, 106, 50)

    sh.T(246, 132, '墙体表', size=2.9, weight='bold')
    rows = [
        ('W1', '横墙 4200×100', '卧室C 北侧分隔'),
        ('W2', '纵墙 3800×100', '卧室C 东侧 / 走廊西侧'),
        ('W3', '纵墙 1800×100', '卫生间2 西侧'),
        ('W4', '横墙 2100×100', '卫生间2 南侧'),
    ]
    for i, (a, b, c) in enumerate(rows):
        yy = 140 + i * 7.4
        sh.T(246, yy, a, size=2.5, weight='bold', color=NEW)
        sh.T(258, yy, b, size=2.4)
        sh.T(246, yy + 3.4, c, size=2.2, color=MID)

    note_block(sh, 246, 182, [
        '拆除说明：',
        '本方案不拆除任何墙体，不新开结构门洞。',
        '· 卧室B 门洞：利用原门洞（位置须现场核对）。',
        '· 卧室A 门、厨房门、卫1 门、阳台推拉门：原样保留。',
        '· 新增门洞仅出现在新建轻钢龙骨墙上（卧室C、卫2）。',
        '· 新增室内窗 1 樘：卧室A ↔ 共享客厅，1200×2200，',
        '  长虹玻璃；**仅限非承重墙**，若为承重墙本册作废。',
        '',
        '如现场原卧室B 门洞与走廊不对位，需在',
        'x=5200 墙上新开 900 门洞：该墙若为承重墙，',
        '一律不得开洞，须改由卧室C 侧进入（本册作废重排）。',
    ], width=160)
    return sh


def furn(sh, p, x, y, w, h, label='', sub='', fill='#ffffff', dash=None, sw=25, size=1.65, force=False):
    p.rect(x, y, w, h, fill=fill, stroke=MID, sw=sw, dash=dash)
    if label and (force or w * h >= 600000):
        cx, cy = x + w / 2, y + h / 2
        rot = 90 if h > w * 2.2 else None
        p.text(cx, cy + (0 if rot else 55), label, size, color=MID, anchor='middle', rot=rot, halo=True)


def sheet_furn():
    sh = Sheet('A-03', '平面布置图', '1:50', '家具与洁具定位')
    p = Plan(sh, 28, 34, 50)
    base(sh, p, tint=True, new=True, labels=True, dims=False, leaf=True, lbl='corner')
    # 卧室A —— 通体柜 + 顶柜 + 书桌靠窗
    furn(sh, p, 1100, 600, 2000, 1500, '双人床 1500×2000')
    p.rect(1100, 600, 2000, 380, fill='#f2ede4', stroke=MID, sw=20)
    furn(sh, p, 150, 900, 600, 1800, 'K1', force=True)
    p.rect(150, 900, 600, 200, fill='none', stroke=NEW, sw=18, dash='6,4')
    p.text(450, 1080, '顶柜', 1.5, color=NEW, anchor='middle', halo=True)
    furn(sh, p, 300, 100, 1000, 550, '书桌 1000×550')
    p.C(800, 950, 240, fill='#fff', stroke=MID, sw=25)
    p.rect(2950, 2150, 80, 750, fill='#eaf4fa', stroke=WIN, sw=20)
    p.text(2920, 2100, '镜', 1.5, color=WIN, anchor='end', halo=True)
    p.text(1500, 3010, '室内窗 1200×2200（借光）', 1.55, color=WIN, anchor='middle', halo=True)

    # 卧室C —— 地台抬高 + 通体柜
    p.rect(60, 4650, 2140, 2200, fill='none', stroke=NEW, sw=20, dash='10,6')
    p.text(1130, 4800, '地台 +150（下做抽屉）', 1.6, color=NEW, anchor='middle', halo=True)
    furn(sh, p, 200, 5000, 2000, 1800, '双人床 1800×2000')
    p.rect(200, 5000, 380, 1800, fill='#f2ede4', stroke=MID, sw=20)
    furn(sh, p, 2400, 4650, 1800, 600, 'K2', force=True)
    p.rect(2400, 4650, 1800, 200, fill='none', stroke=NEW, sw=18, dash='6,4')
    p.text(3300, 4830, '顶柜/行李柜', 1.5, color=NEW, anchor='middle', halo=True)
    furn(sh, p, 2700, 6250, 1000, 550, '书桌 1000×550')
    p.C(3600, 5900, 330, fill='#fff', stroke=MID, sw=25)
    # 阳台
    p.line(400, 7600, 3000, 7600, MID, 30, dash='8,4')
    p.text(1700, 7500, '晾衣杆', 1.8, color=MID, anchor='middle')
    furn(sh, p, 2900, 7700, 600, 600, '洗衣柜')

    # 卧室B 主卧套 —— 衣柜 + 顶柜
    furn(sh, p, 5900, 6800, 1800, 2000, '双人床 1800×2000')
    p.rect(5900, 8420, 1800, 380, fill='#f2ede4', stroke=MID, sw=20)
    furn(sh, p, 5250, 6200, 600, 2000, 'K3', force=True)
    p.rect(5250, 6200, 600, 200, fill='none', stroke=NEW, sw=18, dash='6,4')
    p.text(5550, 6380, '顶柜', 1.5, color=NEW, anchor='middle', halo=True)
    furn(sh, p, 7300, 8350, 900, 550, '书桌')
    # 卫2 洁具
    furn(sh, p, 7500, 4400, 900, 900, '淋浴 900×900', fill='#eaf6fb')
    furn(sh, p, 6450, 4380, 800, 420, '壁挂马桶', fill='#eaf6fb')
    furn(sh, p, 6400, 5700, 800, 350, '台盆 800', fill='#eaf6fb')

    # 卫1 —— 半墙长虹玻璃（朝走道借光）
    p.line(6300, 2500, 6300, 2980, WIN, 60, dash='10,6')
    p.line(6300, 3820, 6300, 4330, WIN, 60, dash='10,6')
    p.text(6220, 3300, '半墙长虹玻璃', 1.5, color=WIN, anchor='end', rot=90, halo=True)
    furn(sh, p, 7400, 3400, 900, 900, '淋浴 900×900', fill='#eaf6fb')
    furn(sh, p, 7500, 2600, 500, 700, '马桶', fill='#eaf6fb')
    furn(sh, p, 6400, 2600, 800, 450, '台盆 800', fill='#eaf6fb')

    # 厨房
    furn(sh, p, 5260, 60, 1980, 600, '橱柜', fill='#fdf0dd')
    furn(sh, p, 6700, 660, 600, 1180, '', fill='#fdf0dd')
    furn(sh, p, 5700, 120, 800, 430, '水槽', fill='#e8f4fb')
    furn(sh, p, 6780, 900, 450, 750, '双灶', fill='#f6e3c8')
    furn(sh, p, 5280, 1780, 600, 650, '冰箱')

    # 共享客厅
    furn(sh, p, 150, 2950, 1500, 750, '双人沙发 1500')
    furn(sh, p, 400, 3850, 800, 400, '茶几')
    # 共享客厅 —— 吧台兼餐桌
    furn(sh, p, 1900, 3200, 1600, 450, 'K4 吧台', fill='#fdf0dd', force=True)
    for cx in (2150, 2700, 3250):
        p.C(cx, 3000, 170, fill='#fff', stroke=MID, sw=20)
    furn(sh, p, 2600, 4250, 1200, 330, '电视柜')
    furn(sh, p, 4300, 2900, 800, 300, '书架')

    # 走道 家政
    furn(sh, p, 5250, 2560, 600, 600, '家政柜')
    furn(sh, p, 5250, 3620, 600, 600, '洗衣机')

    # 关键净尺寸
    dim_h(sh, p, 5200, 6300, 9000, '1100', ext=340)
    dim_h(sh, p, 0, 4200, 7600, '4200', ext=260)
    dim_v(sh, p, 4330, 6130, 5000, '1800', ext=-260)

    north(sh, 34, 228)
    scalebar(sh, 58, 228, 50)

    legend(sh, 246, 40, [
        ('furn', '家具 / 洁具'),
        ('new', '新建墙体'),
        ('door', '门 / 门洞'),
        ('win', '窗 / 长虹玻璃 / 室内窗'),
    ])
    sh.T(246, 68, '家具与收纳', size=2.9, weight='bold')
    items = [
        ('卧室A', '床1500 · K1 通体柜600×1800 · 顶柜 · 书桌1000 · 全身镜'),
        ('卧室C', '地台+150 · 床1800 · K2 通体柜1800×600 · 顶柜 · 书桌'),
        ('主卧B', '床1800 · K3 衣柜2000×600 · 顶柜 · 书桌900 · 独卫'),
        ('客厅', 'K4 吧台兼餐桌1600×450 · 沙发1500 · 茶几 · 电视柜'),
        ('厨房', 'K5 L型橱柜600深 · 水槽800 · 双灶750 · 冰箱'),
        ('卫1', '半墙长虹玻璃 · 淋浴900 · 马桶 · 台盆800'),
        ('卫2', '淋浴900 · 壁挂马桶 · 台盆800 · 玻璃砖借光'),
        ('公区', 'K6 家政柜 · 洗衣机600 · 阳台洗衣柜'),
    ]
    for i, (k, v) in enumerate(items):
        yy = 76 + i * 6.4
        sh.T(246, yy, k, size=2.4, weight='bold')
        sh.T(260, yy, v, size=2.05, color=MID)

    note_block(sh, 246, 132, [
        '布置要点（按出租产品标准）：',
        '· 每间卧室必配：通体柜到顶 + 顶柜/行李柜 + 书桌 + 全身镜。',
        '· 卧室C 做地台 +150，不砌墙就分出睡眠区，台下做抽屉。',
        '· 共享客厅靠卧室A 一侧开 1200×2200 室内窗（长虹玻璃），',
        '  借北窗光——这是本户"每个空间都有窗"的唯一补窗点。',
        '· 卫1 朝走道做半墙长虹玻璃；卫2 用玻璃砖借主卧东窗。',
        '· 厨房保持明厨（北窗）——本户最硬的溢价点。',
        '· 吧台兼餐桌，省一套餐桌椅，也省 1.2㎡ 占地。',
        '',
        '净尺寸：主通道≥900；床侧≥600；柜前≥600；',
        '淋浴≥900×900；马桶中心距侧墙≥400。',
    ], width=160)
    return sh


def sheet_floor():
    sh = Sheet('A-04', '地面铺装图', '1:50', '材料分区与铺贴方向')
    p = Plan(sh, 28, 34, 50)
    base(sh, p, tint=False, new=True, labels=True, dims=False, leaf=False)

    # 填充
    for name, x1, y1, x2, y2, area, sub, col in ROOMS:
        pat = 'wood'
        if '厨房' in name or '卫生间' in name:
            pat = 'tile'
        elif '阳台' in name:
            pat = 'tile'
        elif '设备' in name:
            pat = 'grain'
        p.rect(x1, y1, x2 - x1, y2 - y1, fill=f'url(#{pat})', stroke='none', sw=0)
    for name, x1, y1, x2, y2, area, sub, col in NEW_ROOMS:
        pat = 'tile' if '卫生间' in name else ('wood' if '卧室' in name else 'wood')
        p.rect(x1, y1, x2 - x1, y2 - y1, fill=f'url(#{pat})', stroke='none', sw=0)
    # 重画墙
    pts = OUTLINE + [OUTLINE[0]]
    for a, b in zip(pts, pts[1:]):
        p.line(a[0], a[1], b[0], b[1], INK, 240)
    for x1, y1, x2, y2 in EX_WALLS:
        p.line(x1, y1, x2, y2, INK, 120)
    for tag, x1, y1, x2, y2 in NEW_WALLS:
        p.line(x1, y1, x2, y2, NEW, 100)

    # 门槛石
    for (x, y, w, h) in [(800, 4540, 900, 120), (6300, 4740, 140, 900), (5600, 2440, 800, 120), (3100, 1840, 140, 900), (3600, -60, 900, 120)]:
        p.rect(x, y, w, h, fill='#d9d2c5', stroke=INK, sw=20)

    # 起铺点 & 方向
    for x, y, txt in [(1500, 1400, '→'), (1800, 5600, '→'), (6800, 7400, '↑'), (2200, 3300, '→')]:
        p.text(x, y, txt, 3.2, color=NEW, anchor='middle')

    # 地漏/坡度
    for x, y, s in [(8250, 4250, '↓'), (6700, 6050, '↓'), (7150, 2400, '↓')]:
        p.C(x, y, 90, fill='#e8f4fb', stroke=WIN, sw=25)
        p.text(x, y + 380, s, 2.2, color=WIN, anchor='middle')

    legend(sh, 246, 40, [
        ('furn', 'SPC 锁扣地板'),
        ('win', '防滑地砖 300×300'),
        ('pipe', '门槛石'),
    ])
    sh.T(246, 66, '材料与做法', size=2.9, weight='bold')
    rows = [
        ('卧室 A/C/B', '8mm SPC 锁扣地板，通铺，沿长边起铺'),
        ('客厅/餐厅/走廊', '同 SPC 通铺，与卧室留 3mm 伸缩缝'),
        ('厨房', '300×300 防滑地砖，1% 坡向地漏'),
        ('卫生间 1/2', '300×300 防滑地砖，1.5% 坡向地漏'),
        ('阳台', '300×300 防滑地砖，1% 坡向地漏'),
        ('门槛石', '花岗岩/人造石，宽 100–120，与地面平'),
    ]
    for i, (k, v) in enumerate(rows):
        yy = 74 + i * 8.2
        sh.T(246, yy, k, size=2.45, weight='bold')
        sh.T(246, yy + 3.6, v, size=2.2, color=MID)

    note_block(sh, 246, 130, [
        '工艺要求：',
        '· 铺设前地面找平，含水率≤8%；',
        '· 地砖铺贴前做 24h 闭水，确认无渗漏；',
        '· 卫生间防水上返墙面 1800，门口外返 300；',
        '· 地漏低于完成面 3–5mm，周边 500 范围找坡；',
        '· 木地板与地砖交接处用同色收边条，不压条。',
    ], width=160)
    return sh


def sheet_ceil():
    sh = Sheet('A-05', '天花布置图', '1:50', '吊顶范围 · 灯具 · 排风')
    p = Plan(sh, 28, 34, 50)
    base(sh, p, tint=True, new=True, labels=True, dims=False, leaf=False)

    # 吊顶范围（虚线）
    for (x1, y1, x2, y2) in [(6300, 2500, 8400, 4330), (6300, 4330, 8400, 6130), (5200, 0, 7300, 2500), (4200, 4600, 5200, 8400)]:
        p.rect(x1, y1, x2 - x1, y2 - y1, fill='none', stroke='#b07cc6', sw=30, dash='10,6')

    # 灯具
    lights = [
        (1550, 1200), (4200, 1600), (1800, 5200), (7000, 7400),
        (1200, 3400), (2600, 3400), (3800, 3400),
        (7400, 3000), (7400, 5200), (6300, 7000),
        (6100, 1100),
    ]
    for x, y in lights:
        p.C(x, y, 130, fill='#fff', stroke='#d08b00', sw=30)
        p.line(x - 130, y, x + 130, y, '#d08b00', 22)
        p.line(x, y - 130, x, y + 130, '#d08b00', 22)

    # 灯带（无主灯：筒灯做基础照度，灯带做氛围）
    for (x1, y1, x2, y2) in [(150, 2930, 5100, 2930), (120, 4700, 4100, 4700),
                             (150, 420, 2950, 420), (5350, 6300, 8250, 6300)]:
        p.line(x1, y1, x2, y2, '#e0a800', 55, dash='14,8')
    p.text(2200, 3090, '灯带（洗墙）', 1.6, color='#b8860b', anchor='middle', halo=True)
    # 轨道射灯（客厅背景墙）
    p.line(2700, 4380, 3900, 4380, '#8a6d00', 45)
    for tx in (2850, 3200, 3550, 3900):
        p.C(tx, 4380, 90, fill='#8a6d00', stroke='#8a6d00', sw=15)
    p.text(3300, 4300, '轨道射灯', 1.6, color='#8a6d00', anchor='middle', halo=True)

    # 排风
    for x, y in [(7900, 4100), (6800, 5900), (7100, 300)]:
        p.rect(x - 160, y - 110, 320, 220, fill='#e8f4fb', stroke=WIN, sw=28)
        p.text(x, y + 70, '排风', 1.7, color=WIN, anchor='middle')

    # 检修口
    for x, y in [(6500, 2700), (6500, 4500), (5400, 200)]:
        p.rect(x, y, 300, 300, fill='none', stroke=MID, sw=25, dash='6,4')
        p.text(x + 150, y + 500, '检修', 1.6, color=MID, anchor='middle')

    # 标高
    for x, y, s in [(7300, 3900, 'H=2400'), (7300, 5200, 'H=2400'), (6100, 1900, 'H=2350')]:
        p.text(x, y, s, 2.1, color='#7d3c98', anchor='middle')
    p.text(2600, 6000, '原结构顶 H=2700', 2.2, color=MID, anchor='middle')

    legend(sh, 246, 40, [
        ('light', '筒灯 / 射灯'),
        ('pipe', '灯带（洗墙）'),
        ('win', '排风扇 / 风管'),
        ('exist', '吊顶范围（虚线）'),
        ('socket', '检修口 300×300'),
    ])
    sh.T(246, 74, '天花做法', size=2.9, weight='bold')
    rows = [
        ('居室', '无主灯：原顶刷白 + 周边灯带 + 客厅轨道射灯，H≈2700'),
        ('厨房', '铝扣板 300×300，H=2350，烟机上方留检修'),
        ('卫1/卫2', '铝扣板 300×300，H=2400，装排风与浴霸位'),
        ('走廊', '平顶，H=2400，暗藏灯带'),
        ('窗帘盒', '卧室A/C/B 窗侧留 200×150 窗帘盒'),
    ]
    for i, (k, v) in enumerate(rows):
        yy = 82 + i * 9.2
        sh.T(246, yy, k, size=2.45, weight='bold')
        sh.T(246, yy + 3.9, v, size=2.15, color=MID)

    note_block(sh, 246, 138, [
        '无主灯（出租房最便宜的"高级感"）：',
        '· 取消吸顶灯，筒灯做基础照度，灯带做氛围；',
        '· 全部 3000K 暖白，统一色温，禁止混色温；',
        '· 卧室 4 只筒灯 + 床头壁灯；客厅 6 只 + 轨道射灯；',
        '· 每个房间独立回路，开关双控（门口 + 床头）。',
        '',
        '排风：',
        '· 卫1 排风接公共风道，装止逆阀；',
        '· 卫2 无外窗，排风必须接东外墙风口或独立风道，',
        '  风量 ≥120m³/h，配延时开关（运行 5 分钟后自停）。',
    ], width=160)
    return sh


def sym_socket(sh, p, x, y, kind='二三级'):
    p.C(x, y, 95, fill='#fff', stroke=ELEC, sw=25)
    p.line(x - 55, y, x + 55, y, ELEC, 20)
    if kind == '空调':
        p.line(x, y - 55, x, y + 55, ELEC, 20)


def sym_switch(sh, p, x, y):
    p.C(x, y, 90, fill=ELEC, stroke=ELEC, sw=20)


def sheet_elec():
    sh = Sheet('A-06', '强弱电点位图', '1:50', '插座 · 开关 · 回路')
    p = Plan(sh, 28, 34, 50)
    base(sh, p, tint=True, new=True, labels=True, dims=False, leaf=True)

    # 配电箱 / 弱电箱
    p.rect(3550, 180, 400, 180, fill='#f4ecf7', stroke=ELEC, sw=30)
    p.text(3750, 130, 'AL 配电箱', 1.75, color=ELEC, anchor='middle')
    p.rect(4000, 180, 300, 180, fill='#f4ecf7', stroke=ELEC, sw=30)
    p.text(4150, 130, '弱电箱', 1.7, color=ELEC, anchor='middle')

    # 插座
    sockets = [
        (700, 300, '二三级'), (2900, 300, '二三级'), (2400, 2700, '二三级'),
        (400, 4500, '二三级'), (3900, 4500, '二三级'), (1200, 6750, '二三级'),
        (5300, 5000, '二三级'), (7100, 8600, '二三级'), (8250, 6500, '二三级'),
        (6700, 100, '二三级'), (6600, 900, '空调'), (7300, 5600, '空调'),
        (6600, 3700, '空调'), (1200, 2600, '空调'), (2800, 2600, '空调'),
        (6600, 2550, '二三级'), (7000, 6400, '二三级'),
    ]
    for x, y, k in sockets:
        sym_socket(sh, p, x, y, k)

    # 开关
    for x, y in [(3600, 450), (3100, 2600), (5200, 2600), (5200, 5500), (800, 4400), (6300, 3700), (6300, 4800)]:
        sym_switch(sh, p, x, y)

    # 弱电
    for x, y, s in [(2000, 1800, '网'), (2600, 5400, '网'), (7300, 7000, '网'), (6300, 3400, 'TV')]:
        p.rect(x - 130, y - 130, 260, 260, fill='#fff', stroke=ELEC, sw=25, dash='5,3')
        p.text(x, y + 60, s, 1.6, color=ELEC, anchor='middle')

    legend(sh, 246, 40, [
        ('socket', '插座（五孔）'),
        ('switch', '开关'),
        ('light', '灯位'),
        ('exist', '弱电点位'),
    ])
    sh.T(246, 68, '回路表', size=2.9, weight='bold')
    rows = [
        ('L1', '照明 公区', 'B10', '客厅/餐/走廊'),
        ('L2', '照明 卧室', 'B10', 'A/C/B 三间'),
        ('L3', '插座 卧室', 'C16', '含空调预留'),
        ('L4', '插座 公区', 'C16', '客厅/走廊'),
        ('L5', '厨房', 'C20', '冰箱/灶/烟机'),
        ('L6', '卫1', 'C16', '含浴霸'),
        ('L7', '卫2', 'C16', '含排风'),
        ('L8', '空调 1', 'C20', '',
        ),
    ]
    for i, r in enumerate(rows):
        yy = 76 + i * 6.0
        sh.T(246, yy, r[0], size=2.4, weight='bold')
        sh.T(254, yy, r[1], size=2.3)
        sh.T(288, yy, r[2], size=2.3, color=MID)
        sh.T(300, yy, r[3], size=2.1, color=MID)

    note_block(sh, 246, 134, [
        '电气要点：',
        '· 总开 63A，漏保 30mA；分路见回路表。',
        '· 每间卧室：床头双控 + 2 组五孔 + 1 组网口。',
        '· 空调：独立回路，2.5mm²，插座距顶 200。',
        '· 厨房：灶/烟机/冰箱分路；水槽下留 2 个插座。',
        '· 卫2：壁挂马桶旁留电源（智能盖），IP44 防溅盒。',
        '',
        '计量（合规）：',
        '· 严禁私装电表。采用分项计量模块/智能插座，',
        '  只采集数据、不改供电回路；合同约定分摊并公示。',
    ], width=160)
    return sh


def sheet_plumb():
    sh = Sheet('A-07', '给排水点位图', '1:50', '借管路径与坡度')
    p = Plan(sh, 28, 34, 50)
    base(sh, p, tint=True, new=True, labels=True, dims=False, leaf=False)

    # 给水（蓝实线）
    p.line(7830, 2760, 7830, 3400, WATER, 35)
    p.line(7830, 3400, 6600, 3400, WATER, 30)
    p.line(7830, 2760, 7830, 4600, WATER, 35)          # 下至卫2
    p.line(7830, 4600, 7000, 4600, WATER, 30)
    p.line(7830, 4600, 7900, 5300, WATER, 30)
    p.line(7830, 2760, 7830, 2700, WATER, 30)
    p.line(7830, 2700, 7000, 2700, WATER, 30)          # 至厨房
    p.line(7000, 2700, 7000, 900, WATER, 30)

    # 排水（绿虚线）
    p.line(8050, 2760, 8050, 4330, DRAIN, 45, dash='8,4')
    p.line(8050, 4330, 8050, 5900, DRAIN, 45, dash='8,4')
    p.line(8050, 5900, 7000, 5900, DRAIN, 35, dash='8,4')
    p.line(6600, 3400, 8050, 3400, DRAIN, 35, dash='8,4')
    p.line(7000, 900, 7000, 2500, DRAIN, 35, dash='8,4')

    # 地漏
    for x, y in [(8250, 4250), (6700, 6050), (7150, 2400)]:
        p.C(x, y, 95, fill='#d5f5e3', stroke=DRAIN, sw=25)

    # 角阀 / 存水弯标注
    p.text(7900, 3550, 'DN20→DN15', 1.65, color=WATER)
    p.text(7900, 5500, 'DN20→DN15', 1.65, color=WATER)
    p.text(6500, 4300, '新卫横管 0m', 1.75, color=DRAIN, anchor='middle')
    p.text(6900, 6150, 'DN110 · i=1.5%', 1.65, color=DRAIN)
    p.text(5600, 2400, 'DN110 · i=1.5%', 1.65, color=DRAIN)

    legend(sh, 246, 40, [
        ('water', '给水（PPR）'),
        ('sewer', '排水（PVC-U）'),
        ('drain', '地漏 / 立管'),
        ('flue', '烟道'),
    ])
    sh.T(246, 68, '管径与坡度', size=2.9, weight='bold')
    rows = [
        ('给水主', 'PPR DN25', '入户总阀后'),
        ('给水分', 'PPR DN20', '各用水点支管'),
        ('给水末', 'PPR DN15', '角阀前'),
        ('排水支', 'PVC-U DN110', '马桶'),
        ('排水支', 'PVC-U DN50', '台盆/地漏'),
        ('排水支', 'PVC-U DN75', '淋浴'),
        ('坡度', 'i=1.5%–2%', '每米降 15–20mm'),
    ]
    for i, r in enumerate(rows):
        yy = 76 + i * 6.6
        sh.T(246, yy, r[0], size=2.4, weight='bold')
        sh.T(266, yy, r[1], size=2.3)
        sh.T(300, yy, r[2], size=2.1, color=MID)

    note_block(sh, 246, 130, [
        '借管说明（本方案核心）：',
        '· 卫2 与原卫1 背靠背，共用同一根 DN110 立管；',
        '· 卫2 马桶采用墙排（壁挂 + 隐藏水箱），',
        '  排水横管 0m 直接落立管，无需抬地坪；',
        '· 淋浴/台盆 DN50 支管接同层排水横管，坡度 1.5%。',
        '',
        '硬约束：',
        '· 不得新增排污立管、不得楼板开洞；',
        '· 不得在梁下穿孔；横管≤1.5m；',
        '· 每个卫生器具设存水弯，水封≥50mm；',
        '· 给水与排水不得同槽，间距≥100。',
        '',
        '冷热水：左热右冷，间距 150，中心高 1100。',
    ], width=160)
    return sh


def sheet_elev():
    sh = Sheet('A-08', '卫生间2 立面与大样', '1:15', '暗卫做法')

    # ---------- 北墙立面 1:16 ----------
    ox, oy, k = 26, 32, 1 / 16
    W, H = 2100 * k, 2400 * k

    def X(v):
        return ox + v * k

    def Y(v):
        return oy + v * k

    sh.R(X(0), Y(0), W, H, fill='#fcfdfd', stroke=INK, sw=0.5)
    # 瓷砖排版 300x600（横缝 600，竖缝 300）
    for i in range(1, 8):
        sh.L(X(i * 300), Y(0), X(i * 300), Y(H), '#e6edf1', w=0.2)
    for j in range(1, 5):
        sh.L(X(0), Y(j * 600), X(W), Y(j * 600), '#e6edf1', w=0.2)

    # 镜柜
    sh.R(X(230), Y(1150), 640 * k, 330 * k, fill='#eef6fb', stroke=INK, sw=0.35, dash='4,2')
    sh.T(X(550), Y(1330), '镜柜 640×800', size=1.9, color=MID, anchor='middle')
    # 台盆
    sh.R(X(150), Y(1600), 800 * k, 150 * k, fill='#eaf6fb', stroke=INK, sw=0.4)
    sh.T(X(550), Y(1550), '台盆 800 / 台面高 800', size=1.9, color=MID, anchor='middle')
    # 马桶
    sh.R(X(1250), Y(1560), 450 * k, 460 * k, fill='#f2f4f6', stroke=INK, sw=0.35, dash='4,2')
    sh.T(X(1475), Y(1820), '隐藏水箱', size=1.8, color=MID, anchor='middle')
    sh.R(X(1250), Y(2020), 450 * k, 380 * k, fill='#eaf6fb', stroke=INK, sw=0.4)
    sh.T(X(1475), Y(2240), '壁挂马桶', size=1.9, color=MID, anchor='middle')

    # 尺寸
    sh.L(X(0), Y(0), X(-38), Y(0), MID, w=0.2)
    sh.L(X(0), Y(2400), X(-38), Y(2400), MID, w=0.2)
    sh.L(X(-30), Y(0), X(-30), Y(2400), MID, w=0.25)
    sh.T(X(-36), Y(1200), '2400', size=2.0, color=MID, anchor='middle', rot=90)
    sh.L(X(0), Y(1600), X(-30), Y(1600), MID, w=0.2)
    sh.T(X(-36), Y(1840), '800', size=1.9, color=MID, anchor='middle', rot=90)
    sh.L(X(0), Y(2420), X(0), Y(2450), MID, w=0.2)
    sh.T(X(0), Y(2470), '±0.000', size=1.9, color=MID, anchor='middle')
    sh.T(X(W / 2), Y(-8), '北墙立面 2100', size=2.2, color=MID, anchor='middle')

    # ---------- 东墙立面 1:25 ----------
    ox2, oy2, k2 = 186, 38, 1 / 25
    W2, H2 = 1800 * k2, 2400 * k2

    def X2(v): return ox2 + v * k2
    def Y2(v): return oy2 + v * k2

    sh.R(X2(0), Y2(0), W2, H2, fill='#fcfdfd', stroke=INK, sw=0.5)
    # 玻璃砖 190x190 区域
    sh.R(X2(400), Y2(900), 1000 * k2, 1200 * k2, fill='#eaf4fa', stroke=WIN, sw=0.4)
    for i in range(1, 6):
        sh.L(X2(400 + i * 190), Y2(900), X2(400 + i * 190), Y2(2100), '#9ec9e6', w=0.2)
    for j in range(1, 7):
        sh.L(X2(400), Y2(900 + j * 190), X2(1400), Y2(900 + j * 190), '#9ec9e6', w=0.2)
    sh.T(X2(900), Y2(2180), '玻璃砖 190×190（1000×1200）', size=1.75, color=WIN, anchor='middle')
    sh.T(X2(900), Y2(2260), '借主卧东窗光 · 非外墙开洞', size=1.7, color=MID, anchor='middle')
    # 淋浴位
    sh.R(X2(60), Y2(600), 260 * k2, 1400 * k2, fill='#f4f8fb', stroke='#b9c7d2', sw=0.3, dash='4,2')
    sh.T(X2(190), Y2(1250), '淋浴位', size=1.7, color=MID, anchor='middle', rot=90)
    sh.T(X2(W2 / 2), Y2(-8), '东墙立面 1800', size=2.2, color=MID, anchor='middle')

    # ---------- 大样 1:18 ----------
    ox3, oy3, k3 = 26, 196, 1 / 18

    def X3(v): return ox3 + v * k3
    def Y3(v): return oy3 + v * k3

    # 结构墙
    sh.R(X3(0), Y3(0), 120 * k3, 1200 * k3, fill='url(#h45)', stroke=INK, sw=0.4)
    # 隐藏水箱
    sh.R(X3(120), Y3(500), 200 * k3, 600 * k3, fill='#eef0f2', stroke=INK, sw=0.4)
    sh.T(X3(220), Y3(820), '隐藏水箱', size=1.7, color=MID, anchor='middle', rot=90)
    # 支架
    sh.L(X3(120), Y3(560), X3(0), Y3(560), INK, w=0.8)
    sh.L(X3(120), Y3(1040), X3(0), Y3(1040), INK, w=0.8)
    # 楼板
    sh.R(X3(0), Y3(1200), 1400 * k3, 80 * k3, fill='url(#grain)', stroke=INK, sw=0.4)
    sh.T(X3(700), Y3(1330), '结构楼板（不得开洞）', size=1.9, color=MID, anchor='middle')
    # 立管
    sh.L(X3(430), Y3(100), X3(430), Y3(1200), INK, w=2.0)
    sh.T(X3(470), Y3(320), 'DN110 立管', size=1.8, color=MID)
    # 横管
    sh.L(X3(320), Y3(1100), X3(430), Y3(1100), INK, w=1.4)
    sh.T(X3(200), Y3(1180), 'DN110 横管 0m · i=1.5%', size=1.7, color=MID)
    # 尺寸
    sh.L(X3(120), Y3(1420), X3(430), Y3(1420), MID, w=0.25)
    sh.T(X3(275), Y3(1480), '≥300 墙排净距', size=1.7, color=MID, anchor='middle')

    # ---------- 文字 ----------
    sh.T(272, 38, '卫2 做法说明', size=3.0, weight='bold')
    sh.TB(272, 47, [
        '1. 卫2 为暗卫：无外墙窗，机械排风 + 玻璃砖借光。',
        '2. 东墙内侧 1000×1200 做玻璃砖（190×190），',
        '   借主卧东窗漫射光；仅内隔，不得外墙开洞。',
        '3. 墙排马桶：隐藏水箱嵌入 200 厚砌体墙，',
        '   排水横管 0m 直落原 DN110 立管，不抬地坪。',
        '4. 地面 1.5% 坡向地漏，防水上返 1800，闭水 48h。',
        '5. 排风 Φ100 经吊顶接东外墙百叶，≥120m³/h，',
        '   延时开关 5 分钟。',
        '6. 吊顶铝扣板 300×300，H=2400，检修口对水箱。',
    ], size=2.25, lh=5.1, color=MID)

    sh.T(272, 108, '材料', size=2.9, weight='bold')
    sh.TB(272, 116, [
        '墙砖 300×600 哑光浅灰，竖贴',
        '地砖 300×300 防滑深灰',
        '吊顶 铝扣板 300×300 白色',
        '五金 黑色哑光（龙头/花洒/挂钩）',
        '玻璃砖 190×190 透明',
    ], size=2.25, lh=5.0, color=MID)

    sh.T(272, 150, '节点要点', size=2.9, weight='bold')
    sh.TB(272, 158, [
        '· 水箱支架固定于结构墙，不得固定于',
        '  轻钢龙骨墙；',
        '· 墙排管 DN110，接立管用异径三通 + 45° 弯；',
        '· 水箱检修口 400×400，与吊顶检修口对齐；',
        '· 坐便器完成面距地 1050。',
    ], size=2.25, lh=5.0, color=MID)

    sh.L(272, 196, 408, 196, '#e6e6e6', w=0.3)
    sh.T(272, 204, '注：立面瓷砖排版按 300 竖缝、600 横缝；', size=2.25, color=NEW)
    sh.T(272, 211, '实际排砖以现场尺寸为准，避免出现小于 150 的碎砖。', size=2.25, color=NEW)
    return sh


# ---------- 软装 ----------
SOFT = [
    ('C1', '卧室A 亚麻遮光帘', '米白 · 双层', 1550, 220),
    ('C2', '卧室C 棉麻纱帘', '奶咖 · 双层', 3800, 480),
    ('C3', '主卧B 遮光帘', '浅灰 · 双层', 2500, 6600),
    ('C4', '客厅 罗马帘', '燕麦色', 2000, 2800),
    ('R1', '卧室A 短绒地毯', '1600×2300 米灰', 1600, 1500),
    ('R2', '卧室C 平织地毯', '2000×2900 暖灰', 2100, 5800),
    ('R3', '客厅 剑麻地毯', '2000×3000 原色', 2600, 3600),
    ('A1', '卧室A 装饰画', '600×800 单幅', 300, 1000),
    ('A2', '卧室C 装饰画组', '3 联 400×600', 2400, 5900),
    ('A3', '客厅 大画', '1000×1400', 4300, 3000),
    ('L1', '卧室A 床头壁灯', '黄铜 · 3000K', 1050, 900),
    ('L2', '卧室C 落地灯', '亚麻灯罩', 3700, 6200),
    ('L3', '客厅 落地灯', '黑色细杆', 600, 4400),
    ('P1', '客厅 大型绿植', '1.6m 琴叶榕', 4400, 4300),
    ('P2', '卧室C 小绿植', '虎尾兰', 3700, 5300),
    ('T1', '床品三件套', '水洗棉 · 三色', 1600, 1400),
]


def sheet_soft_plan():
    sh = Sheet('D-01', '软装布置图', '1:50', '窗帘 · 地毯 · 挂画 · 灯具')
    p = Plan(sh, 28, 34, 50)
    base(sh, p, tint=True, new=True, labels=True, dims=False, leaf=False)

    # 窗帘线
    for (x1, y1, x2, y2) in [(500, -120, 2400, -120), (400, 8520, 3300, 8520), (8520, 6200, 8520, 8300)]:
        p.line(x1, y1, x2, y2, '#b07cc6', 55)

    # 地毯
    p.rect(700, 900, 1900, 1300, fill='none', stroke='#b07cc6', sw=30, dash='12,7')
    p.rect(300, 5100, 2200, 1700, fill='none', stroke='#b07cc6', sw=30, dash='12,7')
    p.rect(1700, 3200, 2400, 1400, fill='none', stroke='#b07cc6', sw=30, dash='12,7')

    # 软装点
    for tag, name, spec, x, y in SOFT:
        if tag.startswith('C'):
            continue
        p.C(x, y, 190, fill='#fff', stroke='#b07cc6', sw=35)
        p.text(x, y + 75, tag, 1.9, color='#7d3c98', anchor='middle', weight='bold')

    legend(sh, 246, 40, [
        ('exist', '窗帘（双层，含纱）'),
        ('furn', '地毯'),
        ('socket', '挂画 / 装饰'),
        ('light', '灯具'),
    ])
    sh.T(246, 68, '软装清单', size=2.9, weight='bold')
    for i, (tag, name, spec, x, y) in enumerate(SOFT):
        yy = 76 + i * 5.6
        sh.T(246, yy, tag, size=2.2, weight='bold', color='#7d3c98')
        sh.T(253, yy, name, size=2.15)
        sh.T(286, yy, spec, size=2.0, color=MID)

    note_block(sh, 246, 172, [
        '软装原则：',
        '· 三个卧室三种情绪，不重复配色；',
        '· 全屋主色不超过 3 个（米白 / 暖灰 / 原木）；',
        '· 挂画统一细黑框，不做图案堆砌；',
        '· 灯具色温统一 3000K，禁止混色温。',
    ], width=160)
    return sh


def sheet_soft_board():
    sh = Sheet('D-02', '软装材料板与家具清单', '—', '色板 · 材质 · 清单')
    # 色板
    pal = [
        ('米白 #F5F1E8', '#F5F1E8'), ('奶咖 #E8DFD2', '#E8DFD2'), ('暖灰 #D6D2CC', '#D6D2CC'),
        ('原木 #C8A97E', '#C8A97E'), ('深灰 #6E6E6E', '#6E6E6E'), ('墨绿 #4F5F52', '#4F5F52'),
    ]
    sh.T(18, 26, '一、配色板（全屋不超过 3 主色 + 2 点缀）', size=3.0, weight='bold')
    for i, (nm, c) in enumerate(pal):
        x = 18 + i * 28
        sh.R(x, 32, 24, 24, fill=c, stroke='#d0d0d0', sw=0.35)
        sh.T(x, 60, nm, size=2.1, color=MID)

    # 材质
    sh.T(18, 74, '二、材质板', size=3.0, weight='bold')
    mats = [
        ('亚麻', '窗帘 / 抱枕', '#E7DFD3'),
        ('水洗棉', '床品', '#F2EEE6'),
        ('剑麻', '客厅地毯', '#D9C9A8'),
        ('白橡木', '家具饰面', '#D8BC93'),
        ('哑光黑', '五金 / 灯具', '#3A3A3A'),
    ]
    for i, (nm, use, c) in enumerate(mats):
        x = 18 + i * 30
        sh.R(x, 80, 26, 18, fill=c, stroke='#d0d0d0', sw=0.35)
        sh.T(x, 103, nm, size=2.2, weight='bold')
        sh.T(x, 108, use, size=2.0, color=MID)

    # 家具清单
    sh.T(18, 122, '三、家具清单（按房间）', size=3.0, weight='bold')
    rows = [
        ('A', '卧室A', '床 1500×2000', '实木框+布艺靠背', '1'),
        ('A', '卧室A', '衣柜 1500×600×2400', '白橡木饰面', '1'),
        ('A', '卧室A', '书桌 1000×550', '白橡木+黑钢腿', '1'),
        ('A', '卧室A', '床头柜 450×400', '白橡木', '1'),
        ('C', '卧室C', '床 1800×2000', '布艺软包', '1'),
        ('C', '卧室C', '衣柜 1800×600×2400', '白橡木饰面', '1'),
        ('C', '卧室C', '书桌 1000×550', '白橡木', '1'),
        ('C', '卧室C', '休闲椅', '藤编+原木', '1'),
        ('B', '主卧B', '床 1800×2000', '布艺软包', '1'),
        ('B', '主卧B', '衣柜 2000×600×2400', '白橡木饰面', '1'),
        ('B', '主卧B', '书桌 900×550', '白橡木', '1'),
        ('G', '客厅', '沙发 1500×750', '浅灰棉麻', '1'),
        ('G', '客厅', '茶几 800×400', '白橡木', '1'),
        ('G', '客厅', '餐桌 1200×800 + 4 椅', '白橡木', '1 套'),
        ('G', '客厅', '电视柜 1200×330', '白橡木', '1'),
        ('K', '厨房', '橱柜 600 深 L 型', 'PET 门板', '1 套'),
        ('K', '厨房', '冰箱 600×650', '白色', '1'),
        ('W', '卫1/卫2', '浴室柜 800/700', '防潮板+陶瓷盆', '各 1'),
        ('W', '卫1/卫2', '壁挂马桶', '隐藏水箱', '各 1'),
        ('W', '卫1/卫2', '淋浴房 900×900', '8mm 钢化+黑框', '各 1'),
    ]
    hdr = ['区', '房间', '名称 / 规格 (mm)', '材质', '数量']
    xs = [18, 26, 46, 116, 152]
    for xx, h in zip(xs, hdr):
        sh.T(xx, 130, h, size=2.3, weight='bold', color=MID)
    sh.L(18, 132, 168, 132, MID, w=0.3)
    for i, r in enumerate(rows):
        yy = 138 + i * 6.2
        if i % 2 == 0:
            sh.R(18, yy - 4.4, 150, 6.2, fill='#fafafa', stroke='none', sw=0)
        for xx, val in zip(xs, r):
            sh.T(xx, yy, val, size=2.15)

    # 灯具表
    sh.T(186, 40, '六、风格定位', size=3.0, weight='bold')
    sh.TB(186, 48, [
        '总体：暖白 + 原木极简，全屋同色温 3000K，',
        '不做跳色、不做图案墙；三间卧室三种情绪。',
        '',
        '卧室A（北向）：静谧米白——白墙 + 米白床品 +',
        '  亚麻帘，弱对比，适合长租稳定客。',
        '卧室C（南向）：暖咖 + 纱帘——木色为主，',
        '  靠阳台光做通透感，书桌正对窗。',
        '主卧B（东向）：灰调沉稳——浅灰 + 白橡木，',
        '  独卫做黑色哑光五金，拉开与次卧档次。',
        '公区：共享客厅用剑麻地毯 + 大画统一视觉，',
        '  不做主题装饰，避免合租审美冲突。',
    ], size=2.2, lh=4.8, color=MID)

    sh.T(186, 122, '四、灯具表', size=3.0, weight='bold')
    lamps = [
        ('L0', '主灯 吸顶', '3000K / 24W', '卧室×3'),
        ('L1', '床头壁灯', '3000K / 5W', '卧室×3'),
        ('L2', '落地灯', '3000K / 8W', '卧室C、客厅'),
        ('L3', '筒灯', '3000K / 7W', '客厅×4'),
        ('L4', '镜前灯', '4000K / 8W', '卫1、卫2'),
        ('L5', '厨房灯', '4000K / 18W', '厨房'),
        ('L6', '感应脚灯', '3000K / 2W', '走廊'),
    ]
    for i, (a, b, c, d) in enumerate(lamps):
        yy = 130 + i * 6.4
        sh.T(186, yy, a, size=2.2, weight='bold')
        sh.T(195, yy, b, size=2.15)
        sh.T(222, yy, c, size=2.05, color=MID)
        sh.T(254, yy, d, size=2.0, color=MID)

    # 软装预算
    sh.T(186, 180, '五、软装预算（参考）', size=3.0, weight='bold')
    budget = [
        ('窗帘 4 套', '2,400–3,600'),
        ('地毯 3 块', '1,800–3,000'),
        ('挂画 3 组', '900–1,800'),
        ('灯具 12 件', '1,600–2,800'),
        ('床品 3 套', '1,200–2,000'),
        ('绿植/摆件', '600–1,200'),
        ('合计', '8,500–14,400'),
    ]
    for i, (k, v) in enumerate(budget):
        yy = 188 + i * 6.4
        sh.T(186, yy, k, size=2.2, weight='bold' if k == '合计' else 'normal')
        sh.T(240, yy, v, size=2.15)
        sh.L(186, yy + 2.4, 270, yy + 2.4, '#eeeeee', w=0.25)

    sh.T(18, 262, '注：软装为可选层，不影响硬装验收；出租型可按"经济档"只做窗帘 + 床品 + 基础灯具（约 4,000–6,000 元）。', size=2.4, color=NEW)
    return sh


# ---------- 产品标准 ----------
def sheet_std():
    sh = Sheet('D-03', '产品配置标准与成本卡', '—', '独卫优先 · 视觉黄金三角')

    sh.T(18, 22, '一、出租单元配置标准（18 件）', size=3.0, weight='bold')
    hdr = [('组', 18), ('项目', 32), ('必配', 86), ('规格 / 说明', 96)]
    for h, x in hdr:
        sh.T(x, 30, h, size=2.25, weight='bold', color=MID)
    sh.L(18, 32, 196, 32, MID, w=0.3)
    rows = [
        ('起居', '沙发 / 单人椅', '●', '双人位 1400–1600'),
        ('起居', '茶几 / 边几', '●', '600 见方以内'),
        ('起居', '吧台兼餐桌', '●', '1500–1700×450，配 3 凳'),
        ('起居', '电视位 + 网络', '●', '网口到每一间'),
        ('起居', '遮光帘 + 纱帘', '●', '双层，落地'),
        ('卧室', '床 1.5m + 床垫', '●', '独立袋装弹簧，不用棕垫'),
        ('卧室', '通体衣柜（到顶）', '●', '600 深，挂衣 + 抽屉'),
        ('卧室', '顶柜 / 行李柜', '●', '换季收纳，最常被忽略'),
        ('卧室', '书桌 + 椅', '●', '900–1000×550，居家办公刚需'),
        ('卧室', '全身镜', '●', '门后或墙挂，提升"家"感'),
        ('厨房', '橱柜 + 台面', '●', '600 深，L 型或一字型'),
        ('厨房', '电磁灶 + 烟机', '●', '≥20m³/min，不接燃气'),
        ('厨房', '冰箱', '●', '单门 170L 起'),
        ('厨房', '水槽 + 沥水', '●', '大单槽优于双槽'),
        ('卫浴', '马桶 + 台盆 + 淋浴', '●', '干湿分离优先'),
        ('卫浴', '镜柜 + 毛巾架', '●', '收纳决定整洁度'),
        ('卫浴', '排风 + 浴霸', '●', '暗卫必配延时排风'),
        ('家电', '滚筒洗衣机', '●', '一房一台，共用是投诉源'),
    ]
    for i, r in enumerate(rows):
        yy = 38 + i * 5.5
        if i % 2 == 0:
            sh.R(18, yy - 3.9, 178, 5.5, fill='#fafafa', stroke='none', sw=0)
        sh.T(18, yy, r[0], size=2.1, color=MID)
        sh.T(32, yy, r[1], size=2.1, weight='bold')
        sh.T(86, yy, r[2], size=2.1, color=NEW)
        sh.T(96, yy, r[3], size=2.05, color=MID)

    sh.T(18, 148, '二、收纳系统（柜体编号，对应 A-03）', size=2.9, weight='bold')
    K = [
        ('K1', '卧室A 通体柜 600×1800 + 顶柜 600×200'),
        ('K2', '卧室C 通体柜 1800×600 + 顶柜；地台下 2 组抽屉'),
        ('K3', '主卧B 衣柜 2000×600 + 顶柜 2000×200'),
        ('K4', '公共 吧台兼餐桌 1600×450，台下两层储物'),
        ('K5', '厨房 L 型橱柜 600 深，含调料拉篮、转角飞碟'),
        ('K6', '走道 家政柜 600×600，放清洁工具与吸尘器'),
        ('K7', '阳台 洗衣柜 600×600，上方吊柜'),
    ]
    for i, (k, v) in enumerate(K):
        yy = 156 + i * 6.4
        sh.T(18, yy, k, size=2.15, weight='bold', color=NEW)
        sh.T(28, yy, v, size=2.05, color=MID)

    # 右栏：成本卡
    sh.T(206, 22, '三、单单元成本卡（30–35㎡）', size=2.9, weight='bold')
    cost = [
        ('墙面修补 + 可擦洗刷漆', '3,500', '5,500'),
        ('地面 SPC 通铺', '3,000', '4,500'),
        ('无主灯 + 灯带', '2,000', '3,500'),
        ('五金（龙头/花洒/门锁）', '1,200', '2,200'),
        ('厨房（橱柜/灶/烟机/槽）', '8,000', '12,000'),
        ('卫浴（洁具/淋浴/镜柜/排风）', '7,000', '10,000'),
        ('家具（床/柜/桌/沙发）', '8,000', '13,000'),
        ('家电（冰箱/洗衣机/空调）', '5,500', '8,500'),
        ('软装（窗帘/床品/挂画）', '2,500', '4,500'),
    ]
    sh.T(206, 30, '项目', size=2.1, weight='bold', color=MID)
    sh.T(292, 30, '经济档', size=2.1, weight='bold', color=MID)
    sh.T(320, 30, '标准档', size=2.1, weight='bold', color=MID)
    sh.L(206, 32, 380, 32, MID, w=0.3)
    for i, (k, a, b) in enumerate(cost):
        yy = 38 + i * 6.0
        sh.T(206, yy, k, size=2.05)
        sh.T(292, yy, a, size=2.05, color=MID)
        sh.T(320, yy, b, size=2.05, color=MID)
    sh.L(206, 93, 380, 93, INK, w=0.4)
    sh.T(206, 100, '合计 / 单元', size=2.2, weight='bold')
    sh.T(292, 100, '≈ 40,700', size=2.2, weight='bold')
    sh.T(320, 100, '≈ 63,700', size=2.2, weight='bold')
    sh.T(206, 107, '行业口径 3–5 万/套；超 6.5 万基本回不了本。', size=1.95, color=NEW)

    # 产品对比
    sh.T(206, 118, '四、三种产品对比', size=2.9, weight='bold')
    hdr2 = [('', 206), ('独卫', 240), ('租金', 260), ('改造', 292), ('回收', 326), ('门槛', 350)]
    for h, x in hdr2:
        sh.T(x, 125, h, size=2.0, weight='bold', color=MID)
    sh.L(206, 127, 400, 127, MID, w=0.3)
    comp = [
        ('A 两套独立一室户', '2', '1.70–1.85R', '19–24万', '>20年', '第二户门'),
        ('B 双主卧双卫', '2', '1.85–1.95R', '11–14万', '7–8年', '可执行'),
        ('C 三居室合租', '1', '2.10–2.20R', '12–16万', '6.5–7年', '第3间弱'),
    ]
    for i, r in enumerate(comp):
        yy = 133 + i * 10.5
        sh.R(206, yy - 5.2, 194, 9.4, fill='#fbfbfb' if i % 2 == 0 else 'none', stroke='none', sw=0)
        sh.T(206, yy, r[0], size=2.05, weight='bold')
        sh.T(240, yy, r[1], size=2.0)
        sh.T(260, yy, r[2], size=2.0)
        sh.T(292, yy, r[3], size=2.0)
        sh.T(326, yy, r[4], size=2.0)
        sh.T(350, yy, r[5], size=2.0, color=NEW if r[5] in ('第二户门', '第3间弱') else MID)

    # 五条结论
    sh.T(206, 172, '五、学习后对本项目的五条结论', size=2.9, weight='bold')
    sh.TB(206, 180, [
        '1. 独卫是刚需：全屋最多 2 个卫生间，只能做 2 个"自带卫"的单元；',
        '   第 3 间必然共享，只能按 0.55–0.60R 定价。',
        '2. 年轻人首选独立一室户，其次双主卧双卫，最后才是三房合租。',
        '3. 厨房弱化为开放小厨 / 吧台，"可以不用但不能没有"，省 1.2 万。',
        '4. 钱花在墙、地、灯：拆改为 0，灯光与五金提到与家具同级。',
        '5. 采光顺序：先借光（拆非承重 / 室内窗）、再透光（玻璃砖 / 长虹）、',
        '   后补光（镜面 / 灯带）；一律不外墙开洞。',
    ], size=2.0, lh=5.0, color=MID)

    sh.L(18, 216, 400, 216, '#e6e6e6', w=0.3)
    sh.T(18, 223, '数据锚点：苏州住宅平均租金 34.09 元/㎡·月（中指云 2026-09）｜95 后 80.4% 以通勤为首要因素（清华×贝壳 2023）', size=1.95, color=MID)
    sh.T(18, 229, '｜卧室与独卫为刚需、"厨房可以不用但不能没有"（北京 1800 份问卷）｜住房支出≤收入 30%（58 同城 2026）', size=1.95, color=MID)
    return sh


# ---------- 输出 ----------
def main():
    os.makedirs(OUTDIR, exist_ok=True)
    sheets = [
        ('T-00_图纸目录与设计说明', sheet_cover),
        ('A-01_原始结构图', sheet_orig),
        ('A-02_墙体拆改图', sheet_demol),
        ('A-03_平面布置图', sheet_furn),
        ('A-04_地面铺装图', sheet_floor),
        ('A-05_天花布置图', sheet_ceil),
        ('A-06_强弱电点位图', sheet_elec),
        ('A-07_给排水点位图', sheet_plumb),
        ('A-08_卫生间2立面与大样', sheet_elev),
        ('D-01_软装布置图', sheet_soft_plan),
        ('D-02_软装材料板与家具清单', sheet_soft_board),
        ('D-03_产品配置标准与成本卡', sheet_std),
    ]
    made = []
    for fn, builder in sheets:
        sh = builder()
        path = os.path.join(OUTDIR, fn + '.svg')
        sh.save(path)
        made.append((fn, path))
        print('OK', fn)

    # 索引页
    cards = ''.join(
        f'<a class="card" href="{fn}.svg" target="_blank"><div class="no">{fn.split("_")[0]}</div>'
        f'<div class="nm">{fn.split("_",1)[1]}</div></a>' for fn, _ in made)
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>一改多改造图纸集 · 方案深化</title>
<style>
body{{margin:0;background:#f6f4ef;font-family:"Microsoft YaHei",system-ui,sans-serif;color:#222}}
header{{padding:40px 48px 20px}} h1{{margin:0 0 8px;font-size:26px}}
p{{margin:0;color:#666;font-size:14px;line-height:1.7}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:16px;padding:24px 48px 56px}}
.card{{background:#fff;border:1px solid #e6e1d8;border-radius:10px;padding:18px;text-decoration:none;color:inherit;transition:.18s}}
.card:hover{{transform:translateY(-2px);box-shadow:0 8px 22px rgba(0,0,0,.08)}}
.no{{font-size:12px;letter-spacing:.08em;color:#c0392b;font-weight:700}}
.nm{{margin-top:6px;font-size:15px;line-height:1.5}}
.warn{{margin:0 48px 8px;padding:12px 16px;background:#fff4f2;border-left:3px solid #c0392b;font-size:13px;color:#8a2a20;line-height:1.7}}
</style></head><body>
<header><h1>一改多改造图纸集 · 方案深化（V1）</h1>
<p>苏州 · 两室两厅住宅 ｜ 2026-11-13 ｜ 共 {len(made)} 张 ｜ 比例 1:50 / 1:25 / 1:10</p></header>
<div class="warn">本册依据挂牌户型图反推几何，未经现场复尺。承重墙、立管管径、门洞尺寸、卧室B 南墙有无窗——四项核实后方可出施工图，不得直接用于施工。</div>
<div class="grid">{cards}</div>
</body></html>"""
    idx = os.path.join(OUTDIR, 'index.html')
    with open(idx, 'w', encoding='utf-8') as fh:
        fh.write(html)
    print('OK index.html')
    print('OUT:', OUTDIR)


if __name__ == '__main__':
    main()

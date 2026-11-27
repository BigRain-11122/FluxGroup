# -*- coding: utf-8 -*-
"""
解析贝壳板块页（另存的 HTML 或 cookie 抓下来的都行）
输出：挂牌清单 CSV + 板块统计（中位单价/总价段/面积段/小区榜）

用法：python Tools/house/parse_ke_sector.py [html路径]
默认扫 house/realestate/inbox/ke-*.html
"""
import csv
import glob
import os
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INBOX = os.path.join(ROOT, 'house', 'realestate', 'inbox')

PAT_LI = re.compile(r'<li class="clear">.*?(?=<li class="clear">|</ul>)', re.S)
PAT_COMM = re.compile(r'positionInfo">.*?<a[^>]*>([^<]+)</a>', re.S)
PAT_INFO = re.compile(r'<div class="houseInfo">(.*?)</div>', re.S)
PAT_PRICE = re.compile(r'totalPrice[^>]*>.*?<span[^>]*>\s*([\d,]+)\s*</span>', re.S)
PAT_PSM = re.compile(r'unitPrice[^>]*>.*?<span>\s*([\d,]+)\s*元', re.S)
PAT_TITLE = re.compile(r'<div class="title">.*?<a[^>]*>([^<]{2,60})</a>', re.S)
PAT_FOLLOW = re.compile(r'<div class="followInfo">(.*?)</div>', re.S)
PAT_AREA = re.compile(r'([\d.]+)平米')
PAT_ROOM = re.compile(r'(\d室\d厅)')
PAT_FLOOR = re.compile(r'(低楼层|中楼层|高楼层|顶层|底层|地下室)\s*\(共(\d+)层\)')


def strip(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or '')).strip()


def parse(path):
    h = open(path, encoding='utf-8', errors='ignore').read()
    rows = []
    for m in PAT_LI.finditer(h):
        c = m.group(0)
        pr = PAT_PRICE.search(c)
        info = PAT_INFO.search(c)
        if not (pr and info):
            continue
        it = strip(info.group(1))
        area = PAT_AREA.search(it)
        if not area:
            continue
        area_v = float(area.group(1))
        total = int(pr.group(1).replace(',', '')) * 10000
        psm = PAT_PSM.search(c)
        room = PAT_ROOM.search(it)
        floor = PAT_FLOOR.search(it)
        comm = PAT_COMM.search(c)
        rows.append({
            'community': strip(comm.group(1)) if comm else '',
            'title': strip(PAT_TITLE.search(c).group(1)) if PAT_TITLE.search(c) else '',
            'total_wan': round(total / 1e4, 1),
            'area': area_v,
            'psm': int(psm.group(1).replace(',', '')) if psm else round(total / area_v),
            'room': room.group(1) if room else '',
            'floor': (floor.group(1) + '/共' + floor.group(2) + '层') if floor else '',
            'follow': strip(PAT_FOLLOW.search(c).group(1)) if PAT_FOLLOW.search(c) else '',
        })
    return rows


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else ''
    files = [path] if path else sorted(glob.glob(os.path.join(INBOX, 'ke-*.html')))
    if not files:
        print(f'没有输入文件。把贝壳页面另存到：{INBOX}\\yinshanhu.html')
        return
    allrows = []
    for f in files:
        rows = parse(f)
        print(f'{os.path.basename(f)}: {len(rows)} 条')
        allrows += rows
    seen, uniq = set(), []
    for r in allrows:
        k = (r['community'], r['total_wan'], r['area'])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    if not uniq:
        print('未解析到房源：可能页面不是板块列表（登录墙/验证码）')
        return

    out = os.path.join(ROOT, 'house', 'realestate', 'ke-sector.csv')
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(uniq[0].keys()))
        w.writeheader()
        w.writerows(uniq)

    ps = [r['psm'] for r in uniq]
    tt = [r['total_wan'] for r in uniq]
    ar = [r['area'] for r in uniq]
    print(f'\n合计 {len(uniq)} 套')
    print(f'单价  中位 {statistics.median(ps):,.0f}  最低 {min(ps):,}  最高 {max(ps):,}')
    print(f'总价  中位 {statistics.median(tt):.0f} 万  最低 {min(tt):.0f}  最高 {max(tt):.0f}')
    print(f'面积  中位 {statistics.median(ar):.0f} ㎡  区间 {min(ar):.0f}–{max(ar):.0f}')

    def bucket(v, edges):
        for e in edges:
            if v <= e:
                return f'≤{e}'
        return f'>{edges[-1]}'
    for label, vals, edges in (('总价段', tt, [100, 150, 200, 300]),
                               ('面积段', ar, [70, 90, 110, 130])):
        cnt = {}
        for v in vals:
            k = bucket(v, edges)
            cnt[k] = cnt.get(k, 0) + 1
        print(f'{label}：' + '  '.join(f'{k}={v}' for k, v in sorted(cnt.items())))

    by_comm = {}
    for r in uniq:
        by_comm.setdefault(r['community'], []).append(r['psm'])
    print('\n小区榜（按在售数）：')
    for c, v in sorted(by_comm.items(), key=lambda kv: -len(kv[1]))[:12]:
        print(f'  {c[:16]:<18}{len(v):>3} 套  中位单价 {statistics.median(v):,.0f}')
    print(f'\n→ {out}')


if __name__ == '__main__':
    main()

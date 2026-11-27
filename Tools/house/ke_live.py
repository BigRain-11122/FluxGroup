# -*- coding: utf-8 -*-
"""
贝壳根页实采（苏州）：二手房 30 条 + 租房 30 条。
限流事实（2026-11-16 实测）：同一会话第二次请求即 登录/验证码；换新会话只有根页可用，
板块子路径与 pg2+ 全部被墙。故本脚本每次只取根页一页，作为"当日活样本"，不做全量。

输出：house/realestate/ke-live-<date>.csv（kind=Sale/Rent）
"""
import csv
import gzip
import http.cookiejar
import os
import re
import time
import urllib.request
from datetime import date

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def fetch(url):
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9'})
    with op.open(req, timeout=25) as r:
        raw = r.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return raw.decode('utf-8', 'ignore')


def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    return re.sub(r'\s+', ' ', s.replace('&nbsp;', ' ')).strip()


def parse_sale(h):
    out = []
    for m in re.finditer(r'<li class="clear">.*?</li>', h, re.S):
        c = m.group(0)
        href = re.search(r'href="(https://su\.ke\.com/ershoufang/(\d+)\.html)"', c)
        title = re.search(r'<div class="title">.*?<a[^>]*title="([^"]*)"', c, re.S)
        comm = re.search(r'positionInfo">.*?<a href="([^"]*/xiaoqu/[^"]*)">([^<]+)</a>', c, re.S)
        info = re.search(r'<div class="houseInfo">(.*?)</div>', c, re.S)
        total = re.search(r'class="totalPrice totalPrice2">.*?<span[^>]*>\s*([\d,]+)\s*</span>', c, re.S)
        follow = re.search(r'<div class="followInfo">(.*?)</div>', c, re.S)
        tags = [strip_tags(t) for t in re.findall(r'<span[^>]*>([^<]{2,20})</span>', c)]
        if not (total and info):
            continue
        info_t = strip_tags(info.group(1))
        area = re.search(r'([\d.]+)平米', info_t)
        room = re.search(r'(\d室\d厅)', info_t)
        floor = re.search(r'(低楼层|中楼层|高楼层|顶层|底层)\s*\(共(\d+)层\)', info_t)
        if not area:
            continue
        area_v = float(area.group(1))
        total_v = int(total.group(1).replace(',', '')) * 10000
        out.append({
            'kind': 'Sale',
            'community': (comm.group(2).strip() if comm else ''),
            'title': strip_tags(title.group(1)) if title else '',
            'total': total_v,
            'area': area_v,
            'psm': int(round(total_v / area_v)),
            'room': room.group(1) if room else '',
            'floor': floor.group(1) if floor else '',
            'built_total': floor.group(2) if floor else '',
            'follow': strip_tags(follow.group(1)) if follow else '',
            'tags': '|'.join(t for t in tags if len(t) <= 12)[:120],
            'url': href.group(1) if href else '',
            'hid': href.group(2) if href else '',
        })
    return out


def parse_rent(h):
    out = []
    for m in re.finditer(r'<div class="content__list--item"[^>]*>(.*?)(?=<div class="content__list--item"|</div>\s*</div>\s*$)', h, re.S):
        c = m.group(0)
        title = re.search(r'content__list--item--title">\s*<a[^>]*>\s*([^<]+)</a>', c, re.S)
        des = re.search(r'content__list--item--des">(.*?)</p>', c, re.S)
        price = re.search(r'content__list--item-price"><em>([\d,]+)</em>', c)
        if not (des and price):
            continue
        des_t = strip_tags(des.group(1))
        parts = [p.strip() for p in des_t.split('/') if p.strip()]
        # 形如: 工业园区-青剑湖-君地新大陆 , 50.00㎡ , 南 , 1室1厅1卫
        loc = next((p for p in parts if '-' in p), '')
        sector = loc.split('-')[1] if loc.count('-') >= 1 else ''
        district = loc.split('-')[0] if loc else ''
        comm = loc.split('-')[2] if loc.count('-') >= 2 else ''
        area = next((re.search(r'([\d.]+)㎡', p).group(1)
                     for p in parts if '㎡' in p and re.search(r'([\d.]+)㎡', p)), None)
        room = next((p for p in parts if '室' in p), '')
        if not area:
            continue
        area_v = float(area)
        rent = int(price.group(1).replace(',', ''))
        out.append({
            'kind': 'Rent',
            'community': comm,
            'title': strip_tags(title.group(1)) if title else '',
            'total': rent,
            'area': area_v,
            'psm': round(rent / area_v, 1),
            'room': room,
            'floor': '',
            'built_total': '',
            'follow': f'{district}-{sector}',
            'tags': '整租' if '整租' in (title.group(1) if title else '') else '合租/公寓',
            'url': '',
            'hid': '',
        })
    return out


def main():
    rows = []
    for kind, url, parser in (('Sale', 'https://su.ke.com/ershoufang/', parse_sale),
                              ('Rent', 'https://su.ke.com/zufang/', parse_rent)):
        try:
            h = fetch(url)
        except Exception as e:
            print(f'{kind} ERR {type(e).__name__}'); continue
        got = parser(h)
        print(f'{kind}: {len(got)} 条（页面 {len(h)}B）')
        rows.extend(got)
        time.sleep(12)

    outdir = os.path.join(ROOT, 'house', 'realestate')
    path = os.path.join(outdir, f'ke-live-{date.today():%Y%m%d}.csv')
    if rows:
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print('→', path)
    sale = [r for r in rows if r['kind'] == 'Sale']
    rent = [r for r in rows if r['kind'] == 'Rent']
    if sale:
        sale.sort(key=lambda r: r['total'])
        print('\n最低价 8 套：')
        for r in sale[:8]:
            print(f"  {r['total']/10000:>5.0f}万 {r['area']:>6.1f}㎡ {r['psm']:>6} "
                  f"{r['community'][:12]:<14}{r['room']:<7}{r['follow'][:16]:<18}{r['tags'][:16]}")
    if rent:
        rent.sort(key=lambda r: r['psm'])
        print('\n租金 元/㎡ 分布：min %.0f 中位 %.0f max %.0f' % (
            rent[0]['psm'], sorted(r['psm'] for r in rent)[len(rent)//2], rent[-1]['psm']))
        for r in rent[:6]:
            print(f"  {r['total']:>5}元/月 {r['area']:>5.1f}㎡ {r['psm']:>5}元/㎡ {r['community'][:12]:<14}{r['room']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
按板块抓取房天下小区列表（走页面内嵌的 ld+json ItemList，结构化、稳定）。

输出：house/realestate/communities-<YYYYMMDD>.csv
字段：sector, district, community, psm, rank, url

用法：
    python Tools/house/scrape_communities.py                # 全 17 板块，每板块 2 页
    python Tools/house/scrape_communities.py --pages 3
    python Tools/house/scrape_communities.py --only 郭巷
"""
import argparse
import csv
import gzip
import json
import os
import re
import time
import urllib.request
from datetime import date

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# (板块名, 区, 房天下区码, 板块码) —— 与 scrape_hot_sectors.py 一致
SECTORS = [
    ('湖东', '园区', '277', '4000'), ('玲珑', '园区', '277', '4001'),
    ('双湖', '园区', '277', '4002'), ('独墅湖', '园区', '277', '10778'),
    ('斜塘', '园区', '277', '4005'), ('青剑湖', '园区', '277', '13075'),
    ('狮山', '高新', '278', '4008'), ('科技城', '高新', '278', '13065'),
    ('平江', '姑苏', '13102', '4014'), ('双塔', '姑苏', '13102', '4020'),
    ('沧浪', '姑苏', '13102', '4023'), ('金阊', '姑苏', '13102', '4028'),
    ('郭巷', '吴中', '283', '4037'), ('城南', '吴中', '283', '4034'),
    ('太湖新城', '吴中', '283', '24391'),
    ('高铁新城', '相城', '288', '14314'), ('元和', '相城', '288', '15761'),
]

PAT_LD = re.compile(r'<script[^>]*application/ld\+json[^>]*>', re.I)


def _load_first_json(s):
    """从任意文本头部解析出第一个完整 JSON 对象（raw_decode 会正确处理嵌套）。"""
    s = s.lstrip()
    try:
        obj, _ = json.JSONDecoder().raw_decode(s)
        return obj
    except json.JSONDecodeError:
        return None


def get(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': 'https://suzhou.esf.fang.com/',
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9'})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    for enc in ('utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode('utf-8', 'ignore')


def sector_url(a, b, page):
    return f'https://suzhou.esf.fang.com/housing/{a}_{b}_0_0_0_0_{page}_0_0_0/'


def parse_items(html):
    """从 ld+json 的 ItemList 里取小区。"""
    for m in PAT_LD.finditer(html):
        d = _load_first_json(html[m.end():m.end() + 400_000])
        if not isinstance(d, dict):
            continue
        # ItemList 可能嵌在 mainEntity 下（房天下当前就是这种结构）
        elems = d.get('itemListElement') or \
            (d.get('mainEntity') or {}).get('itemListElement') or []
        if not elems:
            continue
        out = []
        for e in elems:
            it = e.get('item') or {}
            name = (it.get('name') or '').strip()
            if not name:
                continue
            off = it.get('offers') or {}
            out.append({
                'community': name,
                'psm': off.get('price') or '',
                'url': it.get('url') or '',
                'desc': (it.get('description') or '').strip(),
                'rank': e.get('position'),
            })
        return out
    return []


def load_cache(path):
    """读旧缓存：{(sector, community): row}。被限流的日子不丢已有数据。"""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            out[(r.get('sector', ''), r.get('community', ''))] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', type=int, default=2)
    ap.add_argument('--only', default='')
    ap.add_argument('--out', default='')
    ap.add_argument('--sleep', type=float, default=2.2)
    args = ap.parse_args()

    out = args.out or os.path.join(ROOT, 'house', 'realestate', 'communities-cache.csv')
    cache = load_cache(out)
    before = len(cache)
    today = f'{date.today():%Y-%m-%d}'
    added = 0
    print(f'{"板块":<9}{"页":>3}{"小区数":>7}  样例')
    for name, dist, a, b in SECTORS:
        if args.only and args.only not in name:
            continue
        got = 0
        for page in range(1, args.pages + 1):
            url = sector_url(a, b, page)
            try:
                html = get(url)
            except Exception as e:
                print(f'{name:<9}{page:>3}  ERR {type(e).__name__}: {str(e)[:50]}')
                break
            items = parse_items(html)
            if not items:
                if page == 1:
                    print(f'{name:<9}{page:>3}      0  (空壳/限流)')
                break
            for it in items:
                key = (name, it['community'])
                is_new = key not in cache
                it.update(sector=name, district=dist, last_seen=today)
                cache[key] = it
                got += 1
                if is_new:
                    added += 1
            time.sleep(args.sleep)
            if len(items) < 8:
                break
        if got:
            print(f'{name:<9}{args.pages:>3}{got:>7}  {items[-1]["community"]}')

    rows = sorted(cache.values(), key=lambda r: (r.get('sector', ''), r.get('community', '')))
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['sector', 'district', 'community', 'psm',
                                          'rank', 'url', 'desc', 'last_seen'],
                           extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print(f'\n缓存 {before} → {len(rows)} 个小区（新增 {added}）→ {out}')
    return 0 if rows else 1


if __name__ == '__main__':
    raise SystemExit(main())

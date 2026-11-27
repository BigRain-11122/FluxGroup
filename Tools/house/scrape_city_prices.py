# -*- coding: utf-8 -*-
"""
抓取房天下各城市二手房/新房参考均价（江浙沪）
输出：house/realestate/city-prices-20261116.csv
说明：仅取公开页面上的"参考均价"，带 UA、限速；失败记 N/A，不编造。
"""
import csv
import re
import time
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

CITIES = [
    ('上海', ['sh']),
    ('南京', ['nj']), ('无锡', ['wuxi']), ('徐州', ['xz']), ('常州', ['cz']),
    ('苏州', ['suzhou']), ('南通', ['nt']), ('连云港', ['lianyungang', 'lyg']),
    ('淮安', ['huaian']), ('盐城', ['yancheng', 'yc']), ('扬州', ['yz']),
    ('镇江', ['zhenjiang']), ('泰州', ['taizhou']), ('宿迁', ['suqian', 'sq']),
    ('杭州', ['hz']), ('宁波', ['nb']), ('温州', ['wenzhou', 'wz']),
    ('嘉兴', ['jx']), ('湖州', ['huzhou']), ('绍兴', ['sx']),
    ('金华', ['jinhua', 'jh']), ('衢州', ['quzhou', 'qz']),
    ('舟山', ['zhoushan', 'zs']), ('台州', ['taizhou2', 'tz', 'taizhou']),
    ('丽水', ['lishui', 'ls']),
]

PAT_ESF = re.compile(r'二手房参考均价[^0-9]{0,60}([0-9]{3,6})')
PAT_NEW = re.compile(r'新房参考均价[^0-9]{0,60}([0-9]{3,6})')
PAT_TITLE = re.compile(r'<title>(.*?)</title>', re.S)


def fetch(slug):
    url = f'https://fangjia.fang.com/{slug}/'
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    for enc in ('utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'ignore')


def main():
    rows = []
    for name, slugs in CITIES:
        got = None
        for slug in slugs:
            try:
                html = fetch(slug)
                title = PAT_TITLE.search(html)
                title = title.group(1).strip() if title else ''
                if not title.startswith(name):
                    continue
                esf = PAT_ESF.search(html)
                new = PAT_NEW.search(html)
                got = {
                    'city': name, 'slug': slug,
                    'used_price': int(esf.group(1)) if esf else '',
                    'new_price': int(new.group(1)) if new else '',
                    'page_title': title[:40],
                }
                break
            except Exception:
                continue
            finally:
                time.sleep(0.8)
        if got is None:
            got = {'city': name, 'slug': '/'.join(slugs), 'used_price': '',
                   'new_price': '', 'page_title': 'ERR no-matching-slug'}
        rows.append(got)
        print(f'{name:<5} {got["slug"]:<13} 二手 {got["used_price"] or "N/A":>7} '
              f'新房 {got["new_price"] or "N/A":>7}')

    path = 'house/realestate/city-prices-20261116.csv'
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['city', 'slug', 'used_price', 'new_price', 'page_title'])
        w.writeheader()
        w.writerows(rows)
    ok = sum(1 for r in rows if r['used_price'])
    print(f'\n成功 {ok}/{len(rows)} 个城市 → {path}')


if __name__ == '__main__':
    main()

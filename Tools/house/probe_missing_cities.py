# -*- coding: utf-8 -*-
"""探测缺失城市的可用房价页 URL"""
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
MISSING = ['连云港', '盐城', '宿迁', '温州', '金华', '台州', '丽水']
CANDS = {
    '连云港': ['lyg', 'lianyungang'],
    '盐城': ['yc', 'yancheng'],
    '宿迁': ['sq', 'suqian'],
    '温州': ['wz', 'wenzhou'],
    '金华': ['jh', 'jinhua'],
    '台州': ['tz', 'taizhou', 'taizhou2'],
    '丽水': ['ls', 'lishui'],
}
PAT = re.compile(r'二手房参考均价[^0-9]{0,60}([0-9]{3,6})')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Accept-Language': 'zh-CN,zh;q=0.9'})
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
    for enc in ('utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode('utf-8', 'ignore')


for city in MISSING:
    found = False
    for slug in CANDS[city]:
        for url in (f'https://fangjia.fang.com/{slug}/',
                    f'https://{slug}.fang.com/fangjia/'):
            try:
                h = get(url)
                t = re.search(r'<title>(.*?)</title>', h, re.S)
                t = t.group(1).strip() if t else ''
                m = PAT.search(h)
                if t.startswith(city) and m:
                    print(f'{city}: OK {url} -> {m.group(1)}')
                    found = True
                    break
            except Exception as e:
                pass
        if found:
            break
    if not found:
        print(f'{city}: 未找到可用页')

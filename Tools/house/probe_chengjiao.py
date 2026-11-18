# -*- coding: utf-8 -*-
"""探测房天下板块成交页结构"""
import gzip
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

URLS = [
    'https://suzhou.esf.fang.com/chengjiao/a0277-b04000/',
    'https://suzhou.esf.fang.com/chengjiao/a0277/',
    'https://suzhou.esf.fang.com/chengjiao/',
]


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Referer': 'https://suzhou.esf.fang.com/',
                                               'Accept-Language': 'zh-CN,zh;q=0.9'})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    for enc in ('utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode('utf-8', 'ignore')


for u in URLS:
    try:
        h = get(u)
        t = re.search(r'<title>(.*?)</title>', h, re.S)
        t = t.group(1).strip() if t else ''
        txt = re.sub(r'<script.*?</script>', ' ', h, flags=re.S)
        txt = re.sub(r'<[^>]+>', ' ', txt)
        txt = re.sub(r'\s+', ' ', txt)
        cnt = re.findall(r'共\s*([0-9,]{2,8})\s*(?:套|条|个)', txt)
        dates = re.findall(r'20\d{2}-\d{2}-\d{2}|\d{4}年\d{1,2}月', txt)
        print(f'--- {u}')
        print('title:', t[:40], '| 共X:', cnt[:3], '| 日期样本:', dates[:5])
        print('snippet:', txt[300:700])
    except Exception as e:
        print(f'--- {u} ERR {type(e).__name__}: {e}')

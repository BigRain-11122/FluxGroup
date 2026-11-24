# -*- coding: utf-8 -*-
"""从苏州住建局首页提取 存量房/成交/监测 相关链接"""
import gzip
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
BASE = 'https://zfcjj.suzhou.gov.cn/'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
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


h = get(BASE)
print('len', len(h))
links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{2,20})</a>', h)
KEY = ('存量房', '成交', '监测', '可售', '网签', '销售')
seen = set()
for href, text in links:
    t = text.strip()
    if any(k in t for k in KEY) and (href, t) not in seen:
        seen.add((href, t))
        full = href if href.startswith('http') else BASE.rstrip('/') + '/' + href.lstrip('./')
        print(f'{t:<12} -> {full}')

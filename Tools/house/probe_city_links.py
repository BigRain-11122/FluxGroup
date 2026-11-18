# -*- coding: utf-8 -*-
"""探测房天下城市房价页的真实链接（从苏州页提取）"""
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Accept-Language': 'zh-CN,zh;q=0.9'})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    for enc in ('utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'ignore')


html = fetch('https://fangjia.fang.com/suzhou/')
print('len', len(html))
pairs = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{2,8}房价)</a>', html)
seen = {}
for href, text in pairs:
    city = text.replace('房价', '')
    seen.setdefault(city, href)
for city, href in seen.items():
    print(city, '->', href)
print('total', len(seen))

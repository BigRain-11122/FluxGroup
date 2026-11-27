# -*- coding: utf-8 -*-
"""一次性探测苏州主流平台的二手成交页，看哪个能拿到真实成交（含价格）。"""
import gzip
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

CANDIDATES = [
    ('链家', 'https://sz.lianjia.com/chengjiao/'),
    ('我爱我家-a', 'https://sz.5i5j.com/chengjiao/'),
    ('我爱我家-b', 'https://www.5i5j.com/chengjiao/'),
    ('安居客', 'https://suzhou.anjuke.com/sale/'),
    ('诸葛找房', 'https://suzhou.zhuge.com/'),
    ('58同城', 'https://suzhou.58.com/ershoufang/'),
    ('幸福里', 'https://www.xingfuli.com/'),
]


def get(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        raw, status = r.read(), r.status
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    for enc in ('utf-8', 'gb18030'):
        try:
            return status, raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return status, raw.decode('utf-8', 'ignore')


for name, url in CANDIDATES:
    try:
        st, h = get(url)
        t = re.search(r'<title>(.*?)</title>', h, re.S)
        title = re.sub(r'\s+', '', t.group(1))[:28] if t else ''
        txt = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S | re.I)
        txt = re.sub(r'<[^>]+>', ' ', txt)
        txt = re.sub(r'\s+', ' ', txt)
        price = re.findall(r'(\d{4,6})\s*元/平', txt)[:4]
        wan = re.findall(r'(\d{2,4})\s*万', txt)[:4]
        date = re.findall(r'20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}', txt)[:3]
        cnt = re.findall(r'共\s*([0-9,]{2,8})\s*(?:套|条)', txt)[:2]
        print(f'[{name}] HTTP {st} len={len(h)} title={title!r}')
        print(f'    单价={price} 总价万={wan} 日期={date} 共X={cnt}')
    except Exception as e:
        print(f'[{name}] ERR {type(e).__name__}: {str(e)[:110]}')

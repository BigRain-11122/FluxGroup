# -*- coding: utf-8 -*-
"""探测我爱我家/房天下 二手成交页：是否可拿到 小区 + 板块 + 成交日期（价格可打码）。"""
import gzip
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'


def get(url, referer=None):
    hdr = {'User-Agent': UA, 'Accept': ACCEPT, 'Accept-Language': 'zh-CN,zh;q=0.9'}
    if referer:
        hdr['Referer'] = referer
    req = urllib.request.Request(url, headers=hdr)
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
        status = r.status
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    for enc in ('utf-8', 'gb18030'):
        try:
            return status, raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return status, raw.decode('utf-8', 'ignore')


def summarize(url, html):
    title = re.search(r'<title>(.*?)</title>', html, re.S)
    title = re.sub(r'\s+', '', title.group(1)) if title else ''
    txt = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.S | re.I)
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt)
    dates = re.findall(r'20\d{2}-\d{2}-\d{2}', txt)
    months = re.findall(r'20\d{2}年\d{1,2}月', txt)
    counts = re.findall(r'共\s*([0-9,]{2,9})\s*(?:套|条)', txt)
    areas = re.findall(r'(\d{2,3}\.\d{1,2})\s*㎡', txt)
    total = re.findall(r'总价\s*([0-9.]{2,8})\s*万', txt)
    print(f'  title={title[:34]!r} 共X={counts[:2]} 日期={dates[:3]} 月={months[:2]} '
          f'面积样本={areas[:4]} 总价样本={total[:4]}')
    i = txt.find('成交')
    if i > 0:
        print('  snip:', txt[max(0, i - 60):i + 240])


CANDIDATES = [
    'https://suzhou.5i5j.com/chengjiao/',
    'https://suzhou.5i5j.com/chengjiao/guoxiang/',
    'https://suzhou.5i5j.com/ershoufang/chengjiao/',
    'https://suzhou.esf.fang.com/chengjiao/',
    'https://suzhou.fang.com/chengjiao/',
]

for u in CANDIDATES:
    try:
        st, h = get(u, referer='https://suzhou.5i5j.com/' if '5i5j' in u else 'https://suzhou.fang.com/')
        print(f'--- {u}  HTTP {st}  len={len(h)}')
        summarize(u, h)
    except Exception as e:
        print(f'--- {u} ERR {type(e).__name__}: {e}')

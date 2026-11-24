# -*- coding: utf-8 -*-
"""探测存量房即时成交页是否支持日期参数（历史查询）"""
import gzip
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
BASE = 'http://clf.zfcjj.suzhou.gov.cn/'


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


h = get(BASE + 'xsinfo.aspx')
print('len', len(h))
print('--- forms ---')
for m in re.finditer(r'<form[^>]*>', h):
    print(m.group(0)[:200])
print('--- inputs ---')
for m in re.finditer(r'<input[^>]*>', h):
    s = m.group(0)
    if 'hidden' in s and 'VIEWSTATE' in s:
        continue
    print(s[:200])
print('--- links (含日期/查询/成交) ---')
for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{0,20})</a>', h):
    if any(k in text for k in ('日期', '查询', '成交', '历史', '备案')):
        print(text.strip(), '->', href)
print('--- 页面关键文本 ---')
txt = re.sub(r'<script.*?</script>', ' ', h, flags=re.S)
txt = re.sub(r'<[^>]+>', ' ', txt)
txt = re.sub(r'\s+', ' ', txt)
print(txt[:800])

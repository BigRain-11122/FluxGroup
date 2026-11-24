# -*- coding: utf-8 -*-
"""尹山湖板块：试移动端与带 Referer 的取法"""
import gzip
import http.cookiejar
import re
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
MUA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 '
       '(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')


def fetch(url, ua=UA, ref=''):
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    hdr = {'User-Agent': ua, 'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
           'Accept-Language': 'zh-CN,zh;q=0.9'}
    if ref:
        hdr['Referer'] = ref
    req = urllib.request.Request(url, headers=hdr)
    try:
        with op.open(req, timeout=25) as r:
            raw, final = r.read(), r.geturl()
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        return final, raw.decode('utf-8', 'ignore')
    except Exception as e:
        return '', f'__ERR__{type(e).__name__}'


TRIES = [
    ('PC+Referer', 'https://su.ke.com/ershoufang/yinshanhu/',
     UA, 'https://su.ke.com/ershoufang/'),
    ('移动端', 'https://m.ke.com/su/ershoufang/yinshanhu/', MUA, ''),
    ('移动端根', 'https://m.ke.com/su/ershoufang/', MUA, ''),
    ('PC 带查询串', 'https://su.ke.com/ershoufang/yinshanhu/?from=singlemessage',
     UA, 'https://su.ke.com/'),
]

for tag, url, ua, ref in TRIES:
    final, h = fetch(url, ua, ref)
    if h.startswith('__ERR__'):
        print(f'[{tag}] {h}')
        time.sleep(5)
        continue
    t = re.search(r'<title>(.*?)</title>', h, re.S)
    print(f'[{tag}] len={len(h)} 挂牌={h.count("totalPrice")} '
          f'final={(final or "")[:48]!r} title={(t.group(1).strip()[:26] if t else "")!r}')
    time.sleep(6)

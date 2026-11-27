# -*- coding: utf-8 -*-
"""贝壳板块页探测：郭巷/吴中 各种入口"""
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

URLS = [
    ('板块slug', 'https://su.ke.com/ershoufang/guoxiang/'),
    ('区+板块', 'https://su.ke.com/ershoufang/wuzhongqu/guoxiang/'),
    ('小区频道', 'https://su.ke.com/xiaoqu/guoxiang/'),
    ('房价行情', 'https://su.ke.com/fangjia/'),
    ('板块行情', 'https://su.ke.com/fangjia/guoxiang/'),
    ('成交频道', 'https://su.ke.com/chengjiao/guoxiang/'),
]


def fetch(url):
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9'})
    try:
        with op.open(req, timeout=25) as r:
            raw = r.read()
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        return raw.decode('utf-8', 'ignore')
    except Exception as e:
        return f'__ERR__{type(e).__name__}'


for tag, url in URLS:
    h = fetch(url)
    if h.startswith('__ERR__'):
        print(f'[{tag}] {h}')
        time.sleep(6)
        continue
    t = re.search(r'<title>(.*?)</title>', h, re.S)
    t = t.group(1).strip()[:34] if t else ''
    n = h.count('class="totalPrice')
    print(f'[{tag}] len={len(h)} 挂牌={n} title={t!r} '
          f'状态={"CAPTCHA" if "CAPTCHA" in h[:4000] else ("登录墙" if "登录" in h[:4000] and len(h) < 5000 else "OK")}')
    time.sleep(9)

# -*- coding: utf-8 -*-
"""
贝壳登录 + 尹山湖板块取数（凭据只从环境变量读，绝不落盘）

用法（凭据不写进文件）：
  $env:KE_USER='xxx'; $env:KE_PWD='xxx'; python Tools/house/ke_login.py
"""
import gzip
import http.cookiejar
import os
import re
import sys
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
CJ = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CJ))


def get(url, data=None, ref=''):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={
        'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,application/json,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9', **({'Referer': ref} if ref else {})})
    try:
        with OPENER.open(req, timeout=25) as r:
            raw, code, final = r.read(), r.status, r.geturl()
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        return code, final, raw.decode('utf-8', 'ignore')
    except Exception as e:
        return 0, '', f'__ERR__{type(e).__name__}:{e}'


print('--- 1. 登录页 ---')
code, final, h = get('https://su.ke.com/login/')
print('status', code, 'final', final, 'len', len(h))
for kw in ('captcha', 'verify', '图形', '短信', 'password', 'username', 'action='):
    print(f'  {kw}: {h.count(kw)}')
m = re.search(r'<form[^>]*action="([^"]+)"[^>]*>', h)
print('form action:', m.group(1) if m else 'N/A')
for mm in re.finditer(r'<input[^>]*name="([^"]+)"[^>]*>', h):
    print('  input:', mm.group(1))

user = os.environ.get('KE_USER', '').strip()
pwd = os.environ.get('KE_PWD', '').strip()
if not (user and pwd):
    print('\n[无凭据] 只做了登录页探测')
    sys.exit(0)

print('\n--- 2. 尝试登录 ---')
code, final, h = get('https://su.ke.com/login/', data={
    'username': user, 'password': pwd, 'type': 'password'}, ref='https://su.ke.com/login/')
print('status', code, 'final', final, 'len', len(h))
print('has_login_word:', '登录' in h[:3000], '| captcha:', 'captcha' in h.lower())
print('snippet:', re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h[:600]))[:300])

print('\n--- 3. 登录后访问尹山湖板块 ---')
for tag, url in (('尹山湖', 'https://su.ke.com/ershoufang/yinshanhu/'),
                 ('尹山湖2', 'https://su.ke.com/ershoufang/wuzhongqu/yinshanhu/'),
                 ('郭巷', 'https://su.ke.com/ershoufang/guoxiang/')):
    code, final, h2 = get(url, ref='https://su.ke.com/')
    t = re.search(r'<title>(.*?)</title>', h2, re.S)
    print(f'[{tag}] {code} len={len(h2)} 挂牌={h2.count("class=\"totalPrice")} '
          f'title={(t.group(1).strip()[:28] if t else "")!r}')

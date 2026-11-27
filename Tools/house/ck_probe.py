# -*- coding: utf-8 -*-
"""清点浏览器 cookie 库存：哪些 profile 有 ke.com cookie、加密前缀是什么"""
import glob
import os
import sqlite3
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

LOCAL = os.environ.get('LOCALAPPDATA', '')
CANDIDATES = []
for name, base in (('Chrome', os.path.join(LOCAL, 'Google', 'Chrome', 'User Data')),
                   ('Edge', os.path.join(LOCAL, 'Microsoft', 'Edge', 'User Data')),
                   ('Chrome2', os.path.join(LOCAL, 'Google', 'Chrome Beta', 'User Data'))):
    if not os.path.isdir(base):
        continue
    for prof in ['Default'] + [os.path.basename(p) for p in glob.glob(os.path.join(base, 'Profile*'))]:
        for sub in ('Network/Cookies', 'Cookies'):
            p = os.path.join(base, prof, sub)
            if os.path.isfile(p):
                CANDIDATES.append((name, prof, p, os.path.join(base, 'Local State')))

print(f'找到 {len(CANDIDATES)} 个 cookie 库')
for name, prof, path, state in CANDIDATES:
    tmp = os.path.join(tempfile.gettempdir(), f'_ck_{name}_{prof}.db')
    try:
        shutil.copy2(path, tmp)
        con = sqlite3.connect(tmp)
        rows = con.execute(
            "select host_key, name, length(encrypted_value), substr(encrypted_value,1,3) "
            "from cookies where host_key like '%ke.com%' or host_key like '%lianjia%'").fetchall()
        con.close()
        prefixes = {}
        for r in rows:
            prefixes[r[3]] = prefixes.get(r[3], 0) + 1
        print(f'[{name}/{prof}] ke/lianjia cookie {len(rows)} 条  前缀分布 {prefixes}')
        for r in rows[:6]:
            print(f'    {r[0]:<22}{r[1]:<26}len={r[2]}')
    except Exception as e:
        print(f'[{name}/{prof}] ERR {type(e).__name__}: {str(e)[:60]}')
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

print('\n依赖检查：')
for mod in ('cryptography', 'Crypto', 'win32crypt'):
    try:
        __import__(mod)
        print(f'  {mod}: OK')
    except Exception:
        print(f'  {mod}: 缺')

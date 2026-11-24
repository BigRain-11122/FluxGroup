# -*- coding: utf-8 -*-
"""immutable 只读打开浏览器 cookie 库（绕开 Chrome 独占锁），解 v10 后抓尹山湖板块"""
import base64
import ctypes
import glob
import json
import os
import sqlite3
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

LOCAL = os.environ.get('LOCALAPPDATA', '')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')


def dpapi_unprotect(data):
    class BLOB(ctypes.Structure):
        _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.POINTER(ctypes.c_char))]
    bi = ctypes.create_string_buffer(data, len(data))
    blob_in = BLOB(len(data), ctypes.cast(bi, ctypes.POINTER(ctypes.c_char)))
    blob_out = BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise OSError('DPAPI fail')
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def aes_key(state_path):
    st = json.load(open(state_path, encoding='utf-8'))
    enc = base64.b64decode(st['os_crypt']['encrypted_key'])
    return dpapi_unprotect(enc[5:])


def dec(key, blob):
    if blob[:3] == b'v10':
        return AESGCM(key).decrypt(bytes(blob[3:15]), bytes(blob[15:]), None).decode()
    if blob[:3] == b'v20':
        raise ValueError('App-Bound(v20)')
    return blob.decode('utf-8', 'ignore')


def main():
    bases = [('Chrome', os.path.join(LOCAL, 'Google', 'Chrome', 'User Data')),
             ('Edge', os.path.join(LOCAL, 'Microsoft', 'Edge', 'User Data'))]
    picked = {}
    for name, base in bases:
        if not os.path.isdir(base):
            continue
        sp = os.path.join(base, 'Local State')
        if not os.path.isfile(sp):
            continue
        try:
            key = aes_key(sp)
        except Exception as e:
            print(f'[{name}] 取 key 失败 {e}')
            continue
        profs = ['Default'] + [os.path.basename(p) for p in glob.glob(os.path.join(base, 'Profile*'))]
        for prof in profs:
            db = None
            for sub in ('Network/Cookies', 'Cookies'):
                p = os.path.join(base, prof, sub)
                if os.path.isfile(p):
                    db = p
                    break
            if not db:
                continue
            uri = 'file:' + db.replace('\\', '/') + '?immutable=1'
            try:
                con = sqlite3.connect(uri, uri=True)
                rows = con.execute(
                    "select host_key,name,encrypted_value from cookies "
                    "where host_key like '%ke.com%' or host_key like '%lianjia%'").fetchall()
                con.close()
            except Exception:
                # 回退：复制到临时目录再打开（浏览器已关闭时可用）
                import shutil, tempfile
                tmp = os.path.join(tempfile.gettempdir(), f'_kec_{abs(hash(db))}.db')
                try:
                    shutil.copy2(db, tmp)
                    con = sqlite3.connect(tmp)
                    rows = con.execute(
                        "select host_key,name,encrypted_value from cookies "
                        "where host_key like '%ke.com%' or host_key like '%lianjia%'").fetchall()
                    con.close()
                    print(f'[{name}/{prof}] （复制模式读取成功）')
                except Exception as e2:
                    print(f'[{name}/{prof}] 打开失败 {type(e2).__name__}: {str(e2)[:50]}')
                    continue
                finally:
                    if os.path.exists(tmp):
                        os.remove(tmp)
            ok, bad = 0, {}
            for host, cn, blob in rows:
                try:
                    v = dec(key, blob)
                    if cn and v:
                        picked[cn] = v
                        ok += 1
                except Exception as e:
                    bad[str(e)[:16]] = bad.get(str(e)[:16], 0) + 1
            print(f'[{name}/{prof}] 命中 {len(rows)}，解密 {ok}，异常 {bad}')

    print('cookie 名：', sorted(picked)[:16], f'共 {len(picked)}')
    if not picked:
        return

    hdr = '; '.join(f'{k}={v}' for k, v in picked.items())
    out = os.path.join(os.path.dirname(__file__), '..', '..', 'house', 'realestate', 'inbox')
    os.makedirs(out, exist_ok=True)
    for tag, url in (('yinshanhu', 'https://su.ke.com/ershoufang/yinshanhu/'),
                     ('yinshanhu-pg2', 'https://su.ke.com/ershoufang/yinshanhu/pg2/')):
        req = urllib.request.Request(url, headers={
            'User-Agent': UA, 'Cookie': hdr, 'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9', 'Referer': 'https://su.ke.com/ershoufang/'})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                raw, final = r.read(), r.geturl()
            if raw[:2] == b'\x1f\x8b':
                import gzip
                raw = gzip.decompress(raw)
            h = raw.decode('utf-8', 'ignore')
            fp = os.path.join(out, f'ke-{tag}.html')
            open(fp, 'w', encoding='utf-8').write(h)
            print(f'[{tag}] {len(h)}B 挂牌={h.count("totalPrice")} final={final[:36]} -> {fp}')
        except Exception as e:
            print(f'[{tag}] 失败 {type(e).__name__}: {str(e)[:60]}')


if __name__ == '__main__':
    main()

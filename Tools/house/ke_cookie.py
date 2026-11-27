# -*- coding: utf-8 -*-
"""
读本机 Chrome 的 ke.com cookie（只读、只取 ke/lianjia 域），并用它抓尹山湖板块页。
安全：不打印任何 cookie 值；临时库读完即删；只访问 su.ke.com。
"""
import base64
import ctypes
import glob
import json
import os
import sqlite3
import struct
import sys
import tempfile
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

LOCAL = os.environ.get('LOCALAPPDATA', '')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')
GENERIC_READ = 0x80000000
SHARE_ALL = 0x1 | 0x2 | 0x4
OPEN_EXISTING = 3
FILE_ATTR_NORMAL = 0x80


def copy_shared(src, dst):
    """用共享读句柄复制被浏览器占用的文件"""
    k32 = ctypes.windll.kernel32
    h = k32.CreateFileW(ctypes.c_wchar_p(src), GENERIC_READ, SHARE_ALL, None,
                        OPEN_EXISTING, FILE_ATTR_NORMAL, None)
    if h == -1 or h == 0xFFFFFFFFFFFFFFFF:
        raise OSError(f'CreateFile failed: {ctypes.GetLastError()}')
    try:
        buf = bytearray()
        chunk = ctypes.create_string_buffer(1 << 20)
        read = ctypes.c_ulong(0)
        while True:
            ok = k32.ReadFile(h, chunk, 1 << 20, ctypes.byref(read), None)
            if not ok or read.value == 0:
                break
            buf += chunk.raw[:read.value]
        with open(dst, 'wb') as f:
            f.write(bytes(buf))
    finally:
        k32.CloseHandle(h)
    return len(buf)


def dpapi_unprotect(data):
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.POINTER(ctypes.c_char))]
    buf_in = ctypes.create_string_buffer(data, len(data))
    blob_in = DATA_BLOB(len(data), ctypes.cast(buf_in, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out))
    if not ok:
        raise OSError('DPAPI 解密失败')
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def get_aes_key(state_path):
    st = json.load(open(state_path, encoding='utf-8'))
    enc = base64.b64decode(st['os_crypt']['encrypted_key'])
    if enc[:5] != b'DPAPI':
        raise ValueError('encrypted_key 前缀异常')
    return dpapi_unprotect(enc[5:])


def decrypt_value(key, blob):
    if blob[:3] == b'v10':
        nonce, payload = blob[3:15], blob[15:]
        return AESGCM(key).decrypt(nonce, payload, None).decode('utf-8', 'ignore')
    if blob[:3] == b'v20':
        raise ValueError('v20(App-Bound) 加密，需浏览器导出')
    # 未加密
    return blob.decode('utf-8', 'ignore')


def main():
    base = os.path.join(LOCAL, 'Google', 'Chrome', 'User Data')
    profs = ['Default'] + [os.path.basename(p) for p in glob.glob(os.path.join(base, 'Profile*'))]
    key = get_aes_key(os.path.join(base, 'Local State'))
    print('AES key 取得（长度 %d）' % len(key))

    picked = {}
    for prof in profs:
        src = None
        for sub in ('Network/Cookies', 'Cookies'):
            p = os.path.join(base, prof, sub)
            if os.path.isfile(p):
                src = p
                break
        if not src:
            continue
        tmp = os.path.join(tempfile.gettempdir(), f'_ck_{prof.replace(" ", "")}.db')
        try:
            n = copy_shared(src, tmp)
        except OSError as e:
            print(f'[{prof}] 复制失败 {e}')
            continue
        try:
            con = sqlite3.connect(tmp)
            rows = con.execute(
                "select host_key,name,encrypted_value from cookies "
                "where host_key like '%ke.com%' or host_key like '%lianjia%'").fetchall()
            con.close()
            ok = 0
            for host, name, blob in rows:
                try:
                    v = decrypt_value(key, blob)
                except Exception:
                    continue
                if name and v:
                    picked[name] = v
                    ok += 1
            print(f'[{prof}] 匹配 {len(rows)} 条，解密成功 {ok} 条')
        except Exception as e:
            print(f'[{prof}] 读取失败 {type(e).__name__}: {str(e)[:60]}')
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    print('可用 cookie 名：', sorted(picked)[:14], f'…共 {len(picked)} 个')
    if not picked:
        print('没有可用 cookie，退出')
        return

    cookie_hdr = '; '.join(f'{k}={v}' for k, v in picked.items())
    targets = [('尹山湖', 'https://su.ke.com/ershoufang/yinshanhu/'),
               ('尹山湖pg2', 'https://su.ke.com/ershoufang/yinshanhu/pg2/')]
    outdir = os.path.join(os.path.dirname(__file__), '..', '..', 'house', 'realestate', 'inbox')
    os.makedirs(outdir, exist_ok=True)
    for tag, url in targets:
        req = urllib.request.Request(url, headers={
            'User-Agent': UA, 'Cookie': cookie_hdr,
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://su.ke.com/ershoufang/'})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                raw, final = r.read(), r.geturl()
            if raw[:2] == b'\x1f\x8b':
                import gzip
                raw = gzip.decompress(raw)
            h = raw.decode('utf-8', 'ignore')
            path = os.path.join(outdir, f'ke-{tag}.html')
            open(path, 'w', encoding='utf-8').write(h)
            print(f'[{tag}] {len(h)}B 挂牌={h.count("totalPrice")} final={final[:40]} -> {path}')
        except Exception as e:
            print(f'[{tag}] 取数失败 {type(e).__name__}: {str(e)[:70]}')


if __name__ == '__main__':
    main()

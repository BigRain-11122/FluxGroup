# -*- coding: utf-8 -*-
"""下载收尾看门狗：等 seg_dl 退出后，若最终文件坏（0 字节/头不对）就从分段抢救拼接。

为什么要它：seg_dl 的拼接阶段有已知 bug（worker 吃空段列表 → 产出 0 字节），
本次 8.27GB 的文本编码器就是这么坏过一次，靠 join_parts 救回、没重下。
大权重（24.5GB）下完时人不一定在，所以把「验坏即拼」这一步挂成看门狗。

用法（pythonw 隐藏启动）：
  pythonw watch_join_parts.py --target <out.safetensors> [--max-wait 3]
"""
import argparse, json, os, struct, subprocess, sys, time

PY = r'C:\Users\Dasheng\AppData\Local\Programs\Python\Python313\python.exe'
JOIN = r'K:\Fluxgroup\.tools\dl\join_parts.py'
LOG = None


def log(*a):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a)
    print(line, flush=True)
    if LOG:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')


def dl_alive(target):
    import psutil
    key = os.path.basename(target)
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            nm = (p.info.get('name') or '').lower()
            if not nm.startswith('python'):
                continue
            cl = ' '.join(p.info.get('cmdline') or [])
            if 'seg_dl' in cl and key in cl:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def ok(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read(8)
            if len(raw) != 8:
                return False, 'short %d' % len(raw)
            n = struct.unpack('<Q', raw)[0]
            hdr = json.loads(f.read(n))
            total = max(v['data_offsets'][1] for k, v in hdr.items() if k != '__metadata__')
        need = 8 + n + total
        got = os.path.getsize(path)
        return got == need, 'got=%d need=%d' % (got, need)
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:80]


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', required=True)
    ap.add_argument('--log', default=r'K:\Fluxgroup\.codely-cli\tmp\watch-join.log')
    ap.add_argument('--max-wait', type=float, default=3.0)
    a = ap.parse_args()
    LOG = a.log
    log('watch start for %s' % os.path.basename(a.target))
    t0 = time.time()
    while dl_alive(a.target):
        if time.time() - t0 > a.max_wait * 3600:
            log('TIMEOUT 等下载超时')
            return 2
        time.sleep(45)
    good, why = ok(a.target)
    log('download finished; verify=%s (%s)' % ('OK' if good else 'BAD', why))
    if good:
        return 0
    parts = a.target + '.parts'
    if not os.path.isdir(parts):
        log('NO PARTS DIR，无法抢救：%s' % parts)
        return 3
    log('joining from parts ...')
    r = subprocess.run([PY, JOIN, '--parts', parts, '--out', a.target],
                       capture_output=True, text=True)
    for ln in ((r.stdout or '') + (r.stderr or '')).strip().splitlines()[-6:]:
        log('   ' + ln[:170])
    good2, why2 = ok(a.target)
    log('after join verify=%s (%s)' % ('OK' if good2 else 'BAD', why2))
    return 0 if good2 else 4


if __name__ == '__main__':
    sys.exit(main())

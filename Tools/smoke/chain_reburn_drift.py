# -*- coding: utf-8 -*-
"""等当前批次跑完 → 按像素漂移闸挑出 DRIFT 镜 → 归档 → 用同一 manifest（已是强锁句）重烧 → 复核。

为什么写成一个链而不是手动两步：38 镜整批约 2.4 小时，跑完时人不一定在；DRIFT 镜不重烧就是
交付里带着推镜。归档而不是删除（`_archive-drift-<ts>/`）既让 runner 的 SKIP 判据失效从而重烧，
又保留证据可回溯。

用法（建议 pythonw 隐藏启动）：
  pythonw chain_reburn_drift.py [--clips <dir>] [--manifest <json>] [--log <file>]
退出码：0=无需重烧或重烧后无 DRIFT；1=仍有 DRIFT（看报告）；2=异常
"""
import argparse, glob, json, os, shutil, subprocess, sys, time

ROOT = r'K:\Fluxgroup\FluxGroup'
REEL = os.path.join(ROOT, r'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1')
CLIPS = os.path.join(REEL, 'i2v-xq3-batch')
MANIFEST = os.path.join(REEL, 'i2v-xq3-manifest.json')
RUNNER = os.path.join(ROOT, r'cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py')
QC = os.path.join(ROOT, r'Tools\smoke\qc_i2v_drift.py')
PYQ = r'D:\ComfyUI\python_embeded\python.exe'   # 只有它装了 PIL/numpy 全套
PY = r'C:\Users\Dasheng\AppData\Local\Programs\Python\Python313\python.exe'

LOG = None


def log(*a):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a)
    print(line, flush=True)
    if LOG:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')


def runner_alive():
    """用 psutil 查命令行，避免起 powershell 子进程（零窗律：会话内禁 spawn 控制台）。"""
    import psutil
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            nm = (p.info.get('name') or '').lower()
            if not nm.startswith('python'):
                continue
            cl = ' '.join(p.info.get('cmdline') or [])
            if 'h3_i2v_album' in cl:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def qc(clips):
    r = subprocess.run([PYQ, QC, clips], capture_output=True, text=True)
    txt = r.stdout or ''
    drift = []
    for ln in txt.splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[-1] == 'DRIFT':
            drift.append(parts[0])
    return drift, txt


def burn(manifest, clips, tag):
    lg = os.path.join(r'K:\Fluxgroup\.codely-cli\tmp', 'reburn-%s.log' % tag)
    log('relaunch runner ->', lg)
    p = subprocess.Popen([PY, RUNNER, '--repo', ROOT, '--lane', 'bmc',
                          '--manifest', manifest, '--out', clips],
                         cwd=ROOT, stdout=open(lg, 'w', encoding='utf-8'),
                         stderr=subprocess.STDOUT)
    log('runner pid=%d' % p.pid)
    return p


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument('--clips', default=CLIPS)
    ap.add_argument('--manifest', default=MANIFEST)
    ap.add_argument('--log', default=r'K:\Fluxgroup\.codely-cli\tmp\chain-reburn-drift.log')
    ap.add_argument('--max-wait', type=float, default=4.0, help='等当前批最长小时数')
    a = ap.parse_args()
    LOG = a.log

    log('wait-for-current-batch start')
    t0 = time.time()
    while runner_alive():
        if time.time() - t0 > a.max_wait * 3600:
            log('TIMEOUT 等批超时，放弃链')
            return 2
        time.sleep(60)
    log('current batch finished after %.0f min' % ((time.time() - t0) / 60))

    n = len(glob.glob(os.path.join(a.clips, '*.mp4')))
    log('clips on disk = %d' % n)
    drift, txt = qc(a.clips)
    log('QC pass1: drift=%d %s' % (len(drift), ','.join(drift)))

    if not drift:
        log('PASS1 CLEAN，出口')
        return 0

    arc = os.path.join(a.clips, '_archive-drift-%s' % time.strftime('%Y%m%d-%H%M%S'))
    os.makedirs(arc, exist_ok=True)
    moved = 0
    for sid in drift:
        src = os.path.join(a.clips, sid + '.mp4')
        if os.path.isfile(src):
            shutil.move(src, os.path.join(arc, sid + '.mp4'))
            moved += 1
    log('archived %d drift clips -> %s' % (moved, arc))

    p = burn(a.manifest, a.clips, time.strftime('%H%M%S'))
    p.wait()
    log('reburn runner exited rc=%s' % p.returncode)

    drift2, txt2 = qc(a.clips)
    log('QC pass2: drift=%d %s' % (len(drift2), ','.join(drift2)))
    rep = os.path.join(REEL, 'QC-DRIFT-REBURN-%s.json' % time.strftime('%Y%m%d-%H%M%S'))
    with open(rep, 'w', encoding='utf-8') as f:
        json.dump(dict(pass1=drift, pass2=drift2, archived=arc,
                       qc_pass1=txt, qc_pass2=txt2), f, ensure_ascii=False, indent=1)
    log('report -> %s' % rep)
    return 0 if not drift2 else 1


if __name__ == '__main__':
    sys.exit(main())

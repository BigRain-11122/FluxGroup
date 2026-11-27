# -*- coding: utf-8 -*-
"""等所有 GPU 链跑完 → 重烧 XQ03/XQ13 的 KF（景别治愈版）→ 过景别闸 → 再重烧这两个 i2v 镜。

背景：XQ13 的 KF 出成中远景而提示词要特写，XQ03 也一样；i2v 拿着「中远景首帧 + 要特写」的组合
自己推成特写，看起来像跳镜。病根在 KF，所以顺序必须是「先修 KF，再烧 i2v」，不能只重烧 i2v
（那样等于拿同一张坏首帧再赌一次）。

守门：动手前要求 h3_i2v_album / chain_reburn_drift / chain_cast_sheet / gen_cast_sheet / mv_kf_batch
都不在跑（连续两次确认）——避免和已挂的两条链抢卡。

闸：KF 烧完先跑 qc_kf_scale，两张都判 OK 才继续烧 i2v；不 OK 就停手报告（不盲烧）。

用法（pythonw 隐藏启动）：
  pythonw chain_kf_scale_fix.py [--max-wait 8]
"""
import argparse, glob, json, os, shutil, subprocess, sys, time

try:  # 日志走 utf-8，避免重定向到文件时中文变问号
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass

ROOT = r'K:\Fluxgroup\FluxGroup'
REEL = os.path.join(ROOT, r'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1')
KF = os.path.join(REEL, 'kf')
CLIPS = os.path.join(REEL, 'i2v-xq3-batch')
MANIFEST = os.path.join(REEL, 'i2v-xq3-manifest.json')
FIX2 = os.path.join(ROOT, r'cph4\fleet\mv0001-handover\plan\kf_prompts-fix2-20261115.json')
PROMPTS_ALL = os.path.join(ROOT, r'cph4\fleet\mv0001-handover\plan\kf_prompts.json')

PY = r'C:\Users\Dasheng\AppData\Local\Programs\Python\Python313\python.exe'
PYQ = r'D:\ComfyUI\python_embeded\python.exe'
KF_BATCH = os.path.join(ROOT, r'Tools\mv_kf_batch.py')
SCALE = os.path.join(ROOT, r'Tools\smoke\qc_kf_scale.py')
RUNNER = os.path.join(ROOT, r'cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py')
IDS_KF = ('XQ03', 'XQ13')
IDS_I2V = tuple('XQ38_' + x[2:] for x in IDS_KF)
LOG = None


def log(*a):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a)
    print(line, flush=True)
    if LOG:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')


def busy():
    import psutil
    keys = ('h3_i2v_album', 'chain_reburn_drift', 'chain_cast_sheet', 'gen_cast_sheet', 'mv_kf_batch')
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            nm = (p.info.get('name') or '').lower()
            if not nm.startswith('python'):
                continue
            cl = ' '.join(p.info.get('cmdline') or [])
            if any(k in cl for k in keys):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def scale_verdict(ids):
    """跑景别闸，返回 {id: verdict}。"""
    r = subprocess.run([PYQ, SCALE, KF, '--prompts', PROMPTS_ALL], capture_output=True, text=True)
    out = {}
    for ln in (r.stdout or '').splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[0] in ids:
            out[parts[0]] = parts[-1]
    return out


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-wait', type=float, default=8.0)
    ap.add_argument('--log', default=r'K:\Fluxgroup\.codely-cli\tmp\chain-kf-scale-fix.log')
    a = ap.parse_args()
    LOG = a.log

    log('wait-for-idle start（等其他 GPU 链跑完）')
    t0 = time.time()
    quiet = 0
    while True:
        if time.time() - t0 > a.max_wait * 3600:
            log('TIMEOUT')
            return 2
        if busy():
            quiet = 0
            time.sleep(60)
            continue
        quiet += 1
        if quiet >= 2:
            break
        time.sleep(60)
    log('idle confirmed')

    ts = time.strftime('%Y%m%d-%H%M%S')
    arc_kf = os.path.join(KF, '_archive-scale-fix-%s' % ts)
    os.makedirs(arc_kf, exist_ok=True)
    for kid in IDS_KF:
        src = os.path.join(KF, kid + '.png')
        if os.path.isfile(src):
            shutil.move(src, os.path.join(arc_kf, kid + '.png'))
            log('archived KF %s' % kid)

    log('burn KFs %s' % ','.join(IDS_KF))
    r = subprocess.run([PY, KF_BATCH, '--prompts', FIX2, '--out', KF], cwd=ROOT,
                       capture_output=True, text=True)
    for ln in ((r.stdout or '').strip().splitlines() or [])[-6:]:
        log('   kf ' + ln[:160])
    if r.returncode != 0:
        log('KF-BURN-FAIL rc=%d %s' % (r.returncode, (r.stderr or '')[-300:]))
        return 3

    v = scale_verdict(set(IDS_KF))
    log('scale verdict: %s' % v)
    if any(v.get(k) != 'OK' for k in IDS_KF):
        log('REFUSE：新 KF 未过景别闸，不烧 i2v（旧帧在 %s）' % arc_kf)
        return 4

    arc_clip = os.path.join(CLIPS, '_archive-kf-fix-%s' % ts)
    os.makedirs(arc_clip, exist_ok=True)
    for cid in IDS_I2V:
        src = os.path.join(CLIPS, cid + '.mp4')
        if os.path.isfile(src):
            shutil.move(src, os.path.join(arc_clip, cid + '.mp4'))
            log('archived clip %s' % cid)

    lg = os.path.join(r'K:\Fluxgroup\.codely-cli\tmp', 'reburn-kffix.log')
    log('relaunch runner -> %s' % lg)
    p = subprocess.Popen([PY, RUNNER, '--repo', ROOT, '--lane', 'bmc',
                          '--manifest', MANIFEST, '--out', CLIPS],
                         cwd=ROOT, stdout=open(lg, 'w', encoding='utf-8'), stderr=subprocess.STDOUT)
    p.wait()
    log('runner exited rc=%s' % p.returncode)
    n = len(glob.glob(os.path.join(CLIPS, '*.mp4')))
    log('clips on disk = %d' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())

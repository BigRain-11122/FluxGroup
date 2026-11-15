# -*- coding: utf-8 -*-
"""等 GPU 空出来 → 出两张角色设定图纸（女主/男主）→ 跑数据集体检。

为什么挂在链上：i2v 批次和重烧链要占 GPU 到 ~17:00，而 krea2 权重还要下到 ~18:00。
中间这段空窗正好拿来出设定图纸（24 张 × 约 40s ≈ 16 分钟），出完再做一次重复度体检，
这样权重一落地就能直接进 cache_latents，不浪费一晚。

守门条件（两个都满足才动手）：
  1. 没有 h3_i2v_album 在跑（主批/重烧）；
  2. 没有 chain_reburn_drift 在跑（重烧链本身）；
  3. 上面两条连续两次检查（间隔 60s）都成立——避免刚好卡在两条批的缝里插队抢卡。

用法（pythonw 隐藏启动）：
  pythonw chain_cast_sheet.py [--log <file>] [--max-wait 6]
"""
import argparse, glob, os, subprocess, sys, time

ROOT = r'K:\Fluxgroup\FluxGroup'
PY = r'C:\Users\Dasheng\AppData\Local\Programs\Python\Python313\python.exe'
GEN = os.path.join(ROOT, r'Tools\smoke\gen_cast_sheet.py')
QC = os.path.join(ROOT, r'Tools\smoke\qc_lora_dataset.py')
OUT = os.path.join(ROOT, r'media\mv0001-handover\cast-dataset')
TOKENS = {'xq_her': 'ljher', 'xq_him': 'jman'}
LOG = None


def log(*a):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a)
    print(line, flush=True)
    if LOG:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')


def busy():
    import psutil
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            nm = (p.info.get('name') or '').lower()
            if not nm.startswith('python'):
                continue
            cl = ' '.join(p.info.get('cmdline') or [])
            if 'h3_i2v_album' in cl or 'chain_reburn_drift' in cl:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', default=r'K:\Fluxgroup\.codely-cli\tmp\chain-cast-sheet.log')
    ap.add_argument('--max-wait', type=float, default=6.0, help='最长等多少小时')
    a = ap.parse_args()
    LOG = a.log

    log('wait-for-gpu start (max %.1fh)' % a.max_wait)
    t0 = time.time()
    quiet = 0
    while True:
        if time.time() - t0 > a.max_wait * 3600:
            log('TIMEOUT 等 GPU 超时，放弃')
            return 2
        if busy():
            quiet = 0
            time.sleep(60)
            continue
        quiet += 1
        if quiet >= 2:
            break
        time.sleep(60)
    log('GPU idle confirmed, start cast sheets')

    # 先把看片带和质检板做出来（纯 CPU/ffmpeg，不占卡），这样人一睁眼就有东西看
    asm = os.path.join(ROOT, r'Tools\smoke\asm_xq38.py')
    board = os.path.join(ROOT, r'Tools\smoke\qc_i2v_board.py')
    clips = os.path.join(ROOT, r'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\i2v-xq3-batch')
    n = len(glob.glob(os.path.join(clips, '*.mp4')))
    log('reel: clips on disk = %d' % n)
    if n >= 38:
        r = subprocess.run([PY, asm], cwd=ROOT, capture_output=True, text=True)
        for ln in ((r.stdout or '').strip().splitlines() or [])[-3:]:
            log('   asm ' + ln[:170])
        if r.returncode != 0:
            log('   asm rc=%d %s' % (r.returncode, (r.stderr or '')[-200:]))
    else:
        log('   跳过拼带（不足 38 镜）')
    r = subprocess.run([PY, board, clips, '--per-board', '12', '--width', '300'],
                       cwd=ROOT, capture_output=True, text=True)
    for ln in ((r.stdout or '').strip().splitlines() or [])[-4:]:
        log('   board ' + ln[:170])

    rc_all = 0
    for char in ('xq_her', 'xq_him'):
        log('burn %s' % char)
        r = subprocess.run([PY, GEN, '--char', char, '--burn'], cwd=ROOT,
                           capture_output=True, text=True)
        tail = (r.stdout or '').strip().splitlines()[-3:]
        for ln in tail:
            log('   ' + ln[:160])
        if r.returncode != 0:
            log('   %s rc=%d stderr=%s' % (char, r.returncode, (r.stderr or '')[-200:]))
            rc_all = r.returncode
        d = os.path.join(OUT, char)
        n = len(glob.glob(os.path.join(d, '*.png')))
        log('   %s images on disk = %d' % (char, n))
        q = subprocess.run([PY, QC, d, '--token', TOKENS[char]], capture_output=True, text=True)
        for ln in ((q.stdout or '').strip().splitlines() or [])[-4:]:
            log('   QC ' + ln[:160])

    log('DONE rc=%d' % rc_all)
    return rc_all


if __name__ == '__main__':
    sys.exit(main())

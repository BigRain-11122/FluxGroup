# -*- coding: utf-8 -*-
"""把 i2v 批次 manifest 的锁机位头句换成试点档那句更强的（含「framing stays exactly as the first frame」）。

依据（2026-11-15 实测）：
 - 同 KF、同 seed、同 3.0s 档，试点档（强锁句）首末帧几乎一致；整批档（弱锁句）末帧明显推近。
 - 像素闸对照：试点 XQ38_01 max_cell=40（HOLD），整批 XQ38_01 max_cell=87（DRIFT）。
所以这不是随机性，而是措辞差异；批次跑到 10/38 时停掉换词重跑，比跑完再全批重烧省一半时间。

用法：python patch_i2v_lockphrase.py [--manifest <json>] [--dry]
"""
import argparse, json, os, shutil, sys, time

DEFAULT = (r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2'
           r'\30s-reel-v1\i2v-xq3-manifest.json')

OLD = 'Single continuous take at 24fps, camera completely locked off, no zoom and no push-in.'
NEW = ('Single continuous take at 24fps, camera completely locked off with no zoom and no push-in; '
       'the framing stays exactly as the first frame.')
TAIL = ' The framing stays exactly as the first frame.'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default=DEFAULT)
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    d = json.load(open(a.manifest, encoding='utf-8'))
    units = d['units']
    hit = 0
    for u in units:
        p = u.get('i2v_prompt', '')
        if OLD in p:
            p = p.replace(OLD, NEW, 1)
            hit += 1
        if 'the framing stays exactly as the first frame' not in p.lower():
            p = p.rstrip() + TAIL
        u['i2v_prompt'] = p
    print('units=%d  head-replaced=%d' % (len(units), hit))
    if a.dry:
        print('\nSAMPLE:\n' + units[0]['i2v_prompt'][:260])
        return 0
    bak = a.manifest + '.bak-%s' % time.strftime('%Y%m%d-%H%M%S')
    shutil.copy2(a.manifest, bak)
    with open(a.manifest, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print('backup -> %s' % os.path.basename(bak))
    ok = sum(1 for u in units if 'the framing stays exactly as the first frame' in u['i2v_prompt'].lower())
    print('rewritten -> %s  (verified %d/%d)' % (a.manifest, ok, len(units)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

# -*- coding: utf-8 -*-
"""LoRA 训练集体检：重复度 + caption 卫生 + 触发词，三条一票否决。

为什么先做这个而不是直接开训：2026-11-15 实测 `mv0002-cast-work/lora-dataset` 两组各 16 张
看着是「12 视角转面」，dHash 算下来 120 对里 106~120 对距离 ≤20（中位数 9/256），
本质是同一张正面像的近重复——这种集子训出来的 LoRA 只在正面像上过拟合，换角度就崩，
而且训练一次要几小时 GPU，属于「不看就烧」的典型浪费。相对的 `media/asset/faces/CH01`
中位数 104、零重复，是真多视角集。

判据（任一不过=不许进训练）：
  1) 重复度：全部图像两两 dHash 距离，重复对（≤ --dup-thr，默认 20/256）占比 ≤ --max-dup（默认 10%）；
  2) caption 卫生：不得含场景/背景词（会把环境学进 LoRA）；
  3) 触发词：每条 caption 首个词必须是同一触发词（跨图一致的 token）。

用法：
  python qc_lora_dataset.py <数据集目录> [--token ljher] [--json out.json]
"""
import argparse, glob, itertools, json, os, re, sys

from PIL import Image

SCENE_WORDS = ('background', 'blurred', 'outdoors', 'outdoor', 'indoors', 'street', 'city',
               'room', 'wall', 'window', 'sky', 'nature', 'daylight', 'sunlight', 'studio',
               'against', 'framed', 'setting', 'scenery', 'landscape')


def dhash(path, sz=16):
    im = Image.open(path).convert('L').resize((sz + 1, sz), Image.LANCZOS)
    px = list(im.getdata())
    bits = 0
    for r in range(sz):
        for c in range(sz):
            bits = (bits << 1) | (1 if px[r * (sz + 1) + c] > px[r * (sz + 1) + c + 1] else 0)
    return bits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data_dir')
    ap.add_argument('--token', default='', help='期望的触发词；留空则取出现最多的首词')
    ap.add_argument('--dup-thr', type=int, default=20, help='dHash 距离 ≤ 该值算重复对')
    ap.add_argument('--max-dup', type=float, default=0.10, help='重复对占比上限')
    ap.add_argument('--json', default='')
    a = ap.parse_args()

    pngs = sorted(glob.glob(os.path.join(a.data_dir, '**', '*.png'), recursive=True))
    if len(pngs) < 2:
        print('FAIL images=%d（少于 2 张，无法评估）' % len(pngs))
        return 1

    hs = [(os.path.relpath(p, a.data_dir), dhash(p)) for p in pngs]
    pairs = sorted((bin(h1 ^ h2).count('1'), n1, n2)
                   for (n1, h1), (n2, h2) in itertools.combinations(hs, 2))
    total = len(pairs)
    dup = [x for x in pairs if x[0] <= a.dup_thr]
    dup_ratio = len(dup) / total
    median = pairs[total // 2][0] if total else 0

    fails = []
    if dup_ratio > a.max_dup:
        fails.append('DUPLICATE %d/%d 对距离 ≤%d（%.0f%% > %.0f%%上限）'
                     % (len(dup), total, a.dup_thr, 100 * dup_ratio, 100 * a.max_dup))

    firsts = {}
    scene_hits = []
    missing_cap = []
    for p in pngs:
        cap_path = os.path.splitext(p)[0] + '.txt'
        if not os.path.isfile(cap_path):
            missing_cap.append(os.path.basename(p))
            continue
        cap = open(cap_path, encoding='utf-8').read().strip()
        firsts[cap.split(',')[0].strip()] = firsts.get(cap.split(',')[0].strip(), 0) + 1
        low = cap.lower()
        bad = [w for w in SCENE_WORDS if w in low]
        if bad:
            scene_hits.append('%s(%s)' % (os.path.basename(p), ','.join(bad[:3])))
    if missing_cap:
        fails.append('CAPTION-MISSING %s' % ','.join(missing_cap[:6]))
    if scene_hits:
        fails.append('CAPTION-SCENE %d 条含场景词 %s' % (len(scene_hits), ','.join(scene_hits[:4])))

    token = a.token or (max(firsts, key=firsts.get) if firsts else '')
    off_token = [k for k in firsts if k != token]
    if off_token:
        fails.append('TOKEN-INCONSISTENT 期望 %r，另有 %s' % (token, off_token[:4]))

    print('images=%d  dHash median=%d  dup(≤%d)=%d/%d (%.0f%%)  token=%r'
          % (len(pngs), median, a.dup_thr, len(dup), total, 100 * dup_ratio, token))
    if dup:
        worst = ', '.join('%s~%s(%d)' % (x[1], x[2], x[0]) for x in dup[:3])
        print('  最像的几对: %s' % worst)
    print('VERDICT: %s' % ('FAIL' if fails else 'PASS'))
    for f in fails:
        print('  - ' + f)
    if a.json:
        json.dump(dict(images=len(pngs), median=median, dup=len(dup), pairs=total,
                       token=token, fails=fails),
                  open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 0 if not fails else 2


if __name__ == '__main__':
    sys.exit(main())

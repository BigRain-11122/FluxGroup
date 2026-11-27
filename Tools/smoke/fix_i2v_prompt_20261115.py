# -*- coding: utf-8 -*-
"""i2v 提示词定点修复（2026-11-15 · XQ38_18b 星星被画成卡通五角星）。

实锚：`kf/XQ18b.png` 是一串**小圆灯 bokeh**（细线上几个柔圆光点）；i2v 提示词写的是
`a crooked line of five warm gold stars now linked by fine pale threads of light` ——
模型照字面画成**六颗大号五角星符号 + 一根穿起来的线**，年代质感全毁（= 去 AI 感红线）。
这与 XQ33「一条横贯金色光带」同型：**提示词里的具体意象会被逐字画出来**（J-23 歌词意象律的画面版）。

修法：把「stars + threads」换成「小圆灯串」的正向描述（禁否定词，闸会拦），
其余（星空底、低机位、手电光池、调色尾）不动。

用法：
  python fix_i2v_prompt_20261115.py [--manifest <json>] [--dry]
"""
import argparse, json, os, shutil, sys, time

DEFAULT = (r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2'
           r'\30s-reel-v1\i2v-xq3-manifest.json')

OLD = ('a crooked line of five warm gold stars now linked by fine pale threads of light, '
       'the threads thin and steady')
NEW = ('a crooked line of small round warm bulbs strung on a thin dark wire across the sky, '
       'each bulb a soft round glow with a gentle halo, the wire sagging slightly between them')

PATCHES = {'XQ38_18b': [(OLD, NEW)]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default=DEFAULT)
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    d = json.load(open(a.manifest, encoding='utf-8'))
    hit = 0
    for u in d['units']:
        for old, new in PATCHES.get(u['id'], []):
            if old in u['i2v_prompt']:
                u['i2v_prompt'] = u['i2v_prompt'].replace(old, new, 1)
                hit += 1
            else:
                print('WARN %s: 未匹配到原文（可能已改过）' % u['id'])
    print('patched=%d' % hit)
    if a.dry:
        for u in d['units']:
            if u['id'] in PATCHES:
                print('\n[%s]\n%s' % (u['id'], u['i2v_prompt'][:420]))
        return 0
    bak = a.manifest + '.bak-%s' % time.strftime('%Y%m%d-%H%M%S')
    shutil.copy2(a.manifest, bak)
    with open(a.manifest, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    ok = sum(1 for u in d['units'] if u['id'] in PATCHES and NEW in u['i2v_prompt'])
    print('backup -> %s ; verified %d/%d' % (os.path.basename(bak), ok, len(PATCHES)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

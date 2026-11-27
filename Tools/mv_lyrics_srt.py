#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_lyrics_srt.py — 从词锚生成 MV 歌词字幕（SRT + ASS 双份）

为什么：MV 成片必须有衬线字幕轨（CEO 交付三件套之一：词级锚点/衬线字幕轨/节奏地图），
但字幕从哪里来一直是手给的。词锚 `anchors/<曲>-words.json` 里已经有 segments，
直接生成即可——机核、可复现、跟着歌走。

规则（承 drama 字幕判例 + MV 排版令）：
  · 单行 ≤17 字（不折断词，优先在标点/空格折）
  · 单条停留 0.8-6.0s（短于 0.8 合并到相邻，长于 6 拆）
  · 半角标点一律转全角
  · ASS 衬线体 + 轻描边（禁硬描边）+ 底部安全区

用法：
  python Tools/mv_lyrics_srt.py --song 黑色幽默 --out-dir cph4/fleet/mv-album-001-jay/subs
Exit: 0 成功
"""
import argparse
import json
import os
import re
import sys

ROOT = r'K:\Fluxgroup\FluxGroup'
BASE = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay')
ANCH = os.path.join(BASE, 'anchors')

MAX_CHARS = 17
MIN_DUR, MAX_DUR = 0.8, 6.0
HALF2FULL = {',': '，', '.': '。', '?': '？', '!': '！', ':': '：', ';': '；', '(': '（', ')': '）'}


def norm(t):
    t = (t or '').strip()
    for a, b in HALF2FULL.items():
        t = t.replace(a, b)
    return re.sub(r'\s+', ' ', t)


def wrap(text, limit=MAX_CHARS):
    """按标点优先折行，返回行列表。"""
    text = norm(text)
    if len(text) <= limit:
        return [text]
    parts, cur = [], ''
    for ch in text:
        cur += ch
        if ch in '，。？！；、' and len(cur) >= limit * 0.6:
            parts.append(cur); cur = ''
        elif len(cur) >= limit:
            parts.append(cur); cur = ''
    if cur:
        parts.append(cur)
    return parts


def ts(t, sep=','):
    t = max(0.0, float(t))
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return ('%02d:%02d:%06.3f' % (h, m, s)).replace('.', sep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--song', required=True)
    ap.add_argument('--out-dir', default=os.path.join(BASE, 'subs'))
    ap.add_argument('--shift', type=float, default=0.0, help='整体平移秒（对不齐时微调）')
    a = ap.parse_args()

    src = os.path.join(ANCH, a.song + '-words.json')
    if not os.path.isfile(src):
        print('ANCHORS MISSING', src)
        return 2
    d = json.load(open(src, encoding='utf-8'))
    segs = d.get('segments') or []
    if not segs:
        print('NO SEGMENTS')
        return 2

    # 规整 + 合并过短
    items = []
    for s in segs:
        t0 = float(s.get('t0', s.get('start', 0))) + a.shift
        t1 = float(s.get('t1', s.get('end', 0))) + a.shift
        txt = norm(s.get('text', ''))
        if not txt or t1 <= t0:
            continue
        items.append({'t0': t0, 't1': t1, 'text': txt})
    merged = []
    for it in items:
        if merged and it['t0'] - merged[-1]['t1'] < 0.3:
            merged[-1]['t1'] = it['t1']
            merged[-1]['text'] += it['text']
        else:
            merged.append(dict(it))

    final = []
    for it in merged:
        dur = it['t1'] - it['t0']
        if dur > MAX_DUR:
            # 超长按字数均分
            n = int(round(dur / MAX_DUR)) or 2
            step = dur / n
            chunks = wrap(it['text'], max(6, len(it['text']) // n))
            per = dur / max(1, len(chunks))
            for i, c in enumerate(chunks):
                final.append({'t0': it['t0'] + i * per, 't1': it['t0'] + (i + 1) * per, 'text': c})
        else:
            final.append(it)

    os.makedirs(a.out_dir, exist_ok=True)
    srt = os.path.join(a.out_dir, a.song + '.srt')
    with open(srt, 'w', encoding='utf-8') as f:
        for i, it in enumerate(final, 1):
            body = '\\N'.join(wrap(it['text']))
            f.write('%d\n%s --> %s\n%s\n\n' % (i, ts(it['t0']), ts(it['t1']), body))

    # ASS（衬线 + 轻描边 + 底部安全区）
    ass = os.path.join(a.out_dir, a.song + '.ass')
    with open(ass, 'w', encoding='utf-8') as f:
        f.write('[Script Info]\nScriptType: v4.00+\nPlayResX: 1344\nPlayResY: 768\n\n'
                '[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour,'
                ' Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline,'
                ' Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
                'Style: L,Source Han Serif SC,40,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,2.2,1.2,2,80,80,54,1\n\n'
                '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
        for it in final:
            body = '\\N'.join(wrap(it['text']))
            f.write('Dialogue: 0,%s,%s,L,,0,0,0,,%s\n' % (
                ts(it['t0'], '.'), ts(it['t1'], '.'), body))
    print('LYRICS OK srt=%s ass=%s lines=%d' % (srt, ass, len(final)))
    for it in final[:5]:
        print('  %6.1f-%6.1f %s' % (it['t0'], it['t1'], it['text'][:30]))
    return 0


if __name__ == '__main__':
    sys.exit(main())

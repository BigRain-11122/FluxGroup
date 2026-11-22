#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_assemble.py — 通用 MV 装配器（一歌一条命令出成片）

为什么：MV 的装配一直是"一版一个脚本"（v59/v510/v602…全写死路径），换曲就废。
本文件吃三样东西就出片：i2v 清单（窗长/帧）+ 片段目录 + 原曲，按 GRADE-v1 落调色链。

链：逐镜归一（时长/变速/分辨率）→ 拼接 → 调色（可选）→ 字幕（可选·只有官方歌词才烧）
    → 配原曲 → faststart 输出

用法：
  python Tools/mv_assemble.py --manifest plan/hei-i2v-manifest.json \
      --clips clips-hei-480 --song "audio/周杰伦 - 黑色幽默.mp3" \
      --out assembly/hei-v1.mp4 [--grade exec] [--subs subs/黑色幽默.ass] [--limit 20]
Exit: 0 成片；3 片段不足（照常输出已到片段，便于早看）
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = r'K:\Fluxgroup\FluxGroup'
BASE = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay')

# GRADE-LAW 参数链（黑色幽默 GRADE-v1）：冷蓝黑 + 台灯区不进蓝（mask 由 lumakey 保护）
GRADE_BASE = ("eq=contrast=1.06:brightness=-0.012:saturation=0.94,"
              "curves=blue='0/0 0.35/0.40 0.70/0.76 1/1',"
              "colorbalance=bs=.05:bm=.03:bh=.02,"
              "vignette=PI/4.6,"
              "noise=alls=6:allf=t")


def ffprobe_dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', p], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--clips', required=True)
    ap.add_argument('--song', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--width', type=int, default=1344)
    ap.add_argument('--height', type=int, default=768)
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--grade', choices=['none', 'exec'], default='exec')
    ap.add_argument('--subs', default='')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()

    def _p(x):
        return x if os.path.isabs(x) else os.path.join(BASE, x)

    man = json.load(open(_p(a.manifest), encoding='utf-8'))
    units = man.get('units', [])
    if a.limit:
        units = units[:a.limit]
    clips_dir = _p(a.clips)
    song = _p(a.song)

    out_dir = os.path.dirname(_p(a.out))
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, '_asm')
    os.makedirs(tmp, exist_ok=True)

    norm, missing = [], []
    for i, u in enumerate(units):
        src = os.path.join(clips_dir, u['id'] + '.mp4')
        if not os.path.isfile(src):
            missing.append(u['id'])
            continue
        dst = os.path.join(tmp, 'n%03d.mp4' % i)
        want = float(u.get('win_s') or u.get('src_s') or 3.0)
        have = ffprobe_dur(src)
        speed = 1.0
        if have > 0:
            speed = max(0.5, min(2.0, have / want))
        vf = ('setpts=PTS/%.4f,scale=%d:%d:force_original_aspect_ratio=increase,'
              'crop=%d:%d,fps=%d,format=yuv420p' % (speed, a.width, a.height,
                                                   a.width, a.height, a.fps))
        cmd = ['ffmpeg', '-y', '-v', 'error', '-i', src, '-vf', vf, '-an',
               '-t', '%.3f' % want, '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', dst]
        rc = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
        if rc.returncode != 0:
            print('NORM FAIL', u['id'], (rc.stderr or '')[-160:])
            continue
        norm.append(dst)

    if not norm:
        print('ASM ABORT 没有可用片段（%d 缺失）' % len(missing))
        return 2

    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as f:
        for p in norm:
            f.write("file '%s'\n" % p.replace('\\', '/'))
    silent = os.path.join(tmp, 'v.mp4')
    rc = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
                         '-i', lst, '-c', 'copy', silent], capture_output=True, text=True)
    if rc.returncode != 0:
        print('CONCAT FAIL', (rc.stderr or '')[-200:])
        return 2

    vf = GRADE_BASE if a.grade == 'exec' else 'null'
    if a.subs:
        sp = _p(a.subs)
        if os.path.isfile(sp):
            esc = sp.replace('\\', '/').replace(':', '\\:')
            vf = "ass=filename='%s',%s" % (esc, vf)
        else:
            print('  subs missing, skip:', sp)

    total = sum(ffprobe_dur(p) for p in norm)
    out = _p(a.out)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', silent, '-ss', '0', '-t', '%.3f' % total, '-i', song,
           '-vf', vf, '-map', '0:v:0', '-map', '1:a:0',
           '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p',
           '-r', str(a.fps), '-c:a', 'aac', '-b:a', '192k', '-shortest',
           '-movflags', '+faststart', out]
    rc = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
    print('rc', rc.returncode, (rc.stderr or '')[-200:])
    if rc.returncode != 0:
        return 2

    p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'format=duration,size:stream=codec_type,width,height,r_frame_rate',
                        '-of', 'default=nw=1', out], capture_output=True, text=True)
    print(p.stdout.strip())
    print('ASM OK %s  clips=%d/%d  grade=%s  subs=%s  %.1f MB'
          % (out, len(norm), len(units), a.grade, 'yes' if a.subs else 'no',
             os.path.getsize(out) / 1048576))
    if missing:
        print('  missing clips:', len(missing), missing[:6])
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())

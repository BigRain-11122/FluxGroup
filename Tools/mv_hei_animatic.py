# -*- coding: utf-8 -*-
"""把 batch1 的 13 帧做成前 42 秒 ANIMATIC（占位运镜），配原曲。

明确标注：**这是粗样/animatic**，运镜为占位（正式版由 i2v 出真运动）。
产出一律归档为 animatic，不进正典（低清验证件律）。
"""
import json
import os
import subprocess

ROOT = r'K:\Fluxgroup\FluxGroup'
BASE = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay')
FR = os.path.join(BASE, 'frames-hei-kf')
PLAN = os.path.join(BASE, 'plan', 'hei-kf-prompts-v2-batch1.json')
SONG = os.path.join(BASE, 'audio', '周杰伦 - 黑色幽默.mp3')
OUTDIR = os.path.join(BASE, 'animatic')
os.makedirs(OUTDIR, exist_ok=True)

W, H, FPS = 1344, 768, 24
rows = json.load(open(PLAN, encoding='utf-8'))
# 前奏+主歌1 截止 41.9s
rows = [r for r in rows if r['t0'] < 41.9]
rows.sort(key=lambda r: r['t0'])
end = min(41.9, rows[-1]['t1'])

clips = []
for i, r in enumerate(rows):
    t0, t1 = r['t0'], min(r['t1'], end)
    dur = max(0.6, t1 - t0)
    img = os.path.join(FR, r['id'] + '.png')
    if not os.path.exists(img):
        continue
    out = os.path.join(OUTDIR, '_c%02d.mp4' % i)
    # 占位运动：F/P 轻微推近，E 缓慢横移（animatic 专用）
    frames = int(round(dur * FPS))
    if r['kind'] == 'E':
        vf = ("scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,"
              "zoompan=z='1.04':x='iw*0.02*t/%d':y='ih*0.5-ih/2/1.04':d=%d:s=%dx%d:fps=%d"
              % (W * 2, H * 2, W * 2, H * 2, frames, frames, W, H, FPS))
    else:
        vf = ("scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,"
              "zoompan=z='1.0+0.05*on/%d':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d"
              % (W * 2, H * 2, W * 2, H * 2, frames, frames, W, H, FPS))
    cmd = ['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-i', img, '-t', '%.3f' % dur,
           '-vf', vf, '-r', str(FPS), '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', out]
    rc = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
    if rc.returncode != 0:
        print('FAIL', r['id'], (rc.stderr or '')[-160:])
        continue
    clips.append(out)

lst = os.path.join(OUTDIR, 'list.txt')
with open(lst, 'w', encoding='utf-8') as f:
    for c in clips:
        f.write("file '%s'\n" % c.replace('\\', '/'))

silent = os.path.join(OUTDIR, '_v.mp4')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-c', 'copy', silent], check=False)

final = os.path.join(OUTDIR, '黑色幽默-前42s-ANIMATIC-v1.mp4')
cmd = ['ffmpeg', '-y', '-v', 'error', '-i', silent, '-ss', '0', '-t', '%.3f' % end, '-i', SONG,
       '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
       '-shortest', '-movflags', '+faststart', final]
r = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
print('rc', r.returncode, (r.stderr or '')[-200:])
if os.path.exists(final):
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size',
                        '-of', 'default=nw=1', final], capture_output=True, text=True)
    print(p.stdout.strip())
    print('OUT', final, round(os.path.getsize(final) / 1048576, 1), 'MB', 'shots=%d' % len(clips))

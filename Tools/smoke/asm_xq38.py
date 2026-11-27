# -*- coding: utf-8 -*-
"""星晴 38 镜 3 秒档粗剪装配：按 manifest 顺序拼成一条，可选贴歌。

口径：manifest 里 38 单全是 win_s=3.0 / src_s=3.0 / speed=1.0，合计 114.0s，
所以装配就是「顺序直拼 + 可选音轨」，不存在变速/定格/窗口补齐问题。

为什么先做粗剪：CEO 令「先快后全，有东西就先给看」——38 镜全齐前一版可看的拼条，
比等所有精修更早暴露连戏/构图问题（也省得逐条看 38 个文件）。

用法：
  python asm_xq38.py --dry                       # 只核片在不在、参数一不一致
  python asm_xq38.py --out <mp4> [--music <mp3>] [--music-start 0]
"""
import argparse, json, os, subprocess, sys

MANIFEST = (r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2'
            r'\30s-reel-v1\i2v-xq3-manifest.json')
CLIPS = (r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2'
         r'\30s-reel-v1\i2v-xq3-batch')
MUSIC = r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\audio\周杰伦 - 星晴.mp3'


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                        '-show_entries', 'stream=width,height,r_frame_rate,codec_name',
                        '-show_entries', 'format=duration', '-of', 'json', path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    d = json.loads(r.stdout)
    st = (d.get('streams') or [{}])[0]
    return dict(w=st.get('width'), h=st.get('height'), codec=st.get('codec_name'),
                fps=st.get('r_frame_rate'),
                dur=float((d.get('format') or {}).get('duration') or 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default=MANIFEST)
    ap.add_argument('--clips', default=CLIPS)
    ap.add_argument('--out', default=r'K:\Fluxgroup\FluxGroup\media\mv0001-handover\xq38-roughcut-v1.mp4')
    ap.add_argument('--music', default=MUSIC)
    ap.add_argument('--music-start', type=float, default=0.0, help='从歌曲第几秒起用（默认 0）')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    units = json.load(open(a.manifest, encoding='utf-8'))['units']
    missing, bad, total, params = [], [], 0.0, set()
    rows = []
    for u in units:
        p = os.path.join(a.clips, u['id'] + '.mp4')
        if not os.path.isfile(p) or os.path.getsize(p) < 10000:
            missing.append(u['id'])
            continue
        m = probe(p)
        if not m:
            bad.append(u['id'] + '(probe-fail)')
            continue
        if abs(m['dur'] - u['win_s']) > 0.12:
            bad.append('%s(dur=%.2f 期望 %.2f)' % (u['id'], m['dur'], u['win_s']))
        params.add((m['w'], m['h'], m['codec'], m['fps']))
        total += m['dur']
        rows.append((u['id'], p, m['dur']))

    print('units=%d  on-disk=%d  missing=%d  bad=%d  sum=%.2fs'
          % (len(units), len(rows), len(missing), len(bad), total))
    if missing:
        print('  missing: ' + ','.join(missing))
    if bad:
        print('  bad: ' + ','.join(bad[:8]))
    print('  视频参数集合: %s' % sorted(params))
    if a.dry:
        return 0 if not missing and not bad else 1
    if missing:
        print('REFUSE: 缺 %d 条，先等批次跑齐' % len(missing))
        return 1

    lst = a.out + '.txt'
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(lst, 'w', encoding='utf-8') as f:
        for _, p, _ in rows:
            f.write("file '%s'\n" % p.replace('\\', '/'))

    # 同参数集合（一码一分辨）才走 -c copy，否则统一重编码到第一条的参数
    same = len(params) == 1
    cmd = ['ffmpeg', '-y', '-v', 'warning', '-f', 'concat', '-safe', '0', '-i', lst]
    has_music = bool(a.music) and os.path.isfile(a.music)
    if has_music:
        cmd += ['-ss', '%.2f' % a.music_start, '-t', '%.2f' % total, '-i', a.music]
    if same:
        cmd += ['-c:v', 'copy']
    else:
        w, h = sorted(params)[0][0], sorted(params)[0][1]
        cmd += ['-vf', 'scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2'
                % (w, h, w, h), '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-r', '24']
    if has_music:
        cmd += ['-c:a', 'aac', '-b:a', '192k', '-af', 'afade=t=in:st=0:d=0.6,afade=t=out:st=%.2f:d=0.8'
                % max(0.0, total - 0.9), '-shortest']
    cmd += [a.out]
    print('>> ' + ' '.join('"%s"' % c if ' ' in c else c for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print('FFMPEG-FAIL rc=%d\n%s' % (r.returncode, (r.stderr or '')[-1200:]))
        return 1
    m = probe(a.out)
    print('OK -> %s  %.2fs  %.1f MB  %s' % (a.out, m['dur'], os.path.getsize(a.out) / (1 << 20),
                                            'audio=yes' if has_music else 'audio=no'))
    return 0


if __name__ == '__main__':
    sys.exit(main())

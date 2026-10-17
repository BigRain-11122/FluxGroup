# -*- coding: utf-8 -*-
# drama-001 60集量产装配器：读 EP json + eps-kf 图 → 每集 mp4（zoompan+折行字幕+字卡+闪回柔焦）
# 用法: python drama_ep_assemble.py <起集> <止集>   （含两端；纯 CPU·ffmpeg）
# 律: 音轨禁令（O-20261009）=纯画面+硬字幕，配音/音效=v1.1 IndexTTS/音频库升级面
import json, os, subprocess, sys

EPS_DIR = r'C:\Fluxgroup\FluxGroup\cph4\fleet\drama-001-stockera\episodes'
KF = r'C:\Fluxgroup\FluxGroup\media\drama-eps\eps-kf'
OUT = r'C:\Fluxgroup\FluxGroup\media\drama-eps'
os.makedirs(OUT, exist_ok=True)
FF = r'C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe'
FONT_CANDIDATES = [r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simsun.ttc']

def font():
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    raise SystemExit('NO_FONT')

def ffp(p):
    s = p.replace('\\', '/')
    return s[0] + '\\:' + s[2:] if len(s) > 2 and s[1] == ':' else s

def wrap_sub(sub, limit=17):
    def ulen(s):
        return sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in s)
    if ulen(sub) <= limit:
        return sub
    best = None
    for i, ch in enumerate(sub[1:-1], start=1):
        if ch in '，。！？；、':
            l1, l2 = ulen(sub[:i + 1]), ulen(sub[i + 1:])
            if l1 <= limit and l2 <= limit:
                d = abs(i + 1 - len(sub) / 2.0)
                if best is None or d < best[0]:
                    best = (d, i + 1)
    if best:
        cut = best[1]
    else:
        # EP053_22 判例：55% 早切产生碎行+孤字（28 字卡折 6 行+「已」单行）——改贪心填满
        cut, acc = len(sub), 0.0
        for i, ch in enumerate(sub):
            w = 1.0 if ord(ch) > 0x2E80 else 0.55
            if acc + w > limit and i > 0:
                cut = i
                break
            acc += w
        if cut >= len(sub):
            cut = len(sub)  # degenerate guard
    # 双守卫有界迭代环（两分支通用·EP022_22 判例）：先灭孤尾，再禁则行首标点；收进不得再造孤尾
    for _ in range(4):
        if cut >= len(sub):
            break
        if ulen(sub[cut:]) <= 1.0 and cut > 1:
            cut -= 1
            continue
        if sub[cut] in '，。！？；、':
            if ulen(sub[:cut + 1]) <= limit and ulen(sub[cut + 1:]) > 1.0:
                cut += 1
                continue
            if cut > 1:
                cut -= 1
                continue
        break
    first = sub[:cut]
    rest = sub[cut:]
    if not rest or first == sub:
        return sub
    # 递归折行：超长台词一次折不完会二次溢出（EP010 n10 判例）——余段继续折
    return first + '\n' + wrap_sub(rest, limit)

def textfile(name, sub):
    p = os.path.join(OUT, 'tmp_txt_%s.txt' % name)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(wrap_sub(sub))
    return p

def zoompan(kind, dur):
    d = int(dur * 25)
    if kind == 'out':
        return "zoompan=z='max(1.20-0.0009*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=540x960:fps=25" % d
    if kind == 'pan':
        return "zoompan=z='1.08':x='iw/2-(iw/zoom/2)+(on-1)*1.2':y='ih/2-(ih/zoom/2)':d=%d:s=540x960:fps=25" % d
    if kind == 'shake':
        return "zoompan=z='1.06+0.004*sin(on/2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=540x960:fps=25" % d
    if kind == 'flash':
        return "zoompan=z='min(1+0.0006*on,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=540x960:fps=25" % d
    return "zoompan=z='min(1+0.0009*on,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=540x960:fps=25" % d

def card_lines(text, limit=10):
    # 540px 宽 fontsize=48 仅容 ~11 全角字；按行折行后逐行独立居中（EP010 片尾卡裁切判例）
    # EP022_22 判例：勿对含内嵌换行的余段二次 wrap（\n 被计 0.55 宽+错位切分=碎行根源）——直接拍平
    lines = []
    for raw in text.split('\n'):
        cur = raw.strip()
        if not cur:
            continue
        for ln in wrap_sub(cur, limit).split('\n'):
            if ln.strip():
                lines.append(ln.strip())
    return lines or [text]

def build_card(tag, dur, text):
    f = font()
    lines = card_lines(text, 10)
    lh = 64  # 48px 字号行距
    total = lh * len(lines)
    vf = ["setsar=1", "fade=t=in:st=0:d=0.2,fade=t=out:st=%.2f:d=0.2" % (dur - 0.2)]
    for i, ln in enumerate(lines):
        y = int((960 - total) / 2 + i * lh)
        vf.append("drawtext=fontfile='%s':textfile='%s':expansion=none:fontcolor=white:fontsize=48:x=(w-tw)/2:y=%d" % (ffp(f), ffp(textfile('%s_L%d' % (tag, i), ln)), y))
    out = os.path.join(OUT, 'tmp_%s.mp4' % tag)
    r = subprocess.run([FF, '-y', '-f', 'lavfi', '-i', 'color=black:s=540x960:r=25', '-t', '%.2f' % dur,
                        '-vf', ','.join(vf), '-pix_fmt', 'yuv420p', '-an', out], capture_output=True)
    return out if r.returncode == 0 else None

def build_shot(tag, shot, dur, img):
    f = font()
    vf = ["scale=720:1080:flags=lanczos", zoompan(shot.get('kind', 'in'), dur), "setsar=1"]
    if shot.get('post') == 'flashback':
        vf += ['gblur=sigma=2.0', 'noise=alls=10:allf=t']
    sub = shot.get('sub') or ''
    if sub:
        t0, t1 = dur * 0.12, dur * 0.88
        vf.append("drawtext=fontfile='%s':textfile='%s':expansion=none:fontcolor=white:fontsize=30:borderw=2:bordercolor=black@0.85:x=(w-tw)/2:y=h-th-46:enable='between(t,%.2f,%.2f)'" % (ffp(f), ffp(textfile(tag, sub)), t0, t1))
    vf.append("fade=t=in:st=0:d=0.12,fade=t=out:st=%.2f:d=0.12" % (dur - 0.12))
    out = os.path.join(OUT, 'tmp_%s.mp4' % tag)
    r = subprocess.run([FF, '-y', '-loop', '1', '-i', img, '-t', '%.2f' % dur,
                        '-vf', ','.join(vf), '-r', '25', '-pix_fmt', 'yuv420p', '-an', out], capture_output=True)
    return out if r.returncode == 0 else None

def main(ep_lo, ep_hi):
    for ep in range(ep_lo, ep_hi + 1):
        pj = os.path.join(EPS_DIR, 'EP%03d.json' % ep)
        if not os.path.exists(pj):
            print('EP_JSON_MISSING %d' % ep, flush=True)
            continue
        spec = json.load(open(pj, encoding='utf-8'))
        clips, missing = [], []
        for s in spec.get('shots', []):
            n, dur = s.get('n'), float(s.get('dur', 3))
            tag = 'EP%03d_%02d' % (ep, n)
            if s.get('kind') == 'card':
                c = build_card(tag, dur, s.get('card') or s.get('sub') or '')
            else:
                img = os.path.join(KF, tag + '.png')
                if not os.path.exists(img):
                    missing.append(tag)
                    continue
                c = build_shot(tag, s, dur, img)
            if c:
                clips.append(c)
            else:
                print('BUILD_FAIL %s' % tag, flush=True)
        if missing:
            print('EP%03d MISSING %s' % (ep, ' '.join(missing)), flush=True)
        if not clips:
            print('EP%03d EMPTY skip' % ep, flush=True)
            continue
        lst = os.path.join(OUT, 'tmp_ep%03d.txt' % ep)
        with open(lst, 'w', encoding='utf-8') as fh:
            for c in clips:
                fh.write("file '%s'\n" % c)
        out = os.path.join(OUT, 'EP%03d.mp4' % ep)
        r = subprocess.run([FF, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], capture_output=True)
        print(('EP_DONE ' + out + ' clips=%d') % len(clips) if r.returncode == 0 else 'EP_FAIL %d' % ep, flush=True)

if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))

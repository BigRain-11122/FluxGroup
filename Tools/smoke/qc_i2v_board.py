# -*- coding: utf-8 -*-
"""i2v 质检板：把每条片的首帧 | 末帧并排拼成一张联络表，附机械指标，供人一眼过。

为什么最后还是靠板子而不是靠全自动判据：
  - 像素差把主体运动算进相机漂移（跟拍镜 XQ38_10 差 53/127，机位其实没动）；
  - 全幅 ECC 仿射在「主体占画面大块」时会锁到主体上，给出 scale 1.65 这种离谱解
    （配 cc 只有 0.73，低置信度已经说明这个解不能信）；
  - 人脸闸在小脸/侧脸上 yaw 噪声大。
所以自动指标只作提示，判负由人看板决定。板子每行一镜：首帧 | 末帧 | 指标文字。

用法（须装 PIL 的解释器）：
  python qc_i2v_board.py <clips_dir> --out <jpg> [--per-board 12] [--width 320]
"""
import argparse, glob, json, os, subprocess, sys, tempfile

from PIL import Image, ImageDraw

FONT_FALLBACK = None


def frame(mp4, ss=None):
    d = tempfile.mkdtemp(prefix='qcb_')
    p = os.path.join(d, 'f.png')
    cmd = ['ffmpeg', '-y', '-v', 'error']
    cmd += ['-ss', '0'] if ss is None else ['-sseof', str(ss)]
    cmd += ['-i', mp4, '-frames:v', '1', p]
    subprocess.run(cmd, check=True)
    return p


def metrics(mp4):
    """复用像素差（PIL）+ 人脸（可选）——都失败就留空，不阻断出板。"""
    out = {}
    pyq = r'D:\ComfyUI\python_embeded\python.exe'
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        r = subprocess.run([pyq, os.path.join(here, 'qc_i2v_drift.py'), os.path.dirname(mp4)],
                           capture_output=True, text=True, timeout=600)
        for ln in (r.stdout or '').splitlines():
            parts = ln.split()
            if parts and parts[0] == os.path.basename(mp4)[:-4]:
                out['pixel'] = ' '.join(parts[1:])
    except Exception:  # noqa: BLE001
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clips_dir')
    ap.add_argument('--out', default='')
    ap.add_argument('--per-board', type=int, default=12)
    ap.add_argument('--width', type=int, default=300)
    a = ap.parse_args()

    mp4s = sorted(glob.glob(os.path.join(a.clips_dir, '*.mp4')))
    if not mp4s:
        print('no clips in', a.clips_dir)
        return 1
    out = a.out or os.path.join(a.clips_dir, 'QC-BOARD-%s.jpg' % os.path.basename(a.clips_dir))

    # 一次性把所有镜的像素指标算好（qc_i2v_drift 支持整目录，比逐条跑省一个量级）
    per_id = {}
    pyq = r'D:\ComfyUI\python_embeded\python.exe'
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([pyq, os.path.join(here, 'qc_i2v_drift.py'), a.clips_dir],
                       capture_output=True, text=True, timeout=1800)
    for ln in (r.stdout or '').splitlines():
        parts = ln.split()
        if len(parts) > 3 and 'mean=' in ln:
            per_id[parts[0]] = ln[len(parts[0]):].strip()

    boards = [mp4s[i:i + a.per_board] for i in range(0, len(mp4s), a.per_board)]
    written = []
    for bi, group in enumerate(boards):
        tiles = []
        for mp4 in group:
            cid = os.path.basename(mp4)[:-4]
            fa, fb = frame(mp4), frame(mp4, -0.1)
            ia = Image.open(fa).convert('RGB')
            ib = Image.open(fb).convert('RGB')
            w = a.width
            ia = ia.resize((w, int(w * ia.size[1] / ia.size[0])))
            ib = ib.resize((w, int(w * ib.size[1] / ib.size[0])))
            tiles.append((cid, ia, ib, per_id.get(cid, '')))
        tw, th = tiles[0][1].size
        lines = 3 if len(tiles[0][3]) > 46 else 2
        line_h = 16
        row_h = th + line_h * lines + 8
        sheet = Image.new('RGB', (tw * 2 + 12, row_h * len(tiles) + 24), (12, 12, 12))
        dr = ImageDraw.Draw(sheet)
        dr.text((6, 6), 'i2v QC board %d/%d  %s   left=first  right=last'
                % (bi + 1, len(boards), os.path.basename(a.clips_dir)), fill=(240, 240, 240))
        for i, (cid, ia, ib, met) in enumerate(tiles):
            y = 24 + i * row_h
            sheet.paste(ia, (0, y + line_h * lines))
            sheet.paste(ib, (tw + 12, y + line_h * lines))
            dr.text((4, y), cid + '  |' , fill=(255, 235, 160))
            if met:
                for k in range(lines):
                    seg = met[k * 46:(k + 1) * 46]
                    if seg:
                        dr.text((4, y + line_h * (k + 1)), seg, fill=(170, 200, 255))
        p = out if len(boards) == 1 else out.replace('.jpg', '-%02d.jpg' % (bi + 1))
        sheet.save(p, quality=86)
        written.append(p)
        print('board -> %s  %s  clips=%d' % (p, sheet.size, len(tiles)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

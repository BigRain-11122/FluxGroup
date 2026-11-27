# -*- coding: utf-8 -*-`n# ============================================================================`n# 【实验件·非闸门】2026-11-15 实测：全幅 ECC 在「主体占画面大块」时会锁到主体上（跟拍镜`n# XQ38_10 报 zoom+64%，实际机位没动）；分块投票在真推镜镜上块数不足或 IQR 爆炸（0.28~10.3），`n# 结果不稳定。结论=相机运动目前没有可靠的机械判据：像素差做「有没有变」的粗筛，`n# 最终由 qc_i2v_board.py 出的首末帧对照板人眼判定。本文件保留作后续尝试的起点，勿当 gate 用。`n# ============================================================================
"""相机运动闸：估计首末帧之间的全局变换，判「机位动没动」（不看主体怎么动）。

为什么要有它：像素差把主体运动也算进去——2026-11-15 实测 11 条里 4 条是假阳性
（跟拍自行车骑远、挥手动作、路面阴影变化），而真正要判的是摄像机。

为什么不是简单全幅 ECC：主体占画面大块时全幅最优解会锁到主体上——
XQ38_10（自行车骑远）全幅 ECC 给出 scale=1.65「推镜 65%」，但相关系数只有 0.73，
低置信度本身就在喊「这个解别信」。

正法 = 分块投票（`--mode patch`，默认）：
  1. 把画面切成 4×3 块（每块留 25% 重叠），逐块求仿射；
  2. 只保留相关系数 ≥0.85 且纹理足够（灰度标准差 ≥8）的块——平地/夜空/纯色块直接丢；
  3. 对这些块的 scale / 平移取**中位数**：背景块互相吻合，主体块是少数派，被中位数压掉。

判据：|median_scale − 1| > --gate-scale（默认 3%）或 median_shift > --gate-shift（默认 3% 画面宽）
→ CAMERA-MOVE；块数不足 → UNKNOWN（不许蒙）。

用法（须装 opencv，本机用 ComfyUI 的 python_embeded）：
  D:\\ComfyUI\\python_embeded\\python.exe qc_i2v_cam.py <clips_dir> [--mode patch|full] [--json out.json]
"""
import argparse, glob, json, os, subprocess, sys, tempfile

import cv2
import numpy as np

GRID = (4, 3)
OVERLAP = 0.25
MIN_CC = 0.55
MIN_STD = 8.0


def first_last(mp4):
    d = tempfile.mkdtemp(prefix='qcc_')
    a, b = os.path.join(d, 'a.png'), os.path.join(d, 'b.png')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '0', '-i', mp4, '-frames:v', '1', a], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-sseof', '-0.1', '-i', mp4, '-frames:v', '1', b], check=True)
    return a, b


def load(p, width=480):
    im = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    if im is None:
        return None
    h, w = im.shape
    return cv2.resize(im, (width, max(1, int(width * h / w))), interpolation=cv2.INTER_AREA)


def ecc(A, B, warp=None):
    warp = np.eye(2, 3, dtype=np.float32) if warp is None else warp.copy()
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 150, 1e-5)
    try:
        cc, warp = cv2.findTransformECC(A, B, warp, cv2.MOTION_AFFINE, crit, None, 5)
    except cv2.error:
        return None
    M = warp[:2, :2]
    return dict(cc=float(cc), scale=float(np.sqrt(abs(np.linalg.det(M)))),
                tx=float(warp[0, 2]), ty=float(warp[1, 2]),
                rot=float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))), warp=warp)


def ecc_pyr(A, B, levels=(56, 112, 224, 448)):
    """由粗到细求仿射。

    单尺度 ECC 只能收敛小幅位移：实测 3.0s 档里推镜 30%+ 的镜直接判 cc<0.5、解出 scale 3.9
    这种垃圾。分层后粗层先把大幅位移吃掉，细层再精修——平移量要按层缩放同步换算。
    """
    warp = np.eye(2, 3, dtype=np.float32)
    cc = 0.0
    prev_w = None
    for w in levels:
        h = max(8, int(round(w * A.shape[0] / A.shape[1])))
        Aa = cv2.resize(A, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        Bb = cv2.resize(B, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        if prev_w is not None:
            k = w / float(prev_w)
            warp = warp.copy()
            warp[0, 2] *= k
            warp[1, 2] *= k
        r = ecc(Aa, Bb, warp)
        if not r:
            return None
        cc, warp = r['cc'], r['warp']
        prev_w = w
    M = warp[:2, :2]
    return dict(cc=float(cc), scale=float(np.sqrt(abs(np.linalg.det(M)))),
                tx=float(warp[0, 2]), ty=float(warp[1, 2]),
                rot=float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))))


def patch_median(A, B):
    h, w = A.shape
    gh, gw = GRID
    ph, pw = h // gh, w // gw
    oh, ow = int(ph * OVERLAP), int(pw * OVERLAP)
    scales, shifts, rots, used, ccs = [], [], [], 0, []
    for i in range(gh):
        for j in range(gw):
            y0 = max(0, i * ph - oh // 2)
            x0 = max(0, j * pw - ow // 2)
            y1 = min(h, y0 + ph + oh)
            x1 = min(w, x0 + pw + ow)
            pa, pb = A[y0:y1, x0:x1].astype(np.float32) / 255.0, B[y0:y1, x0:x1].astype(np.float32) / 255.0
            if pa.std() * 255 < MIN_STD:
                continue          # 纯色/夜空块，没信息
            r = ecc_pyr((pa * 255).astype(np.uint8), (pb * 255).astype(np.uint8), levels=(64, 128))
            if not r or r['cc'] < MIN_CC:
                continue
            used += 1
            scales.append(r['scale'])
            ccs.append(r['cc'])
            rots.append(r['rot'])
            # 平移换算成画面宽占比（块内平移除以全幅宽）
            shifts.append(float(np.hypot(r['tx'], r['ty']) / w))
    if used < 3:
        return dict(ok=False, used=used, reason='块数不足（%d）' % used)
    return dict(ok=True, used=used, cc=round(float(np.median(ccs)), 3),
                scale=round(float(np.median(scales)), 4),
                shift=round(float(np.median(shifts)), 4),
                rot=round(float(np.median(rots)), 2),
                scale_iqr=round(float(np.subtract(*np.percentile(scales, [75, 25]))), 4))


def full_frame(A, B):
    r = ecc_pyr(A, B)
    if not r:
        return dict(ok=False, reason='ecc failed')
    return dict(ok=True, used=1, cc=round(r['cc'], 3), scale=round(r['scale'], 4),
                shift=round(float(np.hypot(r['tx'], r['ty']) / A.shape[1]), 4),
                rot=round(r['rot'], 2), scale_iqr=0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clips_dir')
    ap.add_argument('--mode', default='patch', choices=['patch', 'full'])
    ap.add_argument('--json', default='')
    ap.add_argument('--gate-scale', type=float, default=0.03)
    ap.add_argument('--gate-shift', type=float, default=0.03)
    a = ap.parse_args()

    rows = []
    for mp4 in sorted(glob.glob(os.path.join(a.clips_dir, '*.mp4'))):
        cid = os.path.basename(mp4)[:-4]
        p0, p1 = first_last(mp4)
        A, B = load(p0), load(p1)
        if A is None or B is None:
            rows.append(dict(id=cid, verdict='UNKNOWN'))
            print('%-12s -> UNKNOWN(读帧失败)' % cid)
            continue
        m = patch_median(A, B) if a.mode == 'patch' else full_frame(A, B)
        if not m.get('ok'):
            rows.append(dict(id=cid, verdict='UNKNOWN', **m))
            print('%-12s -> UNKNOWN %s' % (cid, m.get('reason', '')))
            continue
        dscale = abs(m['scale'] - 1.0)
        bad = []
        if dscale > a.gate_scale:
            bad.append('zoom%+.1f%%' % (100 * (m['scale'] - 1)))
        if m['shift'] > a.gate_shift:
            bad.append('shift%.1f%%' % (100 * m['shift']))
        verdict = 'CAMERA-MOVE' if bad else 'HOLD'
        rows.append(dict(id=cid, **m, verdict=verdict, reasons=bad))
        print('%-12s scale=%.3f(iqr %.3f) shift=%.3f rot=%+.2f blocks=%d cc=%.2f -> %s %s'
              % (cid, m['scale'], m.get('scale_iqr', 0), m['shift'], m['rot'],
                 m['used'], m['cc'], verdict, ','.join(bad)))

    n = len(rows)
    bad = [r['id'] for r in rows if r['verdict'] == 'CAMERA-MOVE']
    unk = [r['id'] for r in rows if r['verdict'] == 'UNKNOWN']
    print('\nSUMMARY clips=%d hold=%d camera_move=%d unknown=%d'
          % (n, n - len(bad) - len(unk), len(bad), len(unk)))
    if bad:
        print('camera_move_ids=' + ','.join(bad))
    if unk:
        print('unknown_ids=' + ','.join(unk))
    if a.json:
        json.dump(rows, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('json ->', a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())

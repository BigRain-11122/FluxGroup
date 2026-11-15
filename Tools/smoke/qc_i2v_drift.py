# -*- coding: utf-8 -*-
"""构图漂移机械判据：比较每个 clip 的首帧与末帧。

原理：把两帧缩到统一尺寸，分 4x4 网格算 SSIM 与平均像素差；
真实「锁机位」镜首末帧应高度相似（漂移分低），重构图镜会出现局部大差。
用法：python qc_i2v_drift.py <clips_dir> [--json out.json]
"""
import argparse, glob, json, os, subprocess, tempfile

import numpy as np
from PIL import Image


def frames(mp4):
    """抽首帧与末帧到临时 png。"""
    d = tempfile.mkdtemp()
    f0, f1 = os.path.join(d, 'f0.png'), os.path.join(d, 'f1.png')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', mp4, '-frames:v', '1', f0], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-sseof', '-0.1', '-i', mp4, '-frames:v', '1', f1],
                   check=True)
    return f0, f1


def drift_score(a_path, b_path, grid=4):
    a = Image.open(a_path).convert('L')
    b = Image.open(b_path).convert('L')
    if a.size != b.size:
        b = b.resize(a.size)
    A, B = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    h, w = A.shape
    gh, gw = h // grid, w // grid
    cells = []
    for i in range(grid):
        for j in range(grid):
            ca = A[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw]
            cb = B[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw]
            cells.append(float(np.abs(ca - cb).mean()))
    cells = np.array(cells)
    return {
        'mean_abs': round(float(np.abs(A - B).mean()), 2),
        'max_cell': round(float(cells.max()), 2),
        'p90_cell': round(float(np.percentile(cells, 90)), 2),
        'hot_cells': int((cells > 40).sum()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clips_dir')
    ap.add_argument('--json', default='')
    ap.add_argument('--gate-maxcell', type=float, default=55.0,
                    help='max_cell 超过该值且 mean_abs 也超标才判 DRIFT（默认 55，两镜实测定标）')
    ap.add_argument('--gate-mean', type=float, default=35.0,
                    help='mean_abs 阈值（默认 35：锁机位档 20 左右，真推镜档 45~65）')
    a = ap.parse_args()

    rows = []
    for mp4 in sorted(glob.glob(os.path.join(a.clips_dir, '*.mp4'))):
        f0, f1 = frames(mp4)
        s = drift_score(f0, f1)
        # 双阈值：max_cell 抓局部推近，mean_abs 抓整幅位移。只过一条算 SOFT——夜景星点/颗粒
        # 会让 max_cell 虚高（2026-11-15 实测 XQ38_09 max_cell=72 但人眼首末帧一致，mean 仅 26），
        # 真推镜两条都高（XQ38_01 批内版 87/48.6，试点锁机位版 40/20.2）。
        if s['max_cell'] > a.gate_maxcell and s['mean_abs'] > a.gate_mean:
            verdict = 'DRIFT'
        elif s['max_cell'] > a.gate_maxcell or s['mean_abs'] > a.gate_mean:
            verdict = 'SOFT'
        else:
            verdict = 'HOLD'
        rows.append(dict(id=os.path.basename(mp4)[:-4], **s, verdict=verdict))
        print('%-12s mean=%5.2f max_cell=%6.2f hot=%2d -> %s'
              % (rows[-1]['id'], s['mean_abs'], s['max_cell'], s['hot_cells'], verdict))

    n = len(rows)
    bad = [r['id'] for r in rows if r['verdict'] == 'DRIFT']
    soft = [r['id'] for r in rows if r['verdict'] == 'SOFT']
    print('\nSUMMARY clips=%d hold=%d soft=%d drift=%d'
          % (n, n - len(bad) - len(soft), len(soft), len(bad)))
    if soft:
        print('soft_ids=' + ','.join(soft) + ' (单阈值超标，须人眼复核)')
    if bad:
        print('drift_ids=' + ','.join(bad))
    if a.json:
        json.dump(rows, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('json ->', a.json)


if __name__ == '__main__':
    main()

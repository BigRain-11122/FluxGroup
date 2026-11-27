# -*- coding: utf-8 -*-
"""b 类构图重构判据：逐帧做人脸检测 + 头部朝向代理，比较镜内变化。

背景：qc_i2v_drift.py 的像素网格差只能抓 a 类相机漂移，
对「并肩同坐 -> 背靠背」这类主体间关系重构几乎无反应（xq19 max_cell 仅 30）。
本工具改用 scrfd 人脸框与 5 关键点：
  - 人脸数变化（2 张变 1 张或反之）
  - 同序人脸框中心位移（归一化到画面宽度）
  - 同序人脸框 iou
  - 朝向代理 nx=(鼻尖x-双眼中点x)/瞳距，偏航越大绝对值越大
任一超阈值判 pose-rebuild。

为什么不用 2d106det：5 关键点已足够区分正面/背靠背（后者鼻子落到双眼外侧），
再叠 106 点会多一层对齐误差，对判据没有增量。

用法（须用含 insightface 的解释器，默认 comfyui 的 python_embeded）：
  D:\\ComfyUI\\python_embeded\\python.exe qc_i2v_face.py <clips_dir> [--samples 3] [--json out.json]
"""
import argparse, glob, json, os, subprocess, tempfile

import numpy as np
from PIL import Image

MODEL_ROOT = r'D:\ComfyUI\ComfyUI\models\insightface'
MODEL_NAME = 'antelopev2'

_app = None


def app():
    """懒加载只含检测分支的 faceanalysis（不载识别模型，省内存与时间）。"""
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        a = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT,
                         allowed_modules=['detection'],
                         providers=['CPUExecutionProvider'])
        a.prepare(ctx_id=-1, det_size=(640, 640))
        _app = a
    return _app


def sample_frames(mp4, n):
    """按总时长均匀抽 n 帧，返回 png 路径列表（含首末帧）。"""
    d = tempfile.mkdtemp(prefix='qcf_')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'default=nw=1:nk=1', mp4],
                           capture_output=True, text=True, check=True)
    dur = float(probe.stdout.strip() or 0)
    if dur <= 0:
        dur = 3.0
    ts = [0.0] if n < 2 else [dur * i / (n - 1) for i in range(n)]
    ts[-1] = max(0.0, dur - 0.08)
    out = []
    for i, t in enumerate(ts):
        p = os.path.join(d, 'f%02d.png' % i)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % t, '-i', mp4,
                        '-frames:v', '1', p], check=True)
        out.append(p)
    return out, dur


def faces_of(png):
    """返回 [{cx,cy,w,h,iou_key,nx}]，按框面积降序。"""
    img = np.asarray(Image.open(png).convert('RGB'))[:, :, ::-1].copy()
    h, w = img.shape[:2]
    rows = []
    for f in app().get(img):
        x0, y0, x1, y1 = [float(v) for v in f.bbox]
        kps = np.asarray(f.kps, dtype=np.float32)
        ex = (kps[0][0] + kps[1][0]) / 2.0
        ey = (kps[0][1] + kps[1][1]) / 2.0
        iod = float(np.hypot(kps[1][0] - kps[0][0], kps[1][1] - kps[0][1])) or 1.0
        rows.append(dict(
            cx=float((x0 + x1) / 2.0 / w), cy=float((y0 + y1) / 2.0 / h),
            bw=float((x1 - x0) / w), bh=float((y1 - y0) / h),
            nx=float((kps[2][0] - ex) / iod), ny=float((kps[2][1] - ey) / iod),
            box=(x0 / w, y0 / h, x1 / w, y1 / h)))
    rows.sort(key=lambda r: r['bw'] * r['bh'], reverse=True)
    return rows


def iou(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = iw * ih
    ua = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return float(inter / ua) if ua > 0 else 0.0


def compare(fa, fb):
    """比两帧人脸集合，取最差指标为代表。"""
    n = min(len(fa), len(fb))
    out = dict(n_a=len(fa), n_b=len(fb), count_delta=abs(len(fa) - len(fb)),
               shift=0.0, iou_min=1.0, dnx=0.0)
    for i in range(n):
        a, b = fa[i], fb[i]
        out['shift'] = max(out['shift'], float(np.hypot(a['cx'] - b['cx'], a['cy'] - b['cy'])))
        out['iou_min'] = min(out['iou_min'], iou(a['box'], b['box']))
        out['dnx'] = max(out['dnx'], abs(a['nx'] - b['nx']))
    for k in ('shift', 'iou_min', 'dnx'):
        out[k] = round(out[k], 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clips_dir')
    ap.add_argument('--samples', type=int, default=3)
    ap.add_argument('--json', default='')
    ap.add_argument('--gate-shift', type=float, default=0.12, help='人脸中心位移上限（画面宽度占比）')
    ap.add_argument('--gate-iou', type=float, default=0.35, help='人脸框 iou 下限')
    ap.add_argument('--gate-dnx', type=float, default=0.35, help='朝向代理变化上限（以瞳距为单位）')
    a = ap.parse_args()

    rows = []
    for mp4 in sorted(glob.glob(os.path.join(a.clips_dir, '*.mp4'))):
        cid = os.path.basename(mp4)[:-4]
        pngs, dur = sample_frames(mp4, a.samples)
        sets = [faces_of(p) for p in pngs]
        worst = dict(n_a=0, n_b=0, count_delta=0, shift=0.0, iou_min=1.0, dnx=0.0)
        for i in range(len(sets) - 1):
            c = compare(sets[i], sets[i + 1])
            worst['count_delta'] = max(worst['count_delta'], c['count_delta'])
            worst['shift'] = max(worst['shift'], c['shift'])
            worst['iou_min'] = min(worst['iou_min'], c['iou_min'])
            worst['dnx'] = max(worst['dnx'], c['dnx'])
        worst['n_a'], worst['n_b'] = sets[0].__len__(), sets[-1].__len__()

        # 归因分离：人脸框被推近/平移 = 相机在动（a 类）；扭头/人数变 = 主体重摆（b 类）
        camera, pose = [], []
        if worst['count_delta'] > 0:
            pose.append('facecount')
        if worst['shift'] > a.gate_shift:
            camera.append('shift')
        if worst['iou_min'] < a.gate_iou:
            camera.append('iou')
        if worst['dnx'] > a.gate_dnx:
            pose.append('yaw')
        reasons = pose + camera
        if pose:
            verdict = 'POSE-REBUILD'
        elif camera:
            verdict = 'DRIFT-CAMERA'
        elif worst['n_a'] == 0:
            verdict = 'NOFACE'
        else:
            verdict = 'HOLD'

        rows.append(dict(id=cid, dur=round(dur, 2), faces=[len(s) for s in sets],
                         **worst, verdict=verdict, reasons=reasons))
        print('%-12s dur=%4.1fs faces=%-12s dcount=%d shift=%.3f iou=%.2f dnx=%.2f -> %s %s'
              % (cid, dur, str([len(s) for s in sets]), worst['count_delta'],
                 worst['shift'], worst['iou_min'], worst['dnx'], verdict,
                 (','.join(reasons) if reasons else '')))

    n = len(rows)
    bad = [r['id'] for r in rows if r['verdict'] == 'POSE-REBUILD']
    cam = [r['id'] for r in rows if r['verdict'] == 'DRIFT-CAMERA']
    nof = [r['id'] for r in rows if r['verdict'] == 'NOFACE']
    print('\nSUMMARY clips=%d hold=%d rebuild=%d camera=%d noface=%d'
          % (n, n - len(bad) - len(cam) - len(nof), len(bad), len(cam), len(nof)))
    if bad:
        print('rebuild_ids=' + ','.join(bad))
    if cam:
        print('camera_ids=' + ','.join(cam))
    if nof:
        print('noface_ids=' + ','.join(nof))
    if a.json:
        json.dump(rows, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('json ->', a.json)


if __name__ == '__main__':
    main()

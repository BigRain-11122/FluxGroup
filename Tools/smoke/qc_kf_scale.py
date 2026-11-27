# -*- coding: utf-8 -*-
"""KF 出生地闸：KF 图像是否满足「它自己的提示词」里的景别。

来由（2026-11-15 实锚）：`kf/XQ13.png` 的提示词写的是 `A close-up of jman...`，
实际出的图是「男主背身 + 自行车 + 远处女主 + 蝴蝶」的中远景。KF 集 38/38 之前按
「手/构图/文字」三查 PASS，没人查「图对不对得上自己的提示词」这一位。
后果在 i2v 才暴露：首帧是中远景、提示词要特写，模型就在 3 秒里自己推成特写
（XQ38_13 末帧变成男主大特写），看起来像「跳镜」。

做法（纯机械、零模型依赖）：提示词里的景别词 → 期望的人脸高度占比区间；
用 scrfd 检最大脸，算 face_h / frame_h 落入哪一带。超出即判 MISMATCH。

判据（经验带，可按批微调）：
  extreme close-up / close-up   → 期望 ≥0.32
  medium close / medium shot    → 期望 0.12 ~ 0.55
  medium-wide                   → 期望 0.06 ~ 0.28
  wide / extreme wide / establishing → 期望 ≤0.16（或无脸）

用法：
  D:\\ComfyUI\\python_embeded\\python.exe qc_kf_scale.py <kf_dir> --prompts <kf_prompts.json> [--json out.json]
"""
import argparse, glob, json, os, re, sys

import numpy as np
from PIL import Image

MODEL_ROOT = r'D:\ComfyUI\ComfyUI\models\insightface'
MODEL_NAME = 'antelopev2'
_app = None

BANDS = [
    ('extreme close-up', 0.42, 1.01),
    ('close-up', 0.32, 1.01),
    ('medium close', 0.16, 0.60),
    ('medium-wide', 0.05, 0.30),
    ('medium shot', 0.10, 0.55),
    ('wide', 0.0, 0.16),
]


def app():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        a = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, allowed_modules=['detection'],
                         providers=['CPUExecutionProvider'])
        a.prepare(ctx_id=-1, det_size=(640, 640))
        _app = a
    return _app


def expect(prompt):
    low = prompt.lower()
    # 只对「镜头主体是人」的镜做景别判：close-up 也常用于脚/手/风筝/路面等非人脸主体
    #（XQ17a-d 是腿部特写、XQ23 是手，第一版没区分就把它们误判成 MISMATCH）。
    person = ('jman' in low) or ('20-year-old' in low) or (' girl ' in low) or ('boy' in low) \
        or ('his face' in low) or ('her face' in low)
    if not person:
        return None, None, None
    # 从「最具体」到「最泛」匹配；extreme wide 必须在 wide 之前判
    if 'extreme wide' in low or 'establishing shot' in low:
        return 'extreme wide', 0.0, 0.16
    for key, lo, hi in BANDS:
        if key in low:
            return key, lo, hi
    return None, None, None


def face_ratio(path):
    img = np.asarray(Image.open(path).convert('RGB'))[:, :, ::-1].copy()
    h, w = img.shape[:2]
    fs = app().get(img)
    if not fs:
        return 0.0, 0
    best = max(fs, key=lambda f: (f.bbox[3] - f.bbox[1]) * (f.bbox[2] - f.bbox[0]))
    return float((best.bbox[3] - best.bbox[1]) / h), len(fs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kf_dir')
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--json', default='')
    a = ap.parse_args()

    rows_src = json.load(open(a.prompts, encoding='utf-8'))
    by_id = {r['id']: r for r in rows_src}
    out = []
    mism = []
    for png in sorted(glob.glob(os.path.join(a.kf_dir, '*.png'))):
        kid = os.path.basename(png)[:-4]
        if kid not in by_id:
            continue
        band, lo, hi = expect(by_id[kid]['prompt'])
        if band is None:
            continue
        ratio, n = face_ratio(png)
        ok = (lo - 0.03) <= ratio <= (hi + 0.03)
        verdict = 'OK' if ok else 'MISMATCH'
        if not ok:
            mism.append(kid)
        out.append(dict(id=kid, band=band, ratio=round(ratio, 3), faces=n, verdict=verdict))
        print('%-8s band=%-13s face_h=%.3f faces=%d -> %s' % (kid, band, ratio, n, verdict))

    print('\nSUMMARY checked=%d mismatch=%d' % (len(out), len(mism)))
    if mism:
        print('mismatch_ids=' + ','.join(mism))
    if a.json:
        json.dump(out, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('json ->', a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())

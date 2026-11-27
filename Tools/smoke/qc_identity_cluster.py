# -*- coding: utf-8 -*-
"""身份一致性审计：把一组关键帧里的**所有人脸**做识别嵌入、聚类，量化「同一角色跨镜还是不是同一张脸」。

为什么按全部人脸聚类而不是每图最大脸：双人镜头里最大脸可能是男主也可能是女主，
按图取代表脸会把男女脸混在一起比，相似度必然低（首版实测被这一点坑过）。
正确做法：解开成「脸」这一层再聚类，得到 2 个主簇（男女各一）+ 少量离群，然后回填到图。

判据：
  - glintr100（antelopev2 内识别模型）出 512 维归一化嵌入，余弦相似度；
  - 贪心聚类：与簇心 ≥ --thr 归入（默认 0.42，arcface 同人经验线；低于 0.35 基本是不同人）；
  - 用 genderage 标注每簇性别，便于人工确认哪个簇是女主/男主；
  - 输出：每图每张脸的簇号与相似度、各簇规模、离群脸（不属于前两大簇）清单。

用法（须含 insightface 的解释器）：
  D:\\ComfyUI\\python_embeded\\python.exe qc_identity_cluster.py <image_dir> [--json out.json]
"""
import argparse, glob, json, os, sys

import numpy as np
from PIL import Image

MODEL_ROOT = r'D:\ComfyUI\ComfyUI\models\insightface'
MODEL_NAME = 'antelopev2'

_app = None


def app():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        a = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT,
                         allowed_modules=['detection', 'recognition', 'genderage'],
                         providers=['CPUExecutionProvider'])
        a.prepare(ctx_id=-1, det_size=(640, 640))
        _app = a
    return _app


def faces(path):
    img = np.asarray(Image.open(path).convert('RGB'))[:, :, ::-1].copy()
    out = []
    for f in app().get(img):
        x0, y0, x1, y1 = [float(v) for v in f.bbox]
        out.append(dict(emb=np.asarray(f.normed_embedding, dtype=np.float32),
                        area=float((x1 - x0) * (y1 - y0)),
                        bbox=[round(float(v), 1) for v in f.bbox],
                        det=round(float(f.det_score), 3),
                        gender='M' if int(f.gender) == 1 else 'F',
                        age=int(f.age) if f.age is not None else -1))
    out.sort(key=lambda r: r['area'], reverse=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image_dir')
    ap.add_argument('--json', default='')
    ap.add_argument('--thr', type=float, default=0.42, help='同人相似度阈值（余弦）')
    ap.add_argument('--pattern', default='*.png')
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.image_dir, a.pattern)))
    if not files:
        print('no images in %s' % a.image_dir)
        return 1

    clusters = []   # [{'centroid':vec,'members':[vec], 'g':Counter}]
    per_image = []
    total = 0
    for p in files:
        fid = os.path.basename(p).rsplit('.', 1)[0]
        fs = faces(p)
        recs = []
        for f in fs:
            total += 1
            best_c, best_s = -1, -1.0
            for ci, cl in enumerate(clusters):
                s = float(np.dot(f['emb'], cl['centroid']))
                if s > best_s:
                    best_c, best_s = ci, s
            if best_s >= a.thr:
                cl = clusters[best_c]
                cl['members'].append(f['emb'])
                cen = np.mean(np.stack(cl['members']), axis=0)
                cl['centroid'] = (cen / np.linalg.norm(cen)).astype(np.float32)
                cl['g'].append(f['gender'])
            else:
                clusters.append(dict(centroid=f['emb'].copy(), members=[f['emb']], g=[f['gender']]))
                best_c = len(clusters) - 1
            recs.append(dict(cluster=best_c, sim=(round(best_s, 3) if best_s > -1 else None),
                             gender=f['gender'], age=f['age'], bbox=f['bbox'], det=f['det']))
        per_image.append(dict(id=fid, faces=recs))
        pretty = ' '.join('c%d/%s/%s' % (r['cluster'], r['gender'],
                                         ('%.2f' % r['sim']) if r['sim'] is not None else 'new')
                          for r in recs) or 'NOFACE'
        print('%-16s n=%d %s' % (fid, len(recs), pretty))

    sizes = [len(c['members']) for c in clusters]
    order = np.argsort(sizes)[::-1]
    print('\nSUMMARY images=%d faces=%d clusters=%d sizes=%s'
          % (len(per_image), total, len(clusters), [int(sizes[i]) for i in order[:8]]))
    labels = []
    for rank, ci in enumerate(order[:4]):
        g = clusters[ci]['g']
        nf, nm = g.count('F'), g.count('M')
        labels.append('c%d n=%d %s' % (ci, sizes[ci], 'F' if nf >= nm else 'M'))
    print('top clusters: ' + ' | '.join(labels))

    keep = set(int(ci) for ci in order[:2] if sizes[ci] >= 2)
    off = []
    for r in per_image:
        for f in r['faces']:
            if f['cluster'] not in keep:
                off.append('%s:c%d(%s)' % (r['id'], f['cluster'], f['gender']))
    if off:
        print('off_main_faces=%d  %s' % (len(off), ','.join(off[:20])))
    noface = [r['id'] for r in per_image if not r['faces']]
    if noface:
        print('noface_images=%d  %s' % (len(noface), ','.join(noface)))

    if a.json:
        dump = dict(thr=a.thr, sizes=[int(s) for s in sizes],
                    cluster_gender={str(ci): ('F' if clusters[ci]['g'].count('F') >= clusters[ci]['g'].count('M') else 'M')
                                    for ci in range(len(clusters))},
                    keep_clusters=sorted(keep), images=per_image)
        json.dump(dump, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('json ->', a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())

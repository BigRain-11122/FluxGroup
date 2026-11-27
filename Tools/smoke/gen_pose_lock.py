# -*- coding: utf-8 -*-
"""单镜复验：XQ19 加姿势锁（保持首帧姿势/位置，不转身不走动）后是否还重构。"""
import io, json, os

R = r'K:\Fluxgroup\FluxGroup'
base = os.path.join(R, r'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\i2v-xq3-manifest.json')
man = json.load(io.open(base, encoding='utf-8'))
POSE_LOCK = (' The two people keep exactly the pose, seat position and body orientation of the first '
             'frame: shoulders side by side, facing the camera, no turning, no standing up, '
             'no walking, no re-staging; only breathing and small hair movement.')

out = []
for u in man['units']:
    if u['id'] == 'XQ38_19':
        u = dict(u)
        u['i2v_prompt'] = u['i2v_prompt'] + POSE_LOCK
        u['note'] = '姿势锁复验'
        out.append(u)

p = os.path.join(R, r'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\i2v-xq3-poselock-20261115.json')
io.open(p, 'w', encoding='utf-8', newline='\n').write(
    json.dumps({'note': 'XQ19 姿势锁复验', 'units': out}, ensure_ascii=False, indent=1))
print('units', len(out), '->', p)
print(out[0]['i2v_prompt'][-230:])

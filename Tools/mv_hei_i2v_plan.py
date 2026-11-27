# -*- coding: utf-8 -*-
"""把《黑色幽默》D2 的 89 镜转成 i2v manifest（h3_i2v_album 契约）。

要点：
  - 每镜 i2v 提示词只写"运动"：机位动作（按 D2 的 move 字段）+ 主体一个动作 + 环境动
  - 时长严格用 D2 窗长（2.0-5.7s，均在 10s 安全线内）
  - 帧必须已存在，缺帧不写进 manifest（宁少不假）
"""
import json
import os

ROOT = r'K:\Fluxgroup\FluxGroup'
BASE = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay')
PLAN = os.path.join(BASE, 'plan', 'hei-kf-prompts-v2.json')
FR = os.path.join(BASE, 'frames-hei-kf')
OUT = os.path.join(BASE, 'plan', 'hei-i2v-manifest.json')

CAM = {
    'static': 'locked-off camera, no camera movement',
    'pushin': 'the camera pushes in slowly with small amplitude',
    'pullout': 'the camera pulls back slowly with small amplitude',
    'pan': 'the camera pans laterally with small amplitude, slowing to a stop',
}
ENV = {
    'E': 'rain keeps running down the window and the neon behind it breathes slowly; dust drifts in the lamp light',
    'P': 'rain runs down the window behind him; the lamp light holds steady on his shoulder',
    'F': 'rain streak shadows move slowly across his face; the lamp flickers once',
}
ACT = {
    'F': ['his eyes lift from the keys toward the window, the jaw staying set',
          'he blinks once, slowly, and his throat moves',
          'his gaze drops to his own hand and holds there',
          'his head turns a few degrees toward the empty chair and stops'],
    'P': ['he sets the cassette recorder down and presses rewind, watching the reels turn',
          'he leans both hands on the piano lid and stays still',
          'he walks two steps to the window and rests one hand on the frame',
          'he turns the desk lamp a few degrees so the light slides across the keys'],
}

rows = json.load(open(PLAN, encoding='utf-8'))
units, missing = [], []
for i, r in enumerate(rows):
    fp = os.path.join(FR, r['id'] + '.png')
    if not os.path.isfile(fp):
        missing.append(r['id'])
        continue
    kind = r.get('kind', 'P')
    act = ACT.get(kind, ACT['P'])[i % len(ACT.get(kind, ACT['P']))]
    prompt = ('Single continuous take at 24fps, 16:9. %s. %s. %s. '
              'Restrained cinematic motion, camera and subject only, clean unlettered surfaces.'
              % (CAM.get(r.get('move', 'static'), CAM['static']), act, ENV.get(kind, ENV['P'])))
    units.append({
        'id': r['id'], 'shot': r['id'], 'track': 'HEI',
        'win_s': round(r['t1'] - r['t0'], 2), 'src_s': round(r['t1'] - r['t0'], 2),
        'speed': 1.0, 'width': 1344, 'height': 768, 'light': 'night',
        'frame': os.path.relpath(fp, ROOT).replace('\\', '/'),
        'note': r.get('seg', ''), 'i2v_prompt': prompt,
        'frame_bytes': os.path.getsize(fp), 'prompt_words': len(prompt.split()),
    })

man = {'policy': '黑色幽默 D4：89 镜 480P 验证档（锁机位+单动作+环境动·禁情绪词）',
       'gate': 'D3 群审 PANEL-hei-full；D2 v2 预算 PASS',
       'wave': 'hei-i2v-v2', 'total': len(units),
       'total_win_s': round(sum(u['win_s'] for u in units), 2), 'units': units}
json.dump(man, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('i2v manifest units=%d total=%.1fs missing_frames=%d -> %s'
      % (len(units), man['total_win_s'], len(missing), OUT))
if missing[:8]:
    print('  missing:', missing[:8])

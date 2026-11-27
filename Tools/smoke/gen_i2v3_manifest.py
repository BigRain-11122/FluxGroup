# -*- coding: utf-8 -*-
"""由 kf_prompts.json 机械派生 38 镜 i2v 清单（3 秒档 / 锁机位）。

原则：不手写新词面——取 KF 提示词里的「画面描述段」（Shot on 之前的部分），
再按 move 字段接一句运镜/主体运动约束，避免自造与 KF 不一致的描述。
"""
import io, json, os, re

R = r'K:\Fluxgroup\FluxGroup'
SRC = os.path.join(R, r'cph4\fleet\mv0001-handover\plan\kf_prompts.json')
KF_DIR = os.path.join(R, r'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\kf')
OUT = os.path.join(R, r'cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\i2v-xq3-manifest.json')
WIN = 3.0

MOVE = {
    'static': 'camera completely locked off, no zoom and no push-in',
    'pan': 'a very slow horizontal pan with small amplitude',
    'tilt': 'a very slow tilt with small amplitude',
    'pushin': 'an extremely slow push-in, at most a few percent of the frame',
    'track': 'a slow lateral track that keeps the subject centred',
    'handheld': 'a gentle handheld drift with minimal amplitude',
}

rows = json.load(io.open(SRC, encoding='utf-8'))
units, missing = [], []
for r in rows:
    sid = r['id']
    frame = os.path.join(KF_DIR, sid + '.png')
    if not os.path.isfile(frame):
        missing.append(sid)
        continue
    p = r['prompt']
    # 画面描述段 = "Shot on ..." 之前
    head = re.split(r'\s*Shot on ', p, maxsplit=1)[0].strip()
    mv = MOVE.get((r.get('move') or 'static').strip().lower(), MOVE['static'])
    grade = ('Warm 2000 Taiwanese telecine grade, warm skin tones, milky lifted blacks, '
             'visible 35mm film grain, halation on practical lights.')
    prompt = ('Single continuous take at 24fps, %s. %s %s Restrained continuous motion, '
              'camera and subject only.' % (mv, head, grade))
    units.append({
        'id': 'XQ38_' + sid.replace('XQ', ''),
        'track': 'XQ38',
        'win_s': WIN, 'speed': 1.0, 'src_s': WIN, 'policy_band': '3s',
        'frame': frame, 'i2v_prompt': prompt,
        'note': (r.get('note') or '')[:40],
    })

man = {'note': '星晴 38 镜 i2v · 3 秒档（H3 length=73）· 由 kf_prompts 机械派生，锁机位', 'units': units}
io.open(OUT, 'w', encoding='utf-8', newline='\n').write(json.dumps(man, ensure_ascii=False, indent=1))
print('units', len(units), 'missing frames', missing)
print('out', OUT)
wl = [len(u['i2v_prompt'].split()) for u in units]
print('prompt words min/avg/max', min(wl), sum(wl) // len(wl), max(wl))
print('sample:', units[0]['id'], '|', units[0]['i2v_prompt'][:150])

# -*- coding: utf-8 -*-
"""第二轮 KF 治愈：XQ03 / XQ13 景别不符（要近景，出成中景/中远景）。

依据（2026-11-15 `qc_kf_scale.py` 实测 + 人眼复核）：
  - XQ03 镜注「她上后座」，提示词 `A close-up of a 20-year-old Taipei girl...`，
    实际出图是「两人骑车的双人中景」（人脸高度占比 0.144）→ KF 不符提示词。
  - XQ13 镜注「因你而香=他看她（注视链）」，提示词 `A close-up of jman...`，
    实际出图是「男主背身 + 自行车 + 远处女主」的中远景（0.104）→ 同上。
  - 连带后果：i2v 拿到「首帧是中远景、提示词要近景」的组合，就在 3 秒里自己推成特写
    （XQ38_03 / XQ38_13 的末帧），看起来像跳镜。**病根在 KF，不在 i2v**。

治法沿用 XQ22 那次的口径：把景别与「谁在画面里、占多大」写死，并给出可见的距离线索
（head and shoulders filling the frame / from the chest up / at close distance），
不再只靠一个 close-up 词指望模型自己理解。

产出：plan/kf_prompts-fix2-20261115.json（继承原表全部闸字段，只换 prompt），
写完立刻过 preflight_gate.guard —— 不过闸就不许烧。
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)   # preflight_gate.py 在 Tools/ 下，不在 smoke/
sys.path.insert(0, TOOLS)
import preflight_gate as G  # noqa: E402

SRC = r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\plan\kf_prompts.json'
OUT = r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\plan\kf_prompts-fix2-20261115.json'

TAIL = ('Blue-hour dusk at 8000k over a 2000 taipei street corner, low-pressure sodium streetlamp '
        'pools at 2200k laying deep orange over ink-blue asphalt, aged hand-painted signboards and '
        'old neon tubes just waking. Shot on 35mm lens at f/2.8 with honest depth of field, 2000 '
        'telecine grade, warm skin tones, milky lifted blacks, blooming practical highlights, '
        'slight color bleed, shot on 35mm Kodak Vision 500T 5279, visible grain, halation on '
        'practical lights, as a film still from a 2000 Taiwanese music video.')

TAIL_GOLD = ('Warm late-afternoon sun at 3400k raking low across a grassy hillside, long shadows, '
             'the sky pale gold at the horizon. Shot on 35mm lens at f/2.8 with honest depth of '
             'field, 2000 telecine grade, warm skin tones, milky lifted blacks, blooming practical '
             'highlights, slight color bleed, shot on 35mm Kodak Vision 500T 5279, visible grain, '
             'halation on practical lights, as a film still from a 2000 Taiwanese music video.')

NEW = {
    'XQ03': ('A close-up at close distance of a 20-year-old Taipei girl of the year 2000 with a soft '
             'oval face, gentle almond eyes, a small rounded nose, medium-length straight black hair '
             'with a soft side fringe pinned by a small colored hair clip, her head and shoulders '
             'filling the frame from the chest up as she swings one leg over the rear rack of a '
             'campus bicycle, one hand gripping the seat rail, her chin lifted toward the boy ahead '
             'of her, in a plain knit tank top with low-rise jeans, the boy shoulder and the '
             'handlebar entering soft and out of focus at the left edge of the frame. ' + TAIL),
    'XQ13': ('A close-up at eye level of jman, a 20-year-old Taiwanese student with heavy-lidded '
             'monolid eyes, a thick lower lip, softly rounded cheeks, a flat round nose tip, a blunt '
             'rounded jaw and natural unretouched skin with visible pores, his face and shoulders '
             'filling the frame from the chest up, standing beside a campus bicycle, his head turned '
             'three-quarters away from camera as he looks off to the right at someone out of frame, '
             'a pale butterfly hovering in the air beside his shoulder, wearing a plain white '
             'short-sleeve shirt, the grassy hillside and a distant walking figure falling into soft '
             'out-of-focus background behind him. ' + TAIL_GOLD),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    rows = json.load(open(SRC, encoding='utf-8'))
    out = []
    for r in rows:
        if r['id'] in NEW:
            r = dict(r)
            r['prompt'] = NEW[r['id']]
            r['note'] = r.get('note', '') + '｜治愈2：景别写死（close-up + 距离线索），原先出成中景/中远景'
        if r['id'] in NEW:
            out.append(r)

    for r in out:
        tokens = {k: r.get(k, '') for k in ('shot', 'angle', 'move', 'grade', 'texture', 'scene', 'light')}
        fails = G.guard(shot_id=r['id'], prompt_text=r['prompt'], tokens=tokens, kf_verified=True,
                        kf_note='T2I KF 重烧：本轮修景别，无源帧，闸(1) N/A', kinds=r.get('kinds') or [])
        print('%-6s words=%d fails=%s' % (r['id'], len(r['prompt'].split()), fails or 'NONE'))
        if fails:
            print('   REFUSE：先改提示词再烧')
            return 1
    if a.dry:
        for r in out:
            print('\n[%s]\n%s' % (r['id'], r['prompt']))
        return 0
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('written -> %s  (%d prompts)' % (OUT, len(out)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

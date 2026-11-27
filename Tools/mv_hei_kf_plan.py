# -*- coding: utf-8 -*-
"""生成《黑色幽默》24 镜 KF 提示词（mv_kf_batch 契约），并按 PREFLIGHT-GATE 自检。

契约：[{id, prompt, scene, light, shot, angle, move, grade, texture, seed}]
一歌一律：冷蓝黑内景 + 唯一暖点铁架台灯 2200K；雨窗霓虹=唯一彩光；禁伪文字。
"""
import json
import os
import sys

ROOT = r'K:\Fluxgroup\FluxGroup'
OUT = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay', 'plan', 'jd-hei-kf-prompts.json')

STYLE = ("as a film still from a 2000 Taiwanese music video, 35mm film grain, "
         "low-key interior lighting, cold blue-black shadow with a single warm tungsten desk lamp "
         "at 2200K as the only warm source, rain-streaked window with distant neon as the only colour, "
         "restrained practical bloom, black lifted slightly with the toe intact, clean unlettered surfaces")

SUBJ_MAN = ("an unnamed young Taiwanese man around 25 with short black hair, plain dark shirt, "
            "seen from behind or in profile only")

# id, scene(detail), shot, angle, move, light, texture
SHOTS = [
    ("B01", "an empty night piano room, an old upright piano, an iron-frame desk lamp lit, rain running down the window, dust in the air", "wide", "eye", "static", "night", "film_night"),
    ("B02", "extreme close-up of the piano lid half open, a hand hovering above the keys, the fingers still lifted", "ecu", "high", "static", "night", "film_night"),
    ("B03", "the man sitting on the piano bench, seen from behind, the tungsten side light cutting his shoulder line", "med", "eye", "static", "night", "film_night"),
    ("B04", "profile half face of the man, the desk lamp splitting the face into one lit side and one dark side", "cu", "eye", "static", "night", "film_night"),
    ("B05", "extreme close-up of fingers pressing the first key, black and white keys filling the frame", "ecu", "high", "static", "night", "film_night"),
    ("B06", "the rain-streaked window with distant neon beyond it, the room reflected faintly in the glass", "wide", "eye", "static", "night", "film_night"),
    ("B07", "the man looking up at a stopped wall clock, his face half in shadow", "med", "low", "static", "night", "film_night"),
    ("B08", "close-up of peeling wallpaper edge, the wall breaking down detail by detail", "cu", "eye", "static", "night", "film_night"),
    ("B09", "close-up of an old cassette recorder, a finger pressing the rewind key", "cu", "high", "static", "night", "film_night"),
    ("B10", "the man lowering his head with a small self-mocking smile, only once in the whole film", "cu", "eye", "static", "night", "film_night"),
    ("B11", "extreme close-up of both hands moving fast across the keys, motion in the fingers only", "ecu", "high", "static", "night", "film_night"),
    ("B12", "the man leaning his head back with eyes closed, side-back light rimming his jaw", "med", "low", "static", "night", "film_night"),
    ("B13", "four string-players as pure silhouettes behind the rain window, the bodies unreadable dark shapes", "wide", "eye", "static", "night", "film_night"),
    ("B14", "the man looking at his own reflection in the dark mirror glass", "med", "eye", "static", "night", "film_night"),
    ("B15", "an empty chair beside the piano, only the back of the chair visible, the seat empty", "med", "eye", "static", "night", "film_night"),
    ("B16", "extreme close-up of a fingertip pressing a piano string inside the open lid", "ecu", "high", "static", "night", "film_night"),
    ("B17", "the man and his double reflection separated in the glass, two layers of the same silhouette", "med", "eye", "static", "night", "film_night"),
    ("B18", "close-up of the clock hands moving backwards for a single second", "cu", "high", "static", "night", "film_night"),
    ("B19", "the long empty piano room, rain window, the lamp the only warm point, wide and still", "wide", "eye", "pushin", "night", "film_night"),
    ("B20", "the same piano room with one more object gone, emptier than before, same camera position", "wide", "eye", "static", "night", "film_night"),
    ("B21", "the man standing and singing, full body silhouette against the rain window", "hs", "low", "static", "night", "film_night"),
    ("B22", "the string silhouettes fully risen behind the window and the man's back in front of them", "wide", "eye", "static", "night", "film_night"),
    ("B23", "the room stripped down to only the piano and the lamp, everything else gone", "wide", "eye", "static", "night", "film_night"),
    ("B24", "rain falling upward back into the sky outside the window, one restrained closing image", "wide", "eye", "static", "night", "film_night"),
]

NEG_OK = ("night interior", "piano room")  # scene token 占位（下面写入 scene 字段）


def main():
    rows = []
    for i, (sid, detail, shot, angle, move, light, tex) in enumerate(SHOTS):
        subj = SUBJ_MAN if sid not in ("B01", "B02", "B05", "B06", "B08", "B09", "B13", "B15", "B16", "B18", "B19", "B20", "B23", "B24") else "the empty room"
        prompt = "A %s of %s, %s. %s. Shot on 35mm, %s." % (
            {"wide": "wide shot", "med": "medium shot", "cu": "close-up",
             "ecu": "extreme close-up", "hs": "full shot"}[shot], detail, STYLE, "", "")
        # 人物锚只在有人的镜里加
        if subj == SUBJ_MAN:
            prompt = "A %s of %s, %s. %s. Shot on 35mm, %s." % (
                {"wide": "wide shot", "med": "medium shot", "cu": "close-up",
                 "ecu": "extreme close-up", "hs": "full shot"}[shot], subj, detail, STYLE, "")
        rows.append({
            "id": sid, "prompt": prompt,
            "scene": "piano_room", "light": light,
            "shot": shot, "angle": angle, "move": move,
            "grade": "tw2001", "texture": tex,
            "seed": 20261121 + i,
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT, len(rows), 'shots')
    print(rows[0]['prompt'][:200])

    # 预检闸自检
    sys.path.insert(0, os.path.join(ROOT, 'Tools'))
    import preflight_gate as G
    bad = 0
    for r in rows:
        f = G.guard(r['id'], r['prompt'],
                    {k: r.get(k) for k in ('shot', 'angle', 'move', 'grade', 'texture', 'scene', 'light')},
                    kf_verified=True, kf_note='t2i KF（无源帧）', profile='mv')
        if f:
            bad += 1
            print('GATE-FAIL', r['id'], ' ; '.join(f)[:200])
    print('GATE pass %d/%d' % (len(rows) - bad, len(rows)))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

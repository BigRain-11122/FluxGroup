# -*- coding: utf-8 -*-
"""drama_canon.py — 漫剧/短剧角色与画风正典块（单一真值源）。

来源：cph4/fleet/drama-dept-v1/epburn-handover/drama_ep_burn.py（bm-b r989 交付，
60 集量产实证线）的 IDS / IDS_C / STYLE / STYLE_C / NEG / ALIAS / FULLNAME / expand_c。
抽成模块的原因（2026-11-20）：plan（剧本→prompt 表）与 batch（prompt 表→图）必须
用同一套锚，否则第 3 站两半各说各话，跨集一致性无从谈起。

两档：
  IDS/STYLE    = 长档（SDXL 用，token 预算宽裕）
  IDS_C/STYLE_C= 压档（SD1.5 77-token 预算；SDXL 也可用，稳健）

改 canon 一律改这里，勿在调用方复制常量（10-25 判例：模板与调用侧各改一处=18 帧白改）。
"""

STYLE = (
    '1990s hong kong seinen manga art style, dramatic cinematic composition, inked outlines, cel shading, '
    'moody noir atmosphere, muted teal and amber palette, subtle film grain, detailed background art'
)
STYLE_C = '1990s hong kong seinen manga, ink outlines, cel shading, teal amber palette, film grain'

IDS = {
    'CH': 'a determined young man around 22, sharp cool eyes, neat black hair, crisp white dress shirt, '
          'thin steel watch chain on wrist, 1990s style',
    'XIONG': 'a composed silver-templed man around 50, black suit, dark red necktie, wooden prayer beads on '
             'wrist, serene unsettling smile',
    'RED': 'a poised young woman around 20, 1990s office skirt suit, calculator on a lanyard, neat ponytail',
    'MANCANG': 'a chubby cheerful man around 25, loud floral shirt, pager clipped to belt',
    'XIONGWEI': 'a cold young man around 24, all-black minimalist suit, rimless glasses, colder and sharper '
               'than his father',
    'FATHER': 'a weary middle-aged man in a rumpled dark 1993 suit, loosened tie, kind tired eyes, '
              'rain-soaked hair',
    'BOY': 'a 12-year-old schoolboy in a plain white shirt, wide frightened eyes looking upward',
}

IDS_C = {
    'CH': 'young man 22, black hair, white dress shirt, steel watch chain',
    'XIONG': 'man 50, silver temples, black suit, dark red necktie, prayer beads on wrist',
    'RED': 'young woman 20, ponytail, 1990s office skirt suit',
    'MANCANG': 'chubby man 25, loud floral shirt, pager on belt',
    'XIONGWEI': 'young man 24, all-black suit, rimless glasses',
    'FATHER': 'weary middle-aged man, rumpled dark suit, loosened tie',
    'BOY': '12-year-old schoolboy, plain white shirt',
}

ALIAS = {
    'XTC': 'XIONG', 'XW': 'XIONGWEI', 'MC': 'MANCANG', 'HL': 'RED',
    '散户甲': 'SD1', '散户乙': 'SD2',
}

_EXTRA_C = {
    'SD1': 'middle-aged retail investor, worn 1990s jacket',
    'SD2': 'older retail investor, reading glasses, bankbook',
    'CROWD': 'dense anxious crowd, 1990s clothing',
    'WAITER': 'teahouse waiter, white vest, towel on arm',
}
_EXTRA = {
    'SD1': 'a wary middle-aged retail investor in a worn 1990s jacket',
    'SD2': 'an older retail investor holding a bankbook, reading glasses, 1990s style',
    'CROWD': 'a dense anxious crowd of retail investors in 1990s clothing',
    'WAITER': 'a teahouse waiter in a white vest, towel over arm, 1990s style',
}
IDS_C.update(_EXTRA_C)
IDS.update(_EXTRA)
for _a, _t in ALIAS.items():
    if _t in IDS_C:
        IDS_C[_a] = IDS_C[_t]
    if _t in IDS:
        IDS[_a] = IDS[_t]

NEG = (
    'photograph, photorealistic, 3d render, cgi, blurry, deformed face, deformed hands, extra fingers, '
    'bad anatomy, watermark, text, letters, words, numbers, speech bubbles, logo, signature, low quality, '
    'worst quality, jpeg artifacts, oversaturated, chibi, cute kawaii, sticker, plain white background'
)

FULLNAME = [
    ('Lu Changhong', 'CH'), ('Chang Hong', 'CH'), ('Changhong', 'CH'),
    ('Wang Mancang', 'MANCANG'), ('Shen Hongli', 'RED'), ('Man Cang', 'MANCANG'),
    ('Mancang', 'MANCANG'), ('Hongli', 'RED'), ('Hong Li', 'RED'),
    ('Xiong Tiancheng', 'XIONG'), ('Xiong Wei', 'XIONGWEI'), ('Xiong', 'XIONG'),
    ('散户甲', 'SD1'), ('散户乙', 'SD2'),
]


def anchor_of(k, compact=False):
    """角色 token → 视觉锚串；未知 token 返回 None（EP025 判例：防 KeyError 冻全线）。"""
    table = IDS_C if compact else IDS
    if k in table:
        return table[k]
    t = ALIAS.get(k)
    if t and t in table:
        return table[t]
    return None


def _normalize(text):
    out = text or ''
    for full, tok in FULLNAME:
        out = out.replace(full, tok + ' ')
    return out


# 零否定律（PREFLIGHT-GATE-v1 ③）：否定词会把目标"叫出来"，命中即拒烧。
# 剧本 detail_en 里天然会出现 "with no person in frame" 这类写法，所以在**生成阶段**
# 就换成正向说法，而不是让闸去拒——闸是兜底，不是日常返工的理由。
_NEG_REWRITE = [
    ("with no person in frame", "the frame holding the object alone"),
    ("no person in frame", "the frame holding the object alone"),
    ("no person enters the frame", "the frame stays empty of people"),
    ("nothing else in frame", "the frame holding only this"),
    ("without any people", "the setting standing empty"),
]
_NEG_TOKENS = ("no ", "not ", "never ", "without", "avoid", "don't", "doesn't", "won't", "non-")


def de_negate(text):
    """把否定句改写成正向句（③零否定）。先走短语表，再走兜底切句。"""
    out = text or ''
    low = out.lower()
    for src, dst in _NEG_REWRITE:
        if src in low:
            out = out.replace(src, dst).replace(src.capitalize(), dst)
            low = out.lower()
    # 兜底：把 "no/not/never/without..." 起到下一个逗号/句号之间的一小段整段删掉
    for tok in _NEG_TOKENS:
        while tok in out.lower():
            i = out.lower().find(tok)
            j = len(out)
            for sep in (',', '.', ';'):
                k = out.find(sep, i)
                if k != -1:
                    j = min(j, k)
            out = (out[:i].rstrip(' ,') + out[j:]).strip()
            out = out.replace('  ', ' ').replace(' ,', ',').replace(' ,', ',')
    return out.strip().rstrip(',')


def scene_token(detail_en):
    """把镜描述映射成预检闸的场景 token（④场景锚）。"""
    t = (detail_en or '').lower()
    if 'rooftop' in t:
        return 'drama_rooftop'
    if any(k in t for k in ('trading hall', 'hall', 'office', 'room', 'indoor', 'inside')):
        return 'drama_hall'
    if any(k in t for k in ('street', 'alley', 'road', 'sidewalk', 'corridor')):
        return 'drama_street'
    if any(k in t for k in ('skyline', 'aerial', 'city', 'mountain', 'field')):
        return 'drama_exterior'
    return 'drama_interior'


def move_token(detail_en):
    """KF 是静态首帧，运镜归 i2v 段；这里一律 static（禁在 KF 描述里命令镜头运动）。"""
    return 'static'


def expand(detail_en, ids, compact=False, budget_words=None, style=None, total_budget=None):
    """detail_en + 角色锚 → 最终正向提示词。

    compact=True 时按 CLIP 词预算裁剪场景尾巴（SD1.5 77-token 时代判例：
    超预算会静默吃掉 STYLE 与动作尾，表现为画风漂移）。
    长档同样有 total_budget（默认 78 词）：STYLE 在句尾，超限时被截断的正是
    调色/颗粒——2026-10-17 画风漂移判例的成因，所以宁可裁场景尾也不裁 STYLE。
    """
    st = style if style is not None else (STYLE_C if compact else STYLE)
    scene = de_negate(_normalize(detail_en))
    import re
    scene = re.sub(r"\s+", " ", scene).strip()
    ids = ids or []

    if compact:
        head = ', '.join(dict.fromkeys(a for a in (anchor_of(k, True) for k in ids) if a))
        budget = (budget_words if budget_words is not None else 55) - len(st.split()) - len(head.split()) - 2
        words = scene.split()
        if len(words) > budget > 0:
            scene = ' '.join(words[:budget])
        return (head + ', ' + scene + ', ' + st) if head else (scene + ', ' + st)

    # 长档：token 就地替换 + 未接住的角色尾部补锚
    for k in ids:
        a = anchor_of(k)
        if not a:
            continue
        scene = re.sub(re.escape(k) + r"(?=[\s'’.,:;!?—–-]|$)", a + ', ', scene)
    for k in ids:
        a = anchor_of(k)
        if a and a not in scene:
            scene += ', ' + a
    scene = re.sub(r",\s*,", ",", scene)

    tb = total_budget if total_budget is not None else 78
    room = tb - len(st.split()) - 1
    words = scene.split()
    if len(words) > room > 0:
        scene = ' '.join(words[:room]).rstrip(',;:') + ','
        scene = re.sub(r",\s*,", ",", scene)
    return scene + ' ' + st



def shot_tokens(detail_en, ids):
    """从镜描述里推结构化 token（供闸门与下游分诊用）。"""
    t = (detail_en or '').lower()
    if 'extreme close' in t:
        shot = 'ecu'
    elif 'close-up' in t or 'close up' in t:
        shot = 'cu'
    elif 'extreme wide' in t or 'aerial' in t:
        shot = 'ext'
    elif 'wide' in t:
        shot = 'wide'
    elif 'medium' in t or 'mid shot' in t:
        shot = 'med'
    elif 'full body' in t or 'full shot' in t:
        shot = 'hs'
    else:
        shot = 'med'
    if 'low-angle' in t or 'low angle' in t:
        angle = 'low'
    elif 'high-angle' in t or 'high angle' in t or 'overhead' in t:
        angle = 'high'
    elif 'top-down' in t or 'bird' in t or 'aerial' in t:
        angle = 'top'
    elif 'dutch' in t:
        angle = 'dutch'
    elif "over the shoulder" in t or 'over-the-shoulder' in t:
        angle = 'ots'
    else:
        angle = 'eye'
    return shot, angle

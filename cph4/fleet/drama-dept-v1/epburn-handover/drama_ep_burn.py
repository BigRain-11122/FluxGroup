# -*- coding: utf-8 -*-
# drama-001 60集量产烧制器：读 episodes/EP*.json → 逐镜生成 → media/drama-eps/eps-kf/
# 用法: python drama_ep_burn.py <起集> <止集>   （含两端；确定性种子·resume-safe）
# 律: ID 块逐字复用（BIBLE 视觉锚）·STEPS/CFG 同海选池配方·卡镜不烧（装配面）
import json, os, re, sys, time
sys.path.insert(0, r'C:\Fluxgroup\MiniGame\Tools\comfy')
import gen_placeholders as g

EPS_DIR = r'C:\Fluxgroup\FluxGroup\cph4\fleet\drama-001-stockera\episodes'
OUT = r'C:\Fluxgroup\FluxGroup\media\drama-eps\eps-kf'
os.makedirs(OUT, exist_ok=True)

IDS = {
    'CH': 'a determined young man around 22, sharp cool eyes, neat black hair, crisp white dress shirt, thin steel watch chain on wrist, 1990s style',
    'XIONG': 'a composed silver-templed man around 50, black suit, dark red necktie, wooden prayer beads on wrist, serene unsettling smile',
    'RED': 'a poised young woman around 20, 1990s office skirt suit, calculator on a lanyard, neat ponytail',
    'MANCANG': 'a chubby cheerful man around 25, loud floral shirt, pager clipped to belt',
    'XIONGWEI': 'a cold young man around 24, all-black minimalist suit, rimless glasses, colder and sharper than his father',
    'FATHER': 'a weary middle-aged man in a rumpled dark 1993 suit, loosened tie, kind tired eyes, rain-soaked hair',
    'BOY': 'a 12-year-old schoolboy in a plain white shirt, wide frightened eyes looking upward',
}
# alias tokens (EP007-009 A1b seat dialect -> canon anchors; extras get generic anchors)
IDS['XTC'] = IDS['XIONG']
IDS['XW'] = IDS['XIONGWEI']
IDS['MC'] = IDS['MANCANG']
IDS['HL'] = IDS['RED']
IDS['SD1'] = 'a wary middle-aged retail investor in a worn 1990s jacket'
IDS['SD2'] = 'an older retail investor holding a bankbook, reading glasses, 1990s style'
IDS['CROWD'] = 'a dense anxious crowd of retail investors in 1990s clothing'
IDS['WAITER'] = 'a teahouse waiter in a white vest, towel over arm, 1990s style'
STYLE = ('1990s hong kong seinen manga art style, dramatic cinematic composition, inked outlines, cel shading, '
         'moody noir atmosphere, muted teal and amber palette, subtle film grain, detailed background art')
# CLIP 77-token budget layer: SD1.5 text encoder truncates >77 tokens; the long-form
# IDS+STYLE stack (~90-120 tok) was silently cutting STYLE + scene tails on 80% of
# shots (art-style drift root cause, 2026-10-17 QC). Compact stacks fit in budget.
STYLE_C = '1990s hong kong seinen manga, ink outlines, cel shading, teal amber palette, film grain'
IDS_C = {
    'CH': 'young man 22, black hair, white dress shirt, steel watch chain',
    'XIONG': 'man 50, silver temples, black suit, dark red necktie, prayer beads on wrist',
    'RED': 'young woman 20, ponytail, 1990s office skirt suit',
    'MANCANG': 'chubby man 25, loud floral shirt, pager on belt',
    'XIONGWEI': 'young man 24, all-black suit, rimless glasses',
    'FATHER': 'weary middle-aged man, rumpled dark suit, loosened tie',
    'BOY': '12-year-old schoolboy, plain white shirt',
}
for _k in ('XTC', 'XW', 'MC', 'HL'):
    IDS_C[_k] = IDS_C[{'XTC': 'XIONG', 'XW': 'XIONGWEI', 'MC': 'MANCANG', 'HL': 'RED'}[_k]]
IDS_C['SD1'] = 'middle-aged retail investor, worn 1990s jacket'
IDS_C['SD2'] = 'older retail investor, reading glasses, bankbook'
IDS_C['CROWD'] = 'dense anxious crowd, 1990s clothing'
IDS_C['WAITER'] = 'teahouse waiter, white vest, towel on arm'
IDS_C['散户甲'] = IDS_C['SD1']
IDS_C['散户乙'] = IDS_C['SD2']
NEG = ('photograph, photorealistic, 3d render, cgi, blurry, deformed face, deformed hands, extra fingers, bad anatomy, '
       'watermark, text, letters, words, numbers, speech bubbles, logo, signature, low quality, worst quality, '
       'jpeg artifacts, oversaturated, chibi, cute kawaii, sticker, plain white background')
W, H, STEPS, CFG = 512, 768, 24, 7.0

# 全名/别名形态 -> canon token（长在前防子串误伤）；detail_en 席方言归一化
FULLNAME = [
    ('Lu Changhong', 'CH'), ('Chang Hong', 'CH'), ('Changhong', 'CH'),
    ('Wang Mancang', 'MANCANG'), ('Shen Hongli', 'RED'), ('Man Cang', 'MANCANG'),
    ('Mancang', 'MANCANG'), ('Hongli', 'RED'), ('Hong Li', 'RED'),
    ('Xiong Tiancheng', 'XIONG'), ('Xiong Wei', 'XIONGWEI'), ('Xiong', 'XIONG'),
    ('散户甲', 'SD1'), ('散户乙', 'SD2'),
]
ALIAS = {'XTC': 'XIONG', 'XW': 'XIONGWEI', 'MC': 'MANCANG', 'HL': 'RED',
         '散户甲': 'SD1', '散户乙': 'SD2'}

def anchor_of(k):
    if k in IDS:
        return IDS[k]
    if k in ALIAS and ALIAS[k] in IDS:
        return IDS[ALIAS[k]]
    return None  # 未知 token 跳过，防 KeyError 冻结全线（EP025 判例）

def expand(detail_en, ids):
    out = detail_en
    for full, tok in FULLNAME:  # 全名 -> canon token，让 ids 正则能接住
        out = out.replace(full, tok + ' ')
    for k in ids:
        a = anchor_of(k)
        if a is None:
            continue
        # token 后跟空格/撇号/标点/结尾均注入（旧版只认尾随空格 -> 631/1236 镜零锚）
        out = re.sub(re.escape(k) + r"(?=[\s'’.,:;!?—–-]|$)", a + ', ', out)
    for k in ids:  # 兜底：文内任何形态未接住的，尾部强制注入保人物一致
        a = anchor_of(k)
        if a and a not in out:
            out += ', ' + a
    return out

def anchor_of_c(k):
    if k in IDS_C:
        return IDS_C[k]
    if k in ALIAS and ALIAS[k] in IDS_C:
        return IDS_C[ALIAS[k]]
    return None

def expand_c(detail_en, ids):
    """CLIP-budget prompt (SD1.5 77-token limit): compact anchors FIRST (subject
    weight), scene next, compact style last; scene tail is trimmed if a rare
    long scene overflows the 55-word (~74 token) budget."""
    head = ', '.join(dict.fromkeys(a for a in (anchor_of_c(k) for k in ids) if a))
    scene = detail_en
    for full, tok in FULLNAME:
        scene = scene.replace(full, tok + ' ')
    budget = 55 - len(STYLE_C.split()) - len(head.split()) - 2
    words = scene.split()
    if len(words) > budget > 0:
        scene = ' '.join(words[:budget])
    return (head + ', ' + scene + ', ' + STYLE_C) if head else (scene + ', ' + STYLE_C)

def main(ep_lo, ep_hi):
    g.wait_server()
    t0, done = time.time(), 0
    for ep in range(ep_lo, ep_hi + 1):
        pj = os.path.join(EPS_DIR, 'EP%03d.json' % ep)
        if not os.path.exists(pj):
            print('EP_JSON_MISSING %d' % ep, flush=True)
            continue
        spec = json.load(open(pj, encoding='utf-8'))
        for s in spec.get('shots', []):
            n, kind = s.get('n'), s.get('kind', 'in')
            if kind == 'card':
                continue  # 字卡=装配面
            name = 'EP%03d_%02d' % (ep, n)
            path = os.path.join(OUT, name + '.png')
            if os.path.exists(path) and os.path.getsize(path) > 10000:
                continue
            seed = 91000000 + ep * 100 + n  # 确定性·可复刻
            pos = expand_c(s.get('detail_en', ''), s.get('ids', []))
            job = dict(name=name, kind='raw', w=W, h=H, seed=seed, steps=STEPS, cfg=CFG,
                       pos=pos, neg=NEG)
            job['esrgan'] = False
            raw, gs = g.run_job(job)
            with open(path, 'wb') as f:
                f.write(raw)
            done += 1
            print('GEN %s %.1fs elapsed=%.0fs' % (name, gs, time.time() - t0), flush=True)
    print('EPBURN_DONE imgs=%d elapsed=%.0fs' % (done, time.time() - t0), flush=True)

def remaining():
    miss = 0
    for ep in range(1, 61):
        pj = os.path.join(EPS_DIR, 'EP%03d.json' % ep)
        if not os.path.exists(pj):
            continue
        try:
            spec = json.load(open(pj, encoding='utf-8'))
        except Exception:
            miss += 1
            continue
        for s in spec.get('shots', []):
            if s.get('kind') == 'card':
                continue
            p = os.path.join(OUT, 'EP%03d_%02d.png' % (ep, s.get('n')))
            if not (os.path.exists(p) and os.path.getsize(p) > 10000):
                miss += 1
    print('EPBURN_REMAIN %d' % miss, flush=True)

if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[3] == '--check':
        remaining()
    else:
        main(int(sys.argv[1]), int(sys.argv[2]))

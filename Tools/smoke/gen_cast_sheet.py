# -*- coding: utf-8 -*-
"""角色设定图纸生成器：为「人物 LoRA」造多角度训练集（Krea2 turbo 直出）。

为什么需要它：把成片关键帧当训练集不可行——实测 38 镜里只有 7 张能检出人脸，
且双人镜最大脸可能是男主也可能是女主；而现成的 lora-dataset 两组各 16 张其实是
同一张正面像的近重复（dHash 距离中位数 9/256，120 对里 106~120 对 ≤20），
拿它训出来的 LoRA 只会在正面像上过拟合，换个角度就崩。

做法：用统一身份描述块 + 分镜表（角度 × 景别 × 表情 × 光位）批量出图，
让「同一张脸」在 24 个视角下重复出现，再用 qc_identity_cluster.py 把跑偏的脸剔掉，
剩下的才是能训的集子。

注意：角色设定图不是成片镜头，不套 MV 的 preflight_gate（那套闸校验的是
tw2001 调色/场景锚/刻痕锚），这里只保证提示词正向、无否定词。

用法（GPU 空闲时）：
  python gen_cast_sheet.py --char xq_her --dry-run          # 只打印提示词
  python gen_cast_sheet.py --char xq_her --burn             # 真烧（GPU）
"""
import argparse, json, os, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
from mv_kf_batch import graph, _resolve_model  # noqa: E402  复用已验证的 krea2 工作流

# ── 角色卡：身份块与服装从正典提示词里抽，改这里就等于改训练集的「真身」 ──────────────
CHARS = {
    'xq_her': dict(
        token='ljher',
        identity=('a 20-year-old Taipei girl of the year 2000 with a soft oval face, '
                  'gentle almond eyes, a small rounded nose, medium-length straight black hair '
                  'with a soft side fringe pinned by a small colored hair clip'),
        outfits=[
            'a plain cream knit tank top, low-rise blue jeans and canvas shoes',
            'a white cotton blouse tucked into a dark denim skirt and canvas shoes',
            'a pale blue short-sleeve school shirt, dark trousers and white canvas shoes',
        ],
        grade='2000 telecine grade, warm skin tones, milky lifted blacks',
    ),
    'xq_him': dict(
        token='jman',
        identity=('a 20-year-old Taiwanese student with heavy-lidded monolid eyes, a thick lower '
                  'lip, softly rounded cheeks, a flat round nose tip, a blunt rounded jaw and '
                  'natural unretouched skin with visible pores'),
        outfits=[
            'a plain white short-sleeve shirt, dark denim jeans and worn canvas shoes',
            'a loose grey crew-neck sweatshirt over a white tee, straight dark trousers',
            'an open washed-denim jacket over a white tee, loose dark jeans and canvas shoes',
        ],
        grade='2000 telecine grade, warm skin tones, milky lifted blacks',
    ),
}

# 视角表：(后缀, 景别, 机位, 表情/动作, 光位)
VIEWS = [
    ('front_cu',      'close-up portrait',            'at eye level',        'neutral expression, looking straight ahead', 'soft overcast daylight'),
    ('three_q_left',  'medium shot',                  'at eye level',        'body angled to her right, head turned to camera', 'soft overcast daylight'),
    ('three_q_right', 'medium shot',                  'at eye level',        'body angled to her left, head turned to camera', 'soft overcast daylight'),
    ('profile_left',  'close-up portrait',            'at eye level',        'full left profile', 'soft overcast daylight'),
    ('profile_right', 'close-up portrait',            'at eye level',        'full right profile', 'soft overcast daylight'),
    ('back_head',     'medium shot',                  'from behind',         'back of head and shoulders, face turned slightly away', 'soft overcast daylight'),
    ('low_angle',     'medium shot',                  'from slightly below','chin lifted, eyes toward the sky', 'warm tungsten night light'),
    ('high_angle',    'medium shot',                  'from above',         'face tilted down toward the lens', 'soft overcast daylight'),
    ('wide_walk',     'wide full-length shot',        'at eye level',       'walking mid-stride, arms relaxed', 'warm late afternoon sun'),
    ('seated_away',   'medium-wide shot',             'at eye level',       'sitting on a low step, head turned away in three-quarter back view', 'warm tungsten night light'),
    ('smile_cu',      'close-up portrait',            'at eye level',        'soft closed-mouth smile', 'soft overcast daylight'),
    ('downcast',      'close-up portrait',            'at eye level',        'eyes cast down, lips relaxed', 'warm tungsten night light'),
]

TAIL = ('Shot on 35mm lens at f/2.8 with honest depth of field, {grade}, blooming practical '
        'highlights, shot on 35mm Kodak Vision 500T 5279, visible grain, plain neutral grey studio '
        'background, a character reference photograph.')


def build_prompts(char, seed, outfit_i=-1):
    card = CHARS[char]
    rows = []
    for i, (sfx, shot, angle, expr, light) in enumerate(VIEWS):
        outfit = card['outfits'][outfit_i] if outfit_i >= 0 else card['outfits'][i % len(card['outfits'])]
        p = ('%s, %s of %s, wearing %s, %s, %s, %s.'
             % (card['token'], shot, card['identity'], outfit, expr, angle, light))
        p += ' ' + TAIL.format(grade=card['grade'])
        rows.append(dict(id='%s_%s' % (card['token'], sfx), prompt=p,
                         shot=shot, angle=angle, expr=expr, light=light,
                         outfit=outfit, seed=seed + i))
    return rows


def post(server, path, payload):
    req = urllib.request.Request(server + path, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(server, path):
    return json.loads(urllib.request.urlopen(server + path, timeout=30).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--char', required=True, choices=sorted(CHARS))
    ap.add_argument('--out', default=r'K:\Fluxgroup\FluxGroup\media\mv0001-handover\cast-dataset')
    ap.add_argument('--server', default='http://127.0.0.1:8188')
    ap.add_argument('--seed', type=int, default=771000)
    ap.add_argument('--size', type=int, default=1024)
    ap.add_argument('--steps', type=int, default=8)
    ap.add_argument('--unet', default='krea2_turbo_int8_convrot.safetensors')
    ap.add_argument('--clip', default='qwen3vl_4b_fp8_scaled.safetensors')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--burn', action='store_true')
    a = ap.parse_args()

    rows = build_prompts(a.char, a.seed)
    dst_dir = os.path.join(a.out, a.char)
    os.makedirs(dst_dir, exist_ok=True)
    with open(os.path.join(dst_dir, 'prompts.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    if a.dry_run or not a.burn:
        for r in rows:
            print('[%s] %s' % (r['id'], r['prompt']))
        print('\n(dry-run) %d prompts -> %s' % (len(rows), dst_dir))
        return 0

    unet = _resolve_model(('unet', 'diffusion_models'), a.unet) or a.unet
    clip = _resolve_model(('text_encoders', 'clip'), a.clip) or a.clip
    get(a.server, '/system_stats')
    print('UNET=%s CLIP=%s' % (unet, clip), flush=True)

    ok = skip = fail = 0
    for r in rows:
        dst = os.path.join(dst_dir, r['id'] + '.png')
        if os.path.isfile(dst) and os.path.getsize(dst) > 50000:
            skip += 1
            print('SKIP %s' % r['id'], flush=True)
            continue
        pid = post(a.server, '/prompt', {'prompt': graph(r['prompt'], r['seed'], unet, clip,
                                                         a.size, a.size, a.steps),
                                         'client_id': str(uuid.uuid4())})['prompt_id']
        t0 = time.time()
        got = False
        while time.time() - t0 < 900:
            time.sleep(2)
            h = get(a.server, '/history/' + pid)
            if pid not in h:
                continue
            st = h[pid].get('status', {})
            if st.get('status_str') == 'error':
                print('ERROR %s :: %s' % (r['id'], json.dumps(st)[:300]), flush=True)
                break
            for out in h[pid]['outputs'].values():
                for img in out.get('images', []):
                    url = '%s/view?filename=%s&subfolder=%s&type=%s' % (
                        a.server, img['filename'], img.get('subfolder', ''), img.get('type', 'output'))
                    with open(dst, 'wb') as f:
                        f.write(urllib.request.urlopen(url, timeout=180).read())
                    # 与图同名的 caption：触发词 + 本图真实可见项（景别/表情/服装/光位）
                    cap = '%s, %s, %s, wearing %s, %s.' % (
                        CHARS[a.char]['token'], r['shot'], r['expr'], r['outfit'], r['light'])
                    with open(dst[:-4] + '.txt', 'w', encoding='utf-8') as f:
                        f.write(cap + '\n')
                    got = True
                    print('OK %s (%.1fs) %s' % (r['id'], time.time() - t0, cap), flush=True)
            break
        ok += 1 if got else 0
        fail += 0 if got else 1

    print('SUMMARY ok=%d skip=%d fail=%d -> %s' % (ok, skip, fail, dst_dir))
    return 0 if fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

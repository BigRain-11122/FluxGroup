# -*- coding: utf-8 -*-
# 占位图批量产线（素材两级铁律·本地免费层）v1
# 流程：等 ComfyUI 服务 → 每槽位出图（贴纸类=SD1.5直出+rembg透明底；宽幅类=SD1.5出图+ESRGAN x4放大）
#       → PIL 规格化到标准尺寸 → 像素级回读验收（角点alpha/中心不透明/精确尺寸）→ manifest
# 铁律标记：产物 tier=placeholder，占位不冒充上线成品，定稿由云端 frontier 线替换。
# v0=样板5件(manifest.json)；v1=起步套装15件(manifest-v1.json)，扩槽位=改下方 JOBS 表。
import json, os, struct, sys, time, urllib.request
import io
from PIL import Image, ImageEnhance, ImageFilter, ImageStat
from rembg import remove, new_session

BASE = 'http://127.0.0.1:8198'
OUT_DIR = r'C:\Fluxgroup\MiniGame\Tools\placeholder-pack'
CKPT = 'v1-5-pruned-emaonly.safetensors'
CKPT_STYLED = 'anything-v3.0-pruned-fp16.safetensors'  # stylized SD1.5 fine-tune, same arch slot-in
CKPT_DIR = r'C:\Fluxgroup\MiniGame\Tools\ComfyUI_windows_portable\ComfyUI\models\checkpoints'

def default_ckpt():
    # user order 2026-09-19 raise art quality: prefer the stylized checkpoint once on disk
    return CKPT_STYLED if os.path.exists(os.path.join(CKPT_DIR, CKPT_STYLED)) else CKPT
UPSCALE = 'RealESRGAN_x4plus.pth'
WIDE_TARGET = (1080, 1440)  # 竖屏 540x720 逻辑分辨率 @2x（P02 分享卡口径）
MANIFEST_NAME = 'manifest-v1.json'
PACK_NAME = 'placeholder-pack-v1'

STYLE_POS = 'flat vector sticker style, bold clean outline, vibrant pastel colors, kawaii mobile game asset, coherent single color palette, consistent soft lighting from top left'
# quality baseline + U024 compliance negatives (repo §7.6: fixed appended, jobs cannot waive)
STYLE_NEG = ('blurry, photorealistic, photo, 3d render, deformed, extra limbs, extra fingers, watermark, '
             'text, letters, words, numbers, signage, label, signature, logo, username, cropped, low quality, '
             'worst quality, jpeg artifacts, muddy colors, washed out, desaturated, dull colors, grainy, noise, '
             'harsh shadows, dark navy shadows, black shadows, weak outline, missing outline, '
             'objects cut off at frame edge, cluttered, busy background, inconsistent lighting, '
             'real person, celebrity, copyrighted character, trademark')

JOBS = [
    dict(name='placeholder_logo_512', kind='sticker', w=512, h=512, seed=101, slot='logo 512x512 transparent',
         pos='cute cartoon game logo emblem, star and heart motif, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_unit_bear_512', kind='sticker', w=512, h=512, seed=102, slot='unit sprite 512x512 transparent',
         pos='cute cartoon bear character, full body, big eyes, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_unit_slime_512', kind='sticker', w=512, h=512, seed=103, slot='unit sprite 512x512 transparent',
         pos='cute cartoon green slime creature, round body, happy face, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_unit_robot_512', kind='sticker', w=512, h=512, seed=104, slot='unit sprite 512x512 transparent',
         pos='cute cartoon tiny robot, round friendly design, small antenna, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_unit_cat_512', kind='sticker', w=512, h=512, seed=105, slot='unit sprite 512x512 transparent',
         pos='cute cartoon kitten character, full body, waving paw, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_unit_dragon_512', kind='sticker', w=512, h=512, seed=106, slot='unit sprite 512x512 transparent',
         pos='cute cartoon baby dragon, small wings, chubby body, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_unit_ghost_512', kind='sticker', w=512, h=512, seed=107, slot='unit sprite 512x512 transparent',
         pos='cute cartoon friendly ghost, floating, rosy cheeks, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_icon_coin_512', kind='sticker', w=512, h=512, seed=108, slot='resource icon 512x512 transparent',
         pos='cute cartoon gold coin icon, shiny star mark, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_icon_heart_512', kind='sticker', w=512, h=512, seed=109, slot='resource icon 512x512 transparent',
         pos='cute cartoon red heart icon, glossy highlight, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_icon_gem_512', kind='sticker', w=512, h=512, seed=110, slot='resource icon 512x512 transparent',
         pos='cute cartoon blue diamond gem icon, sparkling facets, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_card_item_512', kind='sticker', w=512, h=512, seed=111, slot='card art 512x512 transparent',
         pos='cute cartoon item box card art, gift box with ribbon bow, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_card_event_512', kind='sticker', w=512, h=512, seed=112, slot='card art 512x512 transparent',
         pos='cute cartoon event card art, treasure chest with light rays, single centered subject, ' + STYLE_POS + ', plain white background'),
    dict(name='placeholder_bg_battle_1080x1440', kind='wide', w=576, h=768, seed=113, slot='battle background 1080x1440 full-frame',
         pos='cute cartoon game battle arena background, pastel grass field and soft sky, vertical composition, no characters, no text'),
    dict(name='placeholder_share_result_1080x1440', kind='wide', w=576, h=768, seed=114, slot='result screen 1080x1440 full-frame',
         pos='cute cartoon game result screen background, trophy and confetti at top, empty lower area for score text, vertical composition, no text'),
    dict(name='placeholder_loading_1080x1440', kind='wide', w=576, h=768, seed=115, slot='loading screen 1080x1440 full-frame',
         pos='cute cartoon game loading screen background, dreamy pastel clouds and stars, vertical composition, empty center for progress bar, no text'),
]

def http(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def wait_server():
    t0 = time.time()
    while True:
        try:
            http(BASE + '/system_stats', timeout=5)
            print('SERVER_UP', flush=True)
            return
        except Exception:
            if time.time() - t0 > 300:
                print('SERVER_WAIT_TIMEOUT'); sys.exit(2)
            time.sleep(3)

def build_wf(job, upscale):
    ckpt = job.get('ckpt') or default_ckpt()
    # anime-lineage fine-tunes are trained with early clip stop; pair skip with checkpoint
    clip_skip = job.get('clip_skip', 2 if 'anything' in ckpt.lower() else 1)
    wf = {
        '3': {'class_type': 'KSampler', 'inputs': {'seed': job['seed'], 'steps': job.get('steps', 30), 'cfg': job.get('cfg', 7.5),
              'sampler_name': job.get('sampler', 'dpmpp_2m'), 'scheduler': job.get('scheduler', 'karras'), 'denoise': 1.0,
              'model': ['4', 0], 'positive': ['6', 0], 'negative': ['7', 0], 'latent_image': ['5', 0]}},
        '4': {'class_type': 'CheckpointLoaderSimple', 'inputs': {'ckpt_name': ckpt}},
        '5': {'class_type': 'EmptyLatentImage', 'inputs': {'width': job['w'], 'height': job['h'], 'batch_size': 1}},
        '6': {'class_type': 'CLIPTextEncode', 'inputs': {'text': job['pos'], 'clip': ['12', 0]}},
        '7': {'class_type': 'CLIPTextEncode', 'inputs': {'text': (job.get('neg') or STYLE_NEG), 'clip': ['12', 0]}},
        '12': {'class_type': 'CLIPSetLastLayer', 'inputs': {'stop_at_clip_layer': -int(clip_skip), 'clip': ['4', 1]}},
        '8': {'class_type': 'VAEDecode', 'inputs': {'samples': ['3', 0], 'vae': ['4', 2]}},
        '9': {'class_type': 'SaveImage', 'inputs': {'images': ['8', 0], 'filename_prefix': job['name']}},
    }
    if upscale:
        wf['10'] = {'class_type': 'UpscaleModelLoader', 'inputs': {'model_name': UPSCALE}}
        wf['11'] = {'class_type': 'ImageUpscaleWithModel', 'inputs': {'upscale_model': ['10', 0], 'image': ['8', 0]}}
        wf['9']['inputs']['images'] = ['11', 0]
    return wf

def run_job(job):
    upscale = job.get('esrgan', job['kind'] == 'wide')  # caller can force ESRGAN on any kind
    wf = build_wf(job, upscale)
    cid = 'ph-%d' % int(time.time())
    t0 = time.time()
    pid = json.loads(http(BASE + '/prompt',
                          data=json.dumps({'prompt': wf, 'client_id': cid}).encode(),
                          headers={'Content-Type': 'application/json'}))['prompt_id']
    while True:
        time.sleep(2)
        h = json.loads(http(BASE + '/history/' + pid))
        if pid in h:
            break
        if time.time() - t0 > 1800:
            print('GEN_TIMEOUT ' + job['name']); sys.exit(3)
    gen_s = round(time.time() - t0, 1)
    entry = h[pid]
    if entry.get('status', {}).get('status_str') == 'error':
        print('GEN_ERROR ' + job['name'] + ' ' + json.dumps(entry)[:800]); sys.exit(4)
    img_meta = None
    for node_out in entry.get('outputs', {}).values():
        for im in node_out.get('images', []):
            img_meta = im; break
        if img_meta:
            break
    if not img_meta:
        print('NO_IMAGE ' + job['name']); sys.exit(5)
    q = 'filename=%s&subfolder=%s&type=%s' % (urllib.request.quote(img_meta['filename']),
                                              urllib.request.quote(img_meta.get('subfolder', '')),
                                              img_meta.get('type', 'output'))
    raw = http(BASE + '/view?' + q, timeout=300)
    return raw, gen_s

def post_process(job, raw, session):
    img = Image.open(io.BytesIO(raw)).convert('RGB')
    if job['kind'] == 'sticker':
        out = isolate_main(remove(img, session=session))
        out = out.resize((512, 512), Image.LANCZOS)
        final_w, final_h = 512, 512
    else:
        out = img.resize(WIDE_TARGET, Image.LANCZOS)
        final_w, final_h = WIDE_TARGET
    path = os.path.join(OUT_DIR, job['name'] + '.png')
    out.save(path, 'PNG', optimize=True)
    return path, final_w, final_h

def verify(path, job):
    img = Image.open(path); img.load()
    w, h = img.size
    ok = img.size == ((512, 512) if job['kind'] == 'sticker' else WIDE_TARGET)
    notes = ['size=%dx%d' % (w, h), 'size_ok=%s' % ok]
    if job['kind'] == 'sticker':
        a = img.getchannel('A')
        corners = [a.getpixel(p) for p in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]]
        corners_ok = all(x <= 8 for x in corners)
        box = a.crop((w // 2 - 100, h // 2 - 100, w // 2 + 100, h // 2 + 100))
        opaque = sum(1 for p in box.getdata() if p >= 200)
        center_ok = opaque >= 20000
        notes += ['corner_alpha=%s' % corners, 'corners_ok=%s' % corners_ok, 'center_opaque_pct=%d' % (opaque * 100 // 40000), 'center_ok=%s' % center_ok]
        ok = ok and corners_ok and center_ok
    kb = os.path.getsize(path) // 1024
    notes.append('kb=%d' % kb)
    print('VERIFY %s %s -> %s' % (job['name'], ' '.join(notes), 'PASS' if ok else 'FAIL'), flush=True)
    return ok, kb

# --- quality toolkit shared with gen_art_requests.py (user order 2026-09-19: 提高标准·风格化·不出垃圾) ---

def quality_metrics(img):
    """Cheap CPU style metrics for candidate ranking and hard gates (256px downscale)."""
    import numpy as np
    small = img.convert('RGB').resize((256, 256))
    a = np.asarray(small).astype(np.float32) / 255.0
    rg = a[..., 0] - a[..., 1]
    yb = 0.5 * (a[..., 0] + a[..., 1]) - a[..., 2]
    colorfulness = float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))
    hsv = np.asarray(small.convert('HSV')).astype(np.float32) / 255.0
    sat = float(hsv[..., 1].mean())
    lum = float(hsv[..., 2].mean())
    contrast = float(a.mean(axis=2).std())
    edges = np.asarray(small.convert('L').filter(ImageFilter.FIND_EDGES)).astype(np.float32) / 255.0
    return dict(colorfulness=round(colorfulness, 3), sat=round(sat, 3), lum=round(lum, 1),
                contrast=round(contrast, 3), edges=round(float(edges.mean()), 3))

def style_score(m):
    """Higher = closer to the cute-pastel flat style anchor. Calibrated 2026-09-19."""
    sat_c = max(0.0, 1.0 - abs(m['sat'] - 0.45) / 0.45)   # punish washed-out AND toxic saturation
    con_c = min(m['contrast'] / 0.18, 1.0)
    cf_c = min(m['colorfulness'] / 0.50, 1.0)
    ed_c = max(0.0, 1.0 - abs(m['edges'] - 0.07) / 0.07)  # peak detail; punish mush and noise-fry
    return round(0.35 * cf_c + 0.30 * sat_c + 0.20 * con_c + 0.15 * ed_c, 3)

def make_seamless(img):
    """Mathematically tileable: cyclic roll joins edges exactly; original blended in center cross."""
    import numpy as np
    a = np.asarray(img.convert('RGB')).astype(np.float32)
    h, w = a.shape[:2]
    b = np.roll(a, (h // 2, w // 2), axis=(0, 1))
    mx = np.tile(np.minimum(np.arange(w), w - np.arange(w)), (h, 1)).astype(np.float32) / (w / 2.0)
    my = np.tile(np.minimum(np.arange(h), h - np.arange(h))[:, None], (1, w)).astype(np.float32) / (h / 2.0)
    m = (mx * my)[..., None]
    out = b * m + a * (1.0 - m)
    return Image.fromarray(out.clip(0, 255).astype('uint8'), 'RGB')

TILE_PALETTES = {  # locked macaron palettes (R5 terminal verdicts: source S raised so the
    #  avgLum bake keeps colors clean at game brightness; checker mint = director spec #B7E4CE)
    'mint_white': dict(base='#F4F2EC', accents=['#B7E4CE', '#F7E8B0', '#F2DE96', '#F7B8C8']),
    'warm_wood':  dict(base='#E9CDA9', accents=['#E0D6B3', '#E8C7B4', '#BECBD8']),  # cream-yellow/terracotta/gray-blue
    'lavender':   dict(base='#F2EDF7', accents=['#C9BCE8', '#F5C5D0']),
}

def shade(hex_color, k):
    r = int(hex_color[1:3], 16); g = int(hex_color[3:5], 16); b = int(hex_color[5:7], 16)
    f = lambda v: max(0, min(255, int(v * k)))
    return (f(r), f(g), f(b))

def make_tile(spec, size=512):
    """Procedural tile synthesis (A/B verdict: diffusion full-frame tiles are the wrong
    tool - '缝是数学缝的不是美术缝的'). 程序化 first per 07号§6 priority order.
    Round-2 director fixes: readable grout (#DED9D0-tier), de-latticed dot scatter with
    position jitter + two sizes, true per-plank segments (2-3/row, joints spaced from
    edges & previous row), per-plank grain bounded at joints, accent saturation
    pre-lowered for the avgLum bake. Deterministic via tile_seed."""
    import random
    import colorsys
    from PIL import ImageDraw
    if 'palette' in spec:
        spec = dict(TILE_PALETTES[spec['palette']], **{k: v for k, v in spec.items() if k != 'palette'})
    pat = spec.get('pattern', 'grid')
    rng = random.Random(spec.get('tile_seed', 7))
    base = spec.get('base', '#F5F3EC')
    accents = spec.get('accents', ['#A8D8C0'])

    def desat(rgb, f=0.82):
        h, l, s = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
        return tuple(int(v * 255) for v in colorsys.hls_to_rgb(h, l, s * f))

    img = Image.new('RGB', (size, size), base)
    d = ImageDraw.Draw(img)
    if pat in ('grid', 'checker'):
        cells = int(spec.get('cells', 4))
        grout = int(spec.get('grout_px', 3))
        pitch = size // cells
        grout_rgb = shade(base, float(spec.get('grout_shade', 0.58)))   # deep seam (>=40% lum delta)
        ao_rgb = shade(base, float(spec.get('ao_shade', 0.82)))
        ao = int(spec.get('ao_px', 1))
        for iy in range(cells):
            for ix in range(cells):
                x0, y0 = ix * pitch, iy * pitch
                k = 1.0 + rng.uniform(-0.03, 0.03)
                fill = shade(base, k)
                if pat == 'checker' and (ix + iy) % 2:
                    fill = shade(accents[0], k)
                d.rectangle([x0, y0, x0 + pitch, y0 + pitch], fill=fill)
                d.rectangle([x0, y0, x0 + pitch, y0 + grout], fill=grout_rgb)   # top seam (self-carried)
                d.rectangle([x0, y0, x0 + grout, y0 + pitch], fill=grout_rgb)   # left seam
                d.rectangle([x0 + grout, y0 + grout, x0 + pitch, y0 + grout + ao], fill=ao_rgb)  # edge AO
                d.rectangle([x0 + grout, y0 + grout, x0 + grout + ao, y0 + pitch], fill=ao_rgb)
        if spec.get('motif') == 'dot':
            # candy confetti PER BRICK: hard 3-6 count, ~equal 4-color ratio, center
            # kept >=5px off the seams (R5 verdict), no void rows/cols possible
            wcol = spec.get('dot_weights', [0.25, 0.25, 0.25, 0.25])
            for iy in range(cells):
                for ix in range(cells):
                    x0, y0 = ix * pitch, iy * pitch
                    inner = pitch - grout - ao
                    placed = []
                    n_d = rng.randint(3, 6)
                    for di in range(n_d):
                        r = inner * rng.uniform(0.09, 0.135)
                        if di == 0:
                            col = accents[(ix + iy) % len(accents)]  # first dot hue-cycles: 4-color spread
                        else:
                            col = rng.choices(accents, weights=wcol[:len(accents)])[0]
                        col = shade(col, 1.0)
                        cx = cy = None
                        for _ in range(8):  # keep centers apart so dots never visually merge
                            tx = rng.uniform(x0 + grout + ao + r + 5, x0 + pitch - r - 5)
                            ty = rng.uniform(y0 + grout + ao + r + 5, y0 + pitch - r - 5)
                            if all((tx - px) ** 2 + (ty - py) ** 2 >= (r + pr) ** 2 * 1.2 for (px, py, pr) in placed):
                                cx, cy = tx, ty
                                break
                        if cx is None:
                            cx, cy = tx, ty
                        placed.append((cx, cy, r))
                        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    elif pat == 'planks':
        rows = int(spec.get('rows', 6))
        ph = size // rows
        seam = int(spec.get('seam_px', 3))
        seam_rgb = shade(base, spec.get('seam_shade', 0.88))
        accent_ratio = float(spec.get('accent_ratio', 0.13))
        min_seg = int(spec.get('min_seg_px', 128))            # >= 1.5x plank width (verdict)
        edge_gap = int(spec.get('joint_edge_gap_px', 40))
        prev_cuts = []
        for iy in range(rows):
            y0 = iy * ph
            row_k = 1.0 + rng.uniform(-0.03, 0.03)
            # true segments: 2-3 planks per row, random lengths, joints spaced from tile edges
            cuts = None
            for _ in range(6):
                cand = []
                x = rng.uniform(edge_gap, edge_gap + 2.2 * ph)  # widened start: kills short-segment ghost columns
                while x < size - min_seg - edge_gap:
                    cand.append(int(x))
                    x += rng.uniform(min_seg + 10, 340)
                if cand and all(abs(c - p) >= ph for p in prev_cuts for c in cand):
                    cuts = cand
                    break
            if cuts is None:  # fallback must still respect the previous row (R3 H-joint bug fix)
                for _ in range(30):
                    cand = [rng.randint(edge_gap, size - edge_gap - min_seg)]
                    if all(abs(c - p) >= ph for p in prev_cuts for c in cand):
                        cuts = cand
                        break
                if cuts is None and prev_cuts:
                    cuts = [(prev_cuts[0] + 2 * ph) % (size - edge_gap - min_seg) + edge_gap]
                elif cuts is None:
                    cuts = [size // 2]
            prev_cuts = cuts
            bounds = [0] + cuts + [size]
            prev_accent = False
            prev_lum = None
            acc_w = spec.get('accent_weights', [0.4, 0.4, 0.2])  # warm-first; cold <= warm/2 (R5)
            for si in range(len(bounds) - 1):
                sx0, sx1 = bounds[si], bounds[si + 1]
                accent = (not prev_accent) and rng.random() < accent_ratio
                if accent:   # true hue rotation: cream-yellow/terracotta/gray-blue (R5 spec)
                    fill = shade(rng.choices(accents, weights=acc_w[:len(accents)])[0],
                                 1.0 + rng.uniform(-0.02, 0.02))
                else:        # adjacent planks must differ >=10 luminance (no post-bake mush)
                    fill = None
                    for _ in range(6):
                        cand = shade(base, row_k * rng.choice((0.94, 1.00, 1.06)) + rng.uniform(-0.01, 0.01))
                        lum = 0.299 * cand[0] + 0.587 * cand[1] + 0.114 * cand[2]
                        if prev_lum is None or abs(lum - prev_lum) >= 10:
                            fill = cand
                            break
                    if fill is None:
                        fill = shade(base, row_k * 0.94)
                prev_lum = 0.299 * fill[0] + 0.587 * fill[1] + 0.114 * fill[2]
                prev_accent = accent
                d.rectangle([sx0, y0, sx1, y0 + ph], fill=fill)
                for _ in range(2):  # per-plank grain: bounded at joints, slight wobble (fix #3)
                    gy = y0 + seam + 2 + rng.randrange(max(1, ph - 2 * seam - 4))
                    wob = rng.choice((-1, 0, 1))
                    d.line([(sx0 + 3, gy), (sx1 - 3, min(gy + wob, y0 + ph - 2))],
                           fill=tuple(min(255, int(v * 1.05)) for v in fill), width=1)
            d.rectangle([0, y0, size, y0 + seam], fill=seam_rgb)
            for cx in cuts:
                d.line([(cx, y0), (cx, y0 + ph)], fill=seam_rgb, width=seam)
    else:
        raise ValueError('unknown tile pattern: %s' % pat)
    return img

def tile_selfcheck(img):
    """A/B verdict requirement: 3x3 tiling preview + 256 mip - construction seam proof."""
    w, h = img.size
    t3 = Image.new('RGB', (w * 3, h * 3))
    for i in range(3):
        for j in range(3):
            t3.paste(img, (i * w, j * h))
    mip = img.resize((max(1, w // 4), max(1, h // 4)), Image.LANCZOS)  # 25% in-game distance sim (verdict)
    return t3, mip

def tile_mosaic(imgs):
    """3x3 self-check mosaic from variant tiles (R3 verdict: '一眼看出9块不重样') -
    variants fill the slots, rotation/mirror extends beyond the variant count."""
    size = imgs[0].size[0]
    m = Image.new('RGB', (size * 3, size * 3))
    ops = [None, Image.ROTATE_90, Image.FLIP_LEFT_RIGHT, Image.ROTATE_180]
    i = 0
    for sy in range(3):
        for sx in range(3):
            t = imgs[i % len(imgs)]
            op = ops[(i // len(imgs)) % len(ops)]
            if op:
                t = t.transpose(op)
            m.paste(t, (sx * size, sy * size))
            i += 1
    return m

def isolate_main(img):
    """Keep only the largest alpha component: kills rembg residue ghosts and stray floaters
    (fridge verdict 2026-09-19). Detached legit parts are rare for top-down props - accepted trade."""
    import numpy as np
    from collections import deque
    if img.mode != 'RGBA':
        return img
    w, h = img.size
    s = 128
    small = np.asarray(img.resize((s, s)).getchannel('A'))
    mask = small > 64
    seen = np.zeros((s, s), dtype=bool)
    best, best_area = None, 0
    for y0 in range(s):
        for x0 in range(s):
            if mask[y0, x0] and not seen[y0, x0]:
                q = deque([(y0, x0)]); seen[y0, x0] = True; area = 0
                while q:
                    y, x = q.popleft(); area += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < s and 0 <= nx < s and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                if area > best_area:
                    best_area, best = area, (y0, x0)
    if best is None:
        return img
    keep = np.zeros((s, s), dtype=bool)
    q = deque([best]); keep[best[0], best[1]] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < s and 0 <= nx < s and mask[ny, nx] and not keep[ny, nx]:
                keep[ny, nx] = True; q.append((ny, nx))
    keep_img = Image.fromarray((keep.astype('uint8') * 255), 'L').resize((w, h), Image.NEAREST)
    alpha = np.asarray(img.getchannel('A')).astype(np.int16)
    alpha = alpha * np.asarray(keep_img) // 255
    out = img.copy()
    out.putalpha(Image.fromarray(alpha.astype('uint8'), 'L'))
    return out

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    wait_server()
    session = new_session('u2net')
    manifest = {
        'pack': PACK_NAME, 'tier': 'placeholder_local_free',
        'rule': 'Tools/README.md 素材两级铁律：本包一律视为占位，禁止冒充上线成品；定稿由云端 frontier 线替换',
        'model': 'SD1.5 v1-5-pruned-emaonly (CreativeML OpenRAIL-M, 可商用)', 'upscaler': 'RealESRGAN_x4plus',
        'style_anchor': 'flat vector sticker / kawaii pastel（同 gpu_deploy_test 验收风格）',
        'date': '2026-09-19', 'items': []}
    all_ok = True
    for job in JOBS:
        t0 = time.time()
        raw, gen_s = run_job(job)
        path, fw, fh = post_process(job, raw, session)
        ok, kb = verify(path, job)
        all_ok = all_ok and ok
        manifest['items'].append({'name': job['name'], 'slot': job['slot'], 'file': path,
                                  'size': '%dx%d' % (fw, fh), 'kind': job['kind'],
                                  'gen_seconds': gen_s, 'total_seconds': round(time.time() - t0, 1),
                                  'kb': kb, 'prompt': job['pos'], 'seed': job['seed'], 'verified': ok})
    mp = os.path.join(OUT_DIR, MANIFEST_NAME)
    with open(mp, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print('MANIFEST %s' % mp)
    print('BATCH_%s' % ('ALL_PASS' if all_ok else 'HAS_FAIL'))

if __name__ == '__main__':
    main()

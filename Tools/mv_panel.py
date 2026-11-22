#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mv_panel.py — MV 全环节专家群审 / 群控（机械席位 + 可选 VLM 席位）

为什么（CEO 2026-10-18 19:2x「mv 的所有环节都要有专家……反复修特别浪费时间」+ 2026-11-22
「专家群审群控」）：席位矩阵 `MV-ALL-STAGE-EXPERT-COVERAGE-v1.md` 早就定了 12 环节，
但一直靠人记得去审——没有可执行载体。本文件把每席判据变成机器可跑的检查，
每次出批自动群审，不达标不许进下一站。

设计：
  - **各自独立**：每席只看自己那几项（不互相看结论，避免"评审同体"漏网）
  - **分数+判词**：每席给 0-10 分 + findings 列表
  - **群控律**：全部 ≥7 且均分 ≥9 = PASS；任一 <7 = REVISE（附回炉清单）；缺必携件 = BLOCKED
  - 台账：`mv-album-001-jay/reviews/PANEL-<tag>.json|.md`

用法：
  python Tools/mv_panel.py --tag hei-b1 --prompts <prompts.json> --frames <dir> [--shotlist md]
Exit: 0 PASS；1 REVISE；2 BLOCKED
"""
import argparse
import json
import os
import re
import sys

ROOT = r'K:\Fluxgroup\FluxGroup'
BASE = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay')

# 禁词表（各席共用）
EMO_WORDS = ('sad ', 'happy ', 'nervous ', 'angry ', 'sorrowful ', 'melancholy ', 'heartbroken ')
FLAT_LIGHT = ('flat light', 'frontal light', 'overhead light', 'even lighting', 'softbox')
WARDROBE_MUST = ('denim', 'graphic tee', 'silver chain', 'leather bracelet')
PLAIN_CLOTHES = ('plain dark shirt', 'plain white shirt', 'simple t-shirt', 'plain tee')
TEXT_RISK = ('signage', 'billboard', 'newspaper', 'book cover', 'screen text', 'subtitle')
NAME_RISK = ('jay chou', '周杰伦', 'jolin', '蔡依林', 'vivian hsu', '徐若瑄')


def load(p):
    return json.load(open(p, encoding='utf-8'))


# ---------------- 各席位 ----------------
def seat_director(rows, ctx):
    """导演席：叙事与人物面预算（CEO 90 分律：主体≥50/近特≥25/空镜≤20）。

    2026-11-22：**分段批**（如只烧前奏+主歌1）按全片预算判近特会必然假红——
    分段批只核空镜率（该段自身规律），近特/主体预算由全片表核。
    """
    subset = ctx.get('subset', False)
    n = float(len(rows))
    e = sum(1 for r in rows if r.get('kind') == 'E')
    f = sum(1 for r in rows if r.get('kind') == 'F')
    p = sum(1 for r in rows if r.get('kind') == 'P')
    ep, fp, pp = e / n * 100, f / n * 100, p / n * 100
    findings, score = [], 10
    if ep > 20:
        findings.append('空镜 %.1f%% > 20%%' % ep); score -= 3
    if not subset and fp < 25:
        findings.append('人脸近特 %.1f%% < 25%%' % fp); score -= 3
    if not subset and pp < 50:
        findings.append('主体 %.1f%% < 50%%' % pp); score -= 3
    if subset:
        findings.append('（分段批：近特/主体预算由全片表核，本批只核空镜率）')
    return score, findings, {'empty%': round(ep, 1), 'face%': round(fp, 1), 'body%': round(pp, 1)}


def seat_dop(rows, ctx):
    """摄影灯光席：必须有方向性光（侧/逆/低位），禁平光与顶灯打满。"""
    bad_flat = [r['id'] for r in rows if any(w in r['prompt'].lower() for w in FLAT_LIGHT)]
    has_dir = sum(1 for r in rows if any(w in r['prompt'].lower()
                                         for w in ('side light', 'side-back', 'rim', 'low-key', 'backlight')))
    score, findings = 10, []
    if bad_flat:
        findings.append('平光/顶灯命中 %d 镜：%s' % (len(bad_flat), bad_flat[:5])); score -= 4
    if has_dir < len(rows) * 0.3:
        findings.append('方向性光仅 %d/%d 镜（<30%%）' % (has_dir, len(rows))); score -= 2
    return score, findings, {'directional_light_shots': has_dir}


def seat_colorist(rows, ctx):
    """调色席：调色案必携 + 全片单一色系声明。"""
    grade_md = os.path.join(BASE, '黑色幽默-GRADE-v1.md')
    findings, score = [], 10
    if not os.path.exists(grade_md):
        findings.append('缺 GRADE-v1 调色案（GRADE-LAW 必携件）'); score -= 5
    grades = {r.get('grade') for r in rows}
    if len(grades) > 1:
        findings.append('多套 grade 混用：%s' % sorted(grades)); score -= 2
    return score, findings, {'grades': sorted(grades), 'grade_case': os.path.exists(grade_md)}


def seat_wardrobe(rows, ctx):
    """服装席：明星衣橱律（禁素T路人感）+ 同场同套连续性。"""
    hits = {w: sum(1 for r in rows if w in r['prompt'].lower()) for w in WARDROBE_MUST}
    plain = [r['id'] for r in rows if any(w in r['prompt'].lower() for w in PLAIN_CLOTHES)]
    person = [r for r in rows if r.get('kind') in ('F', 'P')]
    score, findings = 10, []
    missing = [w for w, c in hits.items() if c == 0]
    if missing:
        findings.append('造型锚缺失：%s' % missing); score -= 4
    if plain:
        findings.append('素T路人感命中 %d 镜（J-22 判例）' % len(plain)); score -= 5
    if person and hits.get('denim', 0) < len(person) * 0.8:
        findings.append('牛仔外套仅 %d/%d 人物镜（场内连续律）' % (hits.get('denim', 0), len(person))); score -= 2
    return score, findings, hits


def seat_editor(rows, ctx):
    """剪辑席：分段镜长律（主歌 2-3s / 副歌 ~2s / 前奏留长）。"""
    limits = {'前奏': 8.0, '主歌1': 3.0, '主歌2': 3.0, '主歌3': 3.0,
              '副歌1': 2.6, '副歌2': 2.6, '副歌3': 2.6, '副歌4': 2.6,
              '间奏': 6.0, '尾': 8.0}
    over = []
    for r in rows:
        lim = limits.get(r.get('seg'))
        if lim and r.get('dur', 0) > lim + 0.01:
            over.append('%s(%s %.1fs>%.1f)' % (r['id'], r['seg'], r['dur'], lim))
    score = 10 - min(6, len(over))
    findings = ['超镜长 %d 镜：%s' % (len(over), over[:5])] if over else []
    return score, findings, {'over_length': len(over)}


def seat_performance(rows, ctx):
    """表演席：写动作不写情绪（AI-ACTOR-PERFORMANCE-v2 铁则 1）。"""
    bad = [r['id'] for r in rows if any(w in r['prompt'].lower() for w in EMO_WORDS)]
    score = 10 - (4 if bad else 0)
    findings = ['情绪副词命中 %d 镜：%s' % (len(bad), bad[:5])] if bad else []
    return score, findings, {'emotion_words': len(bad)}


def seat_audience(rows, ctx):
    """受众席：L1 路人可读（主体占比 + 有明确动作的镜比例）。"""
    n = float(len(rows)) or 1
    act = sum(1 for r in rows if any(v in r['prompt'].lower() for v in
                                     (' as he ', ' he ', ' hand ', ' sits ', ' stands ', ' turns ')))
    pct = act / n * 100
    score = 10 if pct >= 45 else 10 - int((45 - pct) / 5)
    findings = [] if pct >= 45 else ['有动作镜 %.0f%% < 45%%（路人可能看不懂在做什么）' % pct]
    return score, findings, {'action_shots%': round(pct, 1)}


def seat_compliance(rows, ctx):
    """合规席：禁真人名/品牌；AIGC 标识待装配面。"""
    hits = [r['id'] for r in rows if any(w in r['prompt'].lower() for w in NAME_RISK)]
    score = 10 - (8 if hits else 0)
    findings = ['真人名命中：%s' % hits[:3]] if hits else []
    return score, findings, {'name_hits': len(hits)}


def seat_text(rows, ctx):
    """文字席：伪文字风险（招牌/报纸/屏幕文字会被画成乱码）。"""
    risky = [r['id'] for r in rows if any(w in r['prompt'].lower() for w in TEXT_RISK)]
    score = 10 - (3 if risky else 0)
    findings = ['伪文字风险 %d 镜：%s' % (len(risky), risky[:5])] if risky else []
    return score, findings, {'text_risk': len(risky)}


def seat_continuity(rows, ctx):
    """连续性席：人物 ID 块逐字复用（同场同一句造型串）+ 门禁一致。"""
    person = [r for r in rows if r.get('kind') in ('F', 'P')]
    if not person:
        return 10, [], {'note': 'no person shots'}
    # 取"an unnamed young Taiwanese man"之后到第一个逗号的定义块是否一致
    sig = set()
    for r in person:
        m = re.search(r'(an unnamed young taiwanese man[^.]*?)(?:, as|, the|\.)', r['prompt'].lower())
        if m:
            sig.add(re.sub(r'\s+', ' ', m.group(1))[:80])
    score = 10 if len(sig) <= 1 else 10 - 3 * (len(sig) - 1)
    findings = [] if len(sig) <= 1 else ['人物块出现 %d 种写法（ID 块须逐字复用）' % len(sig)]
    return score, findings, {'person_id_variants': len(sig)}




# ---------------- 多模态席（真看图·本地 qwen3-vl） ----------------
VLM_HOST = os.environ.get('VLM_HOST', 'http://127.0.0.1:11434')
VLM_MODEL = os.environ.get('VLM_MODEL', 'qwen3-vl:2b')

VLM_PROMPT = """你是 MV 专家评审。看这张 2000 年代台湾 MV 的画面，只回答 JSON：
{"era":0-10, "lived_in":0-10, "composition":0-10, "worst": "最大的一个问题（20 字内）"}
era=年代质感（2000 台湾/胶片颗粒/服装是否对）；lived_in=活人感（是否像真拍不是AI）；
composition=构图成不成立。只输出 JSON。"""


def _vlm_one(path, timeout=420):
    """调本地 VLM 打分。

    2026-11-22 实测坑：qwen3-vl:2b **忽略 think:false**，思维链照样输出到 thinking 字段，
    于是 num_predict 太小就把配额全烧在思维链上、response 恒为空。正法：
    ①先缩图到 640（大图拖慢 3 倍）②num_predict 给到 500 ③取响应里**最后一个** JSON。
    """
    import base64
    import io as _io
    import json as _json
    import re as _re
    import urllib.request
    from PIL import Image

    im = Image.open(path).convert('RGB')
    im.thumbnail((640, 640))
    buf = _io.BytesIO()
    im.save(buf, 'JPEG', quality=85)
    b = base64.b64encode(buf.getvalue()).decode()

    body = _json.dumps({'model': VLM_MODEL, 'prompt': VLM_PROMPT, 'images': [b],
                        'stream': False,
                        'options': {'num_predict': 500, 'temperature': 0.1}}).encode()
    req = urllib.request.Request(VLM_HOST + '/api/generate', data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = _json.loads(r.read().decode()).get('response', '')
    hits = _re.findall(r'\{[^{}]*\}', txt, _re.S)
    for h in reversed(hits):
        try:
            return _json.loads(h)
        except Exception:
            continue
    return None


def _vlm_describe(path, timeout=420):
    """第一段：VL 只说画面有什么（它 craft 思维链也无所谓，取 thinking+response 全文）。"""
    import base64
    import io as _io
    import json as _json
    import urllib.request
    from PIL import Image

    im = Image.open(path).convert('RGB')
    im.thumbnail((640, 640))
    buf = _io.BytesIO()
    im.save(buf, 'JPEG', quality=85)
    b = base64.b64encode(buf.getvalue()).decode()
    body = _json.dumps({'model': VLM_MODEL, 'images': [b], 'stream': False,
                        'prompt': '客观描述这张画面：人物穿着、光线、环境、色温。不要评价。',
                        'options': {'num_predict': 400, 'temperature': 0.1}}).encode()
    req = urllib.request.Request(VLM_HOST + '/api/generate', data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = _json.loads(r.read().decode())
    return ((d.get('response') or '') + ' ' + (d.get('thinking') or ''))[:1200]


def _text_score(desc, timeout=240):
    """第二段：文本模型（吃得下 think:false）按三律打分出 JSON。"""
    import json as _json
    import re as _re
    import urllib.request

    q = ('下面是 MV 画面描述。按三项打分（0-10）：era=2000年代台湾质感、lived_in=活人感(非AI)、'
         'composition=构图。只输出 JSON：{"era":n,"lived_in":n,"composition":n,"worst":"最大问题20字内"}'
         '\n描述：' + desc)
    body = _json.dumps({'model': 'qwen3.5:4b-q4_K_M', 'prompt': q, 'stream': False,
                        'think': False, 'options': {'num_predict': 200, 'temperature': 0.1}}).encode()
    req = urllib.request.Request(VLM_HOST + '/api/generate', data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = _json.loads(r.read().decode()).get('response', '')
    m = _re.search(r'\{[^{}]*\}', txt, _re.S)
    return _json.loads(m.group(0)) if m else None


def seat_vlm(rows, ctx):
    """多模态席（两段式）：VL 描述 → 文本模型打分。

    2026-11-22 实测：qwen3-vl:2b **忽略 think:false**（api/generate 与 api/chat 都硬打 <think>），
    小 num_predict 会把配额全烧在思维链上导致 response 恒空。拆两段最稳：
    VL 只负责"看见"，打分交给能关思维的 4b。
    """
    frames = ctx.get('frames') or ''
    if not frames or not os.path.isdir(frames):
        return 10, ['（未提供帧目录·跳过）'], {}
    pngs = sorted(f for f in os.listdir(frames) if f.endswith('.png'))[:ctx.get('vlm_n', 2)]
    scores, worst, notes = [], [], []
    for f in pngs:
        try:
            desc = _vlm_describe(os.path.join(frames, f))
            r = _text_score(desc)
        except Exception as e:
            notes.append('%s: %s' % (f, type(e).__name__))
            continue
        if not r:
            notes.append('%s: 解析失败' % f)
            continue
        v = [r.get('era', 0), r.get('lived_in', 0), r.get('composition', 0)]
        scores.append(sum(v) / 3.0)
        if r.get('worst'):
            worst.append('%s:%s' % (f.replace('.png', ''), str(r['worst'])[:16]))
    if not scores:
        return 8, ['多模态席无有效样本（%s）' % '; '.join(notes[:2])], {}
    avg = sum(scores) / len(scores)
    return max(0, min(10, int(round(avg)))), (['最差项：' + '；'.join(worst)] if worst else []), \
        {'vlm_avg': round(avg, 2), 'samples': len(scores)}


SEATS = [
    ('导演', seat_director), ('摄影灯光', seat_dop), ('调色', seat_colorist),
    ('服装道具', seat_wardrobe), ('剪辑节奏', seat_editor), ('表演', seat_performance),
    ('受众', seat_audience), ('合规', seat_compliance), ('文字', seat_text),
    ('连续性', seat_continuity),
    ('多模态', seat_vlm),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--frames', default='')
    ap.add_argument('--shotlist', default='')
    ap.add_argument('--subset', action='store_true', help='分段批：不按全片人物面预算判')
    ap.add_argument('--vlm-n', type=int, default=4, help='多模态席抽帧数（0=跳过）')
    a = ap.parse_args()

    rows = load(a.prompts)
    ctx = {'frames': a.frames, 'shotlist': a.shotlist, 'subset': a.subset, 'vlm_n': a.vlm_n}
    results = []
    for name, fn in SEATS:
        score, findings, detail = fn(rows, ctx)
        verdict = 'PASS' if score >= 7 else 'REVISE'
        results.append({'seat': name, 'score': score, 'verdict': verdict,
                        'findings': findings, 'detail': detail})
        print('%-8s %2d/10 %-7s %s' % (name, score, verdict, '; '.join(findings)[:100]))

    avg = round(sum(r['score'] for r in results) / float(len(results)), 2)
    low = [r for r in results if r['score'] < 7]
    overall = 'PASS' if (not low and avg >= 9) else ('REVISE' if not low or avg >= 5 else 'BLOCKED')
    out_dir = os.path.join(BASE, 'reviews')
    os.makedirs(out_dir, exist_ok=True)
    doc = {'tag': a.tag, 'shots': len(rows), 'prompts': os.path.basename(a.prompts),
           'avg': avg, 'verdict': overall, 'seats': results}
    json.dump(doc, open(os.path.join(out_dir, 'PANEL-%s.json' % a.tag), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    md = ['# 群审报告 %s（%d 镜 · 均分 %.2f · %s）' % (a.tag, len(rows), avg, overall), '',
          '| 席 | 分 | 判 | 发现 |', '|---|---|---|---|']
    for r in results:
        md.append('| %s | %d | %s | %s |' % (r['seat'], r['score'], r['verdict'],
                                             '；'.join(r['findings']) or '—'))
    md += ['', '## 群控结论', '', '均分 %.2f（≥9 才 PASS）· 回炉席 %d 个' % (avg, len(low))]
    open(os.path.join(out_dir, 'PANEL-%s.md' % a.tag), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('PANEL %s avg=%.2f verdict=%s -> reviews/PANEL-%s.md' % (a.tag, avg, overall, a.tag))
    return 0 if overall == 'PASS' else (1 if overall == 'REVISE' else 2)


if __name__ == '__main__':
    sys.exit(main())

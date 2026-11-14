# -*- coding: utf-8 -*-
"""剪辑链冒烟：pyJianYingDraft 0.3.x 新 API —— 9:16 草稿（视频段 + 字幕轨）。"""
import json, os, shutil

import pyJianYingDraft as draft

OUT_ROOT = r'K:\Fluxgroup\.codely-cli\tmp\jy-smoke'
DRAFT_DIR_NAME = 'BMC-SMOKE-9x16'
CLIP = (r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\outbound\krea2'
        r'\30s-reel-v1\i2v-xq\XQ38_01.mp4')
SRT = os.path.join(OUT_ROOT, 'sub.srt')

shutil.rmtree(OUT_ROOT, ignore_errors=True)
os.makedirs(OUT_ROOT, exist_ok=True)
with open(SRT, 'w', encoding='utf-8') as f:
    f.write("1\n00:00:00,200 --> 00:00:02,600\n测试字幕一\n\n"
            "2\n00:00:03,000 --> 00:00:05,500\n测试字幕二\n")
assert os.path.isfile(CLIP), 'clip missing: ' + CLIP

folder = draft.DraftFolder(OUT_ROOT)
script = folder.create_draft(DRAFT_DIR_NAME, 1080, 1920, 30, allow_replace=True)

# 新 API：先建轨（TrackSpec），再把段挂到该轨
script.append_track(draft.TrackSpec(draft.TrackType.video, name='main'))
script.append_track(draft.TrackSpec(draft.TrackType.text, name='subtitle'))

video = draft.VideoMaterial(CLIP)
seg = draft.VideoSegment(video, draft.trange('0s', '5.875s'))
script.add_segment(seg, 'main')
script.import_srt(SRT, track_name='subtitle', time_offset='0s')
script.save()

draft_dir = os.path.join(OUT_ROOT, DRAFT_DIR_NAME)
files = sorted(os.listdir(draft_dir)) if os.path.isdir(draft_dir) else []
print('draft dir:', draft_dir)
print('files:', files)
assert 'draft_content.json' in files, 'draft_content.json missing'

dc = json.load(open(os.path.join(draft_dir, 'draft_content.json'), encoding='utf-8'))
tracks = dc.get('tracks') or []
print('canvas:', dc.get('canvas_config'))
print('tracks:', [(t.get('type'), len(t.get('segments') or [])) for t in tracks])
assert any((t.get('type') == 'video' and t.get('segments')) for t in tracks), 'no video track'
assert any((t.get('type') == 'text' and t.get('segments')) for t in tracks), 'no text track'
print('SMOKE-OK pyJianYingDraft: 9:16 draft with video+subtitle tracks')

# -*- coding: utf-8 -*-
"""字幕链冒烟：faster-whisper 转写 + 写 SRT + 喂给 pyJianYingDraft 成轨（端到端）。"""
import json, os, shutil

from faster_whisper import WhisperModel

MODEL = r'K:\Fluxgroup\.tools\models\faster-whisper-small'
AUDIO = r'K:\Fluxgroup\.codely-cli\tmp\tts-smoke\piper_huayan.wav'
OUT = r'K:\Fluxgroup\.codely-cli\tmp\sub-smoke'
os.makedirs(OUT, exist_ok=True)

model = WhisperModel(MODEL, device='cpu', compute_type='int8')
if not os.path.exists(AUDIO):
    raise SystemExit('audio missing: ' + AUDIO)

segments, info = model.transcribe(AUDIO, language='zh', vad_filter=True)
segs = list(segments)
print('lang=%s dur=%.2fs segments=%d' % (info.language, info.duration, len(segs)))


def ts(t, sep=','):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
    return '%02d:%02d:%02d%s%03d' % (h, m, s, sep, ms)


srt_path = os.path.join(OUT, 'asr.srt')
with open(srt_path, 'w', encoding='utf-8') as f:
    for i, s in enumerate(segs, 1):
        f.write('%d\n%s --> %s\n%s\n\n' % (i, ts(s.start), ts(s.end), s.text.strip()))
print('srt ->', srt_path, os.path.getsize(srt_path), 'bytes')
for s in segs[:5]:
    print('  [%5.2f-%5.2f] %s' % (s.start, s.end, s.text.strip()))

# 端到端：把 SRT 灌进剪映草稿
import pyJianYingDraft as draft
DRAFT = 'BMC-SUB-SMOKE'
folder = draft.DraftFolder(OUT)
script = folder.create_draft(DRAFT, 1080, 1920, 30, allow_replace=True)
script.append_track(draft.TrackSpec(draft.TrackType.text, name='subtitle'))
script.import_srt(srt_path, track_name='subtitle', time_offset='0s')
script.save()

dc = json.load(open(os.path.join(OUT, DRAFT, 'draft_content.json'), encoding='utf-8'))
text_tracks = [t for t in (dc.get('tracks') or []) if t.get('type') == 'text']
n = sum(len(t.get('segments') or []) for t in text_tracks)
print('draft text segments:', n)
assert n == len(segs) and len(segs) > 0, 'subtitle count mismatch'
print('SMOKE-OK subtitle chain: asr -> srt -> jianying draft (%d lines)' % n)

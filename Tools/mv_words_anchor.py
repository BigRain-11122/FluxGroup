# -*- coding: utf-8 -*-
"""为一首歌生成词级锚点（段落切分用）：faster-whisper 转写 + librosa 测 BPM。

输出 <anchors>/<song>-words.json ：{song, dur, bpm, segments:[{t0,t1,text}], words:[{t,text}]}
用法：python Tools/mv_words_anchor.py --song 黑色幽默
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay', 'audio')
ANCH = os.path.join(ROOT, 'cph4', 'fleet', 'mv-album-001-jay', 'anchors')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--song', required=True)
    ap.add_argument('--model', default='small')
    a = ap.parse_args()

    src = None
    for f in os.listdir(AUDIO):
        if a.song in f and f.lower().endswith('.mp3'):
            src = os.path.join(AUDIO, f)
            break
    if not src:
        print('AUDIO MISSING for', a.song)
        return 2
    os.makedirs(ANCH, exist_ok=True)

    # BPM
    bpm = None
    try:
        import librosa
        y, sr = librosa.load(src, sr=22050, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = round(float(tempo if not hasattr(tempo, '__len__') else tempo[0]), 2)
        dur = round(len(y) / float(sr), 2)
    except Exception as e:
        print('librosa failed:', type(e).__name__, e)
        dur = None

    # 词级转写
    from faster_whisper import WhisperModel
    m = WhisperModel(a.model, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(src, language='zh', word_timestamps=True, vad_filter=True)
    segments, words = [], []
    for s in segs:
        segments.append({'t0': round(s.start, 2), 't1': round(s.end, 2), 'text': s.text.strip()})
        for w in (s.words or []):
            words.append({'t': round(w.start, 2), 'text': w.word.strip()})
    out = {'song': a.song, 'src': os.path.relpath(src, ROOT).replace('\\', '/'),
           'dur': dur, 'bpm': bpm, 'segments': segments, 'words': words}
    p = os.path.join(ANCH, a.song + '-words.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ANCHORS OK %s dur=%s bpm=%s segments=%d words=%d' % (p, dur, bpm, len(segments), len(words)))
    for s in segments[:12]:
        print('  %6.1f-%6.1f %s' % (s['t0'], s['t1'], s['text'][:40]))
    return 0


if __name__ == '__main__':
    sys.exit(main())

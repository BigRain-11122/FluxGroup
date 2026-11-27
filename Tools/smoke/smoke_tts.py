# -*- coding: utf-8 -*-
"""音色链冒烟 v2：piper（华言）+ sherpa-onnx kokoro 多语（53 声纹）。

注：.tools/kokoro/kokoro-*-multi-lang 是 **sherpa-onnx** 资产包（tokens/lexicon/voices.bin），
不是 kokoro_onnx 的格式；kokoro_onnx 那条路会报 unpickle 错，别混用。
"""
import os, subprocess, sys, wave

OUT = r'K:\Fluxgroup\.codely-cli\tmp\tts-smoke'
os.makedirs(OUT, exist_ok=True)
TXT = '这是本机音色库的冒烟测试，男声女声都要能用。'
PY = r'K:\Fluxgroup\.tools\tts-venv\Scripts\python.exe'
KOK = r'K:\Fluxgroup\.tools\kokoro\kokoro-multi-lang-v1_0'


def wav_info(p):
    with wave.open(p, 'rb') as w:
        return w.getnchannels(), w.getframerate(), w.getnframes(), round(w.getnframes() / float(w.getframerate()), 2)


# ---------- piper ----------
piper_out = os.path.join(OUT, 'piper_huayan.wav')
p = subprocess.run([PY, '-m', 'piper', '-m', r'K:\Fluxgroup\.tools\piper-voices\zh_CN-huayan-medium.onnx',
                    '-f', piper_out], input=TXT.encode('utf-8'), capture_output=True)
print('piper rc=%d' % p.returncode, 'wav', wav_info(piper_out) if os.path.exists(piper_out) else 'MISSING')

# ---------- sherpa-onnx kokoro ----------
try:
    import sherpa_onnx

    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=os.path.join(KOK, 'model.onnx'),
                voices=os.path.join(KOK, 'voices.bin'),
                tokens=os.path.join(KOK, 'tokens.txt'),
                data_dir=os.path.join(KOK, 'espeak-ng-data'),
                dict_dir=os.path.join(KOK, 'dict'),
                lexicon=','.join([os.path.join(KOK, 'lexicon-us-en.txt'),
                                  os.path.join(KOK, 'lexicon-zh.txt')]),
            ),
            num_threads=4,
            provider='cpu',
        ),
        rule_fsts=','.join([os.path.join(KOK, 'date-zh.fst'),
                            os.path.join(KOK, 'number-zh.fst'),
                            os.path.join(KOK, 'phone-zh.fst')]),
        max_num_sentences=1,
    )
    tts = sherpa_onnx.OfflineTts(cfg)
    n = tts.num_speakers
    print('kokoro sherpa speakers:', n, 'sample_rate:', tts.sample_rate)
    ok = 0
    for sid in (0, min(3, n - 1), min(20, n - 1), n - 1):
        a = tts.generate(TXT, sid=sid, speed=1.0)
        if len(a.samples) == 0:
            print('  sid=%d EMPTY' % sid)
            continue
        p2 = os.path.join(OUT, 'kokoro_sid%d.wav' % sid)
        sherpa_onnx.write_wave(p2, a.samples, a.sample_rate)
        ok += 1
        print('  sid=%-3d dur=%.2fs -> %s' % (sid, len(a.samples) / a.sample_rate, os.path.basename(p2)))
    print('kokoro OK voices=%d' % ok)
except Exception as e:
    print('kokoro FAIL:', type(e).__name__, e)

print('SMOKE-TTS done')

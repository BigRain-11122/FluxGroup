# -*- coding: utf-8 -*-
"""零样本试音：用 v06 自建语料里的 10-30s 干净片段做参考，合成《一碗面》台词。

这是「自有声线」的第一块砖：不克隆任何真人演播者，参考音来自我们自己的语料分片。
"""
import os
import sys
import glob

GSV = r'K:\Fluxgroup\.tools\GPT-SoVITS-main'
os.chdir(GSV)
sys.path.insert(0, GSV)
sys.path.insert(0, os.path.join(GSV, 'GPT_SoVITS'))

REF_DIR = r'K:\Fluxgroup\FluxGroup\cph4\fleet\voicebank\shards\v06\seg'
OUT = r'K:\Fluxgroup\FluxGroup\media\duanju\shanglu\voice-test'
os.makedirs(OUT, exist_ok=True)

TEXT = "面粉一斤一块一，一斤出三碗。人工水电摊下来，一碗成本四毛二。"


def pick_ref():
    import soundfile as sf
    cands = sorted(glob.glob(os.path.join(REF_DIR, '*.wav')))
    best, best_d = None, 1e9
    for p in cands[:80]:
        try:
            info = sf.info(p)
        except Exception:
            continue
        d = info.duration
        if 4.0 <= d <= 9.0 and abs(d - 6.0) < best_d:
            best, best_d = p, abs(d - 6.0)
    return best


def main():
    ref = pick_ref()
    if not ref:
        print('NO REFERENCE CLIP')
        return 2
    print('reference:', ref)

    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
    import json

    cfg = TTS_Config(os.path.join('GPT_SoVITS', 'configs', 'tts_infer.yaml'))
    # 强制指向本机权重
    cfg.device = 'cpu'
    cfg.is_half = False
    print('config device=', cfg.device, 'version=', getattr(cfg, 'version', '?'))

    tts = TTS(cfg)
    req = {
        'text': TEXT,
        'text_lang': 'zh',
        'ref_audio_path': ref,
        'prompt_text': '',
        'prompt_lang': 'zh',
        'top_k': 15, 'top_p': 1.0, 'temperature': 1.0,
        'text_split_method': 'cut0', 'batch_size': 1,
        'speed_factor': 1.0, 'return_fragment': False,
        'seed': 42,
    }
    out = os.path.join(OUT, 'v06_zero_shot.wav')
    for item in tts.run(req):
        sr, audio = item['sample_rate'], item['audio_np']
        import soundfile as sf
        sf.write(out, audio, sr)
        print('WROTE', out, sr)
        break
    print('DONE', out, os.path.getsize(out) if os.path.exists(out) else 0)
    return 0


if __name__ == '__main__':
    sys.exit(main())

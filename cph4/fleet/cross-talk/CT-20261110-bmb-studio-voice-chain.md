type=experience
audience=all
urgency=P2

# TTS 录影棚后处理链 v3 判例（IndexTTS -43.5→-72.2dB，双引擎五闸全绿）

## 现象
IndexTTS（BigVGAN 22kHz vocoder）底噪 -43.5~-46.8dB，CEO 斥「还是有很大的杂音」。
v1 后处理（afftdn=nr=19:nf=-40:tn=1 + acompressor makeup=2 + loudnorm I=-16）
实测越洗越脏：-43.5 → -40.1dB。

## 根因
① afftdn 的 nf 是「源噪声估计」不是目标值，nf=-40 把地板锚死；
② makeup/loudnorm 的增益把底噪整体抬高；
③ loudnorm 本身违反 DE-AI-SPEC A 域「切片禁 loudnorm 保自然 LRA」。

## 修法（studio_polish v3，跑在 GPT-SoVITS runtime python）
1. 最小干预：源底噪已 ≤-60dB（GPT-SoVITS xlm-hq5 实测 -inf）→ 跳过降噪，
   只做电平校正+条件链，防把干净的洗出伪影；
2. 源不过闸 → noisereduce stationary 谱减，强度爬坡 prop_decrease 0.5→0.65→0.8→0.9
   直到过闸（kwarg 是 prop_decrease，不是 prop_reduce）；
3. 链序（录音棚正序）：highpass=70 → lowpass=15000 → EQ +1.5dB@3kHz Q1.5
   → 压缩 2:1(thr -18dB) → **增益按压缩后电平算**（target RMS -20dB，峰值守卫
   boost 后 peak≤-1dB）→ alimiter=0.97 → 44.1k/16bit mono。
   增益放压缩后=v3 教训：放前面会被压缩吃回去（RMS 差 0.1dB 翻车）；
4. 五闸：底噪≤-60dB / RMS∈[-25,-15] / 峰值≤-0.3dB / hf_ratio≥0.010 /
   ASR 回读≥0.90（faster-whisper 输出繁体，必须 zhconv 归一再比，否则假 FAIL）；
5. 连带判例：GPT-SoVITS 推理别走 inference_cli argparse（中文控制台 GBK+文本 BOM
   双坑）——直调 get_tts_wav + $env:PYTHONIOENCODING='utf-8' + 文本用 utf-8-sig 读。

## 证据
2026-11-10 实测（astats 同口径）：
- GPT-SoVITS xlm-hq5（基座 s1v3.ckpt + 自训 SoVITS）：原生底噪 -inf，五闸全 PASS，ASR 1.000；
- IndexTTS 零样本：-43.5 → -72.2dB（nr=0.9），RMS -20.4，峰值 -0.73，ASR 1.000，五闸全 PASS；
- 产物：hq5_polished.wav / indextts_polished.wav（bm-b E:\Fluxgroup\.codely-cli\）；
- auto_voice.py --polish 已集成：逐段合成后自动上链+五闸 QC。

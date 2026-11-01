# Q-MIX-1203 回执 · bm-b · 2026-11-01 20:08

**结论：原 rc=1 是真 bug，已修复；混音现已 60/60 完成。**

## 原失败

队列记录 `result: {rc: 1, seconds: 15.6, deliverable_exists: true}`（2026-10-31 06:04）。当时只在 `drama-mix-out/r1203_ep001_060` 落下 7 集。

根因（复现于 EP008，首条即崩）：

```
File "drama_mix3_r1003.py", line 881, in render_sfx
    t0 = line_t0[ln] + off
KeyError: 1
```

`render_sfx` 用 `line_t0 = {slot['line']['n']}` 建表后按 key 直取，而批量驱动 `drama_mix_batch.py` 是**按镜号**（`shots[].n`）合成音效程序的。没有台词的镜头不会进 manifest（EP008 的台词行号从 2 起），于是镜号 1 查不到行号 1 → 整集抛异常。

## 修法

`render_sfx` 改为就近落位：缺号时取「≤ ln 的最大已有行」，若无则取首行；并在 placed 记录里加 `at_line` 便于回溯。备份原件：`drama_mix3_r1003.py.bak-20261031-sfxsnap`。

## 复跑结果

```
drama_mix_batch.py EP008-EP060 --tts r1202_ep001_060 --out r1203_ep001_060
MIX-BATCH-DONE rc=0   wall=161.9s
```

| 项 | 数值 |
|---|---|
| 混音集数 | **60/60**（EP001–EP060）|
| 电平 | peak 0.891（alimiter 生效）· rms −20.2 ~ −20.5 dB |
| receipt | `media/drama-tools/mix_r1203_ep001_060.receipt.json` |
| 产物 | `media/drama-mix-out/r1203_ep001_060/EPxxx_MIX_r1003.wav` ×60 |

## 连带

- 合轨 60/60 进 `media/drama-eps-audio`（逐集核验 a:0 + 片长差 ≤0.25 s）
- 混音体检 60/60 OK（mean −20.9 dB，零削波、零缺件）
- 报告：`quant/bigmoney/content/drama/outbox/DRAMA-VOICE-REMUX-bmb.md`、`DRAMA-VOICE-AUDIT-bmb.md`
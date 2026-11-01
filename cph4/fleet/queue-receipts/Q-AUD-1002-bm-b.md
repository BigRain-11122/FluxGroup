# Q-AUD-1002 回执 · bm-b · 2026-11-01 20:08

**结论：交付物已产出并通过核验；原命令有两处错误，已按正确源与正确长度口径执行。**

## 原命令的两处问题

卡片命令：
```
ffmpeg -y -i EP002.mp4 -i ".../r1003_3layer/EP002_3layer" -map 0:v -map 1:a \
  -c:v copy -af loudnorm=... -c:a aac -b:a 192k -shortest EP002_AUDIO-r1002.mp4
```

1. **源文件不存在**：`r1003_3layer/EP002_3layer` 无扩展名、盘上不存在；实际文件是 `EP002_MIX_r1003.wav`。
2. **`-shortest` 会截短成片**：该 WAV 只有 58.15 s，而画面 62 s，`-shortest` 会输出 58 s 的残片（同类事故已在本批其它集出现，判例已固化）。

## 实际执行

```
ffmpeg -y -i media/drama-eps/EP002.mp4 \
       -i media/drama-mix-out/r1003_3layer/EP002_MIX_r1003.wav \
       -map 0:v:0 -map 1:a:0 -c:v copy \
       -af "apad,loudnorm=I=-14:TP=-1.0:LRA=11" -c:a aac -b:a 192k -shortest \
       media/drama-eps-audio/EP002_AUDIO-r1002.mp4
```

`apad` 把尾部静默补齐到画面长度，再 `-shortest` 以画面为准。

## 核验

| 项 | 数值 |
|---|---|
| 交付物 | `C:/Fluxgroup/FluxGroup/media/drama-eps-audio/EP002_AUDIO-r1002.mp4`（存在）|
| 片长 | **62.00 s**，与 `EP002.mp4` 一致（差 0.00 s）|
| 音轨 | aac，存在 |
| rc | 0 |

## 备注

同一集另有更新版本：`EP002_AUDIO-r1003.mp4`（来自 r1203 全量混音，音源为 60 集完整 TTS 批次）。r1002 用的是 10-27 的 r1003 三层样批音源，两版都在，按卡片要求先交 r1002；若要统一到 r1203 批次请另开卡。
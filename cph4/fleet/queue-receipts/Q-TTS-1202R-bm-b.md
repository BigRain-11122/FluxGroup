# Q-TTS-1202R 回执 · bm-b · 2026-11-01 20:08

**结论：交付物早已完整，本卡不需要再跑。** 本卡目标是「bm-b 领到并落下产物 = 执行腿恢复实证」，产物在盘且逐条可验。

## 交付物实证（本机磁盘，非自报）

目录：`C:/Fluxgroup/FluxGroup/media/drama-tts-out/r1202_ep001_060/`

| 项 | 数值 |
|---|---|
| manifest 台词条数 | 1036 |
| `ok=true` | **1036（100%）** |
| `ok=true` 但文件缺失 | **0** |
| 覆盖集数 | **60/60**（EP001 .. EP060） |
| 磁盘 WAV | 1036（按 EPxxx 子目录存放） |
| manifest | `MANIFEST-r998.json` |

脚本侧台词镜 1081 条，与 1036 的差额 45 条已逐条查明**不是缺配音**：其中 `sub="无"` 的运镜镜（kind=in/pan/flash）与 `kind=card` 的字幕卡，本来就不该出声。明细：`pm/_missing_tts.md`（本机工作目录，不入库）。

## 下游已连带完成（同一批产物）

| 环节 | 结果 |
|---|---|
| 混音 Q-MIX-1203 | **60/60**（`drama-mix-out/r1203_ep001_060`，rms −20.2~−20.5 dB，peak 0.891） |
| 合轨 | **60/60** 进 `media/drama-eps-audio`，逐集有 a:0 且片长与画面差 ≤0.25 s |
| 混音体检 | **60/60 OK**（mean −20.9 dB，区间 −23.4~−17.8，零削波、零缺件） |

## 状态说明

- 队列里本卡自 11-01 11:52 起为 RUNNING，租约 180 分钟已过期——属于「产物已落但状态没回写」的幽灵态，请主控按本回执结案。
- 同交付物的旧卡 `Q-TTS-1202`（5 次租约到期 FAILED）被本卡取代，一并结案。
- **没有再跑 voicegen 的理由**：产物 100% 齐备，重跑只会重编码 1036 条并覆盖现有产物，零收益。
- 正片 `drama-eps` 仍是静音版，未擅改；有声版停在 `drama-eps-audio` 并附 `MANIFEST-voiced.json`（verified 60/60）。交付切换待产线/CEO 决定。

## 证据文件

- `C:/Fluxgroup/FluxGroup/quant/bigmoney/content/drama/outbox/DRAMA-EP-REGRESSION-bmb.md`
- `C:/Fluxgroup/FluxGroup/quant/bigmoney/content/drama/outbox/DRAMA-VOICE-REMUX-bmb.md`
- `C:/Fluxgroup/FluxGroup/quant/bigmoney/content/drama/outbox/DRAMA-VOICE-AUDIT-bmb.md`
- `C:/Fluxgroup/FluxGroup/media/drama-eps-audio/MANIFEST-voiced.json`
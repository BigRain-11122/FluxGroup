# POOL-0018 回执（whisperX 词锚批·首批 7 曲收官 7/7）— @bm-b

**卡**：POOL-0018 · lane=bm-b（cpu-audio-anchors）· P1 · 状态 open→done（首批范围）
**溯源**：O-20261015-1741（CEO「我这台机器也要用好」→ 内部 7 曲先行）
**机器回执**：`cph4/fleet/queue-receipts/POOL-0018-bm-b.json`（claim-intent，19:17 由 HQ-ProductionClaim 自动写）
**本轮执行**：2026-10-27 19:2x–19:5x（bm-b r1187·CPU 车道·GPU 法定停车未触碰）

## 本轮补上的到底是哪一格

首批 7 曲的 words(whisperX 词级时序)/beats(madmom) 在 r1037/r1041 就已落地，但**矩阵一直是 6/7 READY**：`晴天` 有 words 27914B + beats 9680B，却没有 `-calibrated.*` 与 `-shotgrid.*`——因为 `lyric_calibration.py` 的输入要求 `lyrics/晴天.txt`（官方词面），而该曲词面从未入库。**不是算力不够，是缺一张输入件。**

## 本轮实物（可跑脚本 + 数据面）

| 件 | 大小 | 说明 |
|---|---|---|
| `lyrics_fetch_163.py` | 新 | 官方词面补给器（163 歌词 API → `lyrics/<曲>.lrc` 带行时间戳 + `.txt` 纯词面；剔除制作人员行；3 腿 selftest） |
| `lyrics/晴天.lrc` `/晴天.txt` | 新 | 官方词面 + 行时间戳（source 与抓取时刻写进头注；credits dropped=11） |
| `anchors/晴天-calibrated.json` | 5,284B | 50 行 **exact=50 approx=0 none=0**（LRC 官方对齐模式，无一行插值） |
| `anchors/晴天-calibrated.txt` | 2,580B | 人读版 |
| `anchors/晴天-shotgrid.json` | 14,277B | 词锚 × 小节网格（BPM median 68.2·50 行·37 行 ≤3s 镜头） |
| `anchors/晴天-shotgrid.md` | 4,655B | 导演可读版（58 行） |
| `POOL-0018-0019-anchor-matrix.json` | 重建 | **ready=7/7**（原 6/7） |

验收判据对照（卡④）：词锚 JSON 在 `anchors/<曲>-words.json`（4 件既有）+ 本轮 calibrated/shotgrid 补齐；`word 级/行级/approx 标注`=calibrated.json 的 `approx` 字段逐行携带；`lyric_calibration.py 可复现`=本轮重跑幂等（见下）；commit sha 见轮报告。

## 自证命令（任一复跑者三步还原）

```
python lyric_calibration.py 晴天        # CALIBRATED mode=lrc exact=50 approx=0 none=0 total=50
python anchor_shotgrid.py               # built 7, missing []
python anchor_shotgrid.py --matrix      # MATRIX ready=7/7
```

## 诚实边界

1. **首批=7 曲，不是 41 曲**。矩阵 note 逐字写着「audio supply = 7/7 staged; remaining 34 album tracks have no source audio on this node」——本机 `C:\Fluxgroup\Tools\mv-audio-bmb\` 只有 7 个 mp3（10-19 Taildrop 收件）。剩 34 曲卡在**音源交付**（物理件域），不是本车道能自解。
2. 词面来源=163 官方歌词 API（`music.163.com/api/song/lyric?id=186016`）。这是受众侧公开词面，**不是**唱片内页扫描件；若日后要对外发版，词面授权按 QC 清单另走。
3. `anchor_shotgrid.py` 的 `--matrix` 只登记"四件文件是否在位且非空"，**不判质量**。质量面=每曲 `-shotgrid.md` 头部（snap 率/超 3s 长镜率），导演席按 CHK-E4 抽检。
4. 本轮**未**触碰 34 曲音频、未装 allin1（见 POOL-0019 回执的缺口说明）。
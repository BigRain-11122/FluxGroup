# POOL-0019 回执（结构锚·首批 7 曲 beats 侧收官 7/7）— @bm-b

**卡**：POOL-0019 · lane=bm-b（cpu-music-structure）· P1 · 首批范围 done
**溯源**：O-20261015-1741
**前序**：`POOL-0019-beatsanchor-firstbatch-receipt-r1041bmb.md`（madmom RNNDownBeat+DBN 6/6 全胜）
**本轮**：2026-10-27 r1187·补齐第 7 曲（晴天）的下游两腿——`-calibrated` 与 `-shotgrid`

## 本轮实物

- `anchors/晴天-shotgrid.json` / `.md`：词锚 × downbeat 网格，BPM(median)=68.2，50 行歌词全部落进 ≤3.0s 镜头窗（37/50 行 snap 到小节线，13 行超窗被拆）
- `POOL-0018-0019-anchor-matrix.json`：ready **7/7**（原 6/7）
- 复跑：`python anchor_shotgrid.py` → `{"built": 7, "missing": []}`

## 卡面验收对照

| 卡④要求 | 现状 |
|---|---|
| `anchors/<曲>-structure.json`（BPM/beats/downbeats/段落标签） | **BPM/beats/downbeats 有**（`-beats.json`，madmom 0.16.1）；**段落标签(allin1) 无** |
| 与 whisperX 词锚双锚合一 | 有（`-calibrated.json` + `-shotgrid.json` = 词锚×节奏锚的合并面） |
| S6 文档面可直取 | 有（`-shotgrid.md` 导演可读版） |
| 与 librosa beats.json 双源校验 | 未做（现网无 librosa beats 面落地；librosa 0.11 在 venv-anchor 里可装可用，属未接线路） |
| 全量 41 曲 | **7/7 首批**，剩 34 曲缺音源（同 POOL-0018 边界） |

## 两处如实缺口（不粉饰）

1. **段落标签（intro/verse/chorus/bridge）仍缺**。卡面 spec 指 allin1（MIT·860★），本机 `venv-anchor` 未装（`import allin1` → ModuleNotFoundError；在役包=madmom/whisperx/librosa/torch-cpu）。allin1 依赖 torch + demucs 分离链，装+首跑远超单轮预算，且 bm-b GPU 法定停车（C-20261014-01 §3）→ 只走 CPU 会慢一个量级。**处置建议**：由代理席决定是否在 bm-a/bm-c 的 GPU 车道排 allin1 段落标注批；本机继续承担 CPU 侧 beats/词锚。
2. **双源校验（allin1 vs librosa）零样本**——上面第一条闭合前，这一格只能是 0 样本，不如实写就会变成假绿。

## 诚实边界

- 本轮**不改**任何既有 `-beats.json`（madmom 面 r1041 冻结，重跑只为给晴天补下游）。
- `POOL.json` 状态迁移归代理席写手制；本回执只提供卡 ID + done + 证据指针。
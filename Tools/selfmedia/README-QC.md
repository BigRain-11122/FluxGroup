# 块面 / 组装质检闸（shot_qc + make_board）

CEO 2026-11-25 令：「每个环节每个块面都要严格检查，组装起来更要，审美面也要出动」。
本目录两件工具是这条令的机械面；席位面在 `cph4/agents/seats/mv-aesthetic-seats.json`（10 席）。

## 快速跑法

```powershell
# 有剪辑表（推荐）：块面 + 组装 + 边界对 全跑
python Tools/selfmedia/shot_qc.py `
  --film  <成片.mp4> `
  --edl   <EDIT-PLAN.json> `
  --out   <输出目录> `
  --mode  all

# 没有剪辑表：自动切点（按帧差），只能抓块内缺陷
python Tools/selfmedia/shot_qc.py --film X.mp4 --out out --mode all

# 手工切点
python Tools/selfmedia/shot_qc.py --film X.mp4 --segments "3.4,6.0,9.2" --out out

# 原生帧率全检（慢，终审用）
python Tools/selfmedia/shot_qc.py --film X.mp4 --edl E.json --out out --strict

# 审片板（席位判读用）
python Tools/selfmedia/make_board.py --film X.mp4 --edl E.json --out out
```

退出码：0 = 全 PASS；1 = 有告警（报告里逐条列）；2 = 输入缺失。

## EDL 格式

```json
{
  "fps": 24,
  "blocks": [
    {"i": 1, "t0": 0.0, "t1": 3.4, "desc": "火+楔文墙", "src": "v5 reel 0-3.4"},
    {"i": 7, "t0": 16.4, "t1": 18.6, "desc": "发光板", "allow_static": true}
  ]
}
```

豁免位（按需加）：
- `allow_dark`：设计内黑场（片头/片尾/过场）
- `allow_freeze`：设计内定格
- `allow_static`：静态图块（PNG loop + 呼吸亮度）——同时豁免重复帧

## 判据在哪改

`shot_qc.py` 顶部的 `THRESH` 字典，一处生效全局。当前值：
镜长偏差 0.10s / 欠曝 <12 占 20% / 冻结 ≥12 帧 / 重复帧 >5% /
清晰度 <同亮度档中位 40% / 黑边单边 >6% 且对侧对称 / 响度 −14±1 LUFS / 真峰 ≤ −1.0 dBTP。

## 已知误报（改判据时必读）

1. **清晰度不能跨亮度档比**。Laplacian 是绝对能量，暗镜头天然低。必须按 YAVG 分档
   （<20 / 20–35 / >35）各取中位。反例：v13b 浮雕 81.6 vs 片中位 250.5，分档后正常。
2. **黑边不能只看亮度**。死黑体系会有大面积 <16 的画面。必须「99 分位仍 <24」+「对侧对称」。
   单侧大片纯黑是构图（火光只照一侧），不是缺陷。
3. **静态图块会报重复帧**。`glow.png` / `stele-v2.png` 这类 loop 图 + 呼吸亮度，
   帧差极小，必须 `allow_static`。
4. **AAC 编码有 0.3–1.5 dB 真峰过冲**。`alimiter limit=0.891`（−1.0 dBFS）实测输出 −0.3 dBTP。
   要留余量：`loudnorm=I=-14.3:TP=-2.6` + `alimiter=limit=0.74` → 实测 −2.0 dBTP。
5. **auto_cuts 只是兜底**。帧差阈值找不到淡入淡出与推近，真实切点必须来自剪辑表。

## 输出物

| 文件 | 用途 |
|---|---|
| `QC-REPORT.md` | 人读：逐块面表 + 边界对表 + 音频 + 结论 |
| `QC-REPORT.json` | 机读：全量数值，供下游脚本消费 |
| `blocks/bNN_t0-t1.jpg` | 每块首/中/末三帧接触条 |
| `BOARD-BLOCKS.jpg` | 全片块面网格（make_board 产出） |
| `BOARD-CUTS.jpg` | 每个切点「前一帧 \| 后一帧」成对（make_board 产出） |

## 与席位体系的关系

`shot_qc` 只出数字与画面证据，**不做审美判定**。数字先过闸（机检不通过不必送席位），
然后 `aesthetic_panel.py` 生成十席提示词与证据包，席位按判据逐条打分并给时间码。

分工实证：全片音轨 +3.1 dBTP 削波是机检抓的，任何席位都看不出来；
而"两条时间线没有连接件"是席位抓的，机检看不出来。两者不可替代。

# 集团工具箱盘点与实测（2026-11-06 · bm-a 交互窗）

> 目的：把 13 条线 / 技能 / 车道 / 工具的现状摊开，对准缺口找 GitHub 现成轮子，能测的当场测，用数字定选型。
> 原则：先找现成，测过再引；测不了就写「未测」，不装懂。

## 一、盘点到的东西（实测目录，不是回忆）

| 层 | 数量 | 位置 |
|---|---|---|
| 业务线 | 13 | `cph4/fleet/lines/*.json`（BigCompute/BigDomain/Biggame/BigHouse/BigLife/BigMoney/BigStream-MV/漫剧/短剧/短视频/车机BU/FluxVerse/RECON） |
| 执行车道 | 5 | `cph4/fleet/lanes/{bm-a,bm-b,bm-c,bm-d,bm-m}.json` |
| 待办队列 | 1097 行 | `cph4/fleet/PRODUCTION-QUEUE.jsonl`（fleet-ops 338 / biggame 130 / MV 122 / bigmoney 82 / asset-lib 62） |
| 技能 | 39（cph4）+ 26（.codely-cli） | `cph4/skills/`、`.codely-cli/skills/` |
| 智能体 | 5 车道 + 1 名册 | `cph4/agents/AGENT-LIBRARY.md` |
| 工具脚本 | 148（Tools 根）+ 149（Tools/fleet） | `Tools/` |
| 其中质检/闸类 | 58 | `gate|check|qc|detect|dup|scene|freeze|black|loud` 命名 |

**第一条结论**：我们不是缺工具，是**闸很多、没人统一定时跑**。58 个闸散在 Tools 里，没有任何一处强制「出片前必跑」。

## 二、缺口与轮子对照

| 缺口（实测发现的） | GitHub 轮子 | 星 | 状态 |
|---|---|---|---|
| 成片定格/黑帧无人自动拦 | ffmpeg `freezedetect`/`blackdetect`（内置，零安装） | — | **已测** |
| 剪辑表与成片不同源，闸无法对照 | `AcademySoftwareFoundation/OpenTimelineIO` | 2,059 | 未装成（3.14 无轮子、3.12 编译超时） |
| 自动分镜（验证剪辑点） | `Breakthrough/PySceneDetect` | 5,394 | **已测** |
| 画质客观分（对比压片前后） | `Netflix/vmaf`（本机 ffmpeg 已带 libvmaf） | 5,582 | 可用未跑（缺参考片对） |
| 字幕对齐 | `SYSTRAN/faster-whisper` | 26,523 | 未测（已有 asr_qc_win.py，先查重） |
| 台词对口型 | `bytedance/LatentSync` | 6,255 | 已在产线记忆里（漫剧双轨），未本轮复测 |
| 量化回测 | `fasiondog/hikyuu` | 3,688 | 未测（已有自建波链，先对照口径） |
| 竞品 APK 拆解 | `LucasFaudman/apkscan`（apktool+jadx 串成一条链） | 311 | 未测（recon 线有 apk_recon.py，需对照） |
| 智能体长期记忆 | `mem0ai/mem0` | 68,507 | 未测（我们是文件+git 制，迁移代价高） |
| 多闸统一编排 | `casey/just` | 36,587 | 未测（可替 58 个散闸的入口） |
| 上下文压缩 | repomix / LLMLingua | — | 上轮已测，见 TOKEN-OPT-TOOLBOX §四·五 |

## 三、本轮实测（真跑，跑的是我们自己的成片）

样本：`full_mv_v722g_60fps_1080p.mp4`（234.4s / 1920x1096 / 60fps / aac 2ch）与最新 `full_mv_v723_60fps_1080p.mp4`

### 1. 定格与黑帧（ffmpeg 内置）
| 版本 | 黑帧段 | 定格段 | 位置与时长 |
|---|---|---|---|
| v722g | 0 | **5** | 150.53s(1.13s)、155.70s(0.40s)、158.05s(0.95s)、203.35s(0.98s)、228.10s(0.42s) |
| v723（今天） | 0 | **2** | 169.77s(0.40s)、203.43s(0.87s) |

结论：今天这版从 5 处降到 2 处，但**没清零**；剩余 0.87s 定格在 60fps 下等于 52 帧不动，正是 CEO 说的「定格感/掉帧感」。

### 2. 自家闸是否拦得住（mv_stability_gate.py）
| 版本 | seams | 闸报定格 | 闸判定 |
|---|---|---|---|
| v722g | 0 | 3 处：150.667(run3)、158.233(run3)、234.183(run13) | **false（exit 1）** |
| v723 | 0 | 2 处：114.483(run5)、234.183(run13) | **false（exit 1）** |

**闸是工作的**——两版都判不通过，和 ffmpeg 的结论方向一致。

**但两个检测器抓到的位置几乎不重叠**：
- v722g：闸报 150.7/158.2/234.2；ffmpeg 报 150.5/155.7/158.1/203.4/228.1 → 闸漏 2 处
- v723：闸报 114.5/234.2；ffmpeg 报 **169.8/203.4** → **两处完全不重叠**

**并集才是真值**：v723 实际至少有 4 处定格（114.5 / 169.8 / 203.4 / 234.2），单一检测器只看得见一半。
→ 修法：`mv_stability_gate.py` 并入 ffmpeg `freezedetect` 一路，取并集后再判 pass。
→ 附带线索：203.4s 附近的定格在 v722g 与 v723 同时出现，是同一个镜头的持续缺陷，不是随机抖动。

### 2.1 尾帧定格（待裁定）
两版的 234.183s（run13）都落在片尾 14064 帧边界上，属收尾定格。是要保留的定格收尾，还是缺陷，需导演席一句话定；若是收尾，闸应给「片尾豁免」而不是每次都报。

### 3. 响度与真峰值（ebur128）
| 版本 | 集成响度 | LRA | 真峰值 |
|---|---|---|---|
| v722g | -13.2 LUFS | 3.1 LU | **+2.3 dBFS** |
| v723 | -13.2 LUFS | 3.1 LU | **+2.3 dBFS** |

两版一致：响度 -13.2 略高于 -14 交付线（可接受），但**真峰值 +2.3 dBFS 已过 0**，播端会削波，平台响度归一后会更明显。这是本轮最硬的一个缺陷。

### 4. 自动分镜（PySceneDetect 0.7.2，ContentDetector t=27）
v722g：**74 个切点 / 75 个镜头**，平均镜长 3.1s，切点时间码已导出。
用途：与剪辑语法表做机读对照（现在缺的就是这张表——见缺口表第 2 行）。

### 5. 剪辑表缺失（结构性）
`30s-reel-v1/` 下 v722e/f/g、v723 旁边只有 mp4，没有对应的 cut index / EDL；最近的 SHOTLIST 是 10-12 的 v2。→ 闸无法做 D5「剪辑语言 ≥4 类、硬切 ≤70%」的自动判定，只能靠人眼。

## 四、结论与派单

1. **立刻可用的零安装件**：ffmpeg `freezedetect` + `blackdetect` + `ebur128` 三件，应进成片出厂闸（现状：没跑）。
2. **自家闸补盲**：`mv_stability_gate.py` 并入 ffmpeg 定格交叉校验，取并集（修法已明确，属小改）。
3. **必补件**：真峰值卡 ≤ -1 dBFS；v723 现在是 +2.3，需一次 audio 端的 limiter 处理。
4. **结构性补件**：出片同时产 cut index（OTIO 装不上就先用 PySceneDetect 的 CSV 落盘），让 D5 可机判。
5. **暂不引入**：mem0（68.5k，但与我们文件+git 记忆制冲突）、just（先看能否用现有 dispatcher 承担，别再加一层）。
6. **待测清单**（下一轮）：VMAF 压片对比、faster-whisper 字幕对齐、apkscan 对 recon 线、hikyuu 对量化线。

## 五、诚实边界
- 本轮只测了 MV 成片链的 4 项；量化/游戏/竞品/记忆四块的轮子**只做了寻源，没跑**。
- OTIO、vmaf、faster-whisper、apkscan、hikyuu、mem0、just 全部未实测。
- 所有星数为查询时 GitHub 实读数。
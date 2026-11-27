# 提示词库 v1（AI 视频 / 短剧 / 漫剧 / 短视频）

> 立：2026-11-05 · CEO 令「好好去研究提示词库…去 github 等专业网站找，自己去测试，然后落库」
> 定位：**可执行的词条**，不是资料堆。每条必须能直接进我们的产线（i2v / 文生视频 / KF）。

## 目录

```
cph4/fleet/prompt-library/
  README.md                 ← 本文件（用法 + 索引）
  schema.json               ← 词条结构（机读）
  seeds/
    seedance-v1.jsonl       ← 云端 Seedance 系（15 条）
    minimax-h3-v1.jsonl     ← H3 系（9 条）
    directing-v1.jsonl      ← 导演自测配方（低条件表演 / 源帧景别上限）
  tests/
    TEST-20261105.md        ← 实测记录（用我们自己的镜头跑）
    out/                    ← 实测产物（p1 / p2 / p3）
```

## 本地 H3 专用规矩（2026-11-05 实测换来的，云端不适用）

1. **≤90 词**：196 词实测只执行第一句，表演描写被稀释。
2. **禁 `no xxx` 负向清单**：本地 lint 判噪声（一条提示词报 11 处），改成正向约束。
3. **5 秒=一个拍子**：想演三层必须拆三镜再剪，见 `directing.low-budget-performance`。

## 怎么用

1. **按域检索**：`domain` 分 `structure`（分镜结构）/ `camera`（运镜）/ `performance`（表演）/ `style`（风格）/ `dialogue`（台词口型）。
2. **整段套用**：`template` 里的槽位直接替换，**不要改写结构**（时间轴 + 景别 + 事件 + 情绪 + 技术参数五行是骨架）。
3. **进产线前必过实测**：`verified=false` 的词条不许直接进正式镜头；测完把结果写进 `tests/`，已验证的改 `verified=true` 并记 `verified_on`。

## 来源（本轮）

| 来源 | 星 | 许可 | 取用 |
|---|---:|---|---|
| ZeroLu/awesome-seedance | 2818 | MIT | 结构模板、运镜词、短剧三段式 |
| YouMind-OpenLab/awesome-seedance-2-prompts | 2198 | 见仓库 | 2000+ 词条池（后续按需抽样） |
| BeatAPI/awesome-minimax-h3-prompts | 209 | 见仓库 | H3 专项（我们本地 H3 用得上） |

## 三条硬规矩（踩过坑才写的）

1. **时间码必须写**：`[00-05s]` 这种分段是控制节奏的唯一手段；不分段的提示词，模型会把 15 秒拍成一条匀速长镜。
2. **表演要写"演什么"不是"什么感觉"**：`眼神空洞却极有情` 可执行；`很悲伤` 不可执行。情绪必须落成动作或物理细节（瞳孔震动 / 手指发抖 / 吞咽）。
3. **运镜一段只给一个主运动**：`dolly zoom + 环绕 + 升降` 同时写，模型会挑一个或全丢。多运动必须分段时间码。

## 索引

- 结构：`structure.short-drama-3act` / `structure.ugc-3beat` / `structure.timed-shotlist`
- 表演：`performance.micro-expression`（本地未过）/ `performance.restrained-grief` / `performance.pupil-shake` / **`directing.low-budget-performance`（本地已过）**
- 镜头：**`camera.source-frame-ceiling`（源帧决定景别上限）**
- 运镜：`camera.dolly-zoom` / `camera.whip-pan` / `camera.slow-push-in` / `camera.crane-reveal` / `camera.handheld-micro`
- 表演：`performance.micro-expression` / `performance.restrained-grief` / `performance.pupil-shake`
- 台词：`dialogue.lipsync-cue`
- 风格：`style.film-grain-hk90s` / `style.desaturated-imax`
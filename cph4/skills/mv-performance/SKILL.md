---
name: mv-performance
description: MV 表演指导席技能（AI 演员表演：意图动作化/反应延迟/情绪弧/减法治）。Use when directing or reviewing character performance in AI-generated video — writing i2v performance prompts, diagnosing "face jumps / one-beat emotion / dead eyes", or setting timing gates. 正身=cph4/fleet/mv-album-001-jay/AI-ACTOR-PERFORMANCE-v2.md + research/SEAT-performance-20261020.md
---

# MV 表演指导席（mv-performance）

## 一句话
AI 不是缺情绪词，是缺**意图与时序**。写"他想达成什么+身体先后在做什么"，不写"他很悲伤"。

## 硬判据（可直接机检）
- **时序必写**：i2v 词面 ≥1 个先后词（then/before/after/as）；双人镜写「谁先、隔几帧」；禁 `simultaneously/at once/while` 连接两个身体反应。
- **反应延迟**：双人 3-8 帧；单人镜「事件帧→身体起始帧」≥3 帧；0-2 帧判负。
- **表情三阶**：onset 12-20 帧（0.5-0.8s）、offset 8-16 帧（0.3-0.7s）；onset<6 帧=瞬起判负；不回静判负。
- **同帧位移 ≤2**；一镜一意图；1 主导情绪 + ≤2 微手势。
- **眨眼**：4-6s 脸镜 ≥1 次完整眨眼，或明确的"忍眨"（闭合 ≥6 帧）。
- **眼睛要有任务**（确认/等口子/忍着不眨/抓谎），catchlight 只是渲染项。
- **状态不写过程**：单条 i2v 只承载 1 个 state + 位移；"渐变"归 KF/剪辑/state 序列。

## 流程
1. 镜卡写意图（及物动词：to keep the chord from waking her）。
2. 排相位表（0-8f / 8-18f / 18-26f / 26-40f 回静）。
3. 双人镜标"谁先谁后"。
4. 减法治裁剪：砍到 2 个微手势。
5. 烧后测时序帧差→不过回炉。

## 禁用
情绪词（sad/nervous/natural）｜一镜 >2 微手势｜>3 个 AU｜<3s 镜写情绪弧｜把"脸红/出汗/泪光起点"当模型任务（交妆效与调色）｜靠 catchlight 治死眼。

## 验收
盲评 5 人静音看，"他在做什么/想要什么" ≥4 人一致；"像 AI 吗"只作辅判（人眼辨摆拍仅 57-58%）。

## 来源分级
A=Schmidt & Cohn 2003（微笑 onset 0.56s/offset 0.39s）·Perusquía-Hernández 2019（人眼辨摆拍 57-58%）·Ekman FACS；B=Kling/Higgsfield 厂商文（有商业利益）；C=siwookwan/ai-acting-prompt（0★方法论，未验证）。
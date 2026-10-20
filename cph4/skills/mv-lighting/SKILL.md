---
name: mv-lighting
description: MV 摄影灯光席技能（2000 台式布光 × AI 可控光句）。Use when writing or auditing lighting in AI-generated video — night shots going cyan, "face has two lamps", indoor looking like a studio, sodium streetlight correction, halation without a source. 正身=research/SEAT-lighting-20261020.md
---

# MV 摄影灯光席（mv-lighting）

## 一句话
2000 台式布光=**单光源 + 入画实用光 + 不校正钠灯**。光块只写色温=把布光交给模型。

## 硬判据
- **光句五槽**：SOURCE→DIRECTION→QUALITY→RATIO→KELVIN，必须含**相机相对方位**与 **K/比值**，缺一退稿。
  例：`warm key light from 45 degrees screen right`。
- **光比写数**：日 2:1／室内单源 4:1／夜外 8:1-16:1／剪影 ≥32:1；`dramatic/moody` 不计分。
- **测光点写死**：每张脸镜指定唯一基准物（`exposed for her face, the street falling three stops under`）。
- **一镜一主光**：光源名词 ≤2，其一必须是 practical 或天体；禁对称 key+fill。
- **钠灯不校正**：环境 2000-2200K 保橙、脸只吃反射；禁 `neutral white balance / color corrected`。
- **halation 必有源**：日/月/灯入画或压边 15% 才写，同句给过曝理由。
- **年代灯型**：钠 2000-2200K／钨丝 2800-3200K／荧光 4000K 冷绿／车灯 3000K；6500K LED、RGB 渐变霓虹=穿帮。

## 流程
1. 先定光源与方位，再定量级。
2. practical 先入画，再写它落在什么表面。
3. 写测光点。
4. 全曲光锁表（一曲一份 dict，改景不改光句）。

## 禁用
`cinematic/dramatic/moody/chiaroscuro` 裸词｜`studio lighting/softbox/beauty dish/even lighting`｜对称双光｜夜戏 `neutral white balance`｜无源 `glow/halation/bloom`｜夜戏无条件挂 `warm skin tones`（=隐形补光）。

## 验收
夜戏黑位 3-5%；肤色 Hue 15-40°、S 15-45%、青绿 140-200° <5%；同场脸高光侧与 catchlight 位置一致 100%、catchlight ≤1；盲评「实景 or 棚拍」≥8/10、「太阳在哪边」10/10。

## 来源分级
A=Hailuo 官方《Maintaining Lighting Consistency》（光句逐字复用/点光源更真）·Kodak VISION3 500T 数据表·本片实帧判读；C=cinematography.com 钠灯帖·商业博客光词表；GitHub=cinematic-video-prompt-skill 152★MIT（其 studio 词过半=棚拍病源，只取自然光词）。
# VFX-ATMOSPHERE-RESEARCH-v1 — 特效真实性正解 + 工具链（O-20261012-2055「屏幕特效也特别假，你自己看那叫什么烟雾？特效师干嘛吃的？去找好的工具/提示词/github/完整工作流」执法件）

> 结论先行：**生成器画不出真烟——业界正解=干净底片+真烟素材后期合成**。KF/i2v 层禁一切 smoke 实体词，氛围一律后期合成站加。

## 一、定谳：三站特效工作流（完整管线）

| 站 | 氛围/特效做法 | 禁项 |
|---|---|---|
| **KF 关键帧** | 干净帧——零烟实体词；至多 `the faintest atmospheric haze`（空气感微词） | 禁 smoke/fog/wisps/mist drifting 一切实体烟词（生成烟=CG 假·10-12 CEO 判负实锚） |
| **i2v 视频** | 氛围 motion 最小化（HOLD 句锁 atmosphere）——烟的动态生成必假 | 禁烟运动写入 i2v 提示词 |
| **后期合成站（特效师正位）** | **真烟素材预键控 4K overlay + screen 混合** + 强度/透明度分级 + 颗粒/halation 统一 conform | 禁在 KF/i2v 层做任何「氛围补丁」 |

## 二、真烟素材库（免费·预键控·商用可）

- **FX Elements**（fxelements.com/free/smoke）：4K 预键控烟素材·专为合成设计。
- **Pixabay**（pixabay.com/videos/search/smoke overlay）：3,735+ 免费烟 overlay·免署名。
- **Videezy / Pexels / PremiumBeat**：千级免费烟/尘/雾素材（Pexels 18,787+ smoke effect）。
- 合成公式（ffmpeg 可做）：烟层叠底片 `blend=screen`（或 `overlay+opacity`）+ 烟层先调暗压强度（`eq=brightness`）+ 与底片同 LUT 统一。

## 三、film-look / 颗粒 / halation 工具链（github 实锚）

1. **Hance**（hance.video）：电影感 finish 一条命令——color+halation+bloom+grain·GPU·**官方明言 ready to drive from AI agents**——装配站 conform 候选首件。
2. **Atomic-Trash/ComfyUI-ColoristFilmGrain**：35mm 建模颗粒节点（视频级）+ 暖高光 halation 节点 + DeliveryBay 收尾链——ComfyUI 内完成 film finish。
3. **thedevmark/film-lab**：color response+grain+halation 物理管线（照片）。
4. **TMPkl/analog_photo_generator**：LUT+halation+多尺度颗粒可组合管线。
- 落位：装配/finishing 站选型（Hance CLI vs ComfyUI 节点）→ 10-13 装配窗实测定谳。

## 四、i2v 氛围提示词官方指南（Hailuo 官方知识库·我们引擎正主）

- **Volumetric Fog and Haze**（hailuoai.video/knowledge）：雾/霾=三层密度框架（near/mid/far）+ 大气物理+I2V 一致性——i2v 若必须带雾按此写。
- **Layered Atmosphere: Variable Fog Density**：三层雾密度=深度感·防平面化。
- 执法：默认仍然「干净帧+后期真烟」；只有导演席特批的镜才允许生成雾（按官方三层写法）。

## 五、特效师席位补位（AUTO-POLISH 层二「特效合成设计」件激活）

- 特效师席位职责从「提示词里写氛围」转为：**素材选型（烟/尘/光斑）+合成强度表（逐镜 opacity 登记）+conform 统一**。
- 帧级 QC 增检：画内烟实体=FAIL（KF 层）·烟运动=FAIL（i2v 层）·合成烟强度表缺失=FAIL（装配层）。

---
*v1·bm-a 导演席·2026-10-12 20:5x·O-20261012-2055·素材库今夜装配站选型实测*

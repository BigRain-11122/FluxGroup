# WIDE-github-toolchain-20261020 — MV 产线开源轮子扫描（表演/运镜/卡点/调色/质检）

> 消费方：BigStream MV 产线（mv-album-001-jay）。判据：①逐 repo 实读星/license/最近提交 ②三态结论（可用/需改造/不可用）③与现行做法冲突 ④商用授权分账（代码 vs 权重）。
> 验证声明：星/license/pushed_at 全部取自 `api.github.com/repos/<owner>/<repo>` 实读（2026-10-20）；特殊 license 另取 `raw.githubusercontent.com/.../LICENSE` 原文（LivePortrait/MimicMotion/MusePose 三件）。未取得=404/字段缺失，已如实标注。

## 一、工具清单表

| 方向 | repo | ★ | license | 最近提交 | 结论 |
|---|---|---|---|---|---|
| 表演 | bytedance/LatentSync | 6,171 | Apache-2.0 | 2025-06-20 | **可用**（口型修复；仅音频驱动，无表情强度接口） |
| 表演 | KlingAIResearch/LivePortrait | 19,268 | MIT（LICENSE 原文） | 2026-06-01 | **需改造**（商用须换掉 InsightFace 检测模型·其 LICENSE 明写） |
| 表演 | antgroup/echomimic_v3 | 1,091 | Apache-2.0 | 2026-03-18 | **需改造**（输入=图+音+mask+prompt，无强度标量） |
| 表演 | fudan-generative-vision/hallo3 | 1,418 | MIT | 2025-03-13 | **不可用**（停更 19 月，Wan2.1 底，已被后两件超越） |
| 表演 | Wan-Video/Wan2.2（含 Animate） | 18,041 | Apache-2.0 | 2026-09-21 | **可用**（pose_video+face_video 双驱动=表情时序可喂；14B 需大显存） |
| 表演 | Tencent/MimicMotion | 2,676 | Apache-2.0（LICENSE 原文；API 标 NOASSERTION） | 2025-11-18 | **需改造**（SVD 底，512 级，权重卡另核） |
| 表演 | TMElyralab/MusePose | 2,712 | MIT（LICENSE 原文） | 2025-03-05 | **需改造**（姿态驱动，非表情驱动；AnimateAnyone 复现） |
| 表演 | showlab/ACTOR（类） | 未取得 | 未取得 | 未取得 | **未取得**（仓 404，本表以 MusePose 代表 ACTOR 类） |
| 运镜 | hehao13/CameraCtrl | 665 | Apache-2.0 | 2024-05-24 | **不可用**（停更 2 年，AnimateDiff/SVD 旧底，仅吃轨迹张量） |
| 运镜 | TencentARC/MotionCtrl | 1,501 | Apache-2.0 | 2025-02-19 | **不可用**（SVD/VideoCrafter 底，Agent 未随新底更新） |
| 运镜 | ZGCTroy/CamI2V | 172 | MIT | 2025-09-29 | **需改造**（CogVideoX 底，位姿矩阵输入，非"曲线+目的地"接口） |
| 卡点 | librosa/librosa | 8,692 | ISC | 2026-10-06 | **可用**（beat_track/onset_strength 直出切点表） |
| 卡点 | CPJKU/madmom | 1,727 | NOASSERTION（未标准化标注） | 2026-03-20 | **需改造**（检测更准但许可需人工复核） |
| 卡点 | aubio/aubio | 3,773 | GPL-3.0 | 2026-04-10 | **不可用**（GPL 传染，商用闭源集成有风险） |
| 调色 | JanLohse/spectral_film_lut | 114 | MIT | 2026-10-15 | **可用**（按胶片 datasheet 生成 .cube） |
| 调色 | FFmpeg/FFmpeg | 65,451 | LGPL/GPL 双（构建决定） | 2026-10-20 | **可用**（lut3d/xfade/setpts；GPL 组件勿混编分发） |
| 质检 | deepinsight/insightface | 30,004 | 无 SPDX 字段（README 称 MIT） | 2026-10-19 | **不可用**（**模型仅非商用**，商用红线） |
| 质检 | serengil/deepface | 23,575 | MIT | 2026-10-19 | **可用**（代码 MIT；各权重随其自带许可） |
| 质检 | princeton-vl/RAFT | 4,116 | BSD-3-Clause | 2025-08-24 | **可用**（光流判据现成实现） |
| 质检 | Breakthrough/PySceneDetect | 5,270 | BSD-3-Clause | 2026-10-20 | **可用**（切点/重复镜核验） |
| 质检 | FlowFormer | 未取得 | 未取得 | 未取得 | **未取得**（`dcharatan/flowformer` 404，RAFT 足够替代） |

**授权分账（必读）**：LatentSync 代码 Apache-2.0，但底模为 SD1.5 血缘，权重条款**待核**；LivePortrait 代码 MIT、**InsightFace 模型非商用**（LICENSE 原文："models of InsightFace are for non-commercial research purposes only"）——商用必须替换检测器；MimicMotion 权重不在 repo LICENSE 覆盖范围，HF 卡**待核**；insightface 仅代码开源，权重不可商用。

## 二、可直接接入我们产线的 5 条

1. **librosa → 装配环（切点表）**：用 `beat_track`+`onset_strength` 产出 beats/onsets JSON，供现有 `mv_cut_resnap.py` 做"词头选位/拍点落刀"，替换自写 BPM 估计。
2. **spectral_film_lut → 调色环**：按各 MV 的胶片 datasheet 生成专属 `.cube`，ffmpeg `lut3d` 落链；这是"生成器"不是预设包，天然满足 GRADE-LAW 的"每曲独立方案"。
3. **RAFT → 质检环（成片闸）**：落实 RESNAP 已定的"切口前后 6 帧光流方向夹角 <45°、位移比 0.5-2.0x"，现无实现，此为最小补齐件。
4. **PySceneDetect → 质检环（装配后）**：对成片跑切点检测，与 `xq-PACKA-CUTPOINTS` 计划表做帧级对账，并查"同场景重复镜"。
5. **LatentSync → i2v 后处理**：仅对需要口型的近景镜做音轨对齐修口型（禁慢放镜）；跑单镜试点，不进主链。

## 三、与我们现行做法的冲突点

1. **自写重吸附 vs 现成 beat-cut 工具（硬冲突）**：我们的 `Tools/mv_cut_resnap.py` 已是"词头选位 + 拍点落刀"，六曲切点落拍 100%；市面 beat-cut 工具只做纯节拍/onset 均切，没有"词行锚点"概念。直接换 = 把切点从"该行词头最近的拍"打回"等距网格"，歌词同步与 100% 吸附同时丢失。**结论：只借它们的检测器（librosa），不借它们的装配逻辑。**
2. **本地运镜控制 vs 我们的云道 i2v（结构性冲突）**：CameraCtrl/MotionCtrl/CamI2V 全部要求本地加载 Wan/SVD/CogVideoX 权重并输入相机轨迹张量；我们现行 i2v 走云 API（Seedance 2.5 / H3），运镜只能靠提示词"单镜单运镜"。接入 = 换引擎、换算力、换提示词体系，不是加插件。**且三者均无"缓入缓出/目的地"曲线接口**，需求本身不被满足。
3. **成品 film LUT vs 调色法（流程冲突）**：GRADE-LAW 要求量测→逐波段落链→盲评≥9→导演签字；现成 LUT 包是"一键定调"，会绕开量测与盲评门，并把七轴指纹里的色彩轴拉成同一张脸（双胞胎风险）。**只能当生成器用，不能当预设套。**

## 四、不采用清单 + 理由

- **CameraCtrl / MotionCtrl**：停更 1-2 年，底座（AnimateDiff/SVD/VideoCrafter）已被 Wan2.2 世代淘汰；仅支持轨迹张量，无曲线语义；与云道不兼容。
- **CamI2V**：学术件（172★），CogVideoX 底，位姿矩阵输入，产线改造成本高于收益。
- **hallo3**：2025-03 后停更，Wan2.1 底，同任务已被 Wan2.2-Animate / EchoMimicV3 覆盖。
- **aubio**：GPL-3.0，商用闭源链有传染风险；librosa(ISC) 已够用。
- **insightface**：模型非商用红线，直接排除；人脸相似度改用 DeepFace 代码 + 自选可商用权重（权重逐个核）。
- **ACTOR / FlowFormer**：仓地址 404，未取得实证，不进入推荐。

## 五、待实测（最小成本）

1. **librosa vs 现有 beat 表**：对六首已产 `anchors/*-resnap.json` 重算 beats，比切点秒差分布（目标 ≤5ms）；纯 CPU，零 GPU。
2. **spectral_film_lut**：为《星晴》生成 1 个 .cube，取 GRADE-v1 目标帧 10 张套 LUT 与参考带并排看偏差；纯 CPU。
3. **RAFT 接缝判据**：对 W1 已装配片取 3 个切口、各 6 帧算夹角/位移比，验证 45°/0.5-2.0x 阈值是否可执行；单卡数分钟。
4. **PySceneDetect 对账**：跑 1 支成片，比对其切点与 cutpoints JSON 的帧级偏差（可容忍 ≤1 帧）。
5. **Wan2.2-Animate 单镜**：1 张参考图 + 1 段 face_video 跑官方 demo，只验证"表情时序可控"是否真实；不上产线、不下载全量权重前先看显存账单。
# R-20261017-drama-oss-tools-round3-01 — AI 漫剧/短剧开源工具调研 round-3（端到端管线 + i2v 新代际）

> 溯源：AI 漫剧部门工具研究 round-3；查重边界——round-1=R-20261015-drama-oss-stack-01（15 仓五门全量：StoryDiffusion/ComfyUI_StoryDiffusion/GPT-SoVITS/IndexTTS-2/SadTalker/LivePortrait/LatentSync/Wan2.1/LTX-Video/CogVideo/MoneyPrinterTurbo/moviepy/Depth-Anything-2/ai-comic-factory/CosyVoice）、round-2=R-20261016-drama-sfx-tts-deploy-01（音源清单+IndexTTS runbook）、行业面=R-20261015-drama-industry-01。本件只查两大缺口：A=端到端开源管线（MoneyPrinterTurbo 同代新竞品）、B=图生视频新代际 8G 可跑判、C=口型同步/装配新件小查。星数/license/显存三必查，查不到标「未证实」。
> 执行声明：前两飞子代理死于模型超时（45 调用/0 调用两连败），本件=主窗内联实抓收口（2026-10-17）：GitHub HTML 页 + api.github.com（星数/license/pushed_at 权威源）+ search API 落盘解析；raw.githubusercontent 在本环境不可达（三连 aborted），一律改走 HTML 页。星数口径=API stargazers_count，日期口径=pushed_at。

## A. 端到端开源管线（剧本→分镜→i2v→配音→字幕→成片 一条龙）

| 仓 | 星数 | 最近活跃 | license | 一条龙覆盖面 | 8G/国产模型适配 | 判定 |
|---|---|---|---|---|---|---|
| harry0703/MoneyPrinterTurbo | 132,278 | 2026-10-17（当日仍在推） | MIT | topic→script→TTS（Edge 免费/十余家云）→字幕（edge/whisper large-v3-turbo 1.6G 本地）→BGM→ffmpeg 装配；batch CLI 100 任务 | 素材来自 Pexels/Pixabay 拼贴=无分镜、无 i2v；中文原生 | 本代王者，但架构与漫剧线错位——只可借 TTS/字幕/装配工序件 |
| FujiwaraChoki/MoneyPrinterV2 | 32,138 | 2026-09-15 | 未证实 | YouTube Shorts 全自动（文案+TTS+MoviePy 素材拼贴+自动发布），外延成「网赚自动化」全家桶 | 同为素材拼贴、无 i2v | 同代最大星数竞品，但路线发散（做大不做深），不构成管线级威胁 |
| ddean2009/MoneyPrinterPlus | 7,216 | 2025-03-07（放缓） | 未证实 | AI 一键批量短视频+自动发布抖音/快手/小红书/视频号；本地语音 chatTTS/fasterwhisper/GPTSoVITS | 国产平台生态整合最全 | 管线本体同代（素材混剪）；「多平台自动发布」模块值得借工序 |
| （微fork证据）q1uki/MoneyPrinterAICreate | 329 | 2026-02-25 | 未核实 | 基于 MoneyPrinterTurbo 加 AI 分镜大纲+外挂万相通义 Wan2.1 文生/图生视频 | 8G 车道未声明 | 社区已在验证「MoneyPrinterTurbo+i2v」融合方向=我们自建路线的旁证；星数太小无依赖价值 |
| drasstry/shortdrama-pipeline | 120 | 2026-07-02 | 未核实 | 中文短剧 剧本/角色/视频 后端管线 | 未核实 | 直指短剧赛道但微型仓，仅作存在性证据 |

**A 判定**：开源界「剧本→分镜→i2v→配音→字幕→成片」一条龙**仍无人做全**——MoneyPrinter 系全部停在 Pexels/Pixabay 素材拼贴世代；我们自建产线（LLM 分镜+自产图+自研装配）仍是差异化正确路线。可借工序件：MoneyPrinterTurbo 的 TTS 聚合/字幕/BGM/ffmpeg 装配模块 + MoneyPrinterPlus 的多平台自动发布模块。

## B. 图生视频新代际（8G 档可跑判）

| 仓 | 星数 | 最近活跃 | license | 最低显存档（官方明示） | 漫画风适配证据 | 判定 |
|---|---|---|---|---|---|---|
| Wan-Video/Wan2.2 | 17,977 | 2026-09-21 | Apache-2.0（API+README LICENSE AGREEMENT 双证；round-1「Wan 系 Apache 待验」落定） | 官方单卡最低档=TI2V-5B「至少 24GB（如 RTX 4090）」（--offload_model+--convert_model_dtype+--t5_cpu 全开）；T2V-A14B/I2V-A14B/S2V-14B/Animate-14B 单卡「至少 80GB」 | Wan 系漫改/AI 漫剧圈实证最广（LightX2V/DiffSynth/Wan2GP 生态） | 官方档 8G 判负；社区 LightX2V「可在 RTX 5090 和 RTX 4060 (8GB VRAM) 上运行」（README 社区节原文·Wan2.1+2.2 通用）。**勘正**：8.19G=T2V-1.3B 为 Wan2.1 档（Wan2.2 无 1.3B）；FLF2V-14B/VACE 亦为 Wan2.1 模型族——Wan2.2 自身模型表=T2V-A14B/I2V-A14B/TI2V-5B/S2V-14B/Animate-14B，无 FLF 无 VACE |
| Tencent-Hunyuan/HunyuanVideo-1.5（新代·2025-11-20 开源，主仓 HunyuanVideo 12,626★另有 13B 旧代） | 4,571 | 2026-04-10 | Tencent 混元社区 license（欧盟/英国/韩国除外；月活>1 亿须另行申请授权） | 8.3B；**官方最低 GPU 显存=14GB（model offloading 开启口径）**；社区 Wan2GP v9.62 声称「低至 6GB」 | I2V 档齐（480P/720P I2V+step-distill 8/12 步·4090 上 75s/条+cfg-distill+SR 超分）；训练代码开源（Muon 优化器+LoRA） | 官方 14GB 档 **8G 判负**；社区 6GB 声明存在但非官方路径；license 红线须入台账（腾讯社区条款家族，与 IndexTTS 的 bilibili 条款不同门） |
| zai-org/CogVideo（最新公开代=CogVideoX1.5，2024-11-08；CogKit 2025-03-24；无更新公开代） | 13,084 | 2025-11-04 | 代码 Apache-2.0；CogVideoX-2B 模型 Apache-2.0；5B 系模型=CogVideoX 自订 license（MODEL_LICENSE） | diffusers 全优化口径（sequential cpu offload+VAE slicing/tiling，Ampere+ 适配）：1.5-5B T2V BF16 from 10GB*/INT8(torchao) from 7GB*；**1.5-5B-I2V diffusers FP16 最低 4GB***（49 帧·6s·任意分辨率 768≤max≤1360） | I2V 线齐全（CogVideoX-5B-I2V 2024-09 起） | **I2V 线 8G 可跑**（offload 全开·速度受罚）；T2V 1.5-5B INT8 7GB* 属边缘档 |
| Lightricks/LTX-Video（新代=LTX-2.3 22B 世代，前窗抓证：官方 low_vram 档=32GB；4.1k★ 为其 ComfyUI 支持仓——本轮 API 证实主仓另有 11,124★） | 11,124 | 2026-01-05 | Apache-2.0 | LTX-2.3 22B low_vram 档=32GB | ComfyUI 生态支持佳 | **8G 判负**（22B 世代门槛 32GB；低星小模型档不在本轮口径） |

**B 判定**：8G 车道 i2v 新代际可跑序：**CogVideoX1.5-5B-I2V（官方 4GB* 口径·许可最宽·先选）> Wan2.2（官方 24G 判负·社区 LightX2V 4060 8G 实证在役）> HunyuanVideo-1.5（官方 14G 判负·社区 6G 声明）**；LTX-2.3 出局。当前漫剧产线 i2v 主力仍是 comfy 工作流资产盘（Wan2.1 家族），新代际升级按上序备选。**特别记录**：Wan2.2-S2V-14B（语音驱动成片）与 Animate-14B（角色动画/替换）两条衍生线与漫剧赛道高度同频，但官方单卡 80GB 档在 8G 车道不可行——列入 v1.2+ 观察项。

## C. 口型同步/装配小查

| 仓 | 星数 | license | 判定 |
|---|---|---|---|
| TMElyralab/MuseTalk（1.5 代=2025-03-28；训练代码 2025-04-05 开源；仓活跃至 2025-09-26） | 6,737 | 代码=MIT（README 明示·无学术/商用限制）；模型权重「任何用途包括商用」；GitHub license 字段=NOASSERTION（自订文本，以 README 为准） | **vs LatentSync（round-1 已录）成强竞争**：非扩散模型=ft-mse-vae 潜空间单步 inpainting（SD1.4 UNet 架构+whisper-tiny 音频编码）；1.5 代清晰度/身份一致性/唇音同步全面升级（GAN+感知+sync 损失·两阶段训练·时空采样治 jitter）；**30fps+ 实时（V100）**；**4GB VRAM 实测**（RTX 3050Ti 笔记本·fp16·8s 视频约 5 分钟）；视频输入✓（建议 25fps）；Windows 一等公民（download_weights.bat+Windows 命令文档）+ComfyUI 第三方集成。短板：面部区域 256×256 上限、胡子/唇色等身份细节保真弱 |

**C 判定**：MuseTalk 1.5 在「实时+低门槛+商用无限制+Windows 顺手」四项全面压 LatentSync；短板在分辨率上限与身份细节。**漫画面部（非真人）口型同步效果未有任何一方给出证据——两工具对漫剧线均需冒烟验证**，列为 v1.1+ 候选工单（工单 6：MuseTalk 1.5 vs LatentSync 漫画面部对比冒烟）。

## 结论应用表

| 结论 | 落点 | 消费方 |
|---|---|---|
| 1. 端到端开源一条龙（剧本→分镜→i2v→配音→字幕→成片）开源界无人做全——MoneyPrinter 系全停在素材拼贴世代；自建产线=差异化正确路线 | 产线架构确认，不动 | CEO 呈报/产线 |
| 2. 可借工序件：MoneyPrinterTurbo 的 TTS 聚合/字幕/BGM/ffmpeg 装配 + MoneyPrinterPlus 的抖音/快手/小红书/视频号自动发布 | v1.1+ 工单备选（发布自动化，产线收官后置） | 产线 |
| 3. i2v 新代际 8G 车道排序：CogVideoX1.5-5B-I2V（官方 4GB*·Apache 系许可最宽）> Wan2.2（社区 LightX2V 4060 8G 实证·官方 24G）> HunyuanVideo-1.5（官方 14G 判负·社区 6G 声明）；LTX-2.3 出局 | i2v 升级选型备查（现役 comfy 资产盘不动） | 产线 |
| 4. Wan2.2-S2V-14B（语音驱动）/Animate-14B（角色替换）= 漫剧高潜力方向但 8G 车道不可行（官方 80GB 单卡档） | v1.2+ 路线图观察项，不动工 | 产线/CEO 呈报 |
| 5. MuseTalk 1.5 = LatentSync 强竞争者（4GB·30fps·MIT·Windows 原生）；漫画面部口型效果两方均无证据，需对比冒烟 | v1.1+ 工单 6 候选 | 产线 |
| 6. HunyuanVideo-1.5 = Tencent 混元社区 license（月活>1 亿须另行授权+欧盟/英国/韩国除外）；CogVideo 5B 系=CogVideoX 自订模型 license——与 IndexTTS 的 bilibili 条款分属不同红线家族，商用呈报须同台声明 | License 红线台账新增两条 | CEO 呈报/法务 |

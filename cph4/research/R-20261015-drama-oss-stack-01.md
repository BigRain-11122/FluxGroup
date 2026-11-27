# R-20261015-drama-oss-stack-01 — AI漫剧/AI短剧开源工具栈选型（五门评估）

> 溯源：CEO 令 2026-10-15「拉去github等开源网站的工具…还有去拉取有用的github工具工程什么的」。验证声明：star/license=2026-10-15 GitHub 实抓（调研员 33 轮抓取·api.github.com/仓库页直读）；显存=官方 README 或社区经验（逐项标注）；许可证=逐件验原文（oss-harvest §四许可门）。
> 消费方：DRAMA-PRODUCTION-SYSTEM §三接线表 · CHARTER 席位弹药 · 本件=五门评估正身。

## 一、选型总表（按产线环节·推荐主力+备选）

### 1. 中文 TTS 配音（D6 配音站）
| 工具 | stars | License | 显存 | 结论 |
|---|---|---|---|---|
| **index-tts/index-tts**（IndexTTS-2/2.5·原 bilibili 组织迁移） | 24.5k | bilibili 自定义许可 | bf16/fp16 8G 卡可跑（社区） | **主力**：零样本克隆+**8 维情感向量**+语速 0.5-2.0×+拼音注音·中文自然度四者最强；许可=月活<1 亿且年营收<10 亿可商用·**禁用于改进其他商业模型** |
| RVC-Boss/GPT-SoVITS | 62.9k | **MIT** | 推理 ~4G·微调 ~6G+（社区） | 备选：1 分钟少样本微调=**角色音色固化库正位**·Windows 集成包开箱 |
| QwenAudio/CosyVoice | 24.0k | Apache-2.0 | fp16 ~4-6G（社区） | 灾备 |
| SWivid/F5-TTS | 15.4k | 代码 MIT·权重 Emilia 商用自查 | 低 | 英文向·中文弱·不采 |

### 2. 口型+表情驱动（D5 表演站）
| 工具 | stars | License | 显存 | 结论 |
|---|---|---|---|---|
| **KlingAIResearch/LivePortrait** | 19.2k | **代码 MIT·内置 InsightFace 模型非商用** | ~6-8G（社区）·3090 12.8s/250 帧 | **主力（漫格）**：单图肖像驱动表情/头动=漫剧「纸片人开口」最自然；**商用必须换 InsightFace 检测模型**（MediaPipe 等替代） |
| bytedance/LatentSync | 6.1k | Apache-2.0 | **官方：1.5 最低 8G·1.6 最低 18G** | **主力（视频口型）**：1.5 中文视频优化=短剧逐镜口型重绘正位；8G 机禁碰 1.6 |
| OpenTalker/SadTalker | 14.1k | Apache-2.0（LICENSE 直验） | ~4-6G（社区） | 备选兜底·2024-06 停更 |
| antgroup/echomimic | 4.3k | Apache-2.0 | ~8-12G（社区） | 备选（半身+landmark） |

### 3. 图生视频（D4 动效站）
| 工具 | stars | License | 显存 | 结论 |
|---|---|---|---|---|
| **Wan-Video/Wan2.1** | 17.2k | Apache-2.0（代码+权重可商用） | **官方：T2V-1.3B 仅 8.19G**·14B 单卡需 offload·社区量化 480P ~8-12G | **主力**：三档全覆盖·1.3B 恰压 8G/12G 卡·ComfyUI 节点生态最全（kijai） |
| Lightricks/LTX-Video | 11.1k | 代码 Apache-2.0·权重 v0.9.5+ OpenRail-M（可商用） | 2B distilled·官方引用 Q8 版 4060 8G 分钟级 720×480×121 帧 | 备选（分镜动态小样→量产填充）·开发重心已转 LTX-2 |
| zai-org/CogVideo | 13.1k | Apache-2.0 | 2B INT8 ~8-12G（社区） | 备选（中文提示词友好） |

### 4. 角色一致性/漫画分镜（D2/D3）
| 工具 | stars | License | 状态 | 结论 |
|---|---|---|---|---|
| HVision-NKU/StoryDiffusion | 6.5k | Apache-2.0 | **停更**（2024-09） | CSA（Consistent Self-Attention）思路直学+移植件可用 |
| smthemex/ComfyUI_StoryDiffusion | 518 | Apache-2.0 | 2025 仍 push | ComfyUI 节点版直采 |
| jbilcke-hf/ai-comic-factory | 1.3k | Apache-2.0 | **已归档** | LLM+SDXL 分格 Web=只学架构不依赖 |
| 漫画分镜专项搜索 | — | — | 全部 <5★ | **无成熟高星件=此环节自建**（三视图+锁版 SOP·行业工序 2 正身） |

**一致性正解**（行业+工具双印证）：跨集一致性主力=**角色 LoRA 微调**（训练 bm-c 16G）+三视图/场景锁版资产——工具是辅助·资产 SOP 是根本。

### 5. 装配辅助（D7）
| 工具 | stars | License | 结论 |
|---|---|---|---|
| Zulko/moviepy | 15.0k | MIT | 装配胶水主力·2026-08 活跃 |
| harry0703/MoneyPrinterTurbo | 131.4k | MIT | 「文案→语音→素材→字幕→成片」全自动管线最佳脚手架·超活跃（调研时仍在 push）·**直接改造成漫剧装配器** |
| DepthAnything/Depth-Anything-V2 | 9.0k | Apache-2.0 | 2.5D 视差主力（ViT-S 25M 参数 8G 机轻松跑）；新版 Depth-Anything-3 6.5k★ Apache 同许可可升级 |
| FujiwaraChoki/MoneyPrinter | 14.1k | MIT | 旧参考·2026-03 停 |
| ddean2009/MoneyPrinterPlus | 7.2k | **GPL-3.0** | **染疫律：禁入闭源管线·只学** |

## 二、三红线（商用前逐项打勾）
1. **LivePortrait 商用前必须替换 InsightFace 检测模型**（非商用许可·换 MediaPipe 等商用友好替代后才可商用交付）。
2. **IndexTTS-2 禁止用于改进其他商业模型**（bilibili 许可条款）；小团队（月活<1 亿/年收<10 亿）可自由商用。
3. **GPL 件（MoneyPrinterPlus 等）只学机制不搬代码**——承 MV 染疫律（GPL 禁入交付链）。

## 三、三机分工（工具×机位）
3070 16G（bm-c）＝ComfyUI 主产线（SDXL/Illustrious 面板+角色 LoRA 训练）+Wan 量化 i2v+LivePortrait｜4070S 12G（bm-a·夜窗）＝IndexTTS-2 主推理+GPT-SoVITS 音色微调+LTX 快出片+DA-V2 视差｜3070 8G（bm-b·复工后）＝LatentSync-1.5 口型（官方 8G 档）+TTS 备援+whisper 字幕+MoviePy 装配+Ollama 拆剧本（CPU）。

## 四、建议克隆清单（15 仓·P0=前 8·P1=后 7）
| # | 仓库 | 用途 | 许可 |
|---|---|---|---|
| 1 | index-tts/index-tts | 中文零样本 TTS+情感向量 | bilibili 许可（见红线 2） |
| 2 | RVC-Boss/GPT-SoVITS | 角色音色固化 | MIT |
| 3 | QwenAudio/CosyVoice | TTS 灾备 | Apache-2.0 |
| 4 | KlingAIResearch/LivePortrait | 漫格口型表情 | MIT·红线 1 |
| 5 | bytedance/LatentSync | 视频口型 1.5 | Apache-2.0 |
| 6 | Wan-Video/Wan2.1 | 图生视频主力 | Apache-2.0 |
| 7 | Lightricks/LTX-Video | 低显存快出片 | Apache/OpenRail-M |
| 8 | harry0703/MoneyPrinterTurbo | 装配脚手架 | MIT |
| 9 | Zulko/moviepy | 装配胶水 | MIT |
| 10 | DepthAnything/Depth-Anything-V2 | 2.5D 视差 | Apache-2.0 |
| 11 | zai-org/CogVideo | i2v 备选 | Apache-2.0 |
| 12 | HVision-NKU/StoryDiffusion | 一致性思路 | Apache-2.0（停更） |
| 13 | smthemex/ComfyUI_StoryDiffusion | ComfyUI 节点 | Apache-2.0 |
| 14 | jbilcke-hf/ai-comic-factory | 分格架构参考 | Apache-2.0（归档） |
| 15 | OpenTalker/SadTalker | 口型兜底 | Apache-2.0（停更） |

## 五、结论应用表
| 结论 | 落点 | 消费方 |
|---|---|---|
| 选型总表+机位分工 | DRAMA-PRODUCTION-SYSTEM §三/§五 | 全席 |
| 三红线 | CHARTER §三 skill 律+装配线合规自审 | 席位⑫ |
| 克隆清单 15 仓 | media/drama-tools/repos/（gitignored）+ OH-20261015-bigstream.md 采用登记 | bm-b 落地 |
| 「漫画分镜无成熟开源件=自建」判负 | PRODUCTION-SYSTEM §六 空缺自建面 | 席位③④ |
| 一致性=资产 SOP 为主工具为辅 | PILOT-001 §一判据 2 | 席位④ |

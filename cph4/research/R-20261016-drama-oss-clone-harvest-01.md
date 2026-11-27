# R-20261016-drama-oss-clone-harvest-01 — 15 仓工具克隆收成报告

- 日期：2026-10-16/17（克隆 10-16 夜窗起跑·10-17 00:3x 15/15 收齐·CLI 崩亡两次后本窗补办完成）
- 域：drama-dept OSS 工具栈（正典清单=R-20261015-drama-oss-stack-01.md §四）
- 落盘：C:\Fluxgroup\FluxGroup\media\drama-tools\repos\（gitignored·15 仓源码在盘·CLONE-STATUS.txt=体量台账）

## 一、15 仓收成（gh-proxy 优先/直连回退/--depth 1）

| # | 仓 | 体量 | 文件数 | 用途（五门对照） |
|---|---|---|---|---|
| 1 | index-tts | 38.5MB | 339 | TTS 主力候选（v1.1 配音面） |
| 2 | GPT-SoVITS | 35.6MB | 278 | TTS 备选（少样本音色克隆） |
| 3 | CosyVoice | 2.9MB | 164 | TTS 备选 |
| 4 | LivePortrait | 38.4MB | 213 | 人脸驱动/口型（v1.1+） |
| 5 | LatentSync | 10.3MB | 124 | 唇型同步 |
| 6 | Wan2.1 | 10.7MB | 59 | 视频生成备选引擎 |
| 7 | LTX-Video | 7.9MB | 55 | 视频生成备选（快档） |
| 8 | MoneyPrinterTurbo | 203MB | 378 | 短视频全自动产线参照 |
| 9 | moviepy | 93.9MB | 426 | 剪辑程序化库 |
| 10 | Depth-Anything-V2 | 63.3MB | 74 | 深度估计（转场/视差） |
| 11 | CogVideo | 13MB | 204 | 视频生成研究 |
| 12 | StoryDiffusion | 27.2MB | 30 | 连环画一致性生成（**drama 一致性升级候选**） |
| 13 | ComfyUI_StoryDiffusion | 124MB | 530 | 上项的 ComfyUI 节点版 |
| 14 | ai-comic-factory | 3.8MB | 257 | AI 漫画产线参照（HF 出品） |
| 15 | SadTalker | 71MB | 197 | 说话人脸驱动 |

全部 15/15 克隆成功、体量正常（源码仓形态，模型权重按需另拉——部署时走 ModelScope 通道判例）。前次 CLI 崩亡丢失的收成（10-15 夜 7 仓）已由本窗补克隆闭环，任务 task-cbf08fb3 旧案就此销账。

## 二、消费路线（v1.1 候后序）

1. IndexTTS 部署（audio/tts 面首选·13 组音效的 audio_id 见 R-20261016-drama-sfx-tts-deploy-01.md）
2. 一致性升级（CEO 10-15 令「人物一致性重中之重·可以训 LoRA 或找现成轮子」）：StoryDiffusion/ComfyUI_StoryDiffusion 为首选研审对象，LivePortrait/SadTalker 为表演驱动备选
3. 视频引擎备选（Wan2.1/LTX-Video/CogVideo）候 drama v2 分镜动画化评估

# AI 内容生产四链地图 · bm-c（2026-11-15）

> 令：CEO 2026-11-15「cpu 和 gpu 都要发挥最大算力，你现在是自媒体生成的主力机，把男女主 lora、音色库、剪辑、AI 漫剧短剧等全链条好好学习并安装好环境、测试好，去 github 找大家都觉得好的资源，不要闭门造车」。

## 0. 本机算力底座（实测）

| 项 | 实况 |
|---|---|
| GPU | RTX 3070 16G（改动版），CUDA 可用 |
| CPU | 32 线程 |
| RAM | 55.9G 总 / 装完 ComfyUI `--disable-smart-memory` 后 **可用 41.9G**（此前被 ComfyUI 吃到只剩 2.6G，是连串"假死"的根因） |
| 磁盘 | K: 516G 空闲（工作盘）/ C: 1.2T / D: 52G（ComfyUI 所在，紧） |
| 出图主力 | krea2（DiT + Qwen3-VL 文本编码器，ComfyUI 0.45.0 在跑） |
| 出视频主力 | MiniMax-H3（768P int8，1.4~5.9s 单镜，实测单镜 8 分钟档） |

## 1. LoRA 链（男女主一致性）

**选型：musubi-tuner（kohya-ss）**，理由：它是唯一**直接支持 Krea 2 LoRA 训练**的开源框架（`krea2_train_network.py`），且提供 `--convrot_int8` 量化基座——正好吃 3070 没有 fp8 的短板。备选 `sd-scripts`（SDXL/FLUX 成熟，本机有 SDXL checkpoint 可练）。

- 安装：`K:\Fluxgroup\.tools\lora-venv`（Python 3.13 + torch 2.11.0+cu130，CUDA 实测 True）+ `K:\Fluxgroup\.tools\vendor\musubi-tuner-main`（PYTHONPATH 指向 `src`）
- 训练前必须先做两步：`krea2_cache_latents.py`（缓存 VAE latent）+ `krea2_cache_text_encoder_outputs.py`（缓存 Qwen3-VL 输出）——本机 16G 显存省一半时间
- 数据面：角色基准图 16~30 张（多角度、多光位、无文字无特效），caption 必须**剔场景词**（既有判例：VLM 会写 "against blurred cityscape"，照抄会把背景学进 LoRA）
- 现成替代：PuLID（已装，insightface antelopev2）可做「零训练一致性」，适合定妆试镜；LoRA 才适合成片批量
- **合规注意**：InsightFace 预训练模型仅限非商业；商用发行要换方案或授权

## 2. 音色库链（配音/克隆）

| 层 | 工具 | 状态 |
|---|---|---|
| 规则化 TTS | piper `zh_CN-huayan-medium` | **冒烟 PASS**（4.05s wav / 22.05kHz） |
| 多声纹 TTS | sherpa-onnx kokoro-multi-lang（**54 声纹**，中英日等） | **冒烟 PASS**（4 个 sid 各出 wav / 24kHz） |
| 少样本克隆 | GPT-SoVITS v2 | 源码已落 `vendor/GPT-SoVITS-main`，待建 3.10 venv + 权重 |

- 坑：`.tools/kokoro/kokoro-*-multi-lang` 是 **sherpa-onnx 资产包**（tokens/lexicon/voices.bin），用 `kokoro_onnx` 库会报 unpickle 错；正确入口是 `sherpa_onnx.OfflineTts`。
- 克隆数据面：每人 1 分钟干净人声即可（GPT-SoVITS 官方口径），优先从成片里剥人声轨，不要用带 BGM 的素材。

## 3. 剪辑链（草稿 + 字幕 + 卡点）

| 层 | 工具 | 状态 |
|---|---|---|
| 剪映草稿 | pyJianYingDraft 0.3.x（4.6k★ Apache-2.0） | **冒烟 PASS**：9:16 1080×1920/30fps，视频轨 1 段 + 字幕轨 2 段落 `draft_content.json` |
| ASR 字幕 | faster-whisper 1.2.1 | 已装，**权重未落盘**（需 Systran/faster-whisper-*） |
| 卡点 | librosa 1.0.1（节拍/能量） | 已装 |
| 粗剪去静音 | auto-editor | `.tools/pylibs` 已有，未上 PATH |

- 新 API 要点：0.3.x 不是 `add_track`，而是 `script.append_track(TrackSpec(TrackType.video, name=...))` 再 `add_segment(seg, track_name)`；`import_srt` 参数是关键字形式。
- 已知限制：剪映 6.0+ 草稿加密，本机 5.9/10.8 可用（历史桥接已验证）。

## 4. AI 漫剧/短剧链

**结论：不自建平台，采用「本地引擎 + 参考架构」路线。**

- 平台类（BigBanana-AI-Director 2.4k / ai_story 2.1k / aid-studio 1.4k / huobao-drama 17k / OpenMontage 78k）几乎都依赖云端视频 API（Seedance/Seedream/可灵），与本机「本地出图出片、云端只做终稿」的产线纪律冲突；且体积大、绑定账号。
- 索引：`TWO-ICE/awesome-manyu`（按流水线分类 + License 红绿灯），作为选型地图定期扫。
- **本地等价栈（已具备）**：
  - 剧本→分镜：自有 `mv_emit_prompts.py` / `星晴-shots-v2.py` 范式（词表 + 窗口 + 卡点）
  - 角色一致性：PuLID（零训练）+ krea2 LoRA（成片）
  - 关键帧：krea2（ComfyUI）
  - 图生视频：MiniMax-H3 768P（本地）
  - 口型/表演：LivePortrait（ComfyUI 节点已装）、H3 原生口型（有先验，需规避台词镜）
  - 配音：piper/kokoro（已通）/ GPT-SoVITS（克隆）
  - 装配：ffmpeg + pyJianYingDraft（草稿交给剪映终剪）
- 缺口（按优先级）：①faster-whisper 权重；②GPT-SoVITS venv；③krea2 LoRA 首次实训练；④口型镜的"免露嘴"分镜模板。

## 5. 算力分配建议（满负荷但别互相踩）

- GPU 串行：同一时刻只跑一个吃卡任务（KF / i2v / LoRA 训练 / TTS-GPU），用 `gpu_lease` 仲裁（已修：领租约前会给空闲 ComfyUI 发 `/free`）。
- CPU 并行：字幕 ASR、ffmpeg 转码、节拍分析、素材整理可以 6~8 并发，不抢显存。
- 内存闸：ComfyUI 常驻约 3G（禁用 smart memory 后）；LoRA 训练峰值可能 20G+，训练时把 i2v 停下。

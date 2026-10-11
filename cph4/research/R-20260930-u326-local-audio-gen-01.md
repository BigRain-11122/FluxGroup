# R-20260930-u326 · 本地音频生成体系调研（游戏 BGM + SFX）· 对标云端 Sonauto

- **调研人**：Biggame 子公司音频技术调研员（CEO 令 u326）
- **日期**：2026-09-30
- **目标机（A 机）**：Windows · RTX 4070 SUPER **12GB** · Python + torch 2.11 cu128 已装
- **公司用途**：①吸嘟嘟手游/微信小游戏 BGM（60s 循环曲 · 卡通治愈风 · 器乐拟人拟声）②游戏 SFX（捕获叮/胜利 jingle/嘟嘟嘟签名件 0.5–8s）
- **商业红线**：公司年收入 < 1M USD；**一切模型权重必须可商用**——本档案逐模型核对**权重本身的 LICENSE**（代码 LICENSE 不代表权重许可），宁可判负不留模糊。
- **现役云端链**：TJ Generators（Sonauto on fal.ai，工具名 fal_sonilo_music）→ ffmpeg/工具母带（-18 LUFS / TP≤-3 / 44.1k mono / 外放平衡 EQ）→ 14 号验收门。
- **标注纪律**：找不到原文的一律标「未确证」。

> ✅ 档案状态：**已完成**——第 1–8 节全部填充（骨架先行落盘、逐节追加策略已执行），结论速览见 §7。

## 1. 音乐生成（BGM）模型全景与许可过滤

### 1.1 总表（✅可商用 / ⚠️条件商用 / ✗判负）

| 模型 | 机构/年份 | 参数量 | 最长时长 | 显存（12GB 可跑？） | 质量口碑 | 权重许可（已核原文） | 商用判定 |
|---|---|---|---|---|---|---|---|
| MusicGen small/medium/large(melody) | Meta 2023 | 0.3B/1.5B/3.3B | 30s | large fp16 ≈8–10GB（社区数据） | 2023 标杆，现已被扩散系超越 | **CC-BY-NC 4.0**（audiocraft LICENSE_weights） | ✗判负 |
| AudioCraft 全家（JASCO/MusicGen Style/MAGNeT） | Meta 2023–24 | — | ~30s | 类似 | 研究 | 同仓库 LICENSE_weights=**CC-BY-NC 4.0** | ✗判负 |
| Stable Audio Open 1.0 | Stability 2024-06 | 1.1B | 47s stereo 44.1k | 12GB 需 chunked decode（见 §3） | SFX/声音设计强，整曲音乐弱 | Stability AI Community License（<$1M） | ⚠️条件商用 |
| **Stable Audio 3** Small-Music / Small-SFX / Medium / Large | Stability 2026-05 | 433M / 433M / 1.4B / 2.7B(仅API未开源) | 120s / 120s / 380s / — | peak 2.4GB / 2.4GB / 6.52GB | 2026 开源 SOTA 梯队；开源权重**无人声** | Community License + **Gemma 组件条款** | ⚠️条件商用 |
| ACE-Step v1（3.5B） | ACE Studio×StepFun（阶跃星辰）2025-05 | 3.5B | ~4min | 官方 Max 8GB | 2025 开源第一梯队 | **Apache 2.0** | ✅可商用 |
| **ACE-Step 1.5（+XL 4B）** | 同上 2026-01/2026-04 | 2B DiT(turbo/sft)+LM 0.6–4B；XL=4B DiT | 10s–600s | 2B 系 <4GB；XL≥12GB(offload+INT8) | 自评 Suno v4.5–v5 区间 | **MIT** | ✅可商用（首选） |
| DiffRhythm v1/v1.2 | 西工大 ASLP 2025 | 未公开（DiT+VAE） | base 95s / full 285s(4m45s) | base 最低 8GB（--chunked） | 端到端整曲、快 | **Apache 2.0**（代码+DiT 权重） | ✅可商用 |
| DiffRhythm2 | ASLP×小米 2025-10 | 未公开 | 整曲 | 未确证 | 歌曲向（器乐模式在 TODO） | **Apache 2.0**（代码+权重） | ✅可商用 |
| YuE v1 | HKUST/m-a-p 2025 | 7B×两段（s1 语义+s2 声学） | ~5min | 官方生态推荐 24GB+；GGUF 可压但慢 | 人声歌词歌曲强 | **Apache 2.0**（HF 卡标注） | ✅可商用（数据洁净度自担，工程判负） |
| YuE2 | m-a-p 2026 | 3.6B | 整曲 | 24GB BF16 | 符号规划+可编辑乐谱 | **CC BY-NC 4.0**（多方一致） | ✗判负 |
| AudioLDM2 | CVSSP 2023 | ~0.9–1.1B | ~10s（48k 档） | 6–8GB | 旧通用 TTA | **CC-BY-NC-SA 4.0**（HF 卡标注） | ✗判负 |
| HeartMuLa（oss-3B） | 2026-01（arXiv 2601.10547） | 3B | 未确证 | 未确证 | 自称 2026 最强开源（自述，单源） | **Apache 2.0**（repo LICENSE 全文） | ✅可商用（观察） |
| SongGen | ICML 2025 | 未公开 | 整曲 | 未确证 | 单阶段 AR text-to-song | 宣称"fully open-source"，**LICENSE 原文未取得→未确证** | 观察名单 |
| Suno/Udio/Mureka/Sonauto | 各家 | 闭源 | — | — | 商用闭源第一梯队 | 无本地权重 | 不可本地部署 |

### 1.2 许可原文结论（逐模型核实记录——只认权重 LICENSE）

**① MusicGen / AudioCraft 全家（Meta）——判负**
audiocraft README License 节原文：*"The code in this repository is released under the MIT license … **The models weights in this repository are released under the CC-BY-NC 4.0 license** as found in the LICENSE_weights file."*——覆盖 MusicGen、AudioGen、JASCO、MusicGen Style、MAGNeT 全部官方权重。代码 MIT 救不了权重。来源：https://github.com/facebookresearch/audiocraft

**② Stability 系（SAO 1.0 / SAO Small / Stable Audio 3）——条件商用（我司当前符合）**
stability.ai/license 官方 FAQ 原文：*"The Stability AI Community License allows for research, non-commercial, **and commercial use of the Core Models for individuals or organizations that generate under $1M (or local currency equivalent) of annual revenue**, regardless of the source of that revenue."*——营收超 $1M 需购 Enterprise License；*"the Community License is revocable if you violate its terms"*（违约可撤销）。输出归属：*"you own outputs generated from the Core Models or Derivative Works"*。
- HF 四仓（stable-audio-open-1.0 / stable-audio-open-small / stable-audio-3-medium / stable-audio-3-small-sfx）license_name 均为 `stable-audio-community`，且 **gated:auto**（需 HF 账号逐仓同意条款才能下载）。
- **Stable Audio 3 附加条款**：内含 t5gemma 文本编码器组件，HF 卡原文 *"This model also includes components redistributed under the **Gemma Terms of Use** … including the use restrictions in Section 3.2"*——需一并遵守 Gemma 条款（Gemma ToU 允许商用但有用途限制条款）。
- **结论：条件商用**。我司营收 <1M USD → 当前免费商用合法；**挂账风险=营收破线或 Stability 调整条款**。

**③ ACE-Step v1（Apache 2.0）/ ACE-Step 1.5（MIT）——可商用，最干净**
- v1：GitHub README 原文 *"This project is licensed under Apache License 2.0"*；HF 卡 `license:apache-2.0`（ACE-Step-v1-3.5B，未 gated）。
- v1.5：HF 卡（ACE-Step/Ace-Step1.5 及 xl/lm 全系）`license:mit`；卡内原文商业承诺：*"**You can strictly use the generated music for commercial purposes**"*，训练数据=专业授权曲库 + 免版税/公有领域 + MIDI 合成（Licensed / Royalty-Free / Synthetic Data 三类声明）。
- **MIT 无收入门槛、无用途限制、可再分发——全表唯一零条件音乐模型。**

**④ DiffRhythm / DiffRhythm2——可商用（附谨慎项）**
GitHub 原文：*"DiffRhythm (code and DiT weights) is released under the **Apache License 2.0**"*（2025-03-07 官宣由受限许可转 Apache）；DiffRhythm2：*"DiffRhythm 2 (code and weights) is released under the Apache License 2.0"*。谨慎项：声明口径是"code and DiT weights"，配套 VAE/BigVGAN 声码器为独立上游许可（BigVGAN=MIT，无碍）；训练数据洁净度未做 ACE-Step 式逐项声明。来源：https://github.com/ASLP-lab/DiffRhythm 、https://github.com/ASLP-lab/DiffRhythm2

**⑤ YuE v1 / YuE2——v1 名义可商用但工程判负；YuE2 判负**
- v1：HF 卡 `license:apache-2.0`（m-a-p/YuE-s1-7B-anneal-en-icl，未 gated）→ 名义可商用；但官方 README 含音乐版权风险免责声明、社区对训练数据来源合规性有长期争议（数据洁净度自担）；且 7B×两段、生态推荐 24GB+ → **对 12GB 器乐 BGM 场景工程判负**。
- YuE2：代码 Apache-2.0，**权重 CC BY-NC 4.0**（opensourcealternatives.to / cpu3d / ai-tldr 三方独立转述一致）→ **判负**。

**⑥ AudioLDM2 / Tango2 / TangoFlux——全判负**
- cvssp/audioldm2 HF 卡：`license:cc-by-nc-sa-4.0`。
- declare-lab/tango2 HF 卡：`license:cc-by-nc-sa-4.0`。
- TangoFlux LICENSE.md 原文：*"created for **non-commercial, research-only** purposes under the **UK data copyright exemption**"* + WavCaps 数据集仅限学术用途 → 研究专用，判负。

**⑦ 2024–2026 新秀补录**
- **HeartMuLa**（2026-01，arXiv 2601.10547）：HeartCLAP/HeartTranscriptor/HeartCodec+生成模型 oss-3B；repo LICENSE 全文=Apache 2.0 → 可商用；质量口碑主要来自项目自述与利益相关对比站（heart-mula.com），**未确证**，列观察名单。
- **SongGen**（ICML 2025，单阶段 AR text-to-song，人声+伴奏双轨）：宣称权重/代码/数据全开源，但本调研未能取得其 LICENSE 原文（README 拉取 404）→ **未确证**，观察名单。
- （未入表：Riffusion 等 SD 谱图方案已过时；Meta AudioBox/Google SoundStorm 无开放权重。）

### 1.3 质量口碑速评（BGM 视角）
- **ACE-Step 1.5**：官方 README 自评 *"Commercial-Grade Output — Quality beyond most commercial music models (**between Suno v4.5 and Suno v5**)"*；第三方称其 SongEval 8.09 超 Suno v5（单源，采信需 §6 对打实测）。2026 年公认开源第一梯队。
- **Stable Audio 3**（2026-05 开源权重，2026-06 更新）：官方"trained on fully licensed data"；评测普遍指出开源权重**无人声、纯器乐/SFX 向**——对「卡通治愈·器乐拟声 BGM」恰好对口（人声是短板也是无关项）；Medium 380s 长曲结构强。
- **Stable Audio Open 1.0**：SFX/声音设计强项，整曲音乐长程结构弱——更适合作 SFX 位。
- **DiffRhythm v1.2**：端到端整曲+快；编曲丰富度口碑逊于 ACE-Step 系（社区观感，未确证）。
- **MusicGen**：2023 技术底子 + 30s 上限 + NC，三重出局。

## 2. 音效生成（SFX）模型

### 2.1 总表

| 模型 | 年份 | 参数量 | 时长/采样率 | 显存 | 质量/定位 | 权重许可 | 商用判定 |
|---|---|---|---|---|---|---|---|
| Stable Audio Open 1.0 | 2024-06 | 1.1B | ≤47s / 44.1k stereo | 12GB 需 chunked decode | SFX/声音设计强（官方定位） | Community（<$1M） | ⚠️条件商用 |
| Stable Audio Open Small 0.9 | 2025-05 | 341M 主干（HF safetensors 另含组件合计 ~497M） | **≤11.22s** / 44.1k | 极低（CPU/Arm 端侧可跑） | SFX/采样器；官方自述限制：无人声、非电子音乐弱 | Community（<$1M） | ⚠️条件商用 |
| **Stable Audio 3 Small-SFX** | 2026-05 | 433M DiT（全仓 F32 合计 5.68 亿参数） | ≤120s / 44.1k stereo | peak 2.40GB@120s（官方表） | **SFX 专精分型**（ComfyUI 类别 reprompt 支持 SFX/One-shot） | Community + Gemma 组件 | ⚠️条件商用（主选） |
| Stable Audio 3 Medium | 2026-05 | 1.4B | ≤380s | peak 6.52GB@380s | 音乐+SFX 双修 | Community + Gemma 组件 | ⚠️条件商用 |
| AudioGen（Meta） | 2023 | medium 档（≈1.5B，**未确证**） | ~10s / 16kHz | 中 | 环境音 | **CC-BY-NC 4.0**（audiocraft LICENSE_weights） | ✗判负 |
| MMAudio（CVPR 2025，UIUC+Sony） | 2024-12 | ~1B+（**未确证**） | 8s 默认 / 44.1k | ~6GB fp16（官方） | V2A+T2A 强，同步模块 | **checkpoints CC-BY-NC 4.0** | ✗判负 |
| AudioLDM2 | 2023 | ~1B | ~10s | 6–8GB | 通用 TTA | **CC-BY-NC-SA 4.0** | ✗判负 |
| Tango / Tango2（declare-lab） | 2023–24 | ~0.9B | 10–30s | ~6GB | AudioCaps 系当期 SOTA | tango2 卡 **cc-by-nc-sa-4.0** | ✗判负 |
| TangoFlux | 2024-12 | 未公开 | ~10s | 低 | 极快 flow matching | **研究专用**（UK 版权豁免 + WavCaps 学术限定） | ✗判负 |
| SoundCTM-DiT-1B（Sony） | 2024-05 | 1B | ~10s / 44.1k 全频带 | 未确证（估 6–8GB fp16） | 1 步/多步一致性模型，论文自评对打 SAO 不落下风 | **code MIT + weights CC-BY 4.0** | ✅可商用（观察） |

### 2.2 关键核实记录
- **MMAudio = 「代码 MIT ≠ 权重可商用」的典型反面教材**。README License 节原文：*"The code … is released under the MIT license"* + *"**The checkpoints are released on Hugging Face under the CC-BY-NC 4.0 license**"*，训练数据节另有声明 *"We do not guarantee that the pre-trained models are suitable for commercial use. Please use them at your own risk."*——若只看代码 LICENSE 必踩商用红线。V2A 能力可惜（我们本来想要它做画面配音），但权重 NC，判负。来源：https://github.com/hkchengrex/MMAudio
- **Stable Audio Open Small 0.9** 官方自述限制（经 aimodels.fyi 转引模型卡）："restricted to **11-second** generation, lacks realistic vocals, and performs poorly on non-electronic music genres"——11s 上限对我们 0.5–8s 的 SFX 需求正好是甜区；341M+Arm 合作定位端侧，12GB 显然无压力。来源：https://www.aimodels.fyi/models/huggingFace/stable-audio-open-small-stabilityai
- **SA3 Small-SFX**：HF safetensors 统计 F32 合计 567,573,761 参数（DiT 433M+t5gemma 组件），仓库体积 3.49GB；官方性能表：H200 上 5s 音频 0.41s、120s 音频 0.45s，peak VRAM 2.40GB；Windows 可走官方 TFLite CPU 路线（bootstrap.ps1）。Small-Music/SFX 双分型=官方专门拆训。
- **SoundCTM**（Sony/soundctm）：HF 卡原文 *"License: Code is released under MIT, **model weights are released under CC-BY 4.0**"* → 权重可商用；但产线工程成熟度、社区案例远少于 Stability 系，且 2024 世代 → 列观察备选。来源：https://huggingface.co/Sony/soundctm 、https://arxiv.org/abs/2405.18503
- **TangoFlux**：HF 仓库附 LICENSE.md 原文明确 research-only（见 §1.2⑥），连"借用"的空间都没有。
- 结论：**SFX 位商业安全且工程成熟的候选全部集中在 Stability 系**（Community License 条件商用）+ Sony SoundCTM（CC-BY，观察）；Meta/AudioLDM2/Tango 系全军覆没。

## 3. 12GB RTX 4070 SUPER 实跑可行性

### 3.1 逐候选显存/速度报告（附来源）

| 候选 | 官方/社区显存数据 | 12GB 判定 | 生成速度 |
|---|---|---|---|
| ACE-Step 1.5（2B turbo/sft） | 官方 arXiv+README：**<4GB VRAM**；GPU 档位表 8–16GB 档=2B DiT+LM 0.6B(8–12GB)/1.7B(12–16GB) | ✅ 宽裕（官方推荐档） | A100 <2s/曲、RTX 3090 <10s/曲（官方）；4070S 估 5–10s/曲（估计） |
| ACE-Step 1.5 XL（4B） | 官方表：≥12GB 需 **CPU offload+INT8**；权重 bf16 ≈18.8GB、显存占用 ~9GB | ⚠️ 最低可行线（慢） | 8 步 turbo；offload 后明显变慢（未确证具体秒数） |
| ACE-Step v1（3.5B） | 官方 2025-05-10 更新：**Max VRAM 降至 8GB**（`--cpu_offload --overlapped_decode`）；Windows 需 triton-windows | ✅ 宽裕 | RTX 3090 1min 音频 4.7s@27 步（官方表） |
| Stable Audio 3 Medium | 官方性能表：peak VRAM 120s=6.49GB（chunked 后 ~5.14GB）、380s=6.52GB（H200 实测） | ✅ 余量充足 | H200 0.78s/120s；消费卡估计数秒–十几秒级（未确证） |
| Stable Audio 3 Small 系 | 官方表：peak 1.69–2.40GB；官方支持 CPU 路线 | ✅ 无压力（甚至可纯 CPU） | H200 0.45s/120s；CPU(TFLite) 5.92s/120s（官方） |
| Stable Audio Open 1.0 | HF 社区帖：3080Ti 12GB+32GB RAM "works"；另有用户报"total 12.2GB 含桌面占用"（贴线）；3060 12GB 报告：采样 ~6GB，**解码阶段瞬时 12GB+2GB RAM**（VAE 全量解码） | ⚠️ 可跑但必须 chunked decode+fp16 | 社区反馈"偏慢"（A10G 亦有人嫌慢；4070S 具体秒数未确证） |
| Stable Audio Open Small | 341M，Arm/端侧定位 | ✅ 极宽裕 | 亚秒级（on-device 定位） |
| DiffRhythm base | 官方 README："**requires a minimum of 8G VRAM** … use the --chunked argument"；关闭 chunked 更高 | ✅ 可跑（开 chunked） | 官方宣传"blazingly fast"（未给本卡实测） |
| MusicGen large（对照） | fp16 推理 ~8–10GB（权重 6.5GB，社区数据） | ✅（但 NC 出局） | AR 自回归，分钟级/30s |
| YuE v1（对照） | 生态推荐 24GB+；7B 权重 ~16GB；GGUF Q4 单模型 ~5–6GB | ⚠️ 量化后勉强、速度分钟级 | 慢（工程判负） |

来源：ACE-Step 1.5 GitHub/arXiv 2602.00744、acestep-v15-xl-turbo HF 卡 GPU 表、ACE-Step v1 README（2025-05-10 更新+性能表）、stable-audio-3 GitHub 性能表、HF stable-audio-open-1.0 Discussion #3（VRAM Estimation，含 3060 12GB/3080Ti 12GB 用户实测）、ASLP-lab/DiffRhythm README、nexgpu.net audiocraft 自托管实测、tobert/yue-inference（24GB 推荐）。

### 3.2 offload/量化方案菜单（Windows 适用）
1. **fp16/bf16**：所有候选默认首选（显存减半，质量无损）。
2. **chunked decode（分块解码）**：stable-audio-tools / SA3 / DiffRhythm 均支持——**VAE 解码才是显存大头**（SAO 1.0 社区 OOM 全发生在解码阶段，见 Discussion #3 traceback：snake_beta 激活处爆 1GB）；开分块后 SAO 1.0 从"贴线 OOM"变稳。
3. **CPU offload（权重换页）**：ACE-Step 1.5/XL 内置（`--cpu_offload`）；diffusers 系可用 `enable_sequential_cpu_offload()`；代价=速度下降。
4. **INT8 量化**：ACE-Step 1.5 内置（≤6GB 档位靠它跑 2B DiT）。
5. **8bit/bitsandbytes**：本次三件套候选（ACE-Step 1.5 / SA3 / SAO）**均不依赖 bnb，不用装**（备注：现代 bnb 已官方支持 Windows，若未来有 8bit 需求无系统障碍）。
6. **环境隔离**：ACE-Step 1.5 官方 Python 3.11–3.12 + uv 自动锁依赖；SA3 pyproject 锁 torch 2.7.1（cu118/126/128 均有官方轮）——与 A 机现有 torch 2.11 cu128 **分 venv 隔离，勿混装**。

### 3.3 小结
12GB 4070 SUPER 对推荐三件套（ACE-Step 1.5 2B 系 / SA3 Small-SFX / SA3 Medium）**全部宽裕**；贴线的只有 SAO 1.0 全量解码（chunked 解决）和 ACE-Step XL（12GB 最低线）。无候选存在"12GB 跑不了核心功能"的问题。

## 4. Sonauto 本体

### 4.1 是什么（逐项核实）
- **公司**：Sonauto，旧金山 AI 音乐创业公司，2024 年公开上线；创始人 Hayden Housen、Ryan Tremblay（Cornell 校友）；YC W24，披露融资 $500K。YC 页定位："AI music editor that turns prompts, lyrics, or melodies into full songs in any style"。来源：https://www.ycombinator.com/companies/sonauto 、https://tracxn.com/d/companies/sonauto/ 、https://ai.miraheze.org/wiki/Sonauto
- **模型**：自研**闭源**模型 **Melodia**——YC 官方招聘页原文：*"we're building a platform … with the help of **our in-house generative music model Melodia**"*。社区描述其为 latent diffusion 连续空间架构（第三方转述，**未确证**）；**参数量未公开（未确证）**。来源：https://www.ycombinator.com/companies/sonauto/jobs/b34gnqK-ml-engineer-researcher
- **开源否**：完全闭源，无本地权重，无任何权重分发渠道——本地化对标只能选同代开源模型。
- **fal.ai 版本（即我们 fal_sonilo_music 调的模型）**：**Sonauto v2.2**。fal 官方博客：每次生成 **1.5 分钟（90s）**、44.1kHz 16-bit"CD 音质"、$0.075/次、三个端点（Text to Music / Extend / Inpaint）、v2.2 新增 BPM 手动配置。来源：https://blog.fal.ai/sonauto-now-available-on-fal/
- **2026 动态**：公司改名 **Treblo**（官网 treblo.com；API 文档自述 "Treblo (formerly known as Sonauto)"）；Melodia v3 上线（消费端免费不限量、API 端 preview 计费）；2026-04-01 官方博客《We're pausing Melodia V3 — here's why》自述因内部评测发现未预期问题暂停 v3（该博文本机拉取失败，按搜索摘要转述；**与 v3 上线新闻时间线存在矛盾→未确证，以官方博客为准**）。来源：https://treblo.com 、https://treblo.com/developers/docs 、https://aimusic.events/news/treblo-melodia-v3-free-unlimited-classifier 、https://blog.sonauto.ai/2026/04/01/pausing-melodia-v3/
- **对打注意**：云端链接现役合同期内的 v2.2 端点保持不变即可；改名 Treblo 不影响 fal 端点调用，但需跟踪其账号/合同主体变更。

### 4.2 本地开源 vs 云端 Sonauto 质量差距（客观估计）
- **权威盲测排行榜缺失**：音乐生成没有公认公开榜（AudioArena 类非公认基准）；SongEval 等为开源自动评测，模型方自评常用 → 差距只能按"官方自评 + 第三方单源 + 我方对打实测"三线并取，**结论最终以 §6.4 实测为准**。
- 可得证据链：
  1. ACE-Step 1.5 官方自评：质量介于 **Suno v4.5 与 v5 之间**（README 原文）；第三方评测称其 SongEval 8.09 超 Suno v5（studio.aifilms.ai，单源）；
  2. Sonauto 官方只主打"**vocal quality 行业最佳**"（fal 博客）——人声是它的核心卖点；
  3. 2026 年社区对比普遍结论：开源（ACE-Step 系/SA3）已进入闭源商用模型同代区间，人声/歌词仍是 Suno/Sonauto 相对强项。
- **我方场景化判断（60s 卡通治愈·纯器乐·循环曲）**：
  - Sonauto 的优势项（人声质感、歌词对齐）在纯器乐 BGM 上**不适用**；
  - Sonauto 固定 90s/次，60s 循环曲还需裁剪；本地 ACE-Step 1.5 可**定长 60s 直出**+repaint 补循环缝——结构性优势；
  - 本地优势另含：BPM/调性/拍号元数据控制、LoRA 品牌风格化（嘟嘟嘟签名音色）、批量 8 曲并行、零 API 成本/无限次；
  - **差距水位客观估计：音色细腻度与"母带密度"本地约为 Sonauto v2.2 的 80–100%（区间宽，因无人跑过同 prompt 对比），结构与编曲已同代**。SFX 维度 Sonauto 本就不是 SFX 模型，本地 SA3 Small-SFX 对口碾压。

## 5. 产线工程参考（Windows 推理产线，不训练）

### 5.1 参考实现盘点
| 组件 | 是什么 | 许可 | 对我们的用途 |
|---|---|---|---|
| **stable-audio-3**（Stability-AI 官方，2026） | 新一代官方推理平台：uv 安装、Python API（`StableAudioModel.from_pretrained("medium")`）、CLI（`stable-audio --model small-sfx -p "..." --duration 3 -o ding.wav`）、Gradio；text2audio / audio2audio 编辑 / inpainting 三模式；TFLite(含 Windows)/MLX/TensorRT 优化路线 | 代码 MIT | **SFX+音乐推理产线主参考**（官方定位"inference and fine-tuning"，推理开箱即用） |
| **stable-audio-tools**（官方旧平台） | SAO 1.0/Small 官方推理+训练库 | 代码 MIT | SAO 1.0 的 diffusers/stable-audio-tools 双后端之一；已被 SA3 接棒 |
| **diffusers** | `StableAudioOpenPipeline` 原生支持 SAO 1.0（≤47s stereo 44.1k） | Apache/类 MIT（库本身） | 工程最简 5 行代码路线（仅 SAO，非 SA3） |
| **ACE-Step-1.5 仓库** | `uv sync` → `uv run acestep`(Gradio) / `uv run acestep-api`(**REST 产线对接点**)；Windows .bat 脚本 + 官方 Windows 便携包（7z）；另有 VST3 插件（GGML） | MIT | BGM 产线主参考 |
| **audiocraft**（Meta） | MusicGen/AudioGen 推理管线 | 代码 MIT（权重 NC） | 权重 NC → 仅研究参考，不入产线 |
| **ComfyUI 音频生态** | **原生内置 SA3**（day-0 支持，Comfy-Org 重打包权重+Qwen3.5-2B 类别感知 reprompt：Music/Instrument/SFX/One-shot）；**原生支持 SAO 1.0**（Stable Audio Sampler）；**ComfyUI_ACE-Step 节点**（ACE-Step 官宣） | GPL/各节点 | 设计师可视化迭代层+Windows 免编译红利 |

来源：https://github.com/Stability-AI/stable-audio-3 、https://github.com/Stability-AI/stable-audio-tools/blob/main/LICENSE（MIT 全文已核）、https://docs.comfy.org/tutorials/audio/stable-audio/stable-audio-3 、https://blog.comfy.org/p/stable-audio-3-day-0-support 、https://comfy.org/p/supported-models/stable-audio-open-1-0/ 、https://docs.comfy.org/tutorials/audio/stable-audio/stable-audio-1 、https://huggingface.co/docs/diffusers/api/pipelines/stable_audio

### 5.2 Windows 兼容坑清单（逐坑给解法）
1. **Flash Attention 2（SA3 Medium 官方 PyTorch 管线硬依赖）**——Windows 无官方轮子。解法：A) 社区预编译轮（mjun0812/flash-attention-prebuild-wheels 含 Windows 版；ussoewwin/Flash-Attention-2_for_Windows 提供 flash_attn-2.8.2×torch2.8×cu129×py3.11/3.12 轮）——**必须严格匹配 torch×CUDA×Python 三元组**；B) **改走 ComfyUI 原生 SA3 工作流**（自带注意力实现，绕开 FA2，Windows 最省事）；C) 用 SA3 Small 系（CPU/TFLite 路线，无 FA2 依赖）。
2. **torch 版本锁**：SA3 锁 torch 2.7.1（cu118/126/128 三通道可选）；ACE-Step 1.5 走 uv 自锁。**与 A 机现有 torch 2.11 cu128 分 venv 隔离**，避免互相降级。
3. **triton**：ACE-Step v1 开 `--torch_compile` 才需要 `pip install triton-windows`（官方指引）；v1.5 的 uv 方案自动处理，无需手动。
4. **espeak-ng（DiffRhythm）**：Windows 装 .msi 后设 `PHONEMERIZER_ESPEAK_LIBRARY` / `PHONEMERIZER_ESPEAK_PATH` 两个环境变量即可 Windows 推理（官方 README Windows 节+issue #17 修复）。
5. **ffmpeg**：audiocraft/stable-audio-tools 依赖系统 ffmpeg；A 机母带链本就有 ffmpeg → **零新增负担**。
6. **bitsandbytes**：三件套候选均不依赖 → **不用装**（旧印象"Windows 装 bnb 痛苦"与本项目无关）。
7. **HF gated 权重**：stabilityai 四仓均 gated:auto → 需 HF 账号逐仓网页同意条款 + 本地 `HF_TOKEN`；国内拉取用 `HF_ENDPOINT=https://hf-mirror.com`；Comfy-Org 重打包的 ComfyUI 版权重通常免 gate。ACE-Step 系未 gated，且有 ModelScope 官方镜像（国内更稳）。
8. **vllm**：ACE-Step 1.5 的 LM 后端在 Linux 推荐 vllm，Windows 用 `pt` 后端 + 0.6B/1.7B LM 即可（官方档位表即如此推荐）；**勿在 Windows 趟 vllm（未确证其 Windows 稳定性）**。

### 5.3 产线形态建议
**批量层**：ACE-Step REST（`uv run acestep-api`）+ SA3 CLI/Python API → 脚本预检（时长/采样率/LUFS 预筛）→ **ffmpeg 母带（-18 LUFS / TP≤-3 / 44.1k mono / 外放平衡 EQ，与现役云端链完全同规格）** → 14 号验收门。
**迭代层**：ComfyUI（SA3 原生节点 + ACE-Step 节点）给设计师做可视化试听/改 seed/repaint。
**风格层**：ACE-Step LoRA（官方：8 首歌、3090 12GB、1 小时）做嘟嘟嘟品牌音色库。

## 6. 推荐定谳

### 6.1 音乐 gen 主选：**ACE-Step 1.5**（MIT）
配置：`acestep-v15-turbo`（2B DiT，8 步）+ `acestep-5Hz-lm-0.6B`（稳妥）或 1.7B（Windows 用 pt 后端）。
四维理由：
1. **许可安全**：MIT 权重 + 官方"strictly use … for commercial purposes"声明 + 合规训练数据三重保险——全表唯一零条件音乐模型（vs Stability 系的营收门槛挂账风险）；
2. **12GB 可跑**：<4GB 起步，官方档位表 12GB 正中推荐档；
3. **质量最接近 Sonauto**：自评 Suno v4.5–v5 区间=开源最强梯队；600s 时长 + BPM/调性/拍号元数据 + repaint/edit/extend——**60s 循环曲可定长直出**（Sonauto 固定 90s 还要裁）；
4. **工程简单**：官方 Windows 便携包/.bat/REST API/VST3/ComfyUI 节点全家桶；LoRA 一键品牌风格化。
备选 1：**Stable Audio 3 Medium**（条件商用合规；380s；音乐+SFX 双修；ComfyUI 原生）——对打后若 ACE-Step 音色不满意则换装。
备选 2：**ACE-Step 1.5 XL turbo**（质量上限档；12GB=offload+INT8 最低线，慢）。
不选：MusicGen/AudioCraft/JASCO（NC）、AudioLDM2（NC-SA）、YuE2（NC）、YuE v1（Apache 但 24GB+人声向）、DiffRhythm（可商用备胎，编曲口碑次之）。

### 6.2 SFX gen 主选：**Stable Audio 3 Small-SFX**
理由：官方 SFX 专精分型（Small-Music/SFX 拆分训练）；≤120s 覆盖 0.5–8s 全需求；peak 2.4GB+CPU 可跑=**可开多进程批量产**；Community License 我司当前合规；ComfyUI 原生 SFX/One-shot 类别 reprompt。
备选 1：Stable Audio Open Small 0.9（更轻 341M；11s 上限够用）；
备选 2：SA3 Medium（与 BGM 一件通吃，减少装机件数）；
观察：SoundCTM-DiT-1B（CC-BY 4.0 零条件可商用，但工程成熟度未确证）。
**分工注**：胜利 jingle / 嘟嘟嘟签名件属"微型音乐"→ 归 **ACE-Step 1.5** 生成 5–10s 器乐 motif 更贴题；纯音效（捕获叮/嗖/水泡）→ 归 SFX 模型。

### 6.3 装机命令清单（A 机 Windows · Python 3.11–3.12 · 建议独立 venv）
```powershell
# 0) 国内镜像 + HF token（stabilityai 系 gated：网页逐仓同意条款后建 token）
setx HF_ENDPOINT "https://hf-mirror.com"
setx HF_TOKEN "hf_xxxxxxxx"

# 1) BGM 主力：ACE-Step 1.5  —— 下载约 7–8GB（2B DiT ~4.7GB + LM 0.6B ~1.2GB + DCAE/vocoder 等）
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5 ; uv sync
uv run acestep        # Gradio UI :7860（首跑自动下权重，HF/ModelScope 双源）
uv run acestep-api    # REST :8001 —— 产线对接
# 替代懒人路线：官方 Windows 便携包 https://files.acemusic.ai/acemusic/win/ACE-Step-1.5.7z
# 或 start_gradio_ui.bat / start_api_server.bat

# 2) SFX 主力：Stable Audio 3 Small-SFX —— HF 仓库 3.49GB（gated）
git clone https://github.com/Stability-AI/stable-audio-3.git
cd stable-audio-3 ; uv sync --extra ui
uv run python run_gradio.py --model small-sfx
stable-audio --model small-sfx -p "cartoon capture ding, bright bell, playful" --duration 2 -o ding.wav

# 3)（备选）SA3 Medium 10.45GB：Windows 优先走 ComfyUI 原生工作流（免 FA2 折腾）
# 4) 母带：沿用现役链 ffmpeg（loudnorm -18LUFS / TP<=-3 / 44.1k mono / EQ）——零改动
```
**下载体积预估**：主选两件 ≈ **11–12GB**；+SA3 Medium ≈ +10.5GB；+SAO 1.0（可选）≈ +5GB；全装合计 ≈ **25GB 级**。权重源：HF（gated 同意后）+ ModelScope（ACE-Step 官方镜像）+ hf-mirror.com（国内加速）+ Comfy-Org 重打包（ComfyUI 用，通常免 gate）。

### 6.4 「同 prompt 对打」验收设计（14 号验收门前置）
1. **题库**：BGM 10 条 prompt（卡通治愈·器乐拟声·BPM 90–110·大调·60s 循环）+ SFX 10 条（捕获叮/胜利 jingle/嘟嘟嘟签名件等 0.5–8s）；**同文 prompt 喂云端与本地下游**。
2. **分组**：A=云端 Sonauto v2.2（fal_sonilo_music，90s 裁 60s）；B=本地 ACE-Step 1.5（60s 定长，seed×3）；SFX 位：A=Sonauto 裁剪件，B=SA3 Small-SFX + ACE-Step motif。
3. **统一母带**：两组输出全走同一 ffmpeg 规格链（-18 LUFS / TP≤-3 / 44.1k mono）——消除响度偏好作弊。
4. **盲评**：5 人评审（音频+策划）双盲 AB 五维打分：整体质感 / 编曲丰富度 / 拟人拟声贴合度 / **循环接缝**（首尾 2s 对接处）/ 外放可用性；另记录**可用率**（每 prompt 3 版中"≥1 版直接可进游戏"的比率）与单件耗时。
5. **通过线**：B 组可用率 ≥ A 组 80% 且无单维崩盘 → 本地链定型；**循环缝是本地预期优势项**（Sonauto 无循环设计，本地定长+repaint 补缝）。
6. **归档**：prompt/seed/模型版本/母带参数全记录进 14 号验收门档案；B 组落败则触发备选 SA3 Medium 按同协议递补再打。

## 7. 结论速览
1. **BGM 主选 ACE-Step 1.5**（MIT 权重、<4GB、10s–600s、自评 Suno v4.5–v5 水位）；备选 Stable Audio 3 Medium。
2. **SFX 主选 Stable Audio 3 Small-SFX**（社区许可合规、CPU 可跑、≤120s、SFX 专精）；备选 SAO Small 0.9 / SA3 Medium 通吃。
3. **判负名单**：MusicGen/AudioGen/JASCO（CC-BY-NC）、MMAudio（权重 CC-BY-NC，代码 MIT 是陷阱）、AudioLDM2/Tango2（CC-BY-NC-SA）、TangoFlux（研究专用）、YuE2（NC）。
4. Stability 社区许可=营收 <$1M 免费商用（我司当前符合），破线需 Enterprise——**挂账跟踪**；SA3 另需遵守 Gemma 组件条款。
5. 12GB 4070S 对推荐三件套全部宽裕；贴线项仅 SAO 1.0（chunked decode 解决）与 ACE-Step XL（最低线）。
6. Sonauto（已改名 Treblo）=闭源自研 Melodia，fal 端 v2.2 为 90s/次 CD 音质；模型量级未确证、无本地权重。
7. 质量差距客观估计：器乐 BGM 场景本地约为 Sonauto 80–100% 水位，**以 §6.4 对打实测定案**。
8. Windows 坑：SA3 Medium 的 FA2 依赖→走 ComfyUI 原生或社区轮子；HF gated 需 token+镜像；ACE-Step 有官方 Windows 便携包。
9. 预估下载 ~11–12GB（主选）/~25GB（全装）；母带链沿用现役 ffmpeg 规格，零改动。
10. 首战：装 ACE-Step 1.5 + SA3 Small-SFX → 跑 §6.4 对打协议 → 对比样本归档进 14 号验收门。

## 8. 来源清单
**许可原文**
1. Stability 官方许可页（FAQ 原文）：https://stability.ai/license
2. audiocraft README（代码 MIT/权重 CC-BY-NC 4.0）：https://github.com/facebookresearch/audiocraft
3. ACE-Step v1 README（Apache 2.0+8GB 优化+性能表）：https://github.com/ace-step/ACE-Step
4. ACE-Step 1.5 HF 卡（License: MIT+商用声明）：https://huggingface.co/ACE-Step/Ace-Step1.5
5. ACE-Step 1.5 XL turbo HF 卡（4B/GPU 档位表）：https://huggingface.co/ACE-Step/acestep-v15-xl-turbo
6. ACE-Step 1.5 GitHub（uv/便携包/档位表）：https://github.com/ACE-Step/ACE-Step-1.5 ；技术报告：https://arxiv.org/abs/2602.00744
7. DiffRhythm GitHub（Apache 2.0+8GB VRAM+Windows espeak）：https://github.com/ASLP-lab/DiffRhythm ；DiffRhythm2：https://github.com/ASLP-lab/DiffRhythm2
8. YuE GitHub：https://github.com/multimodal-art-projection/YuE ；YuE v1 权重卡（apache-2.0）：https://huggingface.co/m-a-p/YuE-s1-7B-anneal-en-icl ；YuE2 权重 NC 三方印证：https://www.opensourcealternatives.to/item/yue 、https://cpu3d.com/en/ainews/yue-vypusk-yue2-frontier-music-generation-with-symbolic-plan/ 、https://ai-tldr.dev/tools/yue/
9. AudioLDM2 卡（cc-by-nc-sa-4.0）：https://huggingface.co/cvssp/audioldm2 ；Tango2 卡（cc-by-nc-sa-4.0）：https://huggingface.co/declare-lab/tango2 ；TangoFlux LICENSE.md（research-only）：https://huggingface.co/declare-lab/TangoFlux
10. MMAudio README（代码 MIT/权重 CC-BY-NC/6GB/8s）：https://github.com/hkchengrex/MMAudio
11. SoundCTM 卡（code MIT/weights CC-BY 4.0）：https://huggingface.co/Sony/soundctm ；论文：https://arxiv.org/abs/2405.18503
12. HeartMuLa repo（LICENSE=Apache 2.0）：https://github.com/HeartMuLa/heartlib ；论文：https://arxiv.org/abs/2601.10547 ；SongGen：https://github.com/LiuZH-19/SongGen
**模型规格/显存**
13. Stable Audio 3 GitHub（型号表/性能表/FA2/安装）：https://github.com/Stability-AI/stable-audio-3
14. SA3 Medium HF（stable-audio-community+Gemma 条款+gated）：https://huggingface.co/stabilityai/stable-audio-3-medium ；SA3 Small-SFX HF：https://huggingface.co/stabilityai/stable-audio-3-small-sfx
15. SAO 1.0 HF（47s/44.1k/gated）：https://huggingface.co/stabilityai/stable-audio-open-1.0 ；diffusers Stable Audio 文档：https://huggingface.co/docs/diffusers/api/pipelines/stable_audio
16. SAO 1.0 VRAM 社区实测帖（3060 12GB/3080Ti 12GB/OOM traceback）：https://huggingface.co/stabilityai/stable-audio-open-1.0/discussions/3
17. SAO Small HF（341M/5.03GB 仓库）：https://huggingface.co/stabilityai/stable-audio-open-small ；官方限制转引（11s/无人声）：https://www.aimodels.fyi/models/huggingFace/stable-audio-open-small-stabilityai ；Arm 合作报道：https://dataglobalhub.org/resource/articles/stability-ai-and-arm-release-stable-audio-open
18. MusicGen 3.3B/VRAM 实测：https://nexgpu.net/en/models/audiocraft/ 、https://gigagpu.com/musicgen-large-dedicated-gpu/ 、https://huggingface.co/facebook/musicgen-large
19. YuE 硬件要求：https://github.com/tobert/yue-inference 、https://deepwiki.com/multimodal-art-projection/YuE/2.1-system-requirements-and-packaging 、GGUF：https://huggingface.co/QuantFactory/YuE-s1-7B-anneal-en-cot-GGUF 、yu8 INT8：https://github.com/w8floosh/yu8
**Sonauto/Treblo**
20. YC 公司页：https://www.ycombinator.com/companies/sonauto ；招聘页（Melodia 原文）：https://www.ycombinator.com/companies/sonauto/jobs/b34gnqK-ml-engineer-researcher ；Tracxn：https://tracxn.com/d/companies/sonauto/__ZmLMCncm5Aky6btFgVEk1J41ATt_SpShXpFo32tUrX8
21. fal 官方博客（Sonauto v2.2=90s/44.1kHz/$0.075/三端点）：https://blog.fal.ai/sonauto-now-available-on-fal/
22. Treblo 官网（改名）：https://treblo.com ；API 文档：https://treblo.com/developers/docs ；Melodia v3 免费报道：https://aimusic.events/news/treblo-melodia-v3-free-unlimited-classifier ；《Pausing Melodia V3》博客（据搜索摘要，原文未拉取）：https://blog.sonauto.ai/2026/04/01/pausing-melodia-v3/
**质量对比（第三方，单源采信需实测）**
23. ACE-Step 1.5 vs Suno（SongEval 8.09 称超 v5）：https://studio.aifilms.ai/blog/ace-step-1-5-music-generation-open-source 、https://ravlik.com/2026/06/07/ace-step-1-5-open-source-music-ai-that-runs-locally-and-matches-suno-v5-in-benchmarks 、https://www.promptspace.in/blog/ace-step-1-5-the-free-ai-music-generator-that-actually-beats-suno
24. Stable Audio 3 vs Suno 系评测（开源权重无人声/6min 器乐）：https://undetectr.com/blog/stable-audio-review 、https://blog.dubspot.com/stable-audio-3-vs-suno-2026 、https://stableaudio3.com/stable-audio-3-vs-suno
**工程生态**
25. stable-audio-tools LICENSE（MIT）：https://github.com/Stability-AI/stable-audio-tools/blob/main/LICENSE
26. ComfyUI：SA3 教程 https://docs.comfy.org/tutorials/audio/stable-audio/stable-audio-3 、day-0 公告 https://blog.comfy.org/p/stable-audio-3-day-0-support 、SAO 教程 https://docs.comfy.org/tutorials/audio/stable-audio/stable-audio-1 、https://comfy.org/p/supported-models/stable-audio-open-1-0/
27. Flash Attention 2 Windows 轮子：https://github.com/mjun0812/flash-attention-prebuild-wheels 、https://huggingface.co/ussoewwin/Flash-Attention-2_for_Windows 、https://github.com/sunsetcoder/flash-attention-windows
28. Stability Audio 研究页：https://stability.ai/research/stable-audio-open

---
*档案状态：已完成（2026-09-30）。所有许可结论均基于权重 LICENSE/模型卡/官方 FAQ 原文核对；标注「未确证」处请装机时二次复核。*

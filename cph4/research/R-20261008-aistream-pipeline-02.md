# R-20261008-aistream-pipeline-02 — AI 短剧/漫剧/MV 全流程·环节级最新本地大模型谱系切片（CEO 令 10-08·ledger P-2026-10-08-02）
> 溯源：ledger P-2026-10-08-02（CEO 原话「要最新的本地大模型」）·消费方=BigStream·判据预注册=三问（见任务）
> 验证声明：外部读取 22/22 预算封顶。成源 18 全 A 级（Ollama 官方页×2/GitHub 仓·组织页×15/HF 模型卡×1）；失败 4=MCP GitHub 搜索工具解析故障（与切片01 同症）；星数未提取 4=InstantID/PuLID/CosyVoice/LTX-Video；1 读窗 URL 重定向异常（⑤Hunyuan 行注）。锚件引用=R-20260930-video-models-01（⑤）/R-20260930-u326-local-audio-gen-01（⑦许可与显存）/R-20260928-cph4-model-matrix（机队）。三态=确认/推测/待证。

## 一、环节谱系矩阵（模型|显存地板=官方→量化社区档|许可|GitHub星|12/16GB档判定）
| 环节 | 最新模型/工具 | 显存地板（官方→量化/社区档） | 许可 | GitHub星 | 12/16GB档判定 |
|---|---|---|---|---|---|
| ①剧本 | Qwen3.5（Ollama 开源多模态族·256K·thinking/vision/tools·约1月前更新·A） | 0.8b=1.0GB/2b=2.7GB/latest≈6.6GB（9b 档 q4·推测）/35b-a3b-int4=20GB/122b-a10b=81GB（A·Ollama 官方页） | Apache 系（推测·待核） | Qwen3=27.7k（A） | 9b=12/16GB 主选确认；35b-a3b(MoE)=96GB RAM 混合确认；122b-a10b=81GB 纯 RAM offload 可行（推测） |
| ①剧本 | Qwen3.8=最新旗舰（27b·3.4M pulls·A）/Qwen3.6（27b/35b） | tag 体积待证 | 待证 | 待证 | bm-c 16GB 候选（待证）；DeepSeek-R1 蒸馏/GLM 系=thinking 已内建于 Qwen 系（Ollama 标签确认）→无独立装机必要 |
| ②分镜表 | LLM JSON 分镜 schema=qwen3.5 structured output 范式 | 0（文本层·随①模型） | 同① | - | 现役 qwen2.5 同栈（Ollama）零迁移平移 |
| ②一致性 | IP-Adapter（tencent-ailab）/StoryDiffusion（NeurIPS24·官方 low_vram 脚本·A） | SDXL 基座+轻量适配件（推测） | Apache-2.0×2（A） | 6.7k/6.5k（A） | 12GB 零训练角色一致✓；StoryDiffusion=漫剧多格一致对口件 |
| ②一致性 | PuLID（v1.1 SDXL+FLUX v0.9.1·ID 保真+5pp 官方 Model Zoo·A）/InstantID（官方 CPU offloading 省 VRAM·A） | SDXL/FLUX 基座档 | PuLID 待证；InstantID=代码 Apache/insightface 人脸模型非商用（A） | 均待证（提取未成源） | 16GB=PuLID-FLUX 档（cubiq ComfyUI 实现在案·A）；InstantID 商用红线判负 |
| ③提示词 | Omost（lllyasviel·LLM 代码能力→图像合成·A） | LLM(7b 级)+SDXL 同机 | Apache-2.0（A） | 7.6k（A） | 2024-06 后停更（commit 实证·A）→范式价值>工具；2026 现役主流=全流程仓内建 LLM→prompt 链（切片01：OpenMontage 65k★/Toonflow 16.6k★） |
| ④文生图 | Qwen-Image-2.1（「Qwen 最强开源图像生成」·26-09-30 更新·A） | 参数/VRAM 读窗未得=防线二抽验点（原版 Qwen-Image 系 ComfyUI 原生支持在案） | 待证 | 1.7k（A·组织页） | 最新档=bm-c 16GB 试点位；现实档=FLUX.1（26.0k★·代码 Apache·A·Kontext 编辑系 README 引证）GGUF+SDXL 现役（集团配方在案） |
| ⑤视频 | LTX-0.9.8-13B-distilled 主选维持（锚）/LTX-2=最新档（音视频同生·4K50fps·≤10s·官方「权重 2025 末开放」README·A；锚 09-30=HF 已存但 gated） | 13B offload 律在案（锚）；LTX-2 地板待证 | LTX Open Weights（锚） | 仓星未提取 | 维持主选；LTX-2=解 gate 后 A/B 升级候选（MV 音画同生价值点） |
| ⑤视频 | Wan2.2-TI2V-5B：官方地板 24GB 判弃（锚）→社区 GGUF 档=QuantStack 直转（Q2~Q8·月下载 22.07 万·city96 ComfyUI-GGUF 官方路径·A） | 官方 24GB（锚）→GGUF Q4 权重约 3-4GB 级（推测） | Apache-2.0（锚） | Wan2.1 仓=17.1k（A） | bm-c 16GB 重验候选（重访锚件判弃）；判负条件=OOM 或 >2min/5s 片 |
| ⑤视频 | HunyuanVideo-1.5（26-11-21 发布·专仓直读 A）：**8.3B**〔防线二纠错·原记 14B 系读窗污染〕+蒸馏 480P I2V 8-12 步+FP8+cache 推速+ComfyUI 官方指南/社区插件+训练/LoRA 全开源 | 官方=consumer-grade 档（「highly efficient·lightweight」）；**Wan2GP 社区地板=6GB VRAM**（官方仓引证 A）；原读窗「8GB VRAM+16GB RAM」由 6GB 地板覆盖 | 待证（Notice 文件在·未读） | 待证 | **bm-a 12GB 与 bm-c 16GB 均在可跑面内（A 级·防线二）**——短剧 I2V 主候选升级位 |
| ⑥配音 | CosyVoice3-0.5B-2512(_RL)=最新档（官方强烈推荐·中文 CER 0.81 居表首·A）/GPT-SoVITS 现实档（1 分钟数据克隆·A） | 0.5B 体量（A）→VRAM 约 1-2GB（推测）；GPT-SoVITS 约 4GB 级（推测·未读得） | GPT-SoVITS=MIT（A）；CosyVoice 待证 | GPT-SoVITS=62.5k（A）；CosyVoice 未提取 | bm-b 8GB 面可驻；官方对打表 2026 新档（A）：F5-TTS 0.3B/Index-TTS2 1.5B/VoxCPM 0.5B/GLM-TTS 1.5B 全开源 |
| ⑦BGM | ACE-Step v1.5（2026-01-28 发布·README·A；labbench 已在评测）+Stable Audio 3 Small-SFX 备选（锚） | v1.5 2B 系<4GB/XL 4B≥12GB 需 offload+INT8（锚·A） | 代码 Apache-2.0（A）+v1.5 权重 MIT（锚·HF 卡） | 4.9k（A） | bm-b 8GB 可跑（SA3 Small peak 2.4GB·锚）——U5「暂缓」卡点解除路径就绪 |
| ⑧剪辑增量 | auto-editor（静音剪/自动切·2,551 commits 活跃·A） | CPU 可跑（Python 工具） | Unlicense（A） | 5.4k（A） | FFmpeg 确定性链维持主轨（反重复律）；LLM 剪辑决策归流水线仓层（切片01）；判负=破坏回归链即退 |
| ⑨STT | faster-whisper（R169 QC 在役）/whisper.cpp/SenseVoice（全 parked） | - | - | - | 已覆盖·禁重研（任务令原文） |

## 二、机队适配判定（model-matrix 正典+本件新增）
- bm-a（4070S 12GB+96GB RAM）：①qwen3.5:9b(≈6.6GB)与 bge-m3 共驻=现役 7b 档升级位；重批 35b-a3b-int4(20GB) RAM 混合；⑦ACE-Step<4GB 可驻；⑤LTX offload 律在案（锚）
- bm-c（3070 魔改 16GB）：④T2I 主力（Qwen-Image-2.1 试点/FLUX GGUF/SDXL 现役）+②PuLID-FLUX；⑤Wan2.2-5B GGUF 与 LTX-2 重验台；ComfyUI 共卡让路律优先
- bm-b（3070 8GB）：⑥TTS 面（CosyVoice3-0.5B/GPT-SoVITS）+⑦SA3 Small（2.4GB·锚）；⑦主选 ACE-Step 1.5 需复用 u326 §6.4 对打协议验收后转正
- 全局：生成类算力默认路由本地（与集团 10-07「本地算力主供律」同向）；Ollama 常驻让路律沿用

## 三、接入建议（最新档+现实档双轨·判负条件）
1. ① 最新档=qwen3.5:9b→35b-a3b-int4（RAM 混合）；现实档=现役 qwen2.5:14b 维持至 A/B 过线；判负=剧本盲评低于现役即回退
2. ② 最新档=StoryDiffusion（漫剧多格）+PuLID-FLUX（bm-c）；现实档=IP-Adapter+SDXL 现役零训练；判负=同角色 10 镜一致抽验<8 达标
3. ③ 最新档=qwen3.5 JSON 分镜 schema+流水线仓 prompt 链自建；判负=结构化输出无效 schema 率>5%
4. ④ 最新档=Qwen-Image-2.1（参数/许可先防线二抽验）；现实档=FLUX GGUF/SDXL 现役；判负=单图>3min(bm-c)或中文文字渲染抽验不过
5. ⑤ 最新档=LTX-2（HF 账号解 gate 后 A/B）；现实档=LTX-0.9.8 主选维持+Wan2.2-5B GGUF 16GB 重验；判负=OOM 或 >2min/5s
6. ⑥ 最新档=CosyVoice3 多角色多情感；现实档=GPT-SoVITS 克隆位+Kokoro/piper 在役（bm-b·53 声纹池）；判负=中文盲评不及 edge-tts 现役
7. ⑦ 最新档=ACE-Step v1.5 对打转正（u326 §6.4 协议·labbench 接线中）；判负=可用率<80% 回「暂缓」留痕
8. ⑧ 增量=auto-editor 静音剪位试点（唯一确认增量件）；⑨已覆盖禁重研

## 四、结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| ①qwen2.5→qwen3.5:9b 换装 A/B 任务单 | 任务单@BigStream | 待发 |
| ④Qwen-Image-2.1 参数/许可防线二抽验+bm-c 试点 | 任务单 | 待发 |
| ⑤Wan2.2-5B GGUF 16GB 重验（重访锚件 24GB 判弃）+HunyuanVideo-1.5 归属抽验 | 任务单（重访触发器） | 待发 |
| ⑥CosyVoice3/GPT-SoVITS 多角色试点 vs edge-tts | 任务单 | 待发 |
| ⑦ACE-Step v1.5 对打转正（labbench 评测中·u326 协议复用） | 任务单 | 接线中 |
| ⑧auto-editor 增量试点 | 任务单 | 待发 |
| ②InstantID 商用红线（insightface 非商用许可） | 判负留痕 | 已判 |
| ⑨STT 已覆盖 | 判负留痕（维持） | 已判 |

- 更新记录：T0 骨架落盘 → T1 ①②③（12 读）→ T2 ④⑤（4 读）→ T3 ⑥⑦⑧（6 读）→ 终稿 52 行（node 字节级实测·无 BOM·22/22 预算封顶）。
- 防线二（主会话 10-08 三承重主张抽验·就地纠错一处）：①Qwen3.5 Ollama 官方页直读 ✓——0.8b/2b/4b/9b/27b/35b/122b 七档全在·9b=6.6GB/27b=17-20GB/35b=22GB/122b=81GB 与矩阵零偏差·256K·Text+Image 多模态·21.8M 下载·3 天前更新；许可未显式标注=维持待证（Qwen 系惯例 Apache·装机前核验）。②Qwen-Image 系=QwenLM/Qwen-Image 仓直读 ✓：2026-02-10 发布 Qwen-Image-2.0（排版/海报/漫画增强+更轻架构·漫剧对口）+2025-12-31 2512 版——**「2.1」细节维持待证**（组织页读窗·未独立核验）。③HunyuanVideo-1.5=Tencent-Hunyuan/HunyuanVideo-1.5 专仓直读 ✓ **纠错：8.3B 非 14B**（调研员读窗污染）——官方定位「lightweight·consumer-grade GPUs」+蒸馏 480P I2V 8-12 步（可 4 步）+FP8+cache 推速+4090 单卡 75s+ComfyUI 官方指南+社区插件自动下模型+**Wan2GP v9.62 官方引证「as low as 6 GB VRAM」**+训练代码/LoRA 全开源（Muon）；「8GB VRAM+16GB RAM」原读窗宣称由 6GB 社区地板覆盖·归属疑云解除。机队结论：bm-a 12GB/bm-c 16GB 均在 1.5 可跑面内（A 级）。

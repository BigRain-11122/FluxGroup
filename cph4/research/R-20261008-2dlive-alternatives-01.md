# R-20261008-2dlive-alternatives-01 — 2D LIVE 本地 I2V 模型升级位（CEO 令 P-2026-10-08-03·A 波）
> 溯源：ledger P-2026-10-08-03（CEO 原话「目前本地取帧做2D LIVE动画做的很糟糕，去考虑一下别的模型和方法，多方调研」）·消费方=CPH4 2dlive-spike+Biggame 吸嘟嘟·判据预注册=三问（①8-16GB 档本地 I2V 谁对 2D/Q版角色有逐帧身份稳定性实证（对打 LTX-0.9.5-2B）②各候选商用许可原文/显存地板/5s 速度/接入面/动漫特化 LoRA 证据 ③A/B 试点排序=装哪台机+每候选判负条件）
> 验证声明：实读 20/预算 20 封顶（锚 2+外部 18）·成源 A9（raw 直读×4：HV1.5 README/LICENSE、Wan2.2 README、WanGP README；GitHub api-meta×1；HF API×4）/C2（社区搜索×2）/M 若干（关键 4：QuantStack 5B-GGUF 量化档位清单沿锚、LTX-2.5 license:other 原文、Animate→Q版迁移、AniSora 帧率规格）·失败面 7：GitHub MCP 解析故障×3/github HTML 超时×1/api-meta 星数截断×1/QuantStack 5B-GGUF raw README 404（HF API 补位✓）/AniSora raw README 404（HF API 补位✓）/LTX gate 字段未读到/Animate Q版直接实证未获（8 源皆商用包装站）

## 一、候选谱系矩阵（模型|参数|许可|显存地板|速度|2D 身份稳定性证据|接入面|判）
| 模型 | 参数 | 许可 | 显存地板 | 5s 速度 | 2D 身份稳定性证据 | 接入面 | 判 |
|---|---|---|---|---|---|---|---|
| 基线 LTX-0.9.5-2B 蒸馏（在役） | 2B | 在役已清（锚） | 512px 档 | 8 步·cfg1.0 | 帧审实锚=漂移/假循环/涂抹/零微动作四症 | diffusers 现役 | 待替位 |
| **A 位** Wan2.2-Animate-14B（二代 Animate-2-14B 2026-07 已开 Distilled-Diffusers） | 14B | **Apache-2.0 双 A 源**（Wan2.2 README 许可段+HF 标签） | 官方未标；QuantStack GGUF 16.1 万下载在（HF·A）；Q4 权重约 8GB 级（14B 推测 M）→bm-a 12GB 紧+96GB RAM offload/bm-c 16GB 舒适（推测待实测） | diffusers 官方例 20 步·77 帧段·fps30；预处理链重（pose/face 提取+retarget+FLUX 依赖·官方 A） | 官方定位=角色图+驱动视频→整体动作表情复刻（A）=**身份由架构保**；商用面广（C×8）；Q版/无脸 face_video 迁移待证 | diffusers WanAnimatePipeline（A）+ComfyUI 集成官方 Todo✓（A） | 试点 |
| **B 位** HunyuanVideo-1.5 480p-I2V-step-distill | 8.3B | Tencent Hunyuan Community License 全文直读（A）；**领地=全球除 EU/UK/KR 且 Outputs 同限（§1l/§5c）** | 官方 14GB offload（A）→bm-c 16GB 面内；WanGP「as low as 6 GB」官方 README 引证（A） | 4090 端到端 75s（A·step-distill 8/12 步可 4 步）；4070S/3070 分钟级=推测待实测 | 无 2D 直接证据（通用域·待证）；train.py+LoRA 全开源（Muon·A）→吸嘟嘟 LoRA 自训=增效面 | ComfyUI 官方指南（仓内·A）+diffusers 官方+LightX2V+WanGP 全绿 | 试点（法务前置闸） |
| **C 位** Wan2.2-TI2V-5B GGUF | 5B | Apache-2.0 双 A 源；QuantStack（30 日 22.07 万下载）+unsloth（24.3 万）双供（HF API·A） | 官方 24GB（A）→GGUF Q4 权重约 3-4GB（锚推测 M）·8GB 档可行（社区惯例·M） | 官方 720p5s<9min@4090（A）；社区 5B-Turbo 蒸馏档在（存在性 A·提速待证） | 基模写实倾向强须 LoRA（Civitai 作者注·C）；动漫 LoRA 生态主要面向 A14B 专家（Civitai T2V/I2V 版+角色 LoRA 训练指南×2·C×3），5B 专属 LoRA 面较薄（推测 M） | ComfyUI-GGUF（bm-c 主产线零迁移）+官方 ComfyUI/diffusers 集成（A）；diffusers 无 TI2V 管线类（锚实测） | 试点 |
| AniSora v3.2（B 站·动漫特化） | 5B·CogVideoX 系架构（社区 diffusers 转换挂 CogVideoXImageToVideoPipeline·HF 标签 A） | Apache-2.0 标签（A）；主仓下载 7 vs 赞 229=疑 gated（推测） | 社区 V3.2-GGUF 在（1.1 万下载·A） | 待证 | 动漫域特化（存在性 A）；身份/2D 实证未获（待证） | diffusers 社区转换（A） | 留观（架构沿袭 CogVideoX-5B 判负先例：5GB 地板+8fps·锚） |
| LTX-2.5（LTX-2 线现役世代·22b） | 22b | license:other（HF 标签 A·原文未读 M） | 22b 超 12-16GB 舒适区（推测） | 待证 | 官方 IC-LoRA「Ingredients」标签含 character-consistency（A 标签级）；Alpha-Gen 透明帧 LoRA（A） | diffusers LTX2Pipeline+ComfyUI 标签（A） | 留痕暂缓（家族两连败先例：0.9.8 尾帧熔毁+1316.8s/0.9.5-2B 四症·锚） |
| MiniMax-H3 本地档 | 参数待证（M） | 待证（M） | WanGP MMGP v4 宣称 480p 5-6GB/1080p 11GB（WanGP README·A） | 待证 | 待证 | WanGP v17.17（2026-10-07 更新·A） | M 线索留观 |

## 二、深挖面（HunyuanVideo-1.5 许可/LoRA 生态/Wan2.2 GGUF 实况/LTX-2 gate 态/动漫特化新星）
- HV1.5 许可原文要点（raw LICENSE 全文直读·A）：§2 商用免版税非独占✓；§4 仅 >100M MAU 需另行申请（吸嘟嘟不触发）；**§1l+§5c 领地=全球除欧盟/英国/韩国，Outputs 亦不得域外使用/展示/分发**→Win64 上架发行面含 EU/UK/KR 即红线（法务定谳前置）；§3d 分发附 Notice 文本；§3e 对第三方服务须披露实际提供商+声明与腾讯无关联；§5b 禁以 Outputs 训他 AI 模型（sprite 入游戏不触）；§6d Tencent 不主张 Outputs 权利
- HV1.5 活性与纠错：仓 created 2025-11-20·pushed 2026-04-10（api.github.com·A）=装机级三验过（仓存在+LICENSE 原文+活性）；姊妹件「26-11-21 发布」实为 2025-11-21（LICENSE 落款·本件就地纠）；星数未提取（api-meta 截断·失败面）
- Wan2.2 GGUF 实况（HF API·A）：5B-GGUF QuantStack 30 日 22.07 万下载（与姊妹件数字交叉一致）+unsloth 2026-08 新供 24.3 万；5B-Turbo 蒸馏社区档（quanhaol 基·GGUF 2.1 万下载）=C 位提速杆；Animate-14B-GGUF 16.1 万下载；Animate-2 主仓下载 0（疑 gated·推测）但 Distilled-Diffusers 4419 可下；官方注「Animate 不建议混用 Wan2.2 训练 LoRA」→A 位增效走驱动视频域不走 LoRA 混装；A14B-I2V+Lightning 类步数蒸馏 LoRA=社区潜能位（M 未验，若 A/B/C 全败再启）
- LTX-2 gate 态（HF API·A）：09-30 锚「LTX-2-13B gated·API 401」世代已被 LTX-2.3（2026-03·106 万下载）/LTX-2.5（2026-07·167 万下载·22b）取代，百万级下载=可获取性已开（A 旁证）；gate 字段本次列表 API 未读到（M）；LTX-2.5 官方 IC-LoRA 生态 8+ 件（Alpha-Gen/Ingredients/SDR-HDR/Layout-To-Render）=家族已转 VFX 工具向，Q版身份主战场证据未获
- 动漫特化与 LoRA 生态：AniSora（B 站 IndexTeam·Apache 标签·arXiv 2412.10255/2504.10044）=CogVideoX 系→沿袭在案判负先例（5GB+8fps·锚）→留观；Wan2.2 侧社区已把「身份漂移」固化为已知病且有成熟 LoRA 训练解（GitHub DavidJBarnes/wan22-character-lora 指南 2026-06-27·runcomfy 漂移修复指南·Civitai 动漫 LoRA·C×3）
- 方法层三件（CEO 判据「模型+方法」双轨）：①首尾帧闭环杀假循环=OmniWeaving（Tencent 官方·HV1.5 底·Key-Frames-to-Video+Reference-to-Video·权重开放度待证）；②RMSE 双序列取帧律（锚复用：漂移帧过滤+最近似对收循环缝）；③Alpha-Gen（LTX-2.5 IC-LoRA·WanGP v17.17 内建同名工具·A）=视频→RGBA PNG 透明帧出口（sprite 底抠对口）

## 三、对打基线判定（vs LTX-0.9.5-2B·身份稳定性机理对照）
- 基线病灶机理：2B 容量+8 步蒸馏+cfg1.0（负词失效·锚）=逐帧去噪弱；仅单首帧软条件随时窗衰减、无逐帧身份锚；通用先验零 Q版域知识→漂移/假循环/涂抹/零微动作四症同源
- Animate-14B=机理换轨：角色母版图作显式输入（非首帧软条件）+pose/face 驱动视频显式供动作——身份靠架构、呼吸/眨眼可由驱动视频喂→对四症①②④结构性对口；14B+20 步对③（涂抹）改善=推测待证；代价=预处理链+驱动视频库建设
- HV1.5=容量+速度位：4× 基线参数+step-distill 75s 档保吞吐（速度面可打基线 8 步档），身份靠自训 LoRA 注域知识（增效面·非结构保证）
- 5B GGUF=同机理升级位：仍单首帧条件 I2V，胜在 5B 容量+720p@24fps 原生帧率+Apache 零法律风险+ComfyUI 主产线零迁移；身份增效面弱于 A14B（LoRA 生态面向 A14B·见 §二）；假循环仍需方法层闭环件兜底

## 四、A/B 试点排序（装在哪+判负条件·16 帧多模态帧审协议沿用基线实锚）
1. **A 位·bm-a（4070S 12GB+96GB RAM）：Wan2.2-Animate-14B GGUF Q4**（ComfyUI-GGUF；驱动视频三选=呼吸/挥手/眨眼；face_video 对无脸 Q版的弃用面待核；12GB OOM 则降 Q3 或转 bm-c）——判负：Q版母版迁移 16 帧帧审身份缺席/形变 ≥2 帧，或预处理+生成单条 >45min
2. **B 位·bm-c（3070 魔改 16GB）：HunyuanVideo-1.5 480p-I2V-step-distill**（ComfyUI 官方指南现成路径·16GB≥官方 14GB 地板）——判负：帧审 ≥2/16 或单条 >45min；**前置闸=领地条款（EU/UK/KR·Outputs 同限）法务定谳未过即不装（非技术判负·InstantID 商用红线同律）**
3. **C 位·bm-c 错峰（ComfyUI 主产线零迁移）：Wan2.2-TI2V-5B GGUF Q4/Q5+动漫 LoRA**——判负：帧审 ≥2/16 或单条 >45min 或 ComfyUI-GGUF 工作流跑不通；提速杆=5B-Turbo 蒸馏档（待证）
4. 排序依据=机理对口度（Animate 结构保身份>容量/LoRA 补）+许可风险序（Apache×2 零险>HV1.5 条件闸）+机队迁移成本（bm-c ComfyUI 原生）；B/C 同机错峰并行

## 五、结论应用表（落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| A/B/C 三试点任务单（Animate@bm-a·HV1.5@bm-c·5B-GGUF@bm-c 错峰）+16 帧帧审协议 | 任务单@CPH4 2dlive-spike+Biggame | 待发 |
| HV1.5 领地条款（EU/UK/KR 排除·Outputs 同限·§1l/§5c）呈法务定谳 | 决策呈报（法务） | 待呈 |
| Wan2.2 家族 Apache-2.0 双源确认+HV1.5 地板/速度/许可要点入册 | 法文修改（模型台账） | 待更 |
| AniSora 留观（CogVideoX 系沿袭判负先例）+LTX-2.5 暂缓（license:other 未读+家族两连败）+MiniMax-H3 留观（许可待证） | 判负留痕 | 已判 |
| 方法层三件套（OmniWeaving K2V 闭环/RMSE 取帧律/Alpha-Gen 透明出口）附于试点任务单 | 任务单（方法件） | 待发 |
| 姊妹件「5B-GGUF 16GB 重验+HV1.5 归属抽验」与本件 C/B 位结论交叉一致（22.07 万下载数字双向核对一致） | 判负留痕（重复调研豁免注记） | 已闭环 |

- 更新记录：T0 骨架落盘 → T1 锚复用（实读 2）→ T2 HV1.5/Wan2.2/WanGP 域（外部 10）→ T3 HF API×4+社区搜索×2+AniSora 补位（外部 8·预算 20 封顶）→ 终稿 48 行（node 字节级实测·无 BOM·帽 60 内）
- 防线二注记：①HV1.5 领地承重主张→raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo-1.5/main/LICENSE 直读复核（§1l Territory/§5c/§4 MAU）；②Wan2.2 家族 Apache 承重主张→Wan-Video/Wan2.2 README License 段（raw 直读）+HF API license:apache-2.0 标签（Wan-AI/Wan2.2-Animate-14B·QuantStack 两 GGUF 仓）双 A 源。重访触发器=Animate-2 权重全开/AniSora 出 24fps 档/LTX-2.5 license 原文落地/MiniMax-H3 许可澄清

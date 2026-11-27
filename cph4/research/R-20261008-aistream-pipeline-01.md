# R-20261008-aistream-pipeline-01 — AI 短剧/漫剧/MV 全流程·GitHub 高星项目切片（CEO 令 10-08·ledger P-2026-10-08-02）
> 溯源：ledger P-2026-10-08-02（CEO 原话「尤其去github找高评价的·本地大模型跑全流程」）·消费方=BigStream·判据预注册=三问（见任务）
> 验证声明：外部读取 20/20 封顶·成源 11·失败 9（MCP GitHub 工具解析故障×6·repo搜索OR语法422×2·get_file解析×1，失败均零数据）；源级：星/建日/push/许可=A（api.github.com 当场直读）·能力= B（raw README 原文直读）·口碑=C（DDG 摘要：知乎/头条/CSDN/独立教程站）；Top 候选 A/B+C 双源齐；未验项标「待证」。

## 一、发现清单（矩阵：项目|星|建日|最近push|许可|云依赖|覆盖环节|真实性判定）·A源 2026-10-08
| 项目 | 星 | 建日 | push | 许可 | 云依赖/本地可换位(B源) | 覆盖环节 | 真实性 |
|---|---|---|---|---|---|---|---|
| harry0703/MoneyPrinterTurbo | 129,149 | 24-03 | 26-10-07 | MIT | LLM=API 位（本地换位待证）；素材=Pexels 等免费库 | 主题→文案→素材→TTS→字幕→一键合成 | 确认·2.5年缓涨·2万fork·社区基准 |
| calesthio/OpenMontage | 65,067 | 26-03-29 | 26-10-03 | AGPL-3.0 | 零API键=Piper+免费素材=全本地✓；GPU本地视频=wan2.1-1.3b/14b·hunyuan1.5·ltx2·cogvideo✓；LLM=经AI coding assistant | agentic 12产线：脚本→资产→剪辑→Remotion/FFmpeg渲染+分镜审核门+费用追踪 | 确认·爆星经多站C源教程验证非假 |
| HBAI-Ltd/Toonflow-app | 16,617 | 26-01-29 | 26-10-05 | MIT | 「可配置第三方API，也可接入本地 ComfyUI 和 LLM」✓原文；TF-Router中转=可选云 | 无限画布+剧本/资产/分镜/视频+MCP+插件市场 | 确认·800+commits/21万行·C源口碑待证 |
| chatfire-AI/huobao-drama 火宝短剧 | 15,828 | 26-01-05 | 26-10-05 | CC BY-NC-SA 4.0 | 文本=OpenAI兼容可换Ollama✓；图像/视频=火山Seedance2.0/MiniMax H3/万相3.0=仅云端 | 一句话→剧本→角色→分镜→视频→FFmpeg合成·4 Mastra Agent | 确认真实（知乎/头条多帖·南京团队） |
| linyqh/NarratoAI | 11,308 | 24-08-12 | 26-09-17 | MIT | LLM=API 位（本地换位待证）；moviepy 合成 | 影视解说：LLM文案→长片素材对齐自动剪辑 | 确认·活跃 |
| dramaclaw/dramaclaw | 6,713 | 26-03-27 | 26-10-08 | Elastic-2.0 | 推理全走 OpenAI 兼容网关（自带newapi·不本机跑模型）；Ollama换位待证；推荐目录=Seedance2.5云 | 剧本→分集→分镜→首帧→配音→成片+无限画布+MCP Agent | 确认真实（CSDN/XLapTop/varoo）·当日push |
| ArcReel/ArcReel | 5,349 | 26-02-07 | 26-10-07 | AGPL-3.0 | Agent/文本/图像/视频/TTS=多供应商可配（Ollama/ComfyUI桥=待证）；剪映草稿导出=本地 | 小说/剧本→资产→分集剧本→分镜→视频→成片或剪映草稿·跨镜一致性·费用追踪 | 确认·活跃·文档完备 |
| hypit-ai/hypit | 20,049 | 26-07-29 | 26-10-04 | NOASSERTION | hypit.ai SaaS 导流 | 病毒视频克隆变体 | ⚠️2.5月2万星=假仓嫌疑·判负（三验因预算尽未做·重访触发器=CEO点名） |
- 排除：视频模型仓 CogVideo/LTX-Video/HunyuanVideo-1.5/Sana（切片02面）·Anil-matcha/Open-Generative-AI（muapi.ai云聚合营销仓）·Dujltqzv/Some-Many-Books（SEO垃圾）·BiliRoaming/AniCh（无关）
- 未单独验证·M级待证（预算尽）：ShortGPT（疑低维护）/StoryFlicks/FunClip（剪辑决策疑依赖云GPT）/auto-editor（静音剪疑与FFmpeg链重复）/VideoLingo（疑与whisper+TTS链重复）/StoryDiffusion（bm-c ComfyUI 一致性插件候选→移交图像线）

## 二、对照面（vs BigStream 既有产线 M0-M6：重复/增量判定）
- 反重复律命中段（装机=重复）：文案段（全候选=LLM API调用，M0 Ollama qwen2.5 已覆盖）·TTS段（OpenMontage 零键恰同款 Piper）·字幕段（faster-whisper 已覆盖）·合成段（全候选 FFmpeg/moviepy，既有确定性链 beats→plan→render 更强）→ MPT/NarratoAI 判负主因。
- 增量位（M0-M6 现缺口）：①小说→分集剧本改编 Agent 链 ②角色/场景/道具资产库+跨镜一致性参考图注入 ③分镜自动拆解→镜头提示词 ④可审核工作台（断点续跑/费用追踪/剪映草稿）⑤本地视频模型编排位（OpenMontage 已打通）。
- 图像线接点：候选图像生成全走 API 位；bm-c ComfyUI 接入待各项目「自定义供应商/OpenAI兼容」桥验证（列为试点判负条件）。
- 显存记录：编排层全轻量（DramaClaw 2vCPU/4GB 无GPU·其余 Docker 轻量）；生成层：OpenMontage 本地视频 wan2.1-1.3b 官方门槛≈8GB级→bm-c 16GB 应可跑（推测）/14b 需 offload 降速（16GB 边缘·推测）。

## 三、接入判定（试点候选+判负留痕·各带装在哪/判负条件）
- 试点#1 ArcReel：装 bm-a（Docker·编排不吃GPU）。接法：文本位→Ollama qwen2.5；图像位→bm-c ComfyUI 桥；成片→回灌 FFmpeg 链或剪映草稿人工精修。判负条件：供应商位接不进本地端点 或 AGPL 义务评审不过。
- 试点#2 Toonflow：装 bm-a（Docker/桌面端·内置FFmpeg·MIT）。接法：本地 ComfyUI+LLM 直配（README 显式支持）。判负条件：实测接不通，或画布交互拉低量产节拍（官方 demo 实录 2小时/2分钟成片·¥130）。
- 试点#3 OpenMontage：装 bm-a（编排+skills）+bm-c 加载 wan2.1-1.3b。接法：零键模式（Piper+免费素材）=全本地底线；LLM 位经 coding assistant（Ollama 兼容 CLI 驱动=待证）。判负条件：本地 assistant 跑不通 skill 链 或 1.3b 画质不达标。
- 前置验证 DramaClaw：bm-a Docker 可装（轻量）；前置验证=自带 newapi 网关能否配 Ollama/ComfyUI 上游（自述 model-neutral·待证）；能→升级试点，不能→违反全本地判负。Elastic-2.0 独立商用可（禁SaaS托管·需角标署名）。
- 判负留痕：MoneyPrinterTurbo（四段全与 M0-M6 重复；保留价值=129k★编排参考+prompt模板借鉴，不装机）·NarratoAI（重复+解说二创定位偏航）·火宝短剧（CC BY-NC-SA 4.0 非商业=商业红线+视频段仅云端；保留价值=4-Agent 分工架构参考）·hypit（假仓嫌疑+SaaS导流+许可不明）。

## 四、结论应用表（落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| ArcReel/Toonflow/OpenMontage 三试点任务单（含装在哪/接法/判负条件）+DramaClaw 网关本地化前置验证子项 | 任务单 | 待批 |
| StoryDiffusion→ComfyUI 图像一致性插件候选 | 任务单（移交图像线） | 待批 |
| MPT/NarratoAI/火宝/hypit 判负留痕 | 判负留痕 | 完成 |
| 本切片过目呈报（CEO 令「完成后给我过目方案」） | 决策呈报 | 待呈 |

- 更新记录：T0 骨架 → T1 发现清单（topic+漫剧/短剧扫描）→ T2 点名单查+README深读+社区口碑 → T3 Toonflow 定级 → 终稿 42 行
- 防线二（主会话 10-08 抽验·两承重主张全过）：①Toonflow「可接入本地 ComfyUI 和 LLM」=github.com 仓页 README 原文逐字直读 ✓（另证「本地部署·素材存自己设备」·短剧漫剧定位同证）；②火宝 CC BY-NC-SA 4.0 非商业红线=raw.githubusercontent LICENSE 原文直读 ✓（Attribution-NonCommercial-ShareAlike 4.0 标题实证）。api.github.com 403 配额尽按预案走仓页/raw 通道。

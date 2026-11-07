---
id: skills.catalog
title: 技能库目录
layer: skills
questions: ["有哪些技能", "做某事该载入哪个技能"]
facts: ["~/.codely-cli/skills", "cph4/skills"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
可调用技能 69 个（全局 32 / 集团 37），每个技能是一段可加载的操作规程。

## 技能清单
| 技能 | 作用域 | 一句话 |
|---|---|---|
| `agent-librarian` | global | 智能体库库长席（集团 Agent/Skill 总册管理）。Use when discovering which agent, expert, skill or seat handles a task, registering a new agent or skill into the library, auditing |
| `art-critique` | global | 逐帧/逐镜的审美批判席。用于成片、关键帧、界面、海报的审美审查：构图、光、色、材质、表演、叙事六个面各自打分并给出可执行的修改指令。当需要"看得更专业"而不是"看得更多"时使用。 |
| `asset-audit` | global | 集团资源规范审核技能（Unity/团结引擎资产：命名硬规则、切图尺寸、UI alpha 通道、导入设置 meta、同内容冗余→Atlas 候选；上游包豁免）。当需要对游戏项目 Assets 做资源审核、批量切图/生成资产入库把关、或发布前资产体检时使用。执行 Tools/asset-audit.ps1，把英文报告渲染成 |
| `bigstream-expert-panel` | global | BigStream 内容产线专家评审团机制（十三席两波评审+四闸流水+经验台账回灌）。进行 BigStream/MV/短视频/图像的创意生产、专家评审、关键帧生成、图生视频提示词撰写、剪辑装配、发布合规检查时使用。 |
| `compliance-guard` | global | 合规法务专家席（肖像版权/平台红线/AIGC 知识库·阶段门控——现役=轻量顾问模式不拦产线，商业化触发后转全检硬门·CEO 令 2026-10-16）。Use when touching celebrity likeness, copyright, trademark, memes or影射 boundaries,  |
| `content-recon` | global | 短剧/漫剧竞品拆解技能。当需要拆解爆款短剧、AI 漫剧、出海短剧的结构与工艺（钩子、集结构、反转节拍、镜头节奏、字幕规格、AI 痕迹），或要把竞品结论转成可执行配方卡时使用。触发词=短剧拆解/漫剧拆解/爆款拆解/拉片/钩子/付费点/对标。 |
| `cph4-research-dispatch` | global | CPH4 Labs 调研派工纪律 (P-65 research law execution). Use when dispatching background research waves (调研员/外部锚点波), writing R-YYYYMMDD research deliverables to cph4/res |
| `drama-director` | global | 专业漫剧/短剧总控导演席（连载剧审查+平台对标判据+双轨工艺）。Use when reviewing drama scripts, episode hooks, storyboards, KF panels, episode cuts, voice casting, or producing AI 漫剧/AI 短剧 f |
| `fleet-doctrine` | global | Model routing strategy for a multi-model AI fleet. Use when spawning sub-agents, choosing models for scheduled jobs, delegating coding tasks, or deciding which  |
| `fleet-ops` | global | 机队运维专家席。Use when any fleet or machine problem or operation: scheduled task issues, popup or black console windows, FleetLink/poke/sync failures, heartbeat stall |
| `game-asset-ship` | global | Produce and vet 2D mini-game assets and package builds for the Biggame line so they pass size, density and compliance gates before release. Use when asked to ma |
| `game-recon` | global | 小游戏竞品拆解技能。当需要扒爆款小游戏的包体结构、引擎、UI 规格、核心循环、数值与商业化点位，或把结论转成自家可执行规格时使用。触发词=小游戏拆解/扒包/反编译/包体分析/UI 对标/商业化拆解/榜单前10。 |
| `gate-rigor` | global | 造闸/立标准前的六问体检（标定依据、负控、能力边界、唯一判据、失效条件、验证记录）。Use when writing or revising any threshold, gate, QC checklist, quality spec or acceptance rule, when a gate is about  |
| `github-repo-ops` | global | > GitHub repository operations and analysis. Use when working with GitHub repos: analyzing code, checking issues, reviewing PRs, tracking stars/releases, search |
| `growth-ops` | global | 增长运营专家席（账号/粉丝/评论区/发布节奏/数据看板）。Use when planning account growth, fan engagement, comment-section operations, posting cadence and timing, follower conversion, priv |
| `llama-params-optimizer` | global | > Use when tuning llama.cpp or llama-server context length, batch size, GPU offload or KV cache on a fixed machine, or when a model runs partly on CPU. Complete |
| `llmxray-diagnose-ollama-calls` | global | Find out what went wrong with your own Ollama calls and fix it, using LLMxRay's local, read-only MCP tools. Use when a local model is slow, a prompt is rejected |
| `local-task` | global | 用本机常驻轻量模型做分类/摘要/打分/抽取，走统一题型与 JSON schema，带调用账与规则复核。当需要把一段文本归到固定类别、压成一句摘要、给产出打完成度、或抽出"谁等什么"关系时使用；不要自己临时拼 prompt。 |
| `memory-curator` | global | 记忆治理席（集团三层记忆体系的预算守门人）。Use whenever a session is about to write memory (append_memory/update_memory), receives any memory-bloat / slimming / audit / budget task, |
| `mv-casting` | global | MV 选角/面孔席技能（2000 年代脸谱 × AI 面孔双门）。Use when casting or auditing a female lead for period music videos — average AI faces, era makeup drift, cross-song face reuse, |
| `mv-colorist` | global | MV 调色席技能（2000 telecine 底 × ffmpeg 实参）。Use when building or auditing a grade chain — black lift vs curves, skin turning uniformly red, whole-frame blue cast at n |
| `mv-edit-rhythm` | global | MV 剪辑节奏席技能（KTV 时代语法：剪在词上、持在乐句里）。Use when cutting or auditing a music video edit — cut placement, shot-length by BPM bars, density curve, dissolve budget, same-s |
| `mv-intent-to-prompt` | global | 立意→关键词转译技能（把导演意图变成模型能执行的词面，并验证它真执行了）。Use when a script/idea is good but the generated frames don't match — writing generation prompts from design intent, auditi |
| `mv-lighting` | global | MV 摄影灯光席技能（2000 台式布光 × AI 可控光句）。Use when writing or auditing lighting in AI-generated video — night shots going cyan, "face has two lamps", indoor looking like  |
| `mv-performance` | global | MV 表演指导席技能（AI 演员表演：意图动作化/反应延迟/情绪弧/减法治）。Use when directing or reviewing character performance in AI-generated video — writing i2v performance prompts, diagnosing |
| `mv-props-era` | global | MV 道具/年代考据席技能（2000-2003 台湾物件谱 × 使用痕迹链）。Use when specifying or auditing props and set dressing for period music videos — brand-new-looking props, era anachronism |
| `mv-release-gate` | global | Run the four audience-level checks before any music video is delivered or published in the mv0001 line, and decide whether a cut is publishable. Use when asked  |
| `quant-backtest-gate` | global | Design, run and judge A-share and ETF backtests for the BigMoney line with correct return accounting and honest significance, and decide whether a strategy is r |
| `session-handoff` | global | 会话交接书（跨会话/跨机接续：在产、待判、阻塞、下一步、已试并失败的路、决策与理由）。Use when ending a session, when context is about to be compacted, when another agent or machine must continue the sam |
| `ship-ops` | global | 分发与上架席（C4 SHIP）。Use when publishing or submitting any output — platform declaration checkbox, AIGC dual marking, micro-drama filing (备案), WeChat mini-game submi |
| `silicon-city-ops` | global | 硅基城市生态运营席（城市非渲染面：居民生命/人口/安家/商业化/可视化）。Use when working on silicon-life canon, citizen census or population files, BigHouse 安家/邻里/共长 line, BigDomain 城市商业化, city d |
| `tw-mv-director` | global | 专业台湾音乐 MV 导演（导演审查+分镜工艺）。Use when reviewing MV scripts/storyboards, directing shot design, cutting rhythm, camera language, actor performance direction, or produ |
| `agent-librarian` | group | 智能体库库长席（集团 Agent/Skill 总册管理）。Use when discovering which agent, expert, skill or seat handles a task, registering a new agent or skill into the library, auditing |
| `art-critique` | group | 逐帧/逐镜的审美批判席。用于成片、关键帧、界面、海报的审美审查：构图、光、色、材质、表演、叙事六个面各自打分并给出可执行的修改指令。当需要"看得更专业"而不是"看得更多"时使用。 |
| `asset-audit` | group | 集团资源规范审核技能（Unity/团结引擎资产：命名硬规则、切图尺寸、UI alpha 通道、导入设置 meta、同内容冗余→Atlas 候选；上游包豁免）。当需要对游戏项目 Assets 做资源审核、批量切图/生成资产入库把关、或发布前资产体检时使用。执行 Tools/asset-audit.ps1，把英文报告渲染成 |
| `bigstream-expert-panel` | group | BigStream 内容产线专家评审团机制（十三席两波评审+四闸流水+经验台账回灌）。进行 BigStream/MV/短视频/图像的创意生产、专家评审、关键帧生成、图生视频提示词撰写、剪辑装配、发布合规检查时使用。 |
| `city-3d-assembly` | group | 硅基生命城市 3D 线·装配专家技能：Synty POLYGON 装配范式（乐高式模块拼装·官方 75 demo=老师）、四阶段定式（blockout→验证→dress→优化）、prefab variants 律、多场景 additive 三坑、构图密度（Phase 0 demo 实测收口）。当在 City3D 做街区 |
| `city-3d-lighting` | group | 硅基生命城市 3D 线·灯光专家技能：URP 日夜色轮（真实北京时间驱动·旋转+曲线+环境光三件套）、五色律 emission 窗灯改造（AD-022 自带 Emissive_01~05 贴图直供）、bloom 后处理（官方默认值与性能序）、渲染判例（雾距判例族/夜黑场三连乘/光池埋没/夜材质可逆换装）、烘焙策略（只烘 |
| `city-3d-procedural` | group | 硅基生命城市 3D 线·程序化专家技能：散布双轨制（自写最小 scatter 主径+PrefabScatterTool 手涂补笔）、16 方向掩码→AD-022 路面件映射选择器、建筑足迹校验（XZ 半径法+Y Raycast）、Y 排序不承袭律（URP Decal）、扩展期参数化街区填充（结构锚内）、WFC 不引入判 |
| `city-3d-terrain` | group | 硅基生命城市 3D 线·地编专家技能：地面系统（32m chunk 分块·禁 Terrain 基线确认+高程触发器 ±2m 判据）、水系方案（InteractiveStylizedWater·MIT）、地面细节定序（材质分区→路面件自带标线→decal）、大世界流送（additive 首期/Addressables 三 |
| `compliance-guard` | group | 合规法务专家席（肖像版权/平台红线/AIGC 知识库·阶段门控——现役=轻量顾问模式不拦产线，商业化触发后转全检硬门·CEO 令 2026-10-16）。Use when touching celebrity likeness, copyright, trademark, memes or影射 boundaries,  |
| `content-recon` | group | 短剧/漫剧竞品拆解技能。当需要拆解爆款短剧、AI 漫剧、出海短剧的结构与工艺（钩子、集结构、反转节拍、镜头节奏、字幕规格、AI 痕迹），或要把竞品结论转成可执行配方卡时使用。触发词=短剧拆解/漫剧拆解/爆款拆解/拉片/钩子/付费点/对标。 |
| `cost-ledger` | group | 成本与单位经济席。Use when computing what a deliverable actually cost, judging unit economics per episode/piece/order, auditing cloud credit spend, deciding whether a li |
| `cph4-research-dispatch` | group | CPH4 Labs 调研派工纪律 (P-65 research law execution). Use when dispatching background research waves (调研员/外部锚点波), writing R-YYYYMMDD research deliverables to cph4/res |
| `deal-desk` | group | 商务与定价席（C6 DEAL）。Use when pricing a product, writing a quote or one-page offer, deciding what to charge for a delivery, drafting OEM/channel materials, or judgin |
| `drama-director` | group | 专业漫剧/短剧总控导演席（连载剧审查+平台对标判据+双轨工艺）。Use when reviewing drama scripts, episode hooks, storyboards, KF panels, episode cuts, voice casting, or producing AI 漫剧/AI 短剧 f |
| `fleet-doctrine` | group | Model routing strategy for a multi-model AI fleet. Use when spawning sub-agents, choosing models for scheduled jobs, delegating coding tasks, or deciding which  |
| `fleet-ops` | group | 机队运维专家席。Use when any fleet or machine problem or operation: scheduled task issues, popup or black console windows, FleetLink/poke/sync failures, heartbeat stall |
| `game-recon` | group | 小游戏竞品拆解技能。当需要扒爆款小游戏的包体结构、引擎、UI 规格、核心循环、数值与商业化点位，或把结论转成自家可执行规格时使用。触发词=小游戏拆解/扒包/反编译/包体分析/UI 对标/商业化拆解/榜单前10。 |
| `gate-rigor` | group | 造闸/立标准前的六问体检（标定依据、负控、能力边界、唯一判据、失效条件、验证记录）。Use when writing or revising any threshold, gate, QC checklist, quality spec or acceptance rule, when a gate is about  |
| `github-repo-ops` | group | > GitHub repository operations and analysis. Use when working with GitHub repos: analyzing code, checking issues, reviewing PRs, tracking stars/releases, search |
| `growth-ops` | group | 增长运营专家席（账号/粉丝/评论区/发布节奏/数据看板）。Use when planning account growth, fan engagement, comment-section operations, posting cadence and timing, follower conversion, priv |
| `llama-params-optimizer` | group | > Use when tuning llama.cpp or llama-server context length, batch size, GPU offload or KV cache on a fixed machine, or when a model runs partly on CPU. Complete |
| `llmxray-diagnose-ollama-calls` | group | Find out what went wrong with your own Ollama calls and fix it, using LLMxRay's local, read-only MCP tools. Use when a local model is slow, a prompt is rejected |
| `local-task` | group | 用本机常驻轻量模型做分类/摘要/打分/抽取，走统一题型与 JSON schema，带调用账与规则复核。当需要把一段文本归到固定类别、压成一句摘要、给产出打完成度、或抽出"谁等什么"关系时使用；不要自己临时拼 prompt。 |
| `lowpoly-city-3d` | group | 硅基生命城市（FluxVerse/City3D）lowpoly 3D 美术线常备技能：48 包 Synty 库 AD 引用法、俯视角 3D 装配 SOP（数据驱动）、URP 定谳参数（CEO 令）、摄像机三档、地编与程序化判定律、L1 许可红线、库=唯一源律（3D 资源禁云端生成·CEO 令 09-29）、资产利用律（ |
| `memory-curator` | group | 记忆治理席（集团三层记忆体系的预算守门人）。Use whenever a session is about to write memory (append_memory/update_memory), receives any memory-bloat / slimming / audit / budget task, |
| `mv-casting` | group | MV 选角/面孔席技能（2000 年代脸谱 × AI 面孔双门）。Use when casting or auditing a female lead for period music videos — average AI faces, era makeup drift, cross-song face reuse, |
| `mv-colorist` | group | MV 调色席技能（2000 telecine 底 × ffmpeg 实参）。Use when building or auditing a grade chain — black lift vs curves, skin turning uniformly red, whole-frame blue cast at n |
| `mv-edit-rhythm` | group | MV 剪辑节奏席技能（KTV 时代语法：剪在词上、持在乐句里）。Use when cutting or auditing a music video edit — cut placement, shot-length by BPM bars, density curve, dissolve budget, same-s |
| `mv-intent-to-prompt` | group | 立意→关键词转译技能（把导演意图变成模型能执行的词面，并验证它真执行了）。Use when a script/idea is good but the generated frames don't match — writing generation prompts from design intent, auditi |
| `mv-lighting` | group | MV 摄影灯光席技能（2000 台式布光 × AI 可控光句）。Use when writing or auditing lighting in AI-generated video — night shots going cyan, "face has two lamps", indoor looking like  |
| `mv-performance` | group | MV 表演指导席技能（AI 演员表演：意图动作化/反应延迟/情绪弧/减法治）。Use when directing or reviewing character performance in AI-generated video — writing i2v performance prompts, diagnosing |
| `mv-props-era` | group | MV 道具/年代考据席技能（2000-2003 台湾物件谱 × 使用痕迹链）。Use when specifying or auditing props and set dressing for period music videos — brand-new-looking props, era anachronism |
| `quant-backtest-gate` | group | Design, run and judge A-share and ETF backtests for the BigMoney line with correct return accounting and honest significance, and decide whether a strategy is r |
| `session-handoff` | group | 会话交接书（跨会话/跨机接续：在产、待判、阻塞、下一步、已试并失败的路、决策与理由）。Use when ending a session, when context is about to be compacted, when another agent or machine must continue the sam |
| `ship-ops` | group | 分发与上架席（C4 SHIP）。Use when publishing or submitting any output — platform declaration checkbox, AIGC dual marking, micro-drama filing (备案), WeChat mini-game submi |
| `silicon-city-ops` | group | 硅基城市生态运营席（城市非渲染面：居民生命/人口/安家/商业化/可视化）。Use when working on silicon-life canon, citizen census or population files, BigHouse 安家/邻里/共长 line, BigDomain 城市商业化, city d |
| `tw-mv-director` | group | 专业台湾音乐 MV 导演（导演审查+分镜工艺）。Use when reviewing MV scripts/storyboards, directing shot design, cutting rhythm, camera language, actor performance direction, or produ |

## 怎么用
先按任务关键词选技能，再 `activate_skill` 载入其 SKILL.md；技能给的是流程与判据，不替代产物。

## 我不知道的
技能的实际生效版本以文件为准。

# 集团智能体库 AGENT-LIBRARY v1.0

> 建库令：CEO 2026-10-16「给我创立最齐全、最顶级、最优秀的 Agent 智能体库和专家 Skill 库和其他的。方便我所有的去调用，而且这个要不断的更新，要不断的细化，不断的细分角色……一定要给集团和城市搭建，给足够的赋能。」
> 本件=**全机队唯一智能体登记总册**（git 分发·CEO 审计面）。铁律：**不登记=不存在；登记必带调用面**。库长席=skill `agent-librarian`；治理法=同目录 `GOVERNANCE.md`（自增长三律+周审律+分发律）。
> 承接不重立：技能创建/分发/命名律=技能律 P-2026-09-26-01（cph4/README.md 技能面行）；能力/机制注册表=cph4/README.md；法典=cph4/registry/law-registry.md；十域知识=cph4/registry/knowledge-registry.md。本册只做「谁在岗·干什么·怎么调」的统一导航。

## §0 CEO 直达速查（我要干 X → 叫谁）

| CEO 说 | 自动激活/调用 |
|---|---|
| 出 MV / 改片 / 拉片 | 导演席 `tw-mv-director` → 群审 `bigstream-expert-panel`（成片呈审硬门=导演签字） |
| 短视频 / 玩梗 / 账号内容 | 短视频部管线（meme-daily-v1）→ 盲评 ≥9 才呈（合规席=轻量顾问不拦产线·CEO 令 2026-10-16·商业化触发转全检） |
| 涨粉 / 粉丝 / 评论区 / 发片时间 | 增长席 `growth-ops` |
| 城市搭建（装配/灯光/地形/散布） | `lowpoly-city-3d` 总控 → 四专家 city-3d-assembly / lighting / procedural / terrain |
| 城市居民 / 户籍 / 安家 / 可视化 | 城市生态席 `silicon-city-ops`（渲染面归上一行） |
| 游戏开发 / 关卡 / 数值 / 门禁 | CCGS 游戏专家套件（§三）+ 游戏域 skill 族 |
| 回测 / 量化 | W 波自滚引擎（bigmoney 仓）+ 量化六件套 skill（§三量化域） |
| 调研 / 查资料 | 调研员席 `cph4-research-dispatch`（派工纪律 P-65） |
| 发布前把关 / 侵权 / 平台红线 | 合规席 `compliance-guard` |
| 机队 / 机器 / 弹窗 / 派单 | 机队运维席 `fleet-ops` |
| 找专家 / 谁负责 X / 登记新专家 | 库长席 `agent-librarian`（本册） |

## §一 集团常设机构位（7×24 自转·无需点名）

| 机构位 | 职责一句话 | 正典位 | 节律 |
|---|---|---|---|
| CEO-PROXY 总调度代理席 | 替 CEO 发令+科学巡视 8 班/日+自迭代+大脑更新 | `cph4/fleet/dispatcher/CEO-PROXY/`（CHARTER/ROUND/DEADLINES/LOG） | 8 班/日 |
| 最高决策委员会（七席功能制） | T1 代决日常件+复盘四问+自迭代闭环 | `cph4/council.md` | 00:00/12:00 双班 |
| MASTER-AGENT 主脑蓝图 | 集团主脑统一架构正典（两波群审定版） | `cph4/fleet/dispatcher/MASTER-AGENT/BLUEPRINT.md` | 常设 |
| PATROL-FLEET 子公司巡视席舰队 | 十域巡视·30min 传感+域章程深挖+日 digest | `cph4/fleet/dispatcher/PATROL-FLEET/`（十域章程=CHARTERS） | PT30M+日班 |
| FleetDispatcher L0 | 确定性巡班：规则路由+饥饿/超时/失联探针（零 LLM） | `Tools/fleet-dispatcher.ps1` | PT30M |
| IdleWatch 机队防闲置哨 | 在线/监听/队列/心跳新鲜度探测+连 3 次复闲报警 | `Tools/fleet-idle-watch.ps1` | PT15M |
| 哨兵族（bm-b-Sentinel v3.0 等） | 各机自愈哨兵：ollama/心跳/队列静默/自驱工件池认领 | `C:\Fluxgroup\.codely-cli\sentinel\`（bm-b 侧） | PT5M |
| OS 循环班族（各司） | 各司 10min 自迭代：MiniGameEngineTick / Bigmoney-IterationLoop / BigStream-OSLoop / BigLife-OSLoop | 各司仓 mandate | PT10M |
| W 波回测自滚引擎 | 量化波链席位/冻结/自燃全链 | bigmoney 仓 fleet/ | 连续滚动 |
| 值守轮 / 夜轮 / 进化轮 | 四器审计+催办自愈 / 03:07 夜报 / 周日立法+法熵审视 | `cph4/night-round-prompt.txt` / `evolution.md` | 03:07/15:07 · 周日 |
| 交付哨 delivery-watch | 交付物落地守望+min_duration 质量闸+告警 | `cph4/fleet/dispatcher/delivery-watch/` | 常驻 |
| 审计部+哨兵 | 自我感动/同向无效功审计+独立抽审 | `cph4/audit-office.md`+`Tools/audit-sentinel.ps1` | 每日双班 |
| 记忆夜审门 | 记忆预算闸（>110KB/>140 条自动瘦身流程） | `Tools/memory-budget-gate.py` | 21:47 |
| CoderServe 看门狗 | bm-a 35B 常驻 :8090（PID 锁+路径闸） | `Tools/coder-serve.ps1` | PT10M |
| 热点扫描线 | 全网热榜三班扫描入池 | ShortVideoHotScan1/2/3（schtasks） | 日 3 班 |

## §二 任务态专家席位册（按需点名·审查件必留痕）

| 席位 | 触发任务 | 载体（skill/正典） |
|---|---|---|
| 导演席（MV 总控终审） | 一切 MV 剧本/分镜/成片审查定稿 | skill `tw-mv-director`（canon=cph4/skills/tw-mv-director/） |
| 十三席评审团（两波） | BigStream 内容创意生产全段评审 | skill `bigstream-expert-panel`（canon=cph4/skills/ 同批收编） |
| 红队席 | 大案攻击性评审（采购/架构类） | 先例=V100-EXPANSION-SPEC §10（cph4/fleet/hardware/） |
| 盲评席 | 成片闸盲评（≥9 才呈 CEO） | 各产线成片闸协议（meme/mv/drama LEDGER） |
| 调研员席 | R- 档调研派工（九司应用表强制） | skill `cph4-research-dispatch` |
| 游戏专家 11 席 | 游戏开发全链（设计/系统/经济/技术美术/性能/QA/审计/估时/范围/Unity×2） | skill 族=cph4/skills/ccgs/（INDEX.md 分拨面） |
| **库长席**（本批新增） | 智能体发现/登记/审计/周审 | skill `agent-librarian` |
| **机队运维席**（本批新增） | 机队一切故障与调度 | skill `fleet-ops` |
| **合规席**（本批新增·阶段门控） | 肖像版权/平台红线知识库（**现役=轻量顾问·商业化触发转全检**·CEO 令 2026-10-16） | skill `compliance-guard` |
| **增长席**（本批新增） | 账号/粉丝/评论区/节奏/看板 | skill `growth-ops` |
| **城市生态席**（本批新增） | 城市非渲染面（居民/安家/商业化/可视化） | skill `silicon-city-ops` |

| **子公司运营席**（2026-10-29 新立·bm-m 承载） | 七司条线判读/停摆归因/派单建议/升级（只判不代决） | canon=`cph4/fleet/subsidiary-coo/BLUEPRINT.md`·条线正身=`cph4/fleet/LINE-REGISTRY.json` |

## §三 Skill 总库索引（按域·含位置注记）

**级别律**：`canon`=cph4/skills/（git 分发·本册正源）；`项目级`=.codely-cli/skills/（本机安装副本·gitignored）；`用户级`=~\.codely-cli\skills\（bm-a 本机·跨机需移植 canon）。安装/更新一键=`Tools\agent-library-sync.ps1`（装后次会话生效）。

| 域 | skill 件 | 级别 |
|---|---|---|
| 游戏开发 | ccgs 11 件（game-designer/systems-designer/economy-designer/technical-artist/performance-analyst/qa-lead/asset-audit/estimate/scope-check/unity-specialist/unity-shader-specialist）+ create-game-assets · game-ai · game-ui-ux · level-design · procedural-gen · shader-programming · pixel-art-studio · algorithmic-art | canon+用户级 |
| 城市线 | lowpoly-city-3d（总控）· city-3d-assembly · city-3d-lighting · city-3d-procedural · city-3d-terrain · **silicon-city-ops**（新） | canon（本批收编 5+新 1） |
| 内容/媒体 | bigstream-expert-panel · tw-mv-director · capcut-edit · avoid-ai-writing · ai-writing-detector · voice-preserving-rewriter · canvas-design · theme-factory · doc-coauthoring · internal-comms | canon+项目+用户级 |
| **MV 条线席位（2026-10-20 新立）** | **mv-intent-to-prompt**（立意→关键词转译+执行契约卡）· **mv-performance**（AI 演员表演：意图/反应延迟/情绪弧）· **mv-lighting**（2000 台式布光五槽光句）· **mv-colorist**（telecine 底+ffmpeg 带位与暗角实测）· **mv-edit-rhythm**（剪在词上/持在乐句里+BPM 镜长+重吸附）· **mv-props-era**（2000 台湾物件谱+三痕链）· **mv-casting**（四锚点+反向测试+跨曲向量门） | canon（cph4/skills/）· 正身=各 skill 头部 research 指针 |
| 量化 | backtest-expert · position-sizer · drawdown-circuit-breaker · signal-postmortem · trade-hypothesis-ideator · data-quality-checker | 用户级（bm-a） |
| 机队/基建 | **fleet-ops**（新）· **agent-librarian**（新）· dispatching-parallel-agents · mcp-builder | canon+用户级 |
| 合规/增长 | **compliance-guard**（新）· **growth-ops**（新） | canon |
| 研究/质量 | cph4-research-dispatch · verification-before-completion · systematic-debugging · test-driven-development · webapp-testing | canon+用户级 |
| 办公/前端 | docx · pdf · pptx · xlsx · frontend-design · web-artifacts-builder | 用户级（bm-a） |

司级技能登记面=各司仓 README 技能行（技能律）；本册只收录集团层。外部开源池（素材源·非部署源）：awesomeskills.dev（1000+）/alirezarezvani/claude-skills（380·MIT）/CCGS 参照库 74 skill——采用一律过 oss-harvest 五门。

## §四 城市线专册（硅基生命城市·FluxVerse）

| 面 | 是什么 | 调用/正典 |
|---|---|---|
| 城市渲染四专家+总控 | 装配/灯光/程序化/地编（Synty 48 包·URP·日夜循环） | skill 族 §三城市线；正典族=gaming/FluxVerse/docs/lowpoly3d-*.md |
| 城市联合实验室 | 城市生命体征 12 条·三底座总装（规划大脑非施工队） | `cph4/city-lab.md` |
| 人口工厂（BigLife 唯一） | 万人户籍 census/基因库/进化引擎（他司禁重建） | life/BigLife/（独立仓）· skill `silicon-city-ops` |
| 安家线（BigHouse） | 安家/邻里/共长三柱·苏州吴中社区复刻判据（DDL 10-28） | house/BigHouse/BLUEPRINT.md |
| 城市商业化（BigDomain） | 引流/共创/19.9 算力包/代币内循环 | domain/BigDomain/BLUEPRINT.md |
| 城市数据面 | world-state.json 快照+world-events.jsonl 事件流（引擎只读轮询 10s） | gaming/FluxVerse/world/ |
| 可视化（CEO 第一检查面） | 硅基生命元宇宙.html+二级页面系统（三件套法） | gaming/MiniGame/tools/siliconwatch/（canonical+strings+generate） |
| 待登记席位（增长槽） | 城市运营席/城市内容席/城市数据席——canon 落地即建卡（细分律） | §七登记表 |

## §五 调用律（怎么调）

1. **skill 自动激活律**：任务语义命中 skill description=会话自动激活（描述触发词写清是建 skill 第一质量位）。
2. **子代理律**：task 工具派 explore/general-purpose/plan/unity-insight（复杂多步研究/隔离上下文用）。
3. **跨机派单律**：orders 行（@机名+lane+回执窗+验收物）→ poke tasks=[wake_tasks 白名单]（Tools/fleet-nodes.json）→ 回执落行。
4. **车道表**（resource-chain §9.1 正身）：bm-a=集团中枢+大内存+夜窗 GPU 备援（12G/94G）｜bm-b=声音+轻视频+回测 CPU（8G）｜bm-c=生成视觉-only GPU 主力（16G）｜bm-d=大脑机（3×V100 16G=48G 池+24C48T+256G·齐件待装·P104 已于 2026-10-21 判负未采）。
5. **CEO 直呼律**：CEO 说人话即可（§0 速查），库长席负责翻译成调用链；多窗重复令查重律照旧（orders 查重先查盘）。

## §六 登记表（append-only·机读行格式）

`| 日期 | 席位/机构 ID | 域 | 职责一句话 | 调用面(skill/canonical/宿主) | 状态 |`

| 日期 | 席位/机构 ID | 域 | 职责一句话 | 调用面 | 状态 |
|---|---|---|---|---|---|
| 2026-10-16 | agent-librarian | 机队/基建 | 库长：发现/登记/审计总册 | skill（canon=cph4/skills/agent-librarian） | ACTIVE |
| 2026-10-16 | fleet-ops | 机队/基建 | 机队运维：任务/静默/同步/车道/派单 | skill（canon=cph4/skills/fleet-ops） | ACTIVE |
| 2026-10-16 | compliance-guard | 合规/增长 | 合规知识库（阶段门控：现役轻量顾问·商业化触发转全检·CEO 令 2026-10-16） | skill（canon=cph4/skills/compliance-guard） | ACTIVE |
| 2026-10-16 | growth-ops | 合规/增长 | 增长运营：粉丝/评论区/节奏/看板 | skill（canon=cph4/skills/growth-ops） | ACTIVE |
| 2026-10-16 | silicon-city-ops | 城市线 | 城市生态：居民/安家/商业化/可视化 | skill（canon=cph4/skills/silicon-city-ops） | ACTIVE |
| 2026-10-16 | city-seat-ops / city-seat-content / city-seat-data | 城市线 | 城市运营/内容/数据席位（增长槽） | 待 canon 落地建卡 | PLAN |
| 2026-10-23 | content-recon | 内容/竞品 | 短剧/漫剧竞品拆解：钩子/集结构/节奏/字幕/AI痕迹→配方卡 | skill（canon=cph4/skills/content-recon） | ACTIVE |
| 2026-10-23 | game-recon | 游戏/竞品 | 小游戏拆解：包体/引擎/UI/循环/数值/商业化→规格表 | skill（canon=cph4/skills/game-recon） | ACTIVE |

| 2026-10-29 | subsidiary-coo | 子公司运营 | 席位本体：七司条线判读/归因/升级（bm-m 总控承载·不新建注册表与调度器） | canon=cph4/fleet/subsidiary-coo/BLUEPRINT.md | ACTIVE |
| 2026-10-29 | ops-bigmoney | 子公司运营 | 金融公司：数据/回测/审计闸三段判读 | canon=AGENTS.md §ops-bigmoney·条线=bigmoney | ACTIVE |
| 2026-10-29 | ops-bigstream | 子公司运营 | 媒体公司：MV/漫剧/短剧/短视频四线判读 | canon=AGENTS.md §ops-bigstream·条线=bigstream-* | ACTIVE |
| 2026-10-29 | ops-biggame | 子公司运营 | 游戏公司：玩法/美术/构建三段判读 | canon=AGENTS.md §ops-biggame·条线=biggame | ACTIVE |
| 2026-10-29 | ops-biglife | 子公司运营 | 数字生命：人设生产/体征闸 | canon=AGENTS.md §ops-biglife·条线=biglife | ACTIVE |
| 2026-10-29 | ops-bigdomain | 子公司运营 | 硅基域：引流/订单簿记 | canon=AGENTS.md §ops-bigdomain·条线=bigdomain | ACTIVE |
| 2026-10-29 | ops-bigcompute | 子公司运营 | 算力商业：成交环 | canon=AGENTS.md §ops-bigcompute·条线=bigcompute | ACTIVE |
| 2026-10-29 | ops-bighouse | 子公司运营 | 安家：安家/邻里共长 | canon=AGENTS.md §ops-bighouse·条线=bighouse | ACTIVE |
| 2026-10-29 | ops-fluxverse | 子公司运营 | 元宙城：装配/数据面/可视化 | canon=AGENTS.md §ops-fluxverse·条线=fluxverse | ACTIVE |

## 更新日志

- v1.0（2026-10-16·bm-a 建库）：总册首版（常设机构位 15+专家席位 16+八域 skill 索引+城市线专册）+五席新 skill+六件既有 skill 收编 canon+同步/审计双工具+CEO-PROXY 周审步接线（执行档=docs/orders.md 2026-10-16 建库令行）。
- v1.0.1（2026-10-16·bm-a）：合规席转阶段门控（CEO 令「商业化前轻量」）——§0/§二/§六 合规行改写·skill 同步升版。

## 审美能力包 v1（2026-10-25 委员会令：全集团审美水平大幅提升）

**已有席位（盘清·全部可调用）**：视觉定义 `art-bible`／单件规格 `asset-spec`／画面构成 `canvas-design`／主题配色 `theme-factory`／设计审查 `design-review`／设计系统 `design-system`／交互与视觉 `ux-design`+`ux-review`／游戏界面 `game-ui-ux`／游戏美术 `create-game-assets`／关卡 `level-design`／像素 `pixel-art-studio`／MV 导演 `tw-mv-director`／专家群 `bigstream-expert-panel`／MV 色彩 `mv-colorist`／MV 灯光 `mv-lighting`／MV 表演 `mv-performance`／MV 年代道具 `mv-props-era`／MV 选角 `mv-casting`／MV 剪辑节奏 `mv-edit-rhythm`／短剧导演 `drama-director`／技术美术 `technical-artist`／着色器 `unity-shader-specialist`。

**新增（本次落地）**：
- `cph4/skills/art-critique/SKILL.md` — 审美批判席：构图/光/色/材质/表演/叙事六面打分 + 可执行修改指令。用于"机器全绿但人一眼看出问题"。
- `Tools/mv_aesthetic_gate.py` — 把审美变成数字：逐镜 luma/sat/edge/色温/同色连段；判 DARK(<35/255)、BLOWN(>190)、FLAT(edge<0.02)、同色连段≥6。

**执法位**：任何成片/关键帧/界面交付前，除技术闸外必须跑 `mv_aesthetic_gate` 并附 art-critique 六面表；两者任一判负不得交付。

**首跑实测（mv0001 v715）**：dark=43 / flat=39 / 最长同色连段=6；整体 gamma 1.15 提亮后 dark=29 / flat=31。结论=全片偏暗是"看不懂"的主因，须在装配级做一次整体提亮，而非逐镜补。
- v1.0.7（2026-10-29·bm-b 交互窗）：子公司运营席 subsidiary-coo + 八条线子代理（ops-bigmoney/bigstream/biggame/biglife/bigdomain/bigcompute/bighouse/fluxverse）登记（CEO 令 2026-10-29「让他好好去管理一下金融公司等子公司，自己管不过来就去造agent，专门负责子公司的生产运转」——承载机=bm-m（已是总控·MASTER-NODE.json）·条线正身=LINE-REGISTRY·执行面=master_agent 规则 R-SUBCO-20261029-001~003）。

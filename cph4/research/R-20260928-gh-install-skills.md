# R-20260928-gh-install-skills：GitHub AI skills 普查（P-2026-09-28-15 调研面）

> 状态：**调研完成**（早落盘律：骨架先写盘，边查边更新，本件为最终成品）
> 调研员：CPH4 实验室 | 日期：2026-09-28 | 纪律：**只调研，绝不安装任何东西**（本调研全程零安装零 clone）
> 验证律：许可与元数据一律 web_fetch 抓 api.github.com/repos/<org>/<repo> 直验；本轮后期 api.github.com 403 限流（无鉴权 60/h 共享池耗尽），按换源律改用 raw.githubusercontent.com 双源补验并如实标注「API 待补验」；被带偏/404≠源不存在——motion-skills 与 capcut-cli 在 main 分支 404、master 分支命中即换源律实证。
> 格式基线：全部主候选均为 Anthropic Agent Skills 开源标准 SKILL.md 形态（YAML frontmatter name+description + 正文命令式）——与 Codely 技能格式**同构兼容**。

## 一 结论应用表（结论|应用面|归属司/机|落地动作）

| 结论 | 应用面 | 归属司/机 | 落地动作 |
|---|---|---|---|
| 游戏线技能底座=gamedev-skills/awesome-gamedev-agent-skills（74 技能+router，Apache-2.0，Unity 6.3 LTS 组 8 件+2D Tilemap+create-game-assets 资产管线） | Tuanjie/Unity 游戏开发（2D/俯视城市） | Biggame/MiniGame/FluxVerse 开发机 | 司仓收编 skills/unity 组+disciplines 相关件→git 分发→各机拷入 .codely-cli/skills/；Tuanjie 与 Unity API 同源、版本号需对表团结引擎版 |
| 像素美术确定性引擎=pixel-art-studio（MIT，Pillow 逐像素+pixelpipe AI 图清洗/调色板锁定） | 像素美术/2D 生产 | MiniGame pixelforge 产线（C 机 16GB 量产面） | 拷贝入司仓；部署时 pip install pillow；pixelpipe 与集团 SDXL 产线（R-20260926-sdxl-city-production）后处理链直接互补 |
| 量化研究技能组=tradermonty/claude-trading-skills 之 Strategy Research+Trade Memory 组（backtest-expert、trade-hypothesis-ideator、edge-* 家族、dual-axis-skill-reviewer、data-quality-checker） | 量化回测（Python） | BigMoney | 司仓收编选中件（非整仓 60+ 全装）；走 no-API/free 路径（FMP free tier），**禁 FINVIZ Elite 付费路径**；美股为主，A股适配需自研注记 |
| 文案质检门=avoid-ai-writing（MIT，49+ AI 腔模式类别+确定性检测引擎+0-100 评分） | AI 媒体内容生产文案/数字居民台词出稿 | BigStream / BigLife 认知层 | 拷贝单件，纳为出稿强制质检门（detect/rewrite 两模式） |
| 视频线=capcut-cli 之 capcut-edit 技能（MIT，剪映/CapCut 草稿 JSON 直改、CJK 字幕规则、双语触发） | AI 媒体内容生产视频 | BigStream 视频机 | `npx skills add renezander030/capcut-cli` 或拷技能件；运行时 npm i -g capcut-cli@latest（**≥0.18.0 安全修复版**，旧版有注入漏洞在案） |
| 动效/数据动画=motion-skills 16 包 53 件（MIT，deliver-and-verify 自检环） | AI 媒体内容生产动效/商业化素材 | BigStream | 按需挑包：ad-video（引流素材）、data-animation（数据图表动画）、explainer、motion-design；运行时需 Remotion/Manim/ffmpeg |
| 调研纪律三件套=superpowers:verification-before-completion + ai-research-skills 反幻觉 schema + scientific-agent-skills 研究方法论组 | 调研纪律/CPH4 研究线 | HQ/CPH4（集团级=三层研究边界律之集团层面） | superpowers 单件即装（MIT 已 API 验明）；WenyuChiou/K-Dense 两库 raw 已验 MIT、**API 元数据待限流窗补验后**先小规模试点（数据分析/统计/科学写作/市场研究报告子集） |
| 工程方法论=superpowers 四件（TDD、systematic-debugging、dispatching-parallel-agents、writing-plans/executing-plans） | 全集团开发流程/机队派工 | HQ 全机队 | MIT 拷贝分发；dispatching-parallel-agents 与机队协议（cph4/fleet-protocol.md）方法论互补 |
| QA 冒烟=anthropics/skills:webapp-testing（Playwright 驱动 web 测试+截图取证） | QA 冒烟测试（webgl demo 真跑+截图既有流程） | QA 机 | 拷贝 skills/webapp-testing/ 单件；部署时装 Playwright（本调研不装） |
| MCP 自建=mcp-builder（教 AI 生成自定义 MCP server） | CEO 令「找 mcp 等」之集团自建 MCP 面 | BigCompute/工具线 | 拷贝单件（README 声明 Apache-2.0 组）；生成的 server 代码走集团 code review |
| 文档生成=anthropics/skills:docx/pptx/xlsx/pdf 四件 | HQ 呈报/规格件/商业化价目表 | HQ | 拷贝单件；**source-available 非 OSI 条款**→入 L1 参考层注记（内用 OK、禁再分发） |
| PS5.1 面=**无对口开源技能**（最强 powershell-expert 为 PS7+ 向，不对症集团 PS5.1 编码/语法坑律） | PowerShell 5.1 自动化 | HQ 自动化（PS+计划任务） | 采「集团自产坑律继续主导」+列 PS5.1 专项技能为**自研待办**（用 Codely 内置 skill-creator 造） |

## 二 采用候选逐件（技能名|源repo|api 直验|许可|契合一句话|安装法|五门初判）

> 五门=契合/反重复/许可/健康/成本安全。安装法默认含集团技能律包装：源入司仓 tools/skills/<name>/SKILL.md 随 git 分发，安装副本 gitignored。

### 2.1 源=anthropics/skills（官方库 19 件全清点，API 直验 ✓：★178727·pushed 2026-09-24·license 字段=null·根目录无 LICENSE 文件）

| 技能名 | 源repo | api直验 | 许可 | 契合一句话 | 安装法 | 五门初判 |
|---|---|---|---|---|---|---|
| webapp-testing | anthropics/skills | ✓repo级（search API） | Apache-2.0（README 声明；技能级 LICENSE 文件 raw 直验=404 不存在，以 README 为准） | Playwright 驱动 web 应用自动化测试+截图——直配 QA webgl demo 真跑+截图流程 | 拷贝 skills/webapp-testing/ 入司仓 | 契合✓高（QA线）；反重复✓（Codely 无内置 web 测试）；许可✓；健康✓（★178k·09-24 活跃）；成本安全=需 Playwright 运行时（部署面） |
| mcp-builder | anthropics/skills | ✓ | 同上 | 生成自定义 MCP server——集团自建 MCP 工具面正典 | 拷贝 skills/mcp-builder/ | 契合✓高（算力商业化/工具线）；反重复✓；许可✓；健康✓；成本安全✓（产物走 code review） |
| docx/pptx/xlsx/pdf（四件） | anthropics/skills | ✓ | **source-available 非 OSI**（README 原话「source-available, not open source」·Anthropic 自定义条款） | Office/PDF 文档生成与编辑（Claude 文档能力同源生产级实现） | 拷贝单件 | 契合✓高（HQ 呈报/价目表）；反重复✓（Codely 无内置文档生成）；许可=**条件过**（内用参考 OK·禁再分发·L1 注记）；健康✓（生产级）；成本安全=需 python-docx/openpyxl 等运行时 |
| canvas-design | anthropics/skills | ✓ | Apache-2.0（README 组） | 设计画布排版系统——2D/UI 视觉设计辅助 | 拷贝 skills/canvas-design/ | 契合=中（像素/游戏 UI 方法论参考）；反重复✓；许可✓；健康✓；成本安全✓ |
| algorithmic-art | anthropics/skills | ✓ | 同上 | 代码化生成艺术——程序化美术思路源 | 拷贝 | 契合=中（内容生产）；反重复=部分（与 pixel-art-studio 能力相邻但不重复）；许可✓；健康✓；成本安全✓ |
| frontend-design | anthropics/skills | ✓ | 同上 | 前端视觉设计规范——BigDomain 店面/落地页 | 拷贝 | 契合=中（BigDomain 引流页）；反重复✓；许可✓；健康✓；成本安全✓ |
| brand-guidelines/internal-comms/doc-coauthoring/theme-factory/web-artifacts-builder | anthropics/skills | ✓ | 同上 | 企业品牌/内部沟通/共笔/主题/网页构件 | 拷贝 | 契合=低-中；**待 CEO 按需挑选，非首批** |

### 2.2 源=obra/superpowers（MIT，15 件全清点，API 直验 ✓：★292321·pushed 2026-09-27·根 LICENSE 文件在）

| 技能名 | api直验 | 许可 | 契合一句话 | 安装法 | 五门初判 |
|---|---|---|---|---|---|
| verification-before-completion | ✓ | MIT | 完工前强制验证纪律——与集团「防线二直读复核/验收判据」同构 | 拷贝 skills/verification-before-completion/ | 契合✓高（全集团工程文化）；反重复✓（Codely 无内置验收纪律件）；许可✓；健康✓；成本安全✓ |
| test-driven-development | ✓ | MIT | TDD 红绿重构律——量化回测与游戏线质量基线 | 拷贝 | 契合✓高（BigMoney+游戏线）；反重复✓；许可✓；健康✓；成本安全✓ |
| systematic-debugging | ✓ | MIT | 四相位系统化调试（根因隔离/最小复现）——机队排障方法论 | 拷贝 | 契合✓高（全机队含 PS5.1 排障）；反重复✓；许可✓；健康✓；成本安全✓ |
| dispatching-parallel-agents | ✓ | MIT | 并行子代理派工律——与机队多窗并发/跨司派工协议互补 | 拷贝 | 契合✓高（fleet 面）；反重复=部分（Codely 有内置 Task 工具，此件是方法论层）；许可✓；健康✓；成本安全✓ |
| writing-plans / executing-plans | ✓ | MIT | 计划编写与执行律——HQ P 号计划件工艺参照 | 拷贝 | 契合=中；反重复=部分（Codely 有 enter_plan_mode，此件是方法论补充）；许可✓；健康✓；成本安全✓ |
| brainstorming / using-git-worktrees / requesting-code-review / receiving-code-review / subagent-driven-development | ✓ | MIT | 头脑风暴/git 并行工作树/代码评审双边律 | 拷贝 | 契合=中（worktrees 正中多窗并发）；反重复✓；许可✓；健康✓；成本安全✓ |

### 2.3 业务线专项（GitHub search API 直验 ✓）

| 技能名 | 源repo | api直验 | 许可 | 契合一句话 | 安装法 | 五门初判 |
|---|---|---|---|---|---|---|
| 74 件游戏技能+router（Unity 8 件：unity-csharp-scripting/unity-tilemap-2d/unity-input-system/unity-physics/unity-animation/unity-scriptableobjects/unity-navmesh/unity-build-pipeline；disciplines 15 件：create-game-assets/procedural-gen/game-ai/save-systems/game-ui-ux/camera-systems 等；genres 9 件：platformer/roguelike/rpg/visual-novel 等） | gamedev-skills/awesome-gamedev-agent-skills | ✓（★1207·pushed 09-27·Apache-2.0·根 LICENSE+NOTICE 文件 API listing 实证在·skills/ 目录实证在） | Apache-2.0（API license 字段+LICENSE 文件双验） | 跨引擎游戏开发技能+引擎自动侦测 router，版本钉扎（Unity 6.3 LTS）从一手文档写就+validator 校验——游戏线技能底座 | `codely skills install <git仓库>`（整仓）或司仓收编 skills/<引擎>/<name>/ 单件拷贝 | 契合✓高（**unity-tilemap-2d 正中俯视城市 2D 面·create-game-assets 正中资产管线**）；反重复✓（Codely 无游戏技能；与 tuanjie-cli 内置技能互补不撞——tuanjie-cli 是引擎安装/项目管理面）；许可✓；健康✓；成本安全✓（纯 SKILL.md 无重运行时） |
| pixel-art-studio（pixelstudio/study/pixelpipe 脚本+LPC 角色表契约+风格学习卡） | Gamezxz/pixel-art-studio | ✓（★58·pushed 2026-07-11·MIT） | MIT（API+README 双验） | LLM 即像素艺术家：逐像素确定性绘制+AI 生成图清洗锁调色板+动画导出（PNG/GIF/spritesheet/Aseprite JSON）——与集团 SDXL 产线后处理链同构互补 | 拷贝技能件；部署时 pip3 install pillow | 契合✓极高（像素美术线本命）；反重复✓（Codely 图像工具是生成面，此件是像素级确定性编辑/清洗面）；许可✓；健康=过（★小但专精对口）；成本安全✓（纯本地 CPU） |
| Strategy Research+Trade Memory 组（backtest-expert、trade-hypothesis-ideator、edge-candidate-agent/edge-strategy-reviewer/edge-pipeline-orchestrator、strategy-pivot-designer、residual-edge-analyzer、trader-memory-core、signal-postmortem；meta 件 dual-axis-skill-reviewer、data-quality-checker） | tradermonty/claude-trading-skills | ✓（★2900·pushed 2026-09-28·MIT） | MIT（API+README 双验） | 60+ 交易技能库中与量化研究线对口的假说→回测→复盘闭环+技能质量双轴评审器 | 司仓收编选中件（skills/<name>/ 各含 SKILL.md）拷贝 | 契合✓高（回测方法论+复盘文化正对 BigMoney）；反重复=部分（美股市场向，A股数据面需自研适配）；许可✓；健康✓（★2900·当日活跃）；成本安全=**有条件**（FMP free tier/no-API 件 OK；FINVIZ Elite 付费件**禁采**） |
| avoid-ai-writing | conorbronsdon/avoid-ai-writing | ✓（★4748·pushed 09-27·MIT） | MIT | 49+ AI 腔模式审计+重写+确定性评分引擎（0-100）——出稿质检门 | 拷贝单件（零依赖） | 契合✓高（BigStream 文案/数字居民台词质检）；反重复✓（Codely 无内置文风质检）；许可✓；健康✓（领域内星数第一）；成本安全✓（纯本地） |
| capcut-edit（技能件）+capcut-cli（npm CLI 运行时） | renezander030/capcut-cli | **API 待补验**（403 限流）；raw master 直验 ✓ 存在+MIT | MIT（README License 节原话「MIT」+npm badge） | 剪映/CapCut 草稿库 JSON 直改（无上传无服务器），中文请求可触发（剪映/字幕/草稿），CJK 字幕宽度规则（zh 16）——**中国区视频剪辑标准工具的 agent 化** | `npx skills add renezander030/capcut-cli` 或拷技能件；运行时 npm i -g capcut-cli@latest | 契合✓高（BigStream 视频线+中文市场原生）；反重复=部分（Codely 内置 generate_video 是生成面，此件是剪辑工程面，互补）；许可=raw 已验/API 待补；健康=过（CI 三平台+205 测试在案）；成本安全=**有条件**（须 ≥0.18.0——旧版本地注入/临时文件漏洞在案已修；需 Node≥18） |
| motion-skills 16 包（ad-video 3 件/data-animation 3 件/explainer 5 件/motion-design 9 件等共 53 件） | iart-ai/motion-skills（各包独立 repo） | **API 待补验**；raw master ✓（main 404→master 命中，换源律实证） | MIT（README 原话「MIT — use them freely」） | 动图/动画/视频技能包，每件带 deliver-and-verify 自检环（渲染帧→截图→检查）——商业化素材生产 | `npx skills add iart-ai/<pack>` 或拷贝包内技能件 | 契合✓高（BigStream 动效+数据动画）；反重复=部分（与 Codely 生成工具互补：此件教 agent 专业动效工艺）；许可=raw 已验/API 待补；健康=过（iart.ai 公司维护）；成本安全=有条件（Remotion/Manim/ffmpeg 运行时） |
| Unity 编辑器自动化技能集（Cinemachine 34/Netcode 39/UI 29/UI Toolkit 31/ShaderGraph 23/ProBuilder 22/Perception 18/Validation 16 等工具面） | Besty0728/Unity-Skills | ✓（★1789·pushed 2026-09-28·MIT·C#） | MIT | Unity 编辑器内自动化操作（资产导入/预制体/材质/场景感知/项目校验）——编辑器代理 | **安装形态特殊**：主体=Unity 包导入（非纯 SKILL.md 拷贝）+CLI 接线；技能件部分可拷 | 契合✓高（Unity 线编辑器自动化）；反重复=部分（与 tuanjie-cli/内置 Unity Insight 工具面有相邻，需对表分工）；许可✓；健康✓（当日活跃）；成本安全=需 Unity 侧安装与真跑验证 |
| 游戏工作室体系（49 agents+74 skills+13 rules+39 templates，Godot/Unity/Unreal 三引擎专家组） | Donchitos/Claude-Code-Game-Studios | ✓（★25491·pushed 09-24·MIT·is_template） | MIT（README License 节） | 游戏工作室层级方法论模板——Unity specialist 组（DOTS/Shader/Addressables/UI Toolkit） | 拷 skills/ 单件**选择性吸收**；**不建议整装**（.claude/agents+hooks 为 Claude Code 专有结构，且 49-agent 层级与集团自有司/机治理体系撞车） | 契合=中（方法论+Unity 知识参考价值高）；反重复=**部分撞**（治理体系面）；许可✓；健康✓（★25k）；成本安全=有条件（hooks 为 bash 脚本，Windows 机队需 git-bash） |

### 2.4 调研纪律面候选（raw 双源已验/MIT 声明在案；**API 元数据待限流窗补验后转正**）

| 技能名 | 源repo | 验证状态 | 许可 | 契合一句话 | 安装法 | 五门初判 |
|---|---|---|---|---|---|---|
| 166 件科研技能（数据分析/可视化 22 件、研究方法论 13 件、科学传播 27 件、ML/时序 14 件；database-lookup 一件打 78 库） | K-Dense-AI/claude-scientific-skills（**已更名 scientific-agent-skills**） | API 403 待补验；raw ✓（README 全文直读） | MIT（README License 节原话）+**注意：每技能自带 license 字段可异于 MIT**（其 docx/pdf/pptx/xlsx 四件=Anthropic source-available 内嵌） | 科研流程程序化知识库——采「统计分析/研究方法论/科学写作/市场研究报告」子集对口 CPH4 调研纪律与 BigMoney 数据面 | `npx skills add K-Dense-AI/scientific-agent-skills` 或司仓收编子集拷贝 | 契合✓高（调研纪律/统计/报告）；反重复=部分（拾遗补缺，非全装——官方自警「勿一次全装」）；许可=**条件过**（逐技能 license 字段必查）；健康=过（安全扫描 CI+技能测试 CI 在案）；成本安全=**有条件**（README 自带安全警告与扫描器推荐——采用前逐件跑 cisco-ai-skill-scanner，合集团 secret-scan 纳管律） |
| 17 件研究技能（8 阶段生命周期：literature-triage-matrix/gap-to-topic/research-design-helper/paper-memory-builder/academic-writing-skills 等；**本仓是目录，实体在各子仓** research-hub 等） | WenyuChiou/ai-research-skills | API 403 待补验；raw ✓ | MIT（README License 节原话「MIT」） | 反幻觉 schema 设计（无证据 claim 强制 status:gap+gap_reason，下游拒收越权交接）+证据感知交接+人工门——与集团防线二/验收判据文化同构 | 从实体子仓（WenyuChiou/research-hub 等）拷 SKILL.md 件 | 契合✓高（CPH4 调研纪律正典参照）；反重复=部分（与 cph4-research-dispatch 互补：此件管单研究工作流纪律，集团件管派工面）；许可=raw 已验/API 待补；健康=过（单人研究生作品·自知局限在案——采方法论而非全信）；成本安全✓（Zotero CRUD 件用前强制备份在案） |

## 三 parked+理由

| 技能/源 | parked 理由 |
|---|---|
| anthropics/skills:skill-creator | **反重复门**：Codely 已内置同名技能（本会话环境在列实证），装=冗余 |
| superpowers:writing-skills | **反重复门**：与 Codely 内置 skill-creator 同能力面 |
| superpowers:using-superpowers / diagnosing-superpowers | superpowers 框架自用 meta 件，脱离其插件体系无独立价值 |
| anthropics/skills:claude-api | 集团主用 Codely CLI 会话面，不涉裸 Claude API 开发，契合窄 |
| anthropics/skills:slack-gif-creator | 集团无 Slack 使用面 |
| hmohamed01/powershell-expert | **双重不过**：①平台面=PS 7+ 向（README Platform 徽章实证），不覆盖集团 PS5.1 编码/语法坑律痛点，甚至可能以 PS7 习语误导 PS5.1；②许可=API license=null 无 LICENSE 文件（README 徽章自称 MIT 无法律文件力）→未验明。集团自产 PS5.1 坑律（CODELY.md 在案）比此件更对症 |
| ianlintner/ai-pixel-art-image-generation | **反重复+成本门**：依赖 GPT-Image-2/Azure Foundry/Gemini 付费 API；能力面与 Codely 内置 generate_image/generate_sprite_animation/sprite atlas 工具组重复 |
| KylinMountain/TradingAgents-AShare | A股多智能体投研契合度诱人（★845），但**许可门不过**：license=NOASSERTION（API 直验），未验明不采信 |
| nowsprinting/claude-code-settings-for-unity | **健康门**：archived=true（API 直验） |
| hesreallyhim/awesome-claude-code | 索引面非技能本体；license=NOASSERTION——用作目录，不安装 |
| ComposioHQ/awesome-claude-skills、travisvn/、BehiSecc/、karanb192/ 同名清单 | 索引面；license 均 null/未声明——作目录用 |
| gavogavogavo/claude-sbox、pt1987/claude-code-psadt-skill、DeusMaximus/rmm-skills 等 | 垂直域不契合（s&box 引擎/Intune 打包/RMM 运维——非集团业务面） |
| WILLOSCAR/research-units-pipeline-skills | 契合（研究管线语义单元）但 license=null 未验明+API 403——列观察位，待验后再议 |
| IvanMurzak/Unity-MCP（★4346·Apache-2.0·09-27 活跃·API ✓） | **形态跨界**：主体=MCP server（Unity 编辑器桥），非 SKILL.md 技能——本次 skills 面边界外；已验数据留档，归 CEO 令「mcp 等」之 MCP 调研面另行立项 |

## 四 实搜面实录

### 4.1 anthropics/skills —— API 直验 ✓（api.github.com/repos/anthropics/skills）
存在性 ✓ · full_name="anthropics/skills" · desc="Public repository for Agent Skills" · **license=null** · ★178727 · forks 21140 · pushed 2026-09-24 · created 2025-09-22 · main · archived=false · topics=["agent-skills"]
- 根目录 API listing：.claude-plugin/.gitignore/README.md/THIRD_PARTY_NOTICES.md/skills/spec/template——**无 LICENSE 文件**
- 技能级 LICENSE 直验：skills/mcp-builder/LICENSE 与 skills/docx/LICENSE raw 端点均 **404**（文件不存在）→许可唯一证据=README
- README（raw 直读）许可原话：「Many skills in this repo are open source (Apache 2.0)」+ docx/pdf/pptx/xlsx「**source-available, not open source**」
- 19 技能 API listing 全清点：academy-guide, algorithmic-art, brand-guidelines, canvas-design, claude-api, discernment-nudge, doc-coauthoring, docx, frontend-design, internal-comms, mcp-builder, pdf, pptx, skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing, xlsx

### 4.2 obra/superpowers —— API 直验 ✓
desc="An agentic skills framework & software development methodology that works." · **license=MIT** · ★292321 · pushed 2026-09-27 · created 2025-10-09 · main · 根 LICENSE 文件在 ✓ · 15 技能全清点（brainstorming…writing-skills，见 2.2）

### 4.3 hesreallyhim/awesome-claude-code —— API 直验 ✓（索引面）
★54732 · pushed 2026-09-28（当日活跃） · **license=NOASSERTION** · created 2025-04-19 · 用作挑候选目录；其 Research/Scientific（K-Dense、WenyuChiou）、Writing（avoid-ai-writing）、Creative Media（motion-skills、capcut-cli）节即本报告 2.3/2.4 候选来源

### 4.4 awesome-claude-skills 消歧 —— search API 直验 ✓（q=awesome-claude-skills，total_count=346）
- 主真身=**ComposioHQ/awesome-claude-skills**（★75766·license=null·pushed 09-18）；同名次位 travisvn（★15196·null·pushed 2026-04-28）/BehiSecc（★10185·null·09-21）/karanb192（★526·MIT·09-01）
- 消歧结论：无单一官方仓；采 ComposioHQ 为主索引面（星数活跃度最高）
- 副产物：bergside/awesome-design-skills（★2962·MIT·67 件设计技能清单）——内容/UI 设计面后备目录

### 4.5 Unity/游戏面 —— search API 直验 ✓（q=claude skills unity，total_count=125）
- **Donchitos/Claude-Code-Game-Studios**：★25491·MIT·pushed 09-24·is_template · raw README 实证结构：agents/49·skills/74（slash commands）·hooks/14（bash）·rules/13·templates/39·Unity/Godot/Unreal 三引擎专家组
- **Besty0728/Unity-Skills**：★1789·MIT·pushed 2026-09-28·C# · raw README 实证=Cinemachine 34/Netcode 39/UI 29/UI Toolkit 31/ShaderGraph 23/ProBuilder 22/Asset 12/Perception 18/Validation 16 等编辑器自动化工具面
- **gamedev-skills/awesome-gamedev-agent-skills**：★1207·Apache-2.0·pushed 09-27 · 根 API listing 实证 LICENSE+NOTICE+skills/+router/ · raw README 全目录直读（74 技能+router；Unity 8 件钉扎 6.3 LTS；create-game-assets/procedural-gen 等 disciplines 15 件）
- IvanMurzak/Unity-MCP（★4346·Apache-2.0）与 Glade-tool/glade-mcp（★223·MIT）=MCP 形态跨界件，留档不采
- nowsprinting/claude-code-settings-for-unity：★39·Unlicense·**archived=true→弃**

### 4.6 PowerShell 面 —— search API 直验 ✓（q=claude skill powershell，total_count=178）
- 最强=hmohamed01/powershell-expert（★50·license=null·pushed 09-13）· raw README 实证=PS 7+ 平台徽章+自称 MIT 徽章+「MIT」节——**无 LICENSE 文件+平台不对症→parked**
- 其余（Orquestrador-Maestro/psadt-speckit/rmm-skills 等）均垂直域不契合或 archived

### 4.7 像素/2D 面 —— search API 直验 ✓（q=claude skills pixel art，total_count=35）
- **Gamezxz/pixel-art-studio**：★58·MIT·pushed 07-11 · raw README 全文实证：pixelstudio.py 逐像素引擎/study.py 风格学习/pixelpipe.py AI 图清洗锁色板/LPC 64×64 通用角色表契约/调色板预设（Game Boy/PICO-8/Sweetie16/C64/Endesga32）/安装=cp -r 技能件+pip3 install pillow
- ianlintner/ai-pixel-art-image-generation（★21·MIT）=付费 API 依赖→反重复+成本门 parked

### 4.8 量化面 —— search API 直验 ✓（q=claude skills trading，total_count=366）
- **tradermonty/claude-trading-skills**：★2900·MIT·pushed 2026-09-28 · raw README 全目录直读：60+ 技能七区（Market Regime/Core Portfolio/Swing/Trade Planning/Trade Memory/Strategy Research/Advanced Satellite+Meta）；API 需求表实证（FMP free 250 次/日·FINVIZ Elite $39.5/mo 付费·Alpaca 免费纸面）；no-API 起步五件套在案
- agiprolabs/claude-trading-skills（★397·MIT·68 件）、MobiusQuant/OpenMobius-skill（★686·Apache-2.0）、ginlix-ai/LangAlpha（★1784·Apache-2.0）=备选留档；KylinMountain/TradingAgents-AShare（★845·NOASSERTION）=许可门 parked

### 4.9 内容生产/调研纪律面 —— search API 直验 ✓（q=claude skills writing content，total_count=99；q=claude skill research methodology，total_count=63）
- **conorbronsdon/avoid-ai-writing**：★4748·MIT·pushed 09-27（领域第一）
- 备选留档：artemnovitckii/content-skills（★101·MIT·5 件 viral-hooks/voice-dna 等）、xiaomoBoy/claude-writing-skills（★32·MIT）、Jeffallan/writing-with-agents（★31·MIT·四工匠写作框架）
- 调研面：tonyazhuuki/deep-research-skill（★32·MIT）、Marazii/research-co-pilot（★13·MIT·14 件）、sshtomar/claude-code-skills-social-science（★15·MIT）=留档；WILLOSCAR/research-units-pipeline-skills（★510·license=null）=观察位

### 4.10 限流与换源实录（工具面事实，留档）
- api.github.com 无鉴权限流：后期 4 连 403 rate limit（anthropics 技能级 listing/Donchitos listing/K-Dense/iart-ai/capcut-cli/WenyuChiou 各 repo API 端点）——已按纪律换 raw.githubusercontent.com 双源补验存在性+许可声明，API 元数据（★/pushed_at/license 字段）标「待补验」
- 换源律实证 2 例：iart-ai/motion-skills 与 renezander030/capcut-cli raw main 分支 404→**master 分支命中**（默认分支非 main），内容全文直读成功——被 404≠源不存在
- raw 直验成功件：K-Dense 166 技能库（MIT·已更名 scientific-agent-skills·每技能独立 license 字段警告）、WenyuChiou/ai-research-skills（MIT·目录式，实体在 research-hub 等子仓）、iart-ai/motion-skills（MIT·16 包 53 件）、capcut-cli（MIT·v0.26.0·旧版安全修复史在案）

### 4.11 格式兼容性定谳
- 全部主候选=Agent Skills 开源标准 SKILL.md（frontmatter name+description+正文）——**与 Codely 技能格式同构 100% 兼容**
- 安装法二选一：`codely skills install <git仓库|目录|.skill包>`（整仓/包形态）或拷 skills/<name>/ 单件入 项目 .codely-cli/skills/（优先）或 ~/.codely-cli/skills/——两法均合集团技能律（源入司仓 tools/skills/<name>/ 随 git 分发·安装副本 gitignored）
- 兼容性降级件：Donchitos（.claude/agents+hooks 专有结构+bash）——只可选择性拷 skills/ 件；Besty0728（主体=Unity 包导入面）
- 运行时依赖（部署面，本调研零安装）：webapp-testing→Playwright；pixel-art-studio→Pillow；docx 组→python-docx 等；capcut-cli→Node≥18+npm 包；motion-skills→Remotion/Manim/ffmpeg；K-Dense→uv+按技能 Python 包

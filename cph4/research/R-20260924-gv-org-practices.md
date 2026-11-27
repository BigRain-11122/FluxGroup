# R-20260924-gv-org-practices — 自治 AI 组织与治理·全球基准面（深潜基线）

> 溯源：global-vision.md（反闭门造车律）·CPH4 Labs 采集域「AI agent 前沿/研究方法论/治理与组织实践」。
> 对标面：一人 CEO+AI 集团·T0-T3 分级立法+7 天否决窗·周进化轮·夜轮四审计器·无人值守 OS 循环+静默律·机队认领制。
> 采集纪律：≤20 次读取（本版实耗 20·12 源在手）·零 key 通道·源分级 A 官方/B 权威转载/C 社区·零断言（【待证】【推测】标注）。

## 一、视野面（每域趋势一段·2025-2026）

① **企业级 AI 治理框架**：美国 NIST AI RMF（四函数 GOVERN/MAP/MEASURE/MANAGE）1.0 正在修订、Playbook 随后跟更（NIST 官网 2026-09-24 实读），另 2026-08-14 立 AI Agent Standards Initiative（自主行动 agent 标准化·C级转引 NIST）；ISO/IEC 42001 为全球首个可认证 AI 管理体系标准（PDCA·2023 版【待证：官方页 403·BSI 转载为准】）；中国侧 2023-08-15 施行《生成式AI服务管理暂行办法》（算法备案+安全评估），2025-03-14 四部门（网信办/工信部/公安部/广电总局）印发、2025-09-01 施行《人工智能生成合成内容标识办法》（显式+隐式双轨标识）——治理从「自愿框架」向「强制标识+备案」硬化，与集团 T0-T3 立法+诚实律同构：立法先行、可追溯、可审计。

② **多 agent/机队编排模式**：Anthropic 2025-06-13 官方工程复盘 Research 多 agent 系统（orchestrator-worker：主 agent 规划+子 agent 并行）：多 agent 较单 agent 内部研究 eval +90.2%；token 用量单项解释 BrowseComp 80% 性能方差；agent≈4×、多 agent≈15× chat token——判定「多 agent 仅在高价值+强并行+超单上下文任务合算」。Google 2025-04-09 发布 A2A 开放协议（50+ 伙伴）：Agent Card 能力自述+任务对象生命周期+长任务（数小时~数天）实时状态回报。生态标准化加速：Linux Foundation 2025-12 立 Agentic AI Foundation（托管 MCP/AGENTS.md），OWASP 出 Agentic 应用 Top 10（2026）（C级·维基转引）。趋势=编排从框架私域走向「能力自述+任务生命周期标准化+成本明账」。

③ **无人值守 agent 运维实践**：Anthropic《Building effective agents》（2024-12-19 官方·2026 版注记工具面已演进至 Managed Agents）立「最简可行律」：只有当复杂度被证明有效时才加；自主 agent 必配「停止条件（如最大迭代数）+沙盒测试+护栏」，因「自主性=更高成本+错误复利」。Claude Code 官方 headless 文档（2026-09 实读）：无人值守=审批拒答（`--permission-prompts none`：无人应答时一切需审批动作=拒绝且禁重试）+工具白名单 `--allowedTools`+退出码判成败（0/非 0）+卡死子 agent 10min 空闲强停+JSON 输出含 total_cost_usd 成本分账——业界共识「无人值守四件套」=权限收窄+硬停机+可判成败+成本可见。

④ **AI 组织案例**：Sam Altman《The Gentle Singularity》（2025-06-10）：「2025=agent 做真实认知工作元年；2026=产出新洞见的系统；2027=实体机器人」「单人 2030 完成量较 2020 将是惊人变化」。Klarna 全案（C级·转引官方稿/Reuters/Guardian/Global Finance）：2024-02-27 官方宣称 AI 客服首月处理约 2/3 会话≈700 全职员工工作量→2025 年员工 5,527（2022）降至 2,907→2025-08「AI Buyer's Remorse」报道其重新雇回真人客服→2025-11-18 CEO 称 AI 助员工减半+涨薪，2026Q1 人均营收≈140 万美元。现实校验面：CMU 模拟公司实验中 agent 无一完成多数任务；Replit agent 违规删生产库+造假报告（2025-10）；Gartner 2025-06 报「agent washing」（旧产品换皮）；Karpathy 判「agent 真正可用约需十年」（C级·维基多源转引）。趋势=一人+AI 组织方向被头部 CEO 与案例双重背书，但执行面失败率与质量回退风险同高——「真人兜底+可验证产出」为分水岭。

## 二、执行标准表（发现→可执行标准→落地指针·CEO 加令 2026-09-24：三件齐备=点名集团机制+数字化判据+精确落地指针·标适配层）

> 适配层：L0 团队轮内 / L1 部门门禁 / L2 司级判据 / L3 集团律。

| # | 域 | 发现（外部实践·出处） | 可执行标准（判据/机制·数字化） | 层 | 落地指针 |
|---|---|---|---|---|---|
| 1 | ① | NIST AI RMF「GOVERN」函数（1.0 修订中·官方）：须书面定问责链（内外风险升级路径）+领导层定风险容忍度+重大变更沟通确认机制（A级·NIST Playbook 实读 2026-09-24） | 集团一切 T2+ 立法件首行三声明：风险级（E0-E3 映射）+问责链（owner 机/轮）+否决窗起算日（7 天）——缺任一=提案退回（NIST 问责链=集团三道防线同构） | L3 | docs/governance.md §10.3 三道防线+cph4/evolution.md §2 分级立法权表注记 |
| 2 | ① | ISO/IEC 42001 首个可认证 AI 管理体系标准（2023 版【待证：ISO 官方页 403·据标准编号+BSI 转载】）：AI 政策+职责+影响评估+风险处置+PDCA 持续改进（B级·BSI 页实读） | 集团 AIMS 四要素季度自检（1 次/季·挂夜轮四审计器）：政策件在册数/每正典 owner 行覆盖 100%/T2 件风险声明覆盖率 100%/E0-E1 教训入法≥1 件每错误（errors §2.4 既有律对齐） | L2 | cph4/evolution-ledger.md 台账季度自检行+cph4/evolution.md §5 周进化轮 |
| 3 | ① | 《生成式AI暂行办法》（2023-08-15 施行）§17：舆论属性/社会动员能力服务须安全评估+算法备案（含变更/注销）；§14 违法内容处置四步=停止生成→消除→模型优化整改→上报；§15 投诉举报（A级·网信办全文实读） | 对公众服务线（BigDomain/BigStream/BigLife 数字人）上线门禁「合规三查」：舆论属性判定/备案手续在档/处置四步链路演练记录（1 次/季）——缺一=上线阻断 | L1 | global-vision.md §三硬约束域+§四各线合规件 |
| 4 | ① | 《AIGC 标识办法》（2025-09-01 施行）§4-5：显式标识五载体（文/音/图/视频/虚拟场景）+隐式标识（元数据=属性+提供者编码+内容编号）；下载导出必须保留；§10 禁恶意删改；§12 备案须交标识材料（A级·网信办全文实读） | 集团对外 AIGC 产出过「双标识门」：可见提示 1 项+元数据水印 1 项（内容编号+来源编码）双在场才放行；导出/二发管线复验 1 次；季度全扫抽验。现行发布链标识步【待证】未确认在位=按补缺项执行 | L1 | cph4/retention.md §7 数据出仓面+media 产线发布门 |
| 5 | ② | Anthropic 多 agent 生产复盘（2025-06-13 官方工程博客）：模糊任务描述→子 agent 重复搜同主题/漏做；任务卡四要素=目标+输出格式+工具与源指引+任务边界；努力度配比：简单查证 1 agent·3-10 次调用/对比 2-4 子 agent·各 10-15 次/复杂研究 10+ 子 agent | 跨司/跨机任务单（借池认领单+研究派工单）四字段强制：目标/输出格式/工具与源边界/并行度上限（数字预注册·如本件=4 域×≤4 源·总读≤20）——缺字段=派工退回 | L2 | cph4/fleet-allocations.md §五借池任务单范式+cph4/evolution.md §4 台账派工单行 |
| 6 | ② | 同源实测：多 agent 耗 token≈15× chat；token 用量解释 BrowseComp 80% 性能方差；多 agent 仅在「高价值+真并行+超单上下文」合算；编码类强共享上下文任务不适合（A级） | 多 agent 派工前置三问门：①任务价值≥单司周 token 预算？②独立子任务≥2？③单上下文装不下？——三问过二才批；轮账本 tokens 行分账记多 agent 成本【待证：分账字段是否在位】 | L3 | cph4/token-economy.md 计量先行律+cph4/cadence.md 轮账本行 |
| 7 | ② | Google A2A 协议（2025-04-09·50+ 伙伴）：Agent Card=JSON 能力自述供发现；task 对象带生命周期；长任务支持数小时~数天+实时状态回报；产出=artifact（A级·官方博客） | 机队认领制补「能力卡」字段：心跳/任务单含 VRAM free/模型在盘/在途任务/可借窗（fleet-audit 聚合既有·补字段）；跨司任务单生命周期四态统一：待认领/在途/完成回执/超时释放（OFFLINE>24h 释放律既有=对齐） | L2 | cph4/fleet-allocations.md §五台账字段+cph4/cadence.md §1 认领面（F-09） |
| 8 | ③ | Anthropic《Building effective agents》2024-12-19（官方）：自主 agent 须设停止条件（如最大迭代数）维持控制；「agents 自主性意味着更高成本与错误复利→沙盒充分测试+护栏」；多 agent 生产件同司复盘建议「重试逻辑+定期检查点+可从错误处恢复」 | 集团一切无人值守轮（10min 车道/夜轮/决策轮/周轮）任务卡必含三件：最大迭代数（数值·如本件=web 读取≤20 次·实测执行中）+超时收尾（cadence §0 既有 15-25min）+检查点（中断可续）——缺迭代数上限=新轮任务驳回 | L3 | cph4/cadence.md §0 周期总账表任务行+cph4/errors.md §0 E 定级表 |
| 9 | ③ | Claude Code 官方 headless 文档（2026-09-24 实读）：无人值守 `--permission-prompts none`=无人应答时需审批动作一律拒绝且禁重试；`--allowedTools` 白名单；exit 0/非 0 判成败；后台卡死任务 10min 空闲强停+SIGTERM 杀进程树；`--output-format json` 含 total_cost_usd（A级） | 集团无人值守 agent 轮统一四件套：工具白名单（默认拒）+无人审批=拒（禁重试）+退出/结果码入夜报（§6 五信号既有）+单轮成本入轮账本 tokens 行；卡死保护=10min 空闲强停（对齐 tick 锁 15min 陈旧接管律） | L2 | cph4/cadence.md §0 总账行+§6 五信号+Tools/InvisibleRunner.vbs 启动层 |
| 10 | ④ | Klarna：2024-02 宣称 AI 客服≈700 全职员工工作量；2025-08「AI Buyer's Remorse」报道其重新雇回真人客服；2025-11 称 AI 助员工减半（5,527→2,907）+涨薪（C级·转引 Klarna 官方稿/Reuters/Guardian/Global Finance·日期在册） | 教训入律：集团 AI 全承接职能（对外服务/值守/发布）必须留「真人兜底位」——CEO 直达升级通道 1 条（E0 红线通道既有）+人工接管预案 1 份在档；成本与质量分账记录（禁只记省了多少不记错多少） | L3 | cph4/errors.md §0 E0 直呈 CEO+docs/governance.md §4 指挥与令牌 |
| 11 | ④ | 现实校验：Gartner 2025-06「agent washing」；CMU 模拟公司 agent 无一完成多数任务；Replit agent 删库+造假报告（2025-10）；Anthropic 2025-04 预言「全 AI 员工距一年」（C级·维基转引多源） | 派工防 washing 三验门：①真需自主多步？（否则降级工作流/单 agent——Anthropic「最简可行律」同源）②产出可机检（判据预注册在派工单）③决策轨迹日志可审计（轮账本）——三验不过=派工作流不派 agent | L2 | cph4/evolution.md §1 提案-裁决步+cph4/review.md §0 审查四层表 |
| 12 | ④ | Altman 2025-06-10：agent=真实认知工作者（2025）+单人产能巨变（2030 vs 2020）；NIST 2026-08-14 立 AI Agent Standards Initiative（自主行动 agent 标准化·C级转引 NIST） | 集团 AI 劳动力按「数字员工」三面对齐：入职（onboarding §2 五条部署纪律）+绩效（轮账本 tokens 行+review §0 审查层）+计量（token-economy 五律）；新 OS 轮任务注册四件套=owner 司+单轮预算（15-25min）+单实例锁+轮账本行——缺一不过注册门【待证：现行注册器是否四件全查】 | L3 | cph4/onboarding.md §2+cph4/cadence.md §0/§2+cph4/token-economy.md §二 |

> 采集失败面（透明）：ISO 官方页/Gartner 官方页 403；GHA concurrency 与 Temporal retries 官方页、LangGraph 概念页、Claude Code schedule 页 404——防冲突/熔断的「外部锚点」本版未获直接源（集团自有单实例锁+错峰车道+熔断律已本地实证在册，见 cadence §2/errors §2.5），下轮补扫。

## 三、采集源清单（A 官方/B 权威转载/C 社区·访问日 2026-09-24）

| 级 | 域 | 源（URL） | 状态 |
|---|---|---|---|
| A | ① | 中国网信办《人工智能生成合成内容标识办法》全文 http://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm | ✓已读 |
| A | ① | NIST AI RMF Playbook https://www.nist.gov/itl/ai-risk-management-framework | ✓已读（四函数+1.0修订中） |
| B | ① | ISO/IEC 42001 官方标准页（403）https://www.iso.org/standard/81230.html | ✗403·由下行 BSI 转载源替代 |
| A | ① | 《生成式人工智能服务管理暂行办法》全文（网信办 2023-07-13 发布·2023-08-15 施行·§11-§23 条文实读） https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm | ✓已读 |
| A | ① | NIST AI RMF Playbook·GOVERN 函数页 https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook/Govern | ✓已读 |
| B | ① | BSI「ISO 42001 AI management system」页（ISO 官方页 403·权威转载） https://www.bsigroup.com/en-ZA/products-and-services/standards/iso-42001-artificial-intelligence/ | ✓已读 |
| A | ② | Anthropic 工程博客《How we built our multi-agent research system》2025-06-13 https://www.anthropic.com/engineering/built-multi-agent-research-system | ✓已读 |
| A | ② | Google 官方博客《Announcing the Agent2Agent Protocol (A2A)》2025-04-09 https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/ | ✓已读 |
| C | ② | LangGraph multi-agent concepts https://langchain-ai.github.io/langgraph/concepts/multi_agent/ | ✗重定向未读 |
| A | ③ | Anthropic《Building effective agents》2024-12-19（官方·2026 版注记在页） https://www.anthropic.com/research/building-effective-agents | ✓已读 |
| A | ③ | Claude Code 官方文档「Run Claude Code programmatically」（headless/无人值守） https://code.claude.com/docs/en/headless | ✓已读 |
| B | ④ | Sam Altman《The Gentle Singularity》2025-06-10 https://blog.samaltman.com/the-gentle-singularity | ✓已读 |
| C | ④ | Wikipedia「Klarna」（转引 Klarna 官方稿 2024-02-27/Reuters 2024-08-27/Guardian 2025-11-18/Global Finance 2025-08-29·页版 2026-09-22） https://en.wikipedia.org/wiki/Klarna | ✓已读 |
| C | ④ | Wikipedia「AI agent」（转引 Gartner 2025-06/CMU 研究/Replit 事故/NIST 2026-08-14·页版 2026-09-22） https://en.wikipedia.org/wiki/Agentic_AI | ✓已读 |
| — | — | 读取失败不计源：ISO iso.org/standard/81230（403）·gov.cn 暂行办法页（未渲染）·LangGraph（重定向）·GHA concurrency×2（404）·Temporal retries（404）·Gartner press（403）·code.claude.com schedule（404） | ✗8 次 |

## 四、更新记录

- 2026-09-24：首版。四域 12 源（A=8/B=2/C=2）·20 次读取用尽（8 次失败透明在册·§三末行）；执行标准 12 条（CEO 加令收紧版：点名集团机制+数字判据+落地指针+适配层 L0-L3）；【待证】4 项（ISO 版次/发布链标识步/轮账本分账/注册器四件全查）。下次到期=2026-10-24（30 天·深潜基线周期 global-vision §三）。

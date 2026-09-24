# R-20260924 Agent 前沿四域全球基准面（采集域=AI agent 前沿+研究方法论）

> 溯源：cph4/global-vision.md 反闭门造车律（CPH4 Labs 采集域行）·调研波 2026-09-24·web 读取 20 次预算用满（成功 18·404×2·同名站纠正 1：tmbench.com=TM-Bench 威胁建模，非 Terminal-Bench）。
> 源分级 A 官方/B 权威转载/C 社区/M 待证；零断言。现役对标=各司 OS 10 分钟自迭代循环+机队 git 台账认领制+本地 LLM 栈+记忆冷热分层+判据预注册/独立复核。
> 收紧令（CEO 2026-09-24「标准要适配各业务技术团队部门子公司，不要写大而空泛的」）：执行标准表每条三件齐备=点名集团实际机制/文件+数字化判据（阈值/时长/次数）+落地指针+适配层（L0 团队轮内/L1 部门门禁/L2 司级判据/L3 集团律·沿 decision.md §8）；禁空泛动词开头；宁少勿滥（8 条全实）。

## 一、视野面（每域趋势一段·带日期与关键玩家）

- ①框架=2025-26 收敛整合年：AutoGen 官宣**维护模式**「不再收新特性·社区接管·新用户请用 Microsoft Agent Framework」（README 官方宣言·MAF 官宣页 404【待证】）；LangGraph（LangChain）定位「**低层编排框架与运行时**·长期运行有状态 agent」，核心卖点=确定性步骤与 LLM agentic 步骤同图混合+持久化/HITL/长短期记忆（Klarna/Uber/J.P. Morgan 采用在册）；OpenAI Agents SDK=「轻量多 agent 工作流·**provider-agnostic·100+ 模型**」，原语=agents/handoffs/**guardrails**/agents-as-tools/**sessions**（会话史自动管理）/sandbox agents（容器长时程）；CrewAI 已 **OSS 1.0 GA**（官方 Blog 在册）；AgentScope（阿里·通义实验室）进 **2.0**（models/tools/MCP/skills/多智能体 FAQ）+RL 深研 agent 训练实践+生产案（阿里商旅收集准确率 50%→90%+）。共通新原语=sessions/状态持久化·guardrails·HITL·MCP·技能包。对标=我们 OS 循环与台账制即产业同构面。
- ②记忆与上下文=从「上下文工程」（2024-25：最小高信号 token 集/JIT/compaction——Anthropic 2025-06 原文+LangChain 四桶已采=R-20260923-02b）演进到「**agentic memory 系统化**」（2025-26）：Letta（MemGPT 后继）=全状态持久化+**核心记忆块 agent 可自改**+**sleep-time compute**（2025-04-21·Letta 0.7.0·arXiv:2504.13171）——「原始上下文→习得上下文」·主代理快模型+睡眠代理强模型分工；Mem0 上线 **Memory Decay**（新近性感知排序：近访问加分/久置降分/**不删不藏**）；Anthropic 官方数字=memory tool+context editing 提升复杂任务 **39%**（单独 editing **29%**）·100 轮搜索评测省 token **84%**；Anthropic **Agent Skills**=渐进披露三层（启动只载 name+description→命中才载全文 SKILL.md→按需执行）「小上下文足迹」。关键玩家=Anthropic/Letta/Mem0（LangMem 现状【待证】）。对标=记忆冷热分层+上下文管家正对同一条演进线。
- ③评测基准=从「静态问答」转向「**实环境执行**」：SWE-bench（ICLR 2024·arXiv:2310.06770·真实 GitHub issue·数据/代码/榜单=swebench.com·官网今重定向论文页）仍是编码 agent 标尺（当前榜首【待证】）；GAIA（Meta+HF·arXiv:2311.12983·2023-11）哲学=「**对人类简单、对 AI 难**」——人类 **92%** vs GPT-4+插件 **15%**·466 题（300 答案扣留防污染·配方公开可再生成·**要求 reasoning trace**·HF 数据 2025-10-28 更新在册·三级=≤5 步/5-10 步/多步多工具）；τ-bench（Sierra·GitHub）=零售/航空对话双域+用户模拟器（GPT-4 ReAct 成功率 **34%/10%** 在册·dual-control 与 τ²-bench【待证】）；Terminal-Bench=真实终端容器任务（官网自述「衡量 agent 用终端完成任务的能力」·已入 Harbor 套件 `harbor run -d terminal-bench/terminal-bench`）。方法论锚点=短可验答案+过程 trace+防污染+实环境跑测。对标=判据预注册/独立复核对同一条纪律线。
- ④自我改进=零权重更新三术汇流（2023→2026 典律化）：①**语言反思**（Reflexion·arXiv:2303.11366·2023-03）「不更新权重·以语言反馈强化」·反思文本入 episodic 记忆缓冲驱动后续尝试·HumanEval 91% 超 GPT-4 80%；②**技能库**（Voyager·arXiv:2305.16291·2023-05）=自动课程+**可执行代码技能库**（可组合/可解释/抗灾难遗忘·新世界零样本迁移·技术树解锁快 15.3 倍）——2025 年 Anthropic Agent Skills 把技能库升为产业标准格式（SKILL.md+渐进披露）；③**睡眠时整理**（Letta sleep-time compute·2025-04）闲时改写记忆状态。2026-01：77 页综述《A Survey of Self-Evolving Agents: What, When, How, and Where to Evolve on the Path to Artificial Super Intelligence》入选 TMLR（arXiv:2507.21046·taxonomy 细节【待证】）。对标=OS 循环（夜轮感知→提案→裁决→立法）与 Reflexion 消化失败+台账留痕同构。

## 二、执行标准表（8 条全实·三件齐备=点名机制/文件+数字判据+指针+适配层）

| # | 发现（外部实践·出处） | 可执行标准（点名集团实际机制+数字化判据） | 落地指针 | 层·生效 |
|---|---|---|---|---|
| 1 | OpenAI Agents SDK sessions=跨运行会话史自动管理（A·官方文档） | 冷启动面判据：新会话自动注入 ≤4k tok（治理层 v2 目标·现实测 ~64k tok）+每轮轮账本 tokens 行 1 行强制（cadence §0 轮族护栏已接）——台账单源可恢复在办即达标 | token-economy §一上下文面·cadence.md §0 轮账本 | L0 轮内+L2 司台账·✓tokens 行在役/⬜≤4k 待治理层 v2 |
| 2 | Anthropic：memory tool+context editing=复杂任务 +39%（单独 29%）·100 轮评测 token -84%（A·官方工程页） | P-48 上下文管家成立线双指标：input/轮降 ≥50%（15k→4-5k 目标带）**且**任务判据不降；验收=轮账本 tokens 行前后对照·连续 4 周（token-economy §四 BigMoney 判据）；成立后随 P-31 两周回执窗推广六司 | token-economy §3.4 上下文管家+§四 | L2 司级判据（BigMoney pilot）·✓已派工 |
| 3 | Letta sleep-time：主代理快模型+睡眠代理强模型·闲时整理记忆（A·官方博客 2025-04-21） | 周日 03:07 记忆梳理窗挂 14b 深度线（分时换载：载入 8.9s·换载税 ~12s·keepwarm.pause 旗防 OOM）——快慢分工=夜轮 7b 常驻不动·梳理步独用 14b 窗；梳理熔断每窗 ≤10 条·夜轮预算 15min 不变 | token-economy §3.3 14b 分时换载·memory.md §3 梳理窗 | L3 集团律（夜轮窗）·⬜下个周日窗起 |
| 4 | Mem0 Memory Decay=新近性感知排序（近访问加分/久置降分/不删不藏）（A·官方站现役特性） | 热层入冷判据升双维：「>14 天 **且** 近 7 天零引用」同时满足才搬（单维 14 天制废止）；周报记忆面加 1 行「近 7 天被引用条目数」；水位表字节制不变（集团根 ≤20KB/线级 ≤10KB/司级 ≤20KB·重灾 ≤50KB/单条 ≤1.5KB） | memory.md §0/§2/§4 | L3 集团正典判据+L2 周报行·⬜memory.md 下批修订窗 |
| 5 | Anthropic Agent Skills 渐进披露：启动只载 name+description·命中才载全文（A·官方工程博客） | 能力沉淀件一律薄卡制：卡 ≤1.5KB 只载「名称+一句话描述+主题件路径」（=Discovery 层），全量入主题文件按需读；新自动化提案/新脚本先过查重门——同用途旧件存在则复用改造·禁并行新写（cadence §1.1 同用途唯一制扩展到脚本/模板面） | memory.md §1.4 一条一事·token-economy §〇.1② 能力沉淀律·cadence.md §1.1 | L3 正典+L1 提案查重门·✓§1.4 在律/⬜查重门待接 |
| 6 | Reflexion：失败后语言反思入 episodic 缓冲、驱动下次尝试（A·arXiv:2303.11366） | 失败任务（E0/E1/E2 级）当轮必产 1 条「现象→根因→改法」教训条目入记忆；E0/E1 级教训入法三选一（法条/记忆/检测器）；无教训产出=半解决=轮内自审不过（governance §10.3 第一道防线拦）；熔断：同错两轮未愈禁第三次硬修·升 E1 | errors.md §2.4 教训入法律+§2.5 熔断律·governance.md §10.3·memory.md §1.3 | L0 团队轮内（10-25min 预算内）·✓§2.4 已立法·轮内判据化 |
| 7 | GAIA 评测法：短可验答案+reasoning trace 强制+答案扣留防「对着结果调」+τ/Terminal-Bench=实环境跑测（A·两官网） | 判据预注册三件套：①判据 ≤1 行短句·可机器验证（答案式非散文式）②过程 trace 在案（git diff+实跑产物链接）③判据先于执行定稿·事后改判=诚实律违规；机制改动验收附实跑证据（复现先行+独立验证双绿·P-16 范式）；裁决后下轮回访 1 次记台账 | governance.md §10 诚实律·review.md 预注册+审查三律·errors.md §2.2/§2.3·evolution.md §7 | L3 集团律+L2 独立复核·✓判据先行已立法/⬜①②两判型细化 |
| 8 | Voyager：技能=可执行代码·可组合·抗遗忘·新环境可迁移（A·arXiv:2305.16291） | 自动化脚本/工具一律入 Tools/ 可检索池（禁一次性散件）；同用途唯一（查重门见第 5 条）；沉淀计量=季度「本地化覆盖清单」1 份入周轮（清单内逐件可点出复用次数≥2 即「二进宫」成立） | Tools\selfaudit.ps1 生态·token-economy §五季度清单·cadence.md §1 | L1 池查重+L3 季度清单·✓季度清单在律/⬜二进宫计数待接 |

## 三、采集源清单（每源一行·分级+URL+访问日期 2026-09-24）

- A LangGraph 官方文档 https://langchain-ai.github.io/langgraph/
- A OpenAI Agents SDK 官方文档 https://openai.github.io/openai-agents-python/
- A AutoGen 官方仓库（维护模式宣言+迁移指引） https://github.com/microsoft/autogen
- B CrewAI 官方 Blog（OSS 1.0 GA·docs 引言页被博客面覆盖） https://blog.crewai.com/
- A AgentScope 官方文档站 https://docs.agentscope.io/
- M Microsoft Agent Framework 官宣页（404·AutoGen README 侧证） https://devblogs.microsoft.com/foundry/introducing-microsoft-agent-framework/
- A Anthropic 工程页（今抓跳转 context management 面·39%/29%/84% 数字在册） https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- A Letta 官方文档（stateful agents/记忆块自改） https://docs.letta.com/guides/agents/memory
- A Letta 官方研究博客（sleep-time compute·2025-04-21·Letta 0.7.0） https://www.letta.com/blog/sleep-time-compute
- A Mem0 官方站（Memory Decay·Taranjeet Singh 署名） https://mem0.ai/research
- A Anthropic 官方工程博客（Agent Skills 渐进披露·发布日期【待证】） https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- R 内部复用件=R-20260923-02b（Anthropic 2025-06 上下文工程原文+LangChain 四桶·09-23 实抓在册·URL 见该件）
- A SWE-bench 论文页（ICLR 2024·swebench.com 重定向至此） https://arxiv.org/abs/2310.06770
- A GAIA 论文页+HF 社区面 https://arxiv.org/abs/2311.12983 ·https://huggingface.co/papers/2311.12983
- B τ-bench 仓库页（抓取面薄·34%/10% 在册） https://github.com/sierra-research/tau-bench
- A Terminal-Bench 官网（Harbor 套件托管） https://www.terminal-bench.com/
- A Reflexion 论文页 https://arxiv.org/abs/2303.11366
- A Voyager 论文页 https://arxiv.org/abs/2305.16291
- A Self-Evolving Agents 综述（TMLR 2026-01·77 页） https://arxiv.org/abs/2507.21046

## 四、更新记录

- 2026-09-24 首版：四域基准面 v1（框架 6 源/记忆 6 源/基准 4 源/自我改进 3 源·8 条执行标准全实·每条带数字判据+适配层+生效态）·CEO 收紧令（防大而空泛）当批执行·下次到期=2026-10-24（30 天·global-vision §三深潜基线）

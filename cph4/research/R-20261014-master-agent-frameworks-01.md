# R-20261014-master-agent-frameworks-01 — 开源多智能体编排/主智能体框架盘点（CEO 常设工作律 2026-10-13 轮子优先）
> 溯源：CEO 常设工作律 2026-10-13「一切动手前先搜 GitHub 高星现成轮子」·消费方=集团主AGENT（主脑）架构蓝图·判据预注册=①高星框架盘点（星/许可/活跃/Windows）②机制对集团栈借鉴价值③直接采用/借模式/判负/待证判定
> 验证声明：外部源实读 20/20 次；成源 18 条全 A 级（api.github.com 仓页+搜索 16、raw.githubusercontent LICENSE 原文 1、arXiv 论文 1）；另 404 直证 1 条（microsoft/magentic-one 仓消亡）；失败面 2：①magentic-one API 404 ②search 走 web_fetch 通道超 100K 截断（改 shell 直连重试成功）；B/C/M 源 0；架构形态未直读官方文档处均标「推」。

## 一、高星框架盘点主表（Q1+Q3；星/许可/活跃度=api.github.com 2026-10-14 直读，含 All-Hands-AI→OpenHands 更名重定向；「确」=官方自述/论文直读）
| 框架 | 星数 | 许可 | 活跃(pushed) | 架构形态 | 落点 |
|---|---|---|---|---|---|
| Dify | 158,425 | Dify 开源许可（修改版 Apache-2.0+附加条件） | 2026-10-14 | 可视化 Agentic 工作流平台 | 判负 |
| TradingAgents | 111,112 | Apache-2.0 | 2026-10-03 | 交易公司多智能体模拟：辩论+风控门（推） | 借模式 |
| OpenHands | 90,857 | MIT | 2026-10-14 | 自治 AI 软件开发平台 | 判负 |
| deer-flow（字节） | 83,844 | MIT | 2026-10-14 | 深研编排 supervisor+researcher（推） | 待证 |
| MetaGPT/ChatDev | 70,844/34,513 | MIT/Apache-2.0 | 2026-01/2026-07 双停滞 | SOP 角色分工「AI 软件公司」（确/推） | 判负 |
| MS AutoGen（+AG2 fork） | 61,394/4,995 | 仓 CC-BY-4.0（代码包 MIT 之说待证）/Apache-2.0 | 2026-04 停滞/2026-10 活跃 | 事件驱动+对话式（推） | 判负 |
| CrewAI | 59,675 | MIT | 2026-10-14 | 角色分工编排（确：role-playing 自述） | 判负 |
| LangGraph | 43,244 | MIT | 2026-10-14 | 图编排/状态机+checkpoint（推；resilient 自述确） | 借模式 |
| AgentScope | 33,226 | Apache-2.0 | 2026-10-14 | 消息驱动+容错重试（推） | 借模式 |
| OpenAI Agents SDK | 30,025 | MIT | 2026-10-14 | 轻量多智能体工作流（确）+handoff（推） | 借模式 |
| smolagents（HF） | 29,838 | Apache-2.0 | 2026-10-06 | 代码即行动 CodeAgent（确：think in code 自述） | 借模式 |
| Semantic Kernel | 28,658 | MIT | 2026-10-14 | LLM SDK+C#/.NET 智能体编排 | 待证 |
| Letta（前 MemGPT） | 25,127 | Apache-2.0 | 2026-09-10 | 有状态分层记忆平台（确：自述） | 借模式 |
| swarm（OpenAI） | 22,056 | MIT | 2026-04 停摆 | 轻量 handoff 编排（确：教育性质自述） | 判负 |
| Google ADK | 21,828 | Apache-2.0 | 2026-10-14 | 代码优先多智能体工具包 | 判负 |
| MS Agent Framework | 14,123 | MIT | 2026-10-14 | SK+AutoGen 合并继任，Python+.NET（确：自述） | 待证 |
| Magentic-One（MS） | 仓已 404 | — | 仓消亡 | Orchestrator+任务台账+双循环（确：arXiv:2411.04468） | 借模式 |

- 搜索面补充（api 搜索 q=multi-agent Top20·同日直读）：TradingAgents/deer-flow/ChatDev 已核入表；另 paperclip 101,817★/ruflo 74,610★/nanobot 49,014★/CowAgent 47,392★/LibreChat 45,658★ 未入表——与主脑编排相关性未采（预算封顶），待证不计。

## 二、可借鉴机制面（Q2·对标集团栈：Win 三机+PowerShell+schtasks+codely cron+llama.cpp 35B+云端 LLM+L0/L1/L2+FleetLink+决策委员会）
- Magentic-One 双循环+任务台账（arXiv 直验）：外环重规划/内环派工，台账 FACTS/PLAN/PROGRESS 三段——与决策委员会+CEO-PROXY 同构，主脑编排核心参考（确认）。
- LangGraph checkpoint+状态图（机制=推断）：L0/L1/L2 显式状态图化+持久 checkpoint，schtasks 崩溃后断点续跑=自愈底座。
- handoff 席位交接（swarm→Agents SDK，推断）：控制权以函数调用显式转移→委员会席位切换协议化。
- Letta 分层记忆+后台整理（自述确认，机制细节推断）：主脑长期记忆库正式化=cph4 台账升级方向。
- smolagents code-as-action（自述确认）：agent 动作=可审计代码片段，比 JSON 工具调用更贴 PowerShell 执行面。
- 自愈循环：Magentic-One re-plan 重规划（arXiv 确认）+AgentScope 容错重试（推断）→巡班失败降级/重试矩阵。
- 任务路由：L1 分诊现役已自研，框架增量≈0——增量在 checkpoint 与台账，不在路由（判定）。

## 三、集成成本 vs 借模式（可行性上限面）
- Windows 兼容（分类推断）：纯 Python 库（LangGraph/CrewAI/ADK/smolagents/Agents SDK/AgentScope/AG2/TradingAgents/deer-flow）可 pip 装；SK/MS Agent Framework=.NET 原生；Dify/OpenHands/Letta 服务端主推 Docker（需 Docker Desktop 常驻）。
- 主栈无常驻 Python/Node/Docker 运行时；L0 确定性巡班不需要 LLM 框架——框架价值全在编排模式层。
- Python 系引入=新增运行时+venv+依赖治理+常驻进程，集成成本>借模式（预注册「直接采用」判据不满足）。
- .NET 系（SK/MS AF）：PowerShell 7 同属 .NET 理论可直载，但 NuGet 装配+学习面+L0-L2 重写成本仍>借模式→留 PoC 待证。

## 四、判定面（Q3·三问一行答案）
- Q1：现成轮子充分且许可普遍宽松（MIT/Apache 为主），但 2026-10 处于洗牌期——MS AutoGen 停滞、Magentic-One 仓消亡、swarm 停摆；当日仍活跃的第一梯队含 Dify/OpenHands/LangGraph/Agents SDK/ADK/MS Agent Framework。
- Q2：六件套最值得主脑借：Magentic-One 双循环+任务台账、LangGraph checkpoint 状态图、handoff 交接、Letta 分层记忆、smolagents code-action、自愈降级矩阵。
- Q3：直接采用 0；借模式 7；判负 7；待证 3（见第五节应用表）——判定柱=「集成成本>借模式」与「洗牌期风险」，非轮子不存在。
- 判负判据示例：Dify=许可附加条件（raw 直验）+Docker 平台错配；AutoGen=停滞 6 个月+仓许可异常；CrewAI=角色分工与决策委员会同构零增量；OpenHands/MetaGPT=场景错配。

## 五、结论应用表（强制·每框架落点四选一，明细见第一节落点列）
| 落点 | 框架清单 | 状态 |
|---|---|---|
| 直接采用 | 无（判据：任一框架集成成本>借模式，主脑现役编排核心已被 codely cron+自制三层覆盖） | 已闭环（判定） |
| 借模式 | LangGraph·Magentic-One·Agents SDK·Letta·smolagents·AgentScope·TradingAgents | 待接线（主脑蓝图） |
| 判负 | Dify·OpenHands·MetaGPT/ChatDev·MS AutoGen/AG2·CrewAI·swarm·Google ADK | 已闭环（留痕） |
| 待证 | Semantic Kernel·MS Agent Framework（.NET/PowerShell 直载 PoC）·deer-flow（深研编排对 cph4 线） | 未启动 |

- 更新记录：T0 骨架落盘（早落盘律）→T1 候选池 12+新发现 3 仓 api 直读核验（16 读）→T2 Dify 许可原文+Magentic-One 论文+高星搜索补验（4 读）→终稿 N 行（node 字节级实测）。
- 防线二：两承重主张已独立直验——①Dify 许可限制=raw/LICENSE 原文（A 级）；②Magentic-One 机制=arXiv:2411.04468 摘要（A 级）；全部星数=api.github.com 2026-10-14 实读；无 B/C/M 源采信。

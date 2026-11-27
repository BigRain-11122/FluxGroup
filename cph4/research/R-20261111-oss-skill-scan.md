# 开源技能/策略扫描 · 2026-11-11

> 目的：CEO「去 GitHub 等开源网站找更好的技能、策略」。
> 方法：GitHub Search API 检索 9 组关键词（agent orchestration / llm router / llm eval / multi-agent debate /
> workflow engine / llm-as-judge / prompt testing / outbox / docs drift），按星数排序取前 5。
> **取证限制**：后续详情请求被限流（60 req/h），所以本文只对"搜索返回字段"负责（星数/许可证/描述）；
> 未逐个 clone 复核实现细节——凡标「未核实」的，不得当结论引用。

## 一、候选清单（按用途分组）

| 组 | 项目 | 星 | 许可 | 与我们何干 |
|---|---|---|---|---|
| 编排 | crewAIInc/crewAI | 60.7k | MIT | 角色化多智能体编排 |
| 编排 | kestra-io/kestra | 30.2k | Apache-2.0 | 声明式工作流控制面 |
| 编排 | PrefectHQ/prefect | 24.1k | Apache-2.0 | 弹性工作流/重试/背压 |
| 编排 | apache/airflow | 47.4k | Apache-2.0 | DAG 调度（重） |
| 路由 | musistudio/claude-code-router | 38.1k | MIT | 本地模型路由控制面 |
| 路由 | Portkey-AI/gateway | 13.4k | MIT | AI 网关+护栏 |
| 路由 | QuantumNous/new-api | 51.7k | AGPL-3.0 | 自建 LLM 网关（AGPL 传染） |
| 路由评估 | lm-sys/RouteLLM | 5.7k | Apache-2.0 | **路由器的离线评估方法** |
| 评测 | openai/evals | 19.7k | 自定义 | 评测框架与用例组织 |
| 评测 | confident-ai/deepeval | 19.4k | Apache-2.0 | LLM 评测断言库 |
| 评测 | evidentlyai/evidently | 8.1k | Apache-2.0 | 观测/漂移检测 |
| 评审可信度 | thunlp/ChatEval | 346 | Apache-2.0 | **多评审 + 位置偏差** |
| 评审可信度 | Skytliang/Multi-Agents-Debate | 623 | GPL-3.0 | 辩论式聚合（GPL 慎用） |
| 提示测试 | promptfoo/promptfoo | 27.1k | MIT | 用例即断言 + 红队 |
| 可靠投递 | dtm-labs/dtm | 10.9k | BSD-3 | Saga/TCC/outbox（Go 生态） |

## 二、采纳决定（要落点，不落点不算采纳）

| # | 来源 | 决定 | 落地位置 | 理由 |
|---|---|---|---|---|
| 1 | ChatEval / Multi-Agents-Debate | **已采纳（本轮）** | `Tools/fleet/panel_review.py::order_invariance`（自检 10/10） | 评审结论会随证据排列变化＝判决不可信。已实现"同证据换顺序必须同判决"，顺序敏感则不放行（`--check-order`），并带"顺序敏感必须被判出"的负控 |
| 2 | RouteLLM | 采纳方法，缓落地 | 已有 `condition_matrix.py` 覆盖端点选择格 | 路由要用"离线胜率"评，不用直觉；下一步需要真实调用样本才能算胜率 |
| 3 | promptfoo | 采纳原则 | 已有 `regression.py`(36) / `condition_matrix.py`(80) / `robustness_suite.py`(10) | 用例即断言、负控优先——我们已在做，不引框架 |
| 4 | Prefect/Airflow/Kestra | **不采纳主体**，只取三概念 | 已具备：租约/attempts、熔断冷却、`hold` 背压 | 引入编排框架会把"谁写哪片"从静态约束变成动态调度，违反一机一写者 |
| 5 | crewAI / 通用多智能体框架 | **不采纳** | — | 我们的席位是"一席一事 + 输出 schema + 判据"，比框架的对话式协作更严；框架会把契约重新软化成对话 |
| 6 | Portkey / new-api / claude-code-router | **不采纳** | 已有本地网关 + 端口判令牌（`llm_client._needs_token`） | 引入外部网关=新增云依赖与运维面，且 AGPL 项目与闭源分发冲突 |
| 7 | deepeval / evidently | 采纳思路，不引依赖 | 已有 `quality_score.py`（六维可复算） | 我们要的是"缺数据按 0 计"的硬口径，不是又一个观测面板 |
| 8 | dtm / CAP（outbox） | 已具备 | git 即 outbox + poke 即通知（`cmd_latency`/`notify`） | 重复投递幂等已由 `robustness_suite` R-04 断言 |

## 三、结论

1. **框架一律不引**：本仓的约束（离线可跑、Windows/macOS 混合、一机一写者、零云依赖）与这些框架的假设相反；
   引进来换来的是运维面与不确定性，不是能力。
2. **真正值得偷的是机制**，本轮偷到并落地 1 条：评审的位置偏差检验（有负控）。
3. **下一步（需真机/数据才能做，列为待办而非承诺）**：
   - 路由胜率：用 30 天真实调用样本评估"本机→大脑→主控"阶梯是否选对；
   - 评审复现率：同一产物两次独立评审的一致率（<80% 视为判决不可用）；
   - 长跑稳定性：24h 常驻下句柄/内存/回执增长曲线。

## 四、来源

- GitHub Search API（2026-11-11 检索，星数与许可证取自搜索返回）：`crewAIInc/crewAI`、`kestra-io/kestra`、`PrefectHQ/prefect`、`apache/airflow`、`musistudio/claude-code-router`、`Portkey-AI/gateway`、`QuantumNous/new-api`、`lm-sys/RouteLLM`、`openai/evals`、`confident-ai/deepeval`、`evidentlyai/evidently`、`thunlp/ChatEval`、`Skytliang/Multi-Agents-Debate`、`promptfoo/promptfoo`、`dtm-labs/dtm`
- 分级：以上均为 **B 级**（仓库元数据）；实现细节**未核实**（限流），引用前须复核。

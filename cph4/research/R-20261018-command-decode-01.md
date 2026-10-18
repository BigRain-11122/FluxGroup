# R-20261018-command-decode-01 — CEO 命令拆解台面·提示词功能调研件

> 令源：CEO 令 2026-10-18 23:1x「委员会牵头，调研提示词的功能，以后我的命令，都要拆解成有效的你们AI能准确识别的命令，然后分发下去，执行正确。当然你们看有必要不，我只是设想。」
> 案卷=C-20261018-06 · 执行落点=CEO-PROXY ROUND 步6 拆解台面 v1 · 调研律=2026-10-14 常设工作律（GitHub 三查）+research-dept-charter §五
> 结论先行：**CEO 设想方向正确且有量级证据背书；集团既有体系已覆盖设想约七成；真缺口三处（分诊/协议锚/断言档位）已按本件证据落台面 v1——零新系统零新运行时零新法条族。**
> 数据口径：GitHub 星数/许可/活跃=2026-10-18 当日 API 实测（CPH4 调研代理 41 工具调用收齐）。

## 一、证据腿：什么让 AI 执行更准（一手来源）

1. **微软实证《Does Prompt Formatting Have Any Impact on LLM Performance?》**（He et al.·arXiv 2411.10541）：同一内容只换呈现格式，GPT-3.5-turbo 准确率最高差 **40%**（MMLU：JSON 59.7% vs Markdown 50.0%；HumanEval：JSON 59.8% vs 纯文本 40.2%）；GPT-4 更稳健但**不存在万能格式**——结构化收益真实、须按所用模型实测选定。→ 结构化字段对「准确识别」是量级变量不是锦上添花（支持缺口 G2）。注：另题《Measuring The Impact Of Prompt Structure On LLM Performance》(2024) 经 arXiv 全字段检索 0 结果（疑企业内部出版物），以本篇公开实证替代。
2. **微软 SAMMO《Prompts As Programs》**（arXiv 2404.02319）：结构感知提示优化对指令类任务提升 **10-100%**；复杂提示须逐 LLM 调优、弱模型受益更大——我方本地量化模型（bm-a 35B/bm-b 4b）恰是「结构化收益更大」的受益带。
3. **官方口径一致**：Anthropic 指南（docs.claude.com prompt-engineering overview+long-context-tips）=先明确请求→复杂任务拆解（chaining）→格式用例子/prefill→长文档置顶+引用 grounding；OpenAI 官方六策略（platform.openai.com/docs/guides/prompt-engineering）含「**Split complex tasks into simpler subtasks**」+系统化评测；Anthropic《Building effective agents》=从简单可组合任务开始。
4. **分解粒度**：Least-to-Most Prompting（arXiv 2205.10625）——分解成子链后难任务正确率显著提升；LLM Agent 规划综述（arXiv 2402.02716）把 Task Decomposition 列五大方向之首；AWS Kiro 判例口径=「每项任务颗粒度恰好可自主执行」。
5. **提示词膨胀（prompt bloat）**（mlops.community 综述）：输入约 **3000 token 起推理退化**、无关/矛盾信息显著掉分（语义相近的无关信息杀伤力最大）。→ 派单卡短而准+只带相关上下文+正典指针（禁按记忆复述律同源）；五型分诊防「口令/方向律误当任务派发」的上下文污染（支持缺口 G1）。
6. **指令特异性**：DETAIL Matters（arXiv 2512.02246·2025-12）——显式成功标准显著影响正确率，CoT 只能部分弥补模糊。→ 验收断言=「具体到可判」的终极形态（支持缺口 G3）。
7. **集团内部判例同向**：B站回复线四闸实证「机械闸优于 prompt 自觉」（10-14 CEO 账号安全令批）+QC-MASTER-CHECKLIST 逐帧断言族+delivery-watch min_duration 闸——本调研=把该内部经验升格为拆解层默认律。

## 二、工具腿：GitHub 高星现成轮（三查=星数/许可/活跃·2026-10-18 API 实测）

**四条结论**：①三查全过且高适配三件=**BMAD-METHOD**（任务卡+验收标准文件模板）、**instructor**（口语→结构化任务卡 JSON 最短路径）、**promptfoo**（机械验收断言）；②多代理框架星虽高但形态=进程内编排，与我方「跨机 CLI agent 会话」错位——**抄其 schema 与模式、不引入运行时**；③结构化输出类云端场景首选 instructor/原生 JSON schema·outlines 面向本地模型（ollama 节点可用）；④「中文口语命令→任务卡」无开箱即用高星成品（semantic-router/TypeChat 仅前置粗分派）——该层我方自建为正道。

| 轮子 | 星 | 许可 | 活跃 | 用途与适配判 |
|---|---|---|---|---|
| **promptfoo/promptfoo** | 26.1k | MIT | 今日（OpenAI/Anthropic 在用） | **高**——断言即机械验收：确定性断言族（contains/equals/regex/is-json 带 schema 校验/javascript/python）+模型评分类（llm-rubric/agent-rubric）谨慎用；「deterministic first」原则=验收断言档位律业界正身·不引运行时 |
| **bmad-code-org/BMAD-METHOD** | 54.3k | MIT+BMad 商标附加条款（GitHub 字段显 Other） | 今日 | **高**——结构化 PRD→story 文件、story 内嵌验收标准段落直接驱动 CLI agent；任务卡模板可参照 |
| **crewAIInc/crewAI** | 59.8k | MIT | 今日 | **中（抄 schema 不抄运行时）**——Task 必填 description+expected_output（+agent/context/output_pydantic）=业界最接近「任务卡」的现成 schema；「无 expected_output 框架拒建卡」＝「无验收物不出单」同律 |
| 567-labs/instructor | 14.0k | MIT | 4 天前 | **高（备查）**——NL→Pydantic schema+校验失败自动重试；未来做「CEO 命令→自动结构化卡」管道时的最短路径 |
| langchain-ai/langgraph | 43.4k | MIT | 今日 | 中——图/状态机编排，自建调度控制流时可参照 |
| microsoft/autogen | 61.5k | **CC-BY-4.0（非典型代码许可·引入须复核子包）** | 2 天前 | 中——对话式多代理；官方后继 Microsoft Agent Framework 14.2k★ MIT |
| FoundationAgents/MetaGPT | 70.9k | MIT | **停滞 ~9 个月** | 低（思想高现状差）——SOP 流水线思想可借鉴（arXiv 2308.00352） |
| pydantic/pydantic-ai | 20.7k | MIT | 今日 | 中——类型化 agent 框架（需自建服务） |
| dottxt-ai/outlines | 16.0k | Apache-2.0 | ~1 月前 | 中——约束解码保证 JSON schema 合规·限本地/自托管推理 |
| guidance-ai/guidance | 21.8k | MIT | **停滞 ~5 个月** | 低——功能已被原生结构化输出覆盖 |
| confident-ai/deepeval | 18.9k | Apache-2.0 | 2 天前 | 中——pytest 式 LLM 评估（偏代码内嵌） |
| vibrantlabsai/ragas | 16.1k | Apache-2.0 | 停滞 ~8 个月 | 低——RAG 专项·我方无 RAG 场景 |
| microsoft/TypeChat | 8.7k | MIT | 3 天前 | 中（范式）——「意图=类型」NL→TS 类型化 JSON 经典范式 |
| aurelio-labs/semantic-router | 4.0k | MIT | 今日 | 中（备查）——嵌入向量毫秒级意图路由免 LLM；未来命令前置粗分派候选 |
| crestalnetwork/intentkit | 6.5k | MIT | — | 低——技能生态向·不对口 |

## 三、判例腿：「NL 命令→结构化指令→分发执行→机械验收」公开案例

- **GitHub spec-kit**（141.8k★·MIT·活跃）：/specify→/clarify→/plan→/tasks→/implement 命令化 SDD 工作流+constitution 约束文件——「自然语言→结构化规范→任务→执行」的现成规模化框架。
- **AWS Kiro**：requirements.md（用户故事+**验收标准**）/design.md/tasks.md 三件套；tasks.md 生成后 agent 自建依赖图、独立任务分波并行执行；AWS 官方案例明言「先与干系人定死验收标准再写码」。
- **GitHub Copilot coding agent（GA）**：指派 issue→agent 自主 plan→draft PR→跑测试→按 review 迭代——CI 检查=机械验收层。
- **Manus 公开博客**：todo.md「复述计划」防长任务走神；planner 派活/executor 干活分工；约 1/3 动作耗在重写 todo→改专职 Planner 子代理返回结构化 Plan 对象按需注入（context engineering 判例）。
- **A2A 协议**（26.2k★·Apache-2.0·Linux Foundation 托管）：公开 Task 对象标准——状态机 submitted/working/input-required/completed/failed/canceled（终态不可复活）——可当我方 POOL 卡状态字段的规范底本（现有五态迁移律已同构·备查参照）。
- **未找到**：AI agent 公司公开的「多机 CLI 机队」完整 SOP（AgentOps 类只到可观测层）——集团场景=自建正道，业界件之长以 schema/方法论层面吸收。

## 四、必要性裁决（对 CEO 问句「有必要不」的证据面回答）

1. **有必要（方向正确）**：结构化+断言=准确执行的量级变量（40% 摆幅/10-100% 指令任务提升）；CEO 直觉与业界证据一致。
2. **不需要重建（七成已建成）**：拆解令（10-16）+九要素卡+card-lint 机械闸（10-14）+分发链+回执链已把设想大面落地——业界判例（Kiro/spec-kit/CrewAI）逐一对位皆有同构件；本案=补三缺口而非建新系统。
3. **三缺口与修法**（已落 ROUND 步6）：G1 分诊无统一首步→五型分诊表；G2 拆解输出无协议锚→拆解五律+派单行 card-lint --min 硬步；G3 验收物散文化→验收断言档位律。
4. **防通胀红线**：不建命令 DSL、不改 CEO 输入方式（CEO 继续说人话·拆解翻译归 AI 侧）、不引入外部编排器运行时——C-20261018-05 配额闸合规（执法强化件零新法条族）。
5. **备查位（未采纳·留档）**：instructor 自动解析管道（未来 CEO 命令→自动结构化卡可用）、semantic-router 粗分派、A2A 状态机对表 POOL 五态——皆记备查不立项。

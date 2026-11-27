# R-20260923-02b 治理层 v2 · 波B 外部对标（业界解法与映射）

> 溯源：CEO 令 2026-09-23 ~22:40（章程 §三 波B）。调研波=20 次实抓验证；每条给来源 URL；查证不到已标「存疑：仅内部知识」。适用语境=一人 CEO+多 AI 子公司+无人值守循环的「组织即代码」治理面。

## 路一 AGENTS.md / CLAUDE.md 入口文件标准与体量指引

- **agents.md 已成事实标准**：60k+ 开源项目采用，Linux 基金会 Agentic AI Foundation 托管；采用方=Codex(OpenAI)/Cursor/Gemini CLI/Warp/VS Code/Copilot coding agent 等（https://agents.md/）。大仓正解=**嵌套 AGENTS.md：每子目录放一张卡，最近者优先**——OpenAI 主仓有 88 个 AGENTS.md。无必填字段，纯 markdown。
- **Codex 官方有硬水位**：全局→根→cwd 逐层拼接，**总量默认 32KiB 上限（project_doc_max_bytes），超限跳过/截断**——官方给的解法就是「拆到嵌套目录」（https://learn.chatgpt.com/docs/agent-configuration/agents-md）。
- **Cursor 官方**：规则 <500 行；**「引用文件而不是复制内容」**；拆成可组合小规则（https://cursor.com/docs/rules）。
- **Gemini CLI**：分层（全局→工作区→**目录触达式 JIT 加载**）+ @import 拆件 + 底栏显示已加载上下文文件数（可观测性）（https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md）。
- **Claude Code 官方**（https://code.claude.com/docs/en/memory + /best-practices）：CLAUDE.md 目标 **<200 行**（「长文件消耗更多上下文并降低遵从度」）；**MEMORY.md 自动加载截断=200 行/25KB，超出部分不载入，近限时主动提醒「一行一条+细节转主题文件」**——索引卡+深指针模式官方实现；4MiB 硬跳过；@import 递归 4 跳；path-scoped 规则按文件域加载；「臃肿的 CLAUDE.md 会让模型忽略你真正的指令」；排除项=「读代码就能知道的」「详细 API 文档给链接」。
- **适用判断**：我们 AI.md（2.6k tok）尺寸合规=正解面；根 CODELY.md（25k tok 自动注入）与 BigMoney 记忆（104k tok）远超官方同款限值——官方解法（薄索引+主题文件+按需）可直接搬。

## 路二 长运行 agent 的 context engineering

- **Anthropic 官方**（https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents）：「好的上下文工程=用**最小的高信号 token 集**达成目标」；**context rot**（上下文越长召回越差）；**JIT 模式=只存轻量标识（路径/查询/链接），运行时按需取**；Claude Code 本身=混合式（CLAUDE.md 预载+glob/grep 即取）；长任务三术=compaction/结构化笔记（笔记写窗外交外部，用时取回）/**子代理只回传 1-2k token 蒸馏摘要**。
- **多代理研究系统**（https://www.anthropic.com/engineering/built-multi-agent-research-system）：「搜索的本质是压缩」；lead 把计划持久化到外部记忆；**rainbow deployments=升级不扰运行中 agent**（我们「禁 big-bang」的业界同款）；产物落文件系统+回传轻量引用（防传话游戏）。
- **LangChain**（https://www.langchain.com/blog/context-engineering）：四桶=write/select/compress/isolate；四种失败态=context poisoning/distraction/confusion/clash。
- **Cognition**（https://cognition.com/blog/dont-build-multi-agents）：默认单线程线性；共享上下文；「上下文发酵」警告。
- **适用判断**：我们的多窗并行=多代理组织；夜报/周报应成为**唯一跨上下文物**（蒸馏摘要制）；集团记忆=结构化笔记面，正对官方模式。

## 路三 单一事实源+派生视图（组织即代码）

- **Backstage 软件目录**（https://backstage.io/docs/features/software-catalog/）：**源真=与代码同仓的元数据 YAML，被收割成目录视图**；官方卖点原话「让一个团队管理 10 个服务——让一家公司管理上千个」。→ 「org.yaml 登记处+派生视图」的直接先例。
- **Event Sourcing**（https://martinfowler.com/eaaDev/EventSourcing.html）：状态=事件序列派生；事件日志可为唯一正史、库随时重建；「事件日志纯增量、极小加锁」→ **orders.md 本质就是事件日志，只是写成了散文**。
- **semantic-release**（https://github.com/semantic-release/semantic-release）：**commit 历史=唯一事实源，changelog 全自动派生**；commitlint 强制提交规范 → 我们的 commit 纪律已强，台账行可派生。
- **docs-as-code**（https://www.writethedocs.com/guide/docs-as-code/）：文档进 git、进评审、进 CI 门禁（无文档可阻断合并）。
- **适用判断**：三件套组合=「orders.jsonl 事件流+org.yaml 登记处+git log 派生视图」，直接满足验收线 1/2。

## 路四 体量治理工具链先例

- 工具级水位：Codex 32KiB 硬上限；Claude Code 200 行目标/4MiB 跳过/**MEMORY 200 行-25KB 截断+近限提醒+超限写入报错反馈**；子代理描述合计超 15k token **启动时警告总 token 数**（启动预算可观测）。
- CI 级门禁：**Danger**（https://danger.systems）`git.lines_of_code > 50_000 → fail` 同款；**性能预算 101**（https://web.dev/articles/performance-budgets-101）「预算=三选一：优化旧件/移除旧件/不加新件」；**markdownlint** 自定义规则+CI（https://github.com/DavidAnson/markdownlint）。
- **适用判断**：selfaudit.ps1 加 size-lint 段（每文件水位线+超线点名周报）+夜轮近限提醒=全有先例可抄，无技术风险。

## 路五 多 agent 组织的上下文分层先例

- Anthropic 多代理系统（同路二）：**每子代理独立隔离窗口、冷启动零继承**、只回传摘要；按任务复杂度配代理数（简单 1 个 3-10 调用/比较 2-4 个/复杂 10+）。
- Claude Code 子代理（https://code.claude.com/docs/en/sub-agents）：「侧任务会淹没主对话→子代理在自己的上下文里干、只回摘要」；omitClaudeMd 可选不注入入口卡。
- **适用判断**：五司 OS 循环=天生的隔离子代理；总部上下文只应收到轮报告摘要（夜报已是雏形）——**总部读全文的时代应终止**。

## 映射表（→章程 §四 七条验收线）

| 验收线 | 支撑模式（来源） | 落地方式 | 风险一句 |
|---|---|---|---|
| 1 单一事实源 | Backstage YAML/event sourcing/semantic-release | orders.jsonl 一令一行+org.yaml 一实体一行；BRAND §8/登记簿/architecture 线表改由 org.yaml 派生；ledger 行从 commit 派生 | 双写过渡期要一代视图共存（分批禁切） |
| 2 机器优先 | 同上+probes 现有消费 | 探针直接吃 jsonl/yaml（顺带根治 P-10 行数游标类问题）；人读视图生成器（PS 小件） | 生成器要进 selfaudit 门禁 |
| 3 冷启动预算 | Claude MEMORY 200 行/25KB+Codex 32KiB | 根 CODELY.md 转≤200 行索引+主题文件；AI.md 保持薄卡；预算定标建议=**自动注入 ≤2k tok+按需首读 ≤2k tok** | 存量 49 条要一次性归档拆分（当批完成） |
| 4 开线成本≤2 | 嵌套 AGENTS.md 最近优先 | 开线=org.yaml 加一行+changelog 自动；线 README 转生成视图 | BRAND locked 行的惯例迁移要一次显式批 |
| 5 体量三律 | Codex/Claude 水位+Danger/markdownlint | selfaudit 加 size-lint 段+夜轮近限提醒+水位线三档（警告/只读归档/阻断） | 水位值需波A 数字定标（见 R-02a §6） |
| 6 禁 big-bang | rainbow deployment | pilot=orders.md 单件→专家审→分批 rollout，每批 git revert 可回（versioning.md revert 律同源） | 探针迁移需影子读（双源对比一晚再切换） |
| 7 运转不中断 | event sourcing 重建/回放 | 夜轮/周轮 mandate 只改「读哪里」；探针逐个迁移；CityWatch 引擎侧同步消费 jsonl | 时序：先加影子源→对比绿→切主源 |

## 最值得抄的三个模式

1. **薄索引+主题文件+按需取**（Claude Code MEMORY.md 200 行/25KB 官方机制）——治根 CODELY.md 与 BigMoney 记忆两个最大膨胀源，机制官方验证过、工具（append_memory 引用模式）原生支持。
2. **YAML 登记处+派生视图**（Backstage）——治「开线碰 6-10 文件」：org.yaml 一行登记，BRAND/登记簿/architecture/线 README 全变派生面。
3. **事件流+自动派生台账**（event sourcing+semantic-release）——治「同令 3-4 遍复述」：orders.jsonl 唯一正史，commit 规范即溯源，台账行自动生成。

## 方法与局限

- 20 次实抓全过；Cognition 原文抓取不完整（已按可见部分引用，未引 30k 框架例证）；Allsources 均为主方官方文档（一手）。
- 波B 结论=模式可搬性高：七条验收线每条都有业界同款先例，无一需要发明新技术——**全是组织工程，不是软件工程**。

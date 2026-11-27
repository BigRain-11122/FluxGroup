# R-20261117 社交自动化 agent 开源调研（客服/养号/回复）

问题：客服、养号、回复这类自动化 agent，社区一定有很多现成的；先把它们摸清，别重复造轮子。

约束（本仓既有口径，决定了"能不能直接用"）：离线可跑、Win+mac 混合、一机一写者、零云依赖；
AGPL/非商用许可不得进产线；对外发送权在 CEO（我们只出草稿）。

## 一 找到的候选（许可证逐个核实过原始 LICENSE 文件）

| 项目 | 许可 | 它能给我们什么 | 决定 |
|---|---|---|---|
| chatwoot/chatwoot（37k★） | 核心 MIT Expat（enterprise/ 另许） | **会话状态机**（open/waiting/resolved/snoozed）、人工接管、SLA、canned responses | **偷模型**（ruby/rails，整仓引不进来） |
| dreammis/social-auto-upload | **MIT** | 多平台发布（抖音/小红书/视频号/B站/tiktok/YouTube），B站走 biliup | **留作发布侧备选**；账号与发布权在 CEO，我们只备材料 |
| NanmiCoder/MediaCrawler | **NCAL 1.1（非商用学习）** | 7 平台采集、CDP 复用真实 Chrome、登录态缓存、断点续爬、代理池 | **只偷机制不引代码**（许可不允许进产线） |
| hay-chat/hay-core、Rogue85/kvitok | 需逐仓核（未进候选） | 自托管 AI 客服 + 读后端做动作 + 人工审批草稿 | 暂不引：依赖电商后端（Shopify/Stripe），与我们场景不符 |
| Dify | Apache 改写（禁多租户商用、禁去标） | 工作流 + 向量 RAG | **不用**：许可灰区 + 重型服务 |
| Rasa | Apache | 意图分类/对话管理 | 不用：我们把意图分类做成确定性判据，效果够且可复算 |

## 二 我们缺什么（对照后只剩两处真空）

1. **会话状态**：现在每条评论独立处理——同一个人连问三句会重复回、已聊完的会被翻出来、
   该人接的丢给模型。这是最大的真空。
2. **未回积压**：没有"等我方超过 X 小时"的概念，也没有转人工后的封存。

其余（频控/冷却、登录态、断点、打码）我们已经有了，社区方案不比我们的强，没必要换。

## 三 本轮落地

`Tools/fleet/social_threads.py`——照 Chatwoot 的会话模型重写成本仓口径（纯 python + json，无依赖）：

- 状态：open / waiting / resolved / snoozed / handoff；**转移表写死**，表外一律拒绝（防调用方自觉）。
- 语义细节照抄 Chatwoot 实务：resolved 有新消息自动重开；snoozed 到点自醒；
  **handoff 后机器不许再发**，只有人工回复能把会话交还机器。
- SLA：等我方 ≥24h 标 overdue，只标不自动发（对外发送权在 CEO）。
- 审计：每次转移写 `cph4/fleet/social/threads-events.jsonl`。
- 自检 9/9，含四条负控：resolved→waiting 必须被拒、handoff 后机器必须被拒、
  超 24h 必须 overdue、due 必须最久优先。

自检当场抓出两个真 bug（记在这里防重犯）：
1. `ts or time.time()` 把 0 当假值——自检与回放都用 ts=0，判断全错；
2. `waiting_since = 0` 表示"未设置"与"时间戳 0"冲突，tick/due 全部失效。
   修法：未设置一律用 `None`，不用 0。

## 四 下一步（按价值排序，都不是"再造一个"）

1. 把 threads 接到 `social_drafts`：handoff/waiting 的会话不许出草稿（一个 conv→comment 映射即可）。
2. 事实检索：现在是规则模糊匹配（`faq_lookup` min_score 0.34）。本机有 qwen3-embedding，
   可换向量 top-k——但只在事实包超过 50 条时才有意义，现在 3 条，先不做。
3. 发布侧：等 CEO 决定发布流程后，MIT 的 social-auto-upload 可作为"备好材料→一键出包"参考，
   不接它的账号体系。

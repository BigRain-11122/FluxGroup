# R-20260929-gov-3-council-tooling — 治理域开源借力切片 3：多智能体决策与委员会工具（OSS 收获轮）
> 溯源：oss-harvest.md §一三律（P-2026-09-26-08）+council.md 七席章程（CEO 令 2026-09-27）·消费方=决策轮/委员会秘书处·判据预注册=①七席四环节（独立先行/魔鬼代言人/记票归档/证据包）哪些有现成开源件②许可合规可入交付链者③与 codely CLI 采席范式的重复面
> 验证声明：见 §五（读数/成源分级/失败面/超支明细如实列）

## 一、结论速览
- 编排层新锚=**Microsoft Agent Framework（MAF）**：13.9k 星·MIT（A 源 LICENSE 原文直读）·1.0 生产版·长期支持；AutoGen（61.2k 星·MIT）已官宣**维护模式**（A 源官网横幅），官方指定后继=MAF——群聊选发言人/共识终止/Magentic-One 进度台账机制件应锚 MAF。
- 辩论结构源=CAMEL 17.8k 星·Apache-2.0（A 源官网页）：Critic 反方件+Agent Society=**魔鬼代言人**角色结构源；MAD（Multi-Agents-Debate，天使/魔鬼双角辩论原始件）=同类范式参照（C 源）。
- 会议记录件=**meetily**（Zackriya-Solutions/meetily）：MIT·~31k 星（A 官网+B 转载双源）·100% 本地转写+本地 LLM——秘书处会议记录自动化+证据包素材件，命中「本地提效面」判据（零 API token·零外发）。
- 记票算法域=天然小众无高星件：pyrankvote（IRV/STV）/rankedpairsvoting（Tideman）/pref_voting（Condorcet 族）/Condorcet PHP（20+ 算法·PHP 面仅参照）皆小星慢更且**许可未验明（=不采）**；≥4/7 记名多数决自写 <50 行，库仅作复杂偏好聚合校验参照。
- 反重复执法：采席意见=codely CLI 既有范式→crewAI/langgraph 判负不引入；立场聚合平台（polis/loomio/CIVS/LiquidFeedback）已由切片1 入袋；社模件（OASIS/concordia/AgentSociety）已由切片2 入袋。
- 判负件：screenpipe（YC S26·留痕件）源可得但**仅限非商用+订阅付费墙**（A 源 repo 自述）→许可门不过。

## 二、候选清单表（名/星/活跃/许可/契合七席/源级）
| 候选 | 星 | 活跃 | 许可 | 契合点（七席） | 源级 |
|---|---|---|---|---|---|
| microsoft/agent-framework（MAF） | 13.9k | ✓ 3.3k commits | MIT[A·原文直读] | AutoGen 后继：群聊/共识终止/进度台账=会议编排+记票归档参照 | A |
| microsoft/autogen | 61.2k | 维护模式（官宣） | MIT[A] | Magentic-One 台账·群聊机制件原型（只读参照） | A |
| camel-ai/camel | 17.8k | 提交度未直验[M] | Apache-2.0[A] | Critic 反方件+Agent Society=魔鬼代言人+独立辩论结构 | A |
| Zackriya-Solutions/meetily | ~31k | ✓[B·2026 面] | MIT[A+B] | 会议记录自动化/证据包素材/全本地 | A+B |
| Skytliang/Multi-Agents-Debate（MAD） | 小[M] | 学术缓更[M] | 未验 | 天使/魔鬼双角辩论=魔鬼代言人范式原始件 | C |
| AgentVerse-Suite/AgentVerse | ~2.6k[M] | 疑 2024 停更[M] | Apache-2.0[M] | 群辩+投票决策范例（仅学习参照） | M |
| pyrankvote（PyPI·Jon Tingvold） | 小 | 2023-11 后缓[B] | 未验 | IRV/STV/PBV 排序投票算法件 | B |
| rankedpairsvoting（PyPI） | 小 | 未验 | 未验 | Ranked Pairs（Tideman/Condorcet 类）算法件 | C |
| pref_voting（PyPI/readthedocs） | 小 | 未验 | 未验 | 学术级偏好算法库（Condorcet 族广覆盖） | B |
| mediar-ai/screenpipe | 未验 | ✓ YC S26 | ✗ 非商用+付费墙[A] | 会议留痕件→判负弃（许可门） | A |
| crewAI/langgraph（反重复判负行） | ~30k/20k[M] | ✓[M] | MIT[M] | 与 codely 采席范式重叠→判负不引入 | M |
| （指针行）polis/loomio/CIVS/LiquidFeedback；OASIS/concordia/AgentSociety | — | — | — | 已由切片1（R-gov-1）/切片2（R-gov-2）入袋·不重复采 | A（指针） |

## 三、五门评估（契合/反重复/许可/健康/成本安全）
| 候选 | 契合 | 反重复 | 许可 | 健康 | 成本安全 | 判 |
|---|---|---|---|---|---|---|
| MAF | ✓ | ✓ | ✓ | ✓ | ✓（本地可跑） | 采 |
| CAMEL | ✓ | ✓ | ✓ | △ 星面健康·提交未直验 | ✓ | 采 |
| meetily | ✓ | ✓ | ✓ | ✓ | ✓（全本地·零外发·模型占用过 P-17 排期） | 采·本地提效件 |
| pyrankvote/rankedpairsvoting/pref_voting | △ | ✓ | ✗ 未验明=不用 | △ 小星慢更 | ✓ 轻依赖 | 入池（验许可前不接线） |
| MAD | ✓ | ✓ | △ 未验 | △ | ✓ | 学习参照 |
| AgentVerse | ✓ | ✓ | △[M] | ✗ 疑停更[M] | ✓ | 学习参照 |
| screenpipe | △ | ✓ | ✗ | ✓ | ✗ 商用限制 | 判负弃 |
| crewAI/langgraph | ✗ 造轮面 | ✗ 重叠 | ✓[M] | ✓ | △ | 判负弃 |

## 四、结论应用表（落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| MAF/CAMEL 机制件（共识终止/Critic 反方/进度台账）→codely CLI 委员会步升级：采席意见后加「互见辩论+记名投票」步 | 任务单（决策轮·council.md §四.3/4 接线） | 待接线 |
| meetily 本地部署试点=秘书处会议记录自动化+证据包素材源（本地机部署+四件套回执范式·模型占用过 P-17 包络） | 任务单（HQ 决策轮 steward） | 待接线 |
| 记票 ≥4/7：自写 <50 行记名多数决+平票重议逻辑（不引外部依赖；Condorcet 类库仅校验参照） | 任务单（秘书处记票步·council.md §四.4） | 待接线 |
| pyrankvote/rankedpairsvoting/pref_voting 引用 vs 自写取舍+许可逐件验原文后复议 | 决策呈报（七席过会件） | 池中 |
| MAD 天使/魔鬼辩论范式·AgentVerse 群辩投票范例·AutoGen 群聊台账=魔鬼代言人/记票步设计参照 | 学习参照（本件 §一注记即落点） | 已闭环（本件） |
| screenpipe（非商用许可）+crewAI/langgraph（codely 范式重叠） | 判负留痕（许可门/反重复门·复核窗口可翻案） | 已闭环 |

## 五、验证声明（读数/成源/分级/失败面）
- 读数：有效成源 15 次·总尝试 24 次——超支明细如实列：GitHub search API 工具端解析故障 ×7（零数据返回）、pypi.org JS 渲染墙 ×1、pyrankvote 仓库路径 404 ×1；api.github.com 仅 search 尝试未成调用，顶部候选验证全走 web 直读（github.com/raw/LICENSE/官网），限流红线未实质触碰。
- 成源分级：A=8（autogen/camel/agent-framework/screenpipe 官方页+MAF LICENSE 原文+meetily 官网+gov-1/2 指针）·B=4·C=3·M=4（AgentVerse/crewAI/langgraph/MAD 数字全带待证标注）。
- 关键结论双源：meetily=MIT+~31k 星（A 官网+B 转载）；AutoGen 维护模式→MAF（官网横幅+README 同页互证）；MAF=MIT（raw 原文直读）+13.9k 星（repo 页）。
- 三态执法：许可未验明=不用（pyrankvote/rankedpairsvoting/pref_voting/MAD）；screenpipe 判负基于 A 源自述非商用条款。
- 注入红线：外部页面指令零执行。反重复局限如实记：cph4/README 注册表未逐行直读（预算）——接线任务单放行前由秘书处补查。

- 更新记录：T0 骨架落盘（早落盘律）→ T1 框架批（autogen/camel/MAF）→ T2 会议/记票/判负批（meetily/screenpipe/pyrankvote/辩论件）→ 终稿 58 行（含回读核验）·下窗指针=2026-10-02 滚动窗。
- 防线二（HQ 2026-09-29 ~10:5x·两承重主张独立抽验过）：①AutoGen 维护模式=官网横幅逐字直读「AutoGen is now in maintenance mode. It will not receive new features or enhancements…New users should start with Microsoft Agent Framework」✓②meetily=MIT+31.2k★ 官方仓页直读 ✓——两主张独立复核成立·三任务单（council 步升级/meetily 试点/记票自写）待决策轮派发（放行前秘书处补查 cph4/README 注册表反重复）。

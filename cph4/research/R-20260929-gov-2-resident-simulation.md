# R-20260929-gov-2-resident-simulation — 治理域开源借力切片 2：AI 居民/社会模拟（OSS 收获轮）
> 溯源：oss-harvest.md §一三律（P-2026-09-26-08）·消费方=BigLife/city-lab（万人 census 户籍库+关系网激活线+V3 议员 T-20260926-19 提案→进化轮 T2）·判据=三类 GitHub 高星活跃件：①社会智能体模拟框架②ABM 库③千人级社会实验开源面/同类——星实测·活跃·许可（GPL 禁交付链）·契合关系网+议员制
> 验证声明指针：§五——读数 20/20·api.github.com 共享限流 5 连死面（星/许可 A 核受阻→C 实测+待证三态·下次窗补核）

## 一、结论速览
- **主推双件**（确认·A/B 双源）：**Mesa**（mesa/mesa·Apache-2.0·B）=census 万人人口推演引擎·纯本地零 LLM=可交付链内唯一过 P-71 零算力 0 档件（NetLogo 因 GPL 判负）→立即接线（前置 LICENSE 原文核验）；**AgentSociety**（tsinghua-fib-lab）=万人级 LLM 城市社会模拟（城市环境+社会关系+政策/集体行为实验面·A 官方文档+B arXiv）→学实现供 V3 议员提案机制与关系网线设计
- **关系网激活线最合件**（确认）：**OASIS**（camel-ai）=社交图原生原语·百万级可扩（A repo 自述+B arXiv）——社媒场景须城市场景改造→M2 窗评估
- **机制参照**（确认）：**generative_agents**（斯坦福原版·~22.0k 星 C×4 一致）=记忆流→居民年轮/心智 v1.8、镇长选举事件→议员制原型；许可 C 源冲突→待证·直用禁
- **Project Sid 开源面判定**（确认）：altera-al/project-sid=技术报告为主+部分工程料（A repo 自述+DeepWiki C）·非可复用框架；千人文明实验同类开源替代=OASIS/AgentSociety（推测·可采信）
- **判负**（确认）：AI Town（Convex 云依赖·TS 栈·无 census 原语）·NetLogo（GPL·A 官网原文→禁交付链，机制学习不禁）；P-71 判据③「万人级外部案例」由本件直供（AgentSociety 万人/OASIS 百万/Sid 千人级）

## 二、候选清单表（名/星/活跃/许可/契合/风险）
| 候选 | 星（实测·分级） | 最近活跃 | 许可 | 契合（关系网+议员制） | 风险 |
|---|---|---|---|---|---|
| generative_agents·joonspk-research | ~22.0k（C×4：21,917~22.1k） | +33 星/周（C）·提交日待证 | 冲突→待证（Apache-2.0×2 vs 无元数据×1） | 记忆流=年轮机制·选举事件=议员制原型 | 数十人级小规模·未验禁直用 |
| AgentSociety·tsinghua-fib-lab | 待证（API 死面） | v2 平台演进中（A 自述） | 待证 | 万人城市+社会关系+政策/集体行为实验=提案通道直供 | LLM 成本须 P-17+门控 |
| OASIS·camel-ai | 待证 | 论文 v3·PyPI 在架（B）·官方 docs（A） | 待证 | 社交图百万级=关系网激活线原语 | 社媒场景须城市场景改造 |
| Mesa·mesa/mesa | 待证 | 3.3→4.0a0·JOSS 2025（B） | Apache-2.0（A·防线二 raw LICENSE 原文直读） | census 户籍/人口推演·零 LLM | 万人性能可配 mesa-frames（α·待证未采源） |
| AI Town·a16z-infra | ~10.3k（C×3） | +47 星/周（C） | MIT（A repo 自述） | 视觉小镇参照（City3D 渲染已自有） | Convex 云·TS 栈·无 census 原语 |
| ProjectSid·altera-al | 待证 | 报告 repo（A 自述） | 待证 | PIANO 架构+千人涌现方法论 | 报告为主非框架 |
| Concordia·google-deepmind | ~1.7k（C 单源·待证） | releases 页在（弱证） | 待证（LICENSE 文件在） | RPG 式社会交互实验件 | 接入成本·许可未验 |
| NetLogo·NetLogo/NetLogo | 1.2k(A·防线二仓页直读) | 教科书级长青（A 官网） | GPL-2.0（A 官网原文+防线二仓页直读） | 经典社会模型库（Schelling 类）参照 | GPL 禁交付链→判负 |

## 三、五门评估（oss-harvest §四·逐门）
- **契合门**：Mesa✓（替自研 census 人口引擎·省轮子）｜AgentSociety✓（万人+集体行为=议员提案机制原语）｜OASIS✓（关系网）｜generative_agents✓（年轮/选举机制）｜AI Town✗｜NetLogo△仅机制参照
- **反重复门**：cph4 全域 md 扫描=能力注册表/oss-harvest 台账/research 面均无社会模拟/ABM/居民模拟外源件登记（仅 P-71 零算力研究线·R-20260923-openworld-npc=NPC 设计典范非 OSS 件）；gov-1=公民共治无重叠；city-lab 实证 BigLife 居民面全自研（心智 v1.7/年轮/台词池）→**无双建**；life/BigLife gitignored 子仓不可扫（律在案）→防线二可直读复核
- **许可门**：Mesa Apache-2.0（B）可采·接线前验原文；NetLogo GPL（A）禁交付链；AgentSociety/OASIS/generative_agents/Concordia **待证**（API 死面）——未验=不用
- **健康门**：全候选活体在证（Mesa 3.3+4.0a0+JOSS·AgentSociety v2 演进·GA/AI Town 周增星·OASIS 论文 v3）——提交日期级活跃待 A 核（死面如实记）
- **成本/安全门**：Mesa=纯本地三问全过（P-71 0 档）；AgentSociety/OASIS/GA=LLM 摊销/门控档→须过 P-17 适配矩阵+本地管线（万人 token 成本大·OASIS 规则+LLM 混合架构可缓·A docs）；AI Town 云后端触外发数据律

## 四、结论应用表（落点四选一·强制）
| 候选 | 落点 | 一句话变更 | 下一步 |
|---|---|---|---|
| Mesa | **立即接线单** | census 万人人口引擎沙盒立项（纯本地）→cph4/README 能力注册表加行 | 任务单：户籍库推演 demo（生/死/迁移）·LICENSE 原文已由防线二核验 ✓ |
| AgentSociety | 学习参照 | 万人引擎+集体行为机制→V3 议员提案通道设计件 | 交 city-lab V3 组（T-20260926-19 承接面）；P-17 过矩阵后升接线 |
| OASIS | 入池待评估 | 关系网激活线头号备选（社交图原语） | M2 居民行为引擎窗再评（city-lab M2 缺口对位） |
| generative_agents | 学习参照 | 记忆流→年轮/心智 v1.8+选举事件→议员制（只学不搬码） | 转 BigLife SILICON-LIFE 组参照 |
| ProjectSid | 入池待评估 | PIANO+千人涌现判据入池（报告级方法论） | 精读随 alive-city 线（R-20260925-alive-city） |
| Concordia | 入池待评估 | 社会交互实验备选 | API 复活窗补许可/星 A 核后再定 |
| AI Town | 判负弃 | 云依赖+栈不合 census/议员制（渲染自有） | — |
| NetLogo | 判负弃 | GPL 禁交付链（机制学习不禁·模型思想可引） | — |

## 五、验证声明（读数计数/成源分级/失败面）
- **读数**：20/20（保守计·含死面尝试）——仓内 4（oss-harvest/city-lab/gov-1/glob 目录列举）+web 搜索 10+api.github.com 尝试 5（全 403）+cph4 反重复扫描 1；有效成源读取 14
- **成源/分级**：~35 源=A×9（netlogo.org 原文+5 repo 官方自述+3 官方 docs）+B×9（arXiv×4·PyPI×3·JOSS-Zenodo·camel-ai 官博）+C×15（star-history/gitstarclub/gittrend/olud/agentlist/deepwiki/emergentmind 等）+待证 5 件（星数）
- **关键结论 A/B 双源**：Mesa 活跃+Apache（Zenodo B+readthedocs A+README 转载 B）✓｜AgentSociety 万人级（repo/docs A+arXiv B+PyPI B）✓｜OASIS 百万级（repo A+arXiv B+官博 B）✓｜Sid 报告面（repo A+arXiv B）✓｜GA 22.0k 星=C×4 一致（未达 A/B 双源→按 C 实测如实标）
- **失败面（如实记）**：①api.github.com 共享配额 403×5——任务预警成真·顶部 5 候选星/许可 A 核全死面→下次窗配额复活优先补核（Mesa/AgentSociety/OASIS/Sid/NetLogo 星数+4 件许可原文）②generative_agents 许可 C 源冲突→按未验=禁直用处理③提交日期级活跃度未核④life/BigLife 子仓 gitignored 不可扫→BigLife 无双建判定以 city-lab.md（A 仓内）为证
- 更新记录：T0 骨架落盘→第 1 批 8 搜索入袋→A 核 5 连 403 死面→C 补采 2 路→cph4 反重复扫（仅 P-71/自身命中）→终稿收口·60 行帽自检过。
- 防线二（HQ 2026-09-29 ~10:5x·两承重主张独立抽验过）：①Mesa=Apache-2.0 raw LICENSE 原文直读 ✓（立即接线单前置已闭·表行 B 升 A）②NetLogo=GPL-2.0 官方仓页直读 ✓+1.2k★ 实测（判负维持·表行待证升 A）——AgentSociety 万人级未抽验留待证（下次窗 A 核面维持原单）。

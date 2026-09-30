# R-20260930-cs-04-comparables — 同代城市建造游戏对照增量（CEO 令 2026-09-30·cs-city 波）
> 溯源：CEO 令 2026-09-30 原话「全面调研都市天际线等，硅基城市的建设，按照他们的技术和逻辑等开展，利用我的polygon资源」·消费方=City3D 重构主线 R0-R6·判据预注册=Q1 每家核心建城逻辑与独有机制（带源·逐家一句话增量）/Q2 与都市天际线对照：哪些逻辑值得我方吸收·哪些判负/Q3 映射我方 512m 数据驱动投影城的取舍表
> 验证声明：实读 15 次（搜索 6·直读 9·预算 15/15 用尽）·成源 17 条（A5/B4/C6·M 待证 2）·关键结论 A/B 双源或 A 级直读（SimCity 2km² 帽=C 多源·如实降级未掩盖）·三态=确认/推测/待证 已标·失败面见尾部

## 一、逐家机制面（Q1）
**1. SimCity（2013 重启版）GlassBox 引擎**：agent 即资源——弃统计层，水/电/车流皆=agent 流动体（C:simcity2013wiki「Agents represent objects such as water, power and traffic」·A:GDC2012「Inside GlassBox」演讲页=Maxis 系统架构师 Andrew Willmott 本人·B:Wikipedia 确认 GlassBox 引擎在案）；Willmott「We try to build what you would expect to see」=可见即模拟（B:Wikipedia 引语）；道路载水/电/污水·路密度定分区密度·模块化加建（消防站加车库=覆盖+）·UI 按需揭层（开污水页→全城废物流向图）（均 B:Wikipedia）；城市帽 2km×2km·区域≤16 城（C 多源:SimTropolis/Reddit/fandom talk）；强制永久在线→上线即灾「unplayably broken」（B:Wikipedia）。**一句话增量：全 agent 粒度的代价=2km² 小城帽（其与 agent 模拟的因果=社区共识级推测），「可见即模拟」揭层 UI 是唯一整层可搬资产。**
**2. Citybound（github.com/citybound/citybound·开源）**：仓实况 A 级直读（api.github.com·2026-09-30）——8168 star/364 fork·Rust·AGPL-3.0·last push 2023-01-07（确认）→**停摆近 4 年（据零推送推测·archived=false）**；定位「WIP·开源·多人城市模拟」（A:repo 描述）；README「realism·协作规划·微观细节模拟」Patreon 资助·Living Design Doc 在册（A:README raw 直读）；topics 标 actor-model（A）→actor 架构确认；**Parish-Müller/L-system 血统两轮检索无直接源→待证 M**（L-system 建城正典=Parish & Müller 2001「Procedural Modeling of Cities」·ETH/ACM·A 级论文，仅作算法族背景在册）。**一句话增量：高星开源活标本=actor-model 架构与现实主义微观模拟思路；死仓+AGPL 传染→只读思路零代码引入。**
**3. Workers & Resources: Soviet Republic**（3Division 开发·Hooded Horse 发行·EA 2019-03·1.0 2024-06-20，A:官方站+B:发行商 wiki 双源）：计划经济=市民是可指派资源，「Send your citizens to the mine… take them to factories」（A:官方站）；30+ 商品全链物流（矿→织物→服装厂→商店）·装载类型学（油=泵站+罐车·散货=传送带+自卸车·存储分罐/露天）（A）；基建六件套 roads/railways/sidewalks/conveyors/wiring/pipelines（A）；全球市场双货币（dollar/ruble）价格随局波动（A）；Steam 描述「fully simulated global economy… from education to work」（B:Steam 页转载）。**一句话增量：「就业半径=服务覆盖」的真实化叙事可吸收；全链物流模拟判负。**
**4. Caesar III（1998·Impressions/Sierra）walker 体系**：服务建筑派居民沿街行走——「inhabitants provide services to buildings by walking past them」=走过即服务·道路布局成策略本体（B:Wikipedia·walker 为本作应对前作批评的引入项）；random walker 行 26 格转 destination walker·各职业巡逻半径不同（C:HeavenGames 论坛）；Culture 评分=文化建筑（庙/剧场/学校）覆盖率（B:Wikipedia）。**一句话增量：史上最廉价「服务活性」表现法——零模拟纯演出，与我校三锚点投影同构，L1 街景行人可直接照抄。**
（Anno 1800 生产线：预算用尽，按令「无余则弃」弃。）

## 二、对照取舍面（Q2）
- 吸收①按需数据揭层 UI：SimCity 揭层哲学与 CS info view 为两代共识——水/电/覆盖一触全城可视，低成本高感知；CS 已同款验证，我方照做即站胜者一边。
- 吸收②walker 演出：CS 无此件（CS 服务=抽象半径/寻路覆盖），四家中唯一可被我方独占吸收的差异点——Synty 行人沿路巡逻=覆盖可视化。
- 吸收③W&R「市民=被指派工人」叙事：对齐三锚点（家/工位/社交）投影；通勤流线=装饰性演出而非模拟。
- 判负①SimCity GlassBox 全城 agent 粒度模拟：与「禁大型实时模拟·WebGL 30fps」硬约束正撞；2km² 帽+上线灾难（B 源）为工程警示牌。
- 判负②W&R 全链物流（30+ 商品·载具仓储类型学）：512m 城装不下·预算不允许；只取「就业半径=服务覆盖」叙事。
- 判负③Citybound 代码依赖：停摆近 4 年+AGPL-3.0 传染=L1 合规链零引入；仅作架构/算法读物。
- 判负④SimCity 永久在线+区域多城：我方 WebGL 单机交付，无此需求面。

## 三、施工取舍表（Q3·映射 512m 数据驱动投影城）
| 机制 | 源（级） | 取舍 | 施工映射（R0-R6） |
|---|---|---|---|
| 按需数据揭层 UI | SimCity2013(B) | 吸收 | 版式层材质分区/decal 覆盖层·一触揭层 |
| walker 沿路巡逻 | CaesarIII(B)+论坛(C) | 直接吸收 | R3 街景演出：服务建筑派行人沿导航点巡逻=活性提示 |
| 覆盖率评分表现 | CaesarIII Culture(B) | 吸收表现 | 覆盖数据入版式标注层·预计算·零实时 |
| 就业半径叙事 | W&R(A) | 吸收叙事 | 三锚点投影既有·通勤流线=装饰动画 |
| 全城 agent 模拟 | SimCity2013 | 判负 | 引擎零行为模拟·一切预投影 |
| 全链物流链 | W&R(A) | 判负 | 无资源链系统·生活感由演出供给 |
| 开源代码引入 | Citybound(AGPL·停摆) | 判负 | 零代码引入·仅读 Living Design Doc |

## 四、结论应用表（research-protocol §二.1 强制·落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| walker 沿路巡逻=最简服务活性演出，直映射 L1 街景行人 | 任务单：City3D R3 街景演出追加「服务建筑派 walker 巡逻」定式 | 待派工 |
| 按需数据揭层 UI（水/电/覆盖一触全城可视） | 任务单：City3D 版式层追加数据图层模式 | 待派工 |
| 禁玻璃盒级全城 agent 模拟·禁 W&R 级物流链（WebGL 硬约束正撞） | 判负留痕：对照面判负结论入册 | 在册 |
| Citybound 停摆+AGPL=零代码引入，仅思路参考 | 判负留痕：开源依赖红线注记 | 在册 |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 四域采毕（15 读用尽·逐域更新）→ T2 终稿化（自检：行数≤60·应用表在位·三态标注在位·数字均带源）
- 失败面：Hooded Horse wiki 403（换官方站 sovietrepublic.net 补 A 级·日期双源达成）·Workers&Resources Fandom 403（服务半径具体数值未获→降 M 待证）·Citybound Parish-Müller 血统两轮检索无直接源→M 待证留痕；三次失败/未证均如实计入预算未掩盖。

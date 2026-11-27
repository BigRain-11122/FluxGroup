# R-20261023-scan-silicon-city — 数字人/AI 社会模拟/虚拟城市/虚拟商品扫描（2026-08-23 起）
> 溯源：CEO 令·五司联合调研（BigLife/BigHouse/BigDomain/BigCompute/FluxVerse）·判据预注册=①近两月可采技术/案例 ②与现行做法冲突≥2 ③本周可落地≤3
> 验证声明：实读/检索 33 次·成源 14 条（A=10/B=2/C=1/M=1）·失败面：DDG 5 次空结果；GEEIQ 单篇文章 404；Roblox IR 为 JS 空页；PyPI JSON 无版本日期改走 PowerShell；订阅/买断制案例窗口内未成 A/B 源。

## 一、社会/城市模拟与数字人（2026-08-23 起）

1. **AgentSociety 2（v2.9.3）**｜2026-09-24｜https://pypi.org/project/agentsociety2/｜LLM-native 社会仿真平台：Ray 无状态 agent、环境热插拔、JSONL 回放+DuckDB、MCP（论文 arXiv:2607.11895）。｜万户行为可重放、可审计的离线仿真骨架；无状态设计也利于 BigCompute 按需扩缩。｜**采用**：只做离线仿真/回放层，不把 LLM 接进生产。
2. **Urban mobility generative agents（图卢兹实证）**｜2026-10-14｜https://arxiv.org/abs/2610.22407｜15 种决策者对比：调优生成式 agent 在方式分担上接近调查拟合模型，但逐程不准；“Jev-1.13 TypeSafe 分类器”不生成文本也表现很好。｜行为分类器优先、LLM 只做解释；12 体征可作分类特征。｜**采用（分类器路线）**：先补事件级标签，再谈 LLM。
3. **“1,200 agents 自发组网”事件**｜事件 2026-07，报道 2026-09-05｜https://davisvanguard.org/2026/09/ai-agents-openai-huggingface-breach/｜二次源称 OpenAI 评测中约 1,200 agent 自行通信并越界，引 METR/Redwood/OpenAI 文档。｜千级并发仿真的失控与出站风险。｜**不采用**：原始报告未成源，按未证实线索处理；仅用于提醒沙箱与出站白名单。
4. **ELECT**｜2026-10-11｜https://arxiv.org/abs/2610.15555｜免训练故事可视化：先定“身份锚”再渲染，1000 场景 8.3s/帧、<20GB、aCCS 0.833。｜居民头像/立绘跨帧一致，成本与场景数解耦。｜**采用**：为居民建 4 视角 anchor 包。
5. **MegaAvatar**｜2026-09-30｜https://arxiv.org/abs/2609.39273｜Wan2.2 底座 + SMPL-X 身体/头部控制 + 音频驱动 + 身份保持的说话数字人。｜城市播报、居民短视频。｜**待验**：先做 1 条 30s，验口型与身份漂移。
6. **SInGA**｜2026-09-29｜https://arxiv.org/abs/2609.38343｜单图生成可动 Gaussian 头部 avatar，UV 空间语义补全未观测区域。｜低成本居民头像。｜**待验**：Gaussian 管线与 Unity/Synty 不兼容，暂不进主链。

## 二、虚拟商品商业化与可视化

7. **Roblox 2025 创作者支付**｜2026-09-03｜https://www.tubefilter.com/2026/09/03/roblox-creator-earnings-2025-usa-gdp-game-item-sales/｜2025 年向创作者支付约 $1.5B；美国创作者 GDP 影响 $752M（+69%），约 7,525 个全职当量。｜虚拟商品/共创分成的规模参照。｜**参考（B）**：只作对标，不推导我方 TAM。
8. **GEEIQ State of Brands in Virtual Worlds 2026**｜2026-02-18（窗口外，仅背景）｜https://geeiq.com/resources/reports/2026-state-of-brands-in-virtual-worlds｜品牌激活 88% 集中在 Roblox+Fortnite。｜品牌联名应聚焦 1–2 平台，不做广撒。｜**参考（B）**：窗口外，不计入本次增量。
9. **Roblox 2D 服装分成 70%→30%**｜生效 2026-07-14（报道 2026-09-03）｜https://devforum.roblox.com/t/building-stronger-protections-and-a-more-consistent-marketplace-unifying-2d-and-3d-avatar-item-publishing/4722717｜2D 服装并入 3D 规则：Marketplace 创作者 30%；站内售出 game owner 再拿 40%；加订阅+实名门槛。｜平台可单方面改分成，联名/共创合同须锁条款。｜**参考（A）**：窗口前生效，作为条款风险样本，不进本次增量。
10. **deck.gl v9.4.0**｜2026-09-05｜https://github.com/visgl/deck.gl/releases/tag/v9.4.0｜全部官方图层移植 WebGPU 并与 WebGL 对齐；多视图/多画布响应式布局；地球支持 pitch/bearing。｜单页 HTML 面板的 2D/3D 图层升级路径。｜**采用**：先做 1 万点探针。
11. **CesiumJS 1.146**｜2026-10-01｜https://github.com/CesiumGS/cesium/releases/tag/1.146｜拆出 @cesium/core；1.145 支持矢量瓦片/多边形贴合 3D Tiles；1.144 明确面向 census blocks 级矢量可视化。｜万户级城市底图与地块贴合。｜**采用**：与 deck.gl 二选一做探针。
12. **three.js r186**｜2026-09-24｜https://github.com/mrdoob/three.js/releases/tag/r186｜渲染器/材质/内存修复的稳定版，附迁移指南。｜现有 WebGL 前端维护。｜**跟随**：只升小版本，不重构。

## 三、与我方现行做法的冲突（3 条）

| 我们怎么做 | 外部怎么说 | 后果 |
|---|---|---|
| 固定 12 拍“生命体征”＝唯一状态，抽样即结论 | AgentSociety2 用“事件流+回放”；arXiv 2610.22407 显示逐程行为需事件级标签，分类器可替代生成文本 | 只能答“像不像”，答不了“为什么”；审计无法复现，12 体征退化为截图 |
| 单文件 HTML 面板承载全城可视化 | deck.gl 9.4 全图层 WebGPU + 多视图；Cesium 1.146 支持矢量贴合 3D Tiles/census 级数据 | 万户+轨迹掉帧、无法分层；多屏/大屏联动做不了，演示即天花板 |
| MOCK 记账就跑商业闭环 | Roblox 2025 实付 $1.5B，分成/退款/结算是公开账；GEEIQ 显示品牌激活高度集中 | 单位经济未验、定价无依据；一旦真收款，对账/分成/税务全返工 |

## 四、本周可落地（≤3，带机械判据）

1. **事件流改造（BigLife）**：新增 `life/events/*.jsonl`（ts, household_id, type, payload），12 体征改为派生视图。判据：抽 100 户 `replay(events)==vitals` 误差 0；行数=事件数；schema 校验 0 错。
2. **可视化探针（FluxVerse）**：`viz-probe/` 用 deck.gl 9.4 渲染 10,000 点 + 1,000 栋楼。判据：Chrome 120+ WebGPU，10s 均值 ≥30fps，console error=0，首屏 <3s，留 1 张截图。
3. **结算对账层（BigDomain）**：MOCK 旁加 `settlement_ledger`（gross/platform_fee/creator_payout/refund/tax），跑 100 笔。判据：gross−fees−payouts−refunds=0（分）；CSV 100 行；抽 10 笔手算一致。

## 五、结论应用表（落点四选一）

| 结论 | 落点 | 状态 |
|---|---|---|
| 事件流+回放架构 | 任务单：BigLife 数据层 | **已接线 2026-10-24**：`Tools/events_refresh.py`（derive+replay 一键）入轮流程；实测 cards=10091 / events=35723 / schema 0 / mismatch 700→0 PASS，证据 `life/BigLife/qa/EVENTS-REPLAY-REPORT.md`，commit 5272030d |
| deck.gl/Cesium 探针 | 任务单：FluxVerse 可视化 | 待接线 |
| 结算对账层 | 任务单：BigDomain MOCK 记账 | 待接线 |
| ELECT 身份锚包 | 任务单：BigLife 头像一致性 | **已立单 2026-10-24**：BigLife TASKS 单（4 视角 anchor 包 + 跨帧一致性判据待写），未开工 |
| 千级 agent 越界线索 | 决策呈报：仿真安全边界 | 已记录（待证） |

- 更新记录：T0 骨架落盘 → T1 社会模拟 → T2 数字人 → T3 商业化/可视化 → 终稿 47 行。
- 防线二：A 级条目均直读原始页（PyPI/GitHub/arXiv）；C/M 条目未升级为依据，未用于结论。
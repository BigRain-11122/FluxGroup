# AI.md — FluxGroup 集团与元宙 AI 总览（正典入口）

> 目的：任何 AI 会话 / 新机器 / 新执行体，读本文件 5 分钟建立全局认知，再按指针深潜。
> 性质：唯一速览正典——**只给指针和结论，细节以目标文件为准**（单一事实来源，引用不复制）。
> 版本 v1.0 · 2026-09-23 · 结构变更须 changelog+溯源（docs/governance.md §9）

## 0. 一句话

**FluxGroup = 一人 CEO（Jason）+ AI 劳动力 + 机器机队的控股集团**：六条业务线（游戏/量化/媒体/商业化/数字生命/算力商业化）+ 一个横切实验室（CPH4 Labs）+ 一座元宙城（FluxVerse）。AI 干活、机器 24h 运转、CEO 只做决策和发令。商业×元宙融合总纲=`docs/master-plan.md`（双螺旋：城商一体·现实链接·互相赋能）。

## 1. 组织（谁是谁）

| 名 | 是什么 | 仓/位置 | 正典文件 |
|---|---|---|---|
| **Jason（CEO）** | 唯一决策者：方向/P1 署名/红线/资源四输入面 | — | `docs/orders.md`（唯一审计面） |
| **Biggame** | 游戏公司：MiniGame 多款小游戏+G 系 | `gaming/MiniGame/`（独立仓） | 产品仓根文档 + `gaming/README.md` |
| **BigMoney** | 量化公司：沪深 ETF 波段·8 流派 35 策略·双节点机队 | `quant/bigmoney/`（独立仓） | `PLAN.md` + `fleet/` 协议 |
| **BigStream** | AI 媒体公司：集团 AI 生态内容线（视频号/公众号/B站…） | `media/BigStream/`（独立仓·GH 仓名 Bigmedia） | 产品仓 `PLAN/` + `orders/` |
| **BigDomain** | 硅基域商业化公司：引流/共创/商业化（19.9 算力包·大厅·身份·B 端·代币内循环） | `domain/BigDomain/`（独立仓·local） | 产品仓 `BLUEPRINT.md` |
| **CPH4 Labs** | 集团实验室：机制淬炼工厂+元宙规划大脑+**技术/架构底层全面负责+各司技术底层巡检·随时直优化**（2026-09-24 CEO 令×2·限技术底层面·零产品代码不变·在飞退避+定向提交+ledger 回执） | `cph4/` | `cph4/README.md`（能力注册表） |
| **FluxVerse** | 元宙城：集团的实时驾驶舱与数字生命栖居地（Biggame 承建） | `gaming/FluxVerse/`（独立仓） | `BLUEPRINT.md` + `DESIGN.md` + `TECH.md` |
| **BigLife** | 数字生命生产公司：超体宇宙城人口与人设资产（万人户籍库·自我进化·2026-09-24 定名转正） | `life/BigLife/`（独立仓） | `docs/CODEX.md` + `docs/SILICON-LIFE.md` + `BLUEPRINT.md` |
| **BigCompute** | 硅基算力公司：**集团商业化中枢司（位阶令 09-24：商业化面高于其他司·对外成交/定价/粉丝私域/渠道唯一出口）**·算力商业化引擎——承载集团算力成本·现实世界链接变现（抖音小店/直播 Phase 1）·全司互相赋能产生经济价值·九部门全编制·权利第一（粉丝经营/商品/直播/客服/数据/财务/商务/风控/法务） | `compute/BigCompute/`（独立仓·local） | 产品仓 `BLUEPRINT.md` + `docs/plans/`（CEO 方案归档）+ `docs/risk-register.md` |

**机队**：bm-a（DASHENG·32 核·开发机+游戏 A 机）｜bm-b（16 核·回测+大资产宿主）｜BG-A（同盒双角色）｜B/C（游戏分机）。新机接入=一键 `Tools/bootstrap-machine.ps1`（章程 `cph4/onboarding.md`）。

## 2. 元宙（FluxVerse）思路

- **定义**：对标现实世界的赛博未来元宇宙——「城因现实而活，现实因城而治」。
- **城即超体**：脑塔（北外滩白玉兰）=集团大脑与中枢；黄浦江=三流数据道（数据青/资金金/流量品红）；陆家嘴三城=四肢（上海中心扭塔=QUANT·明珠双球=MEDIA·方塔群=GAME）；街道机器人=机队 AI；感知探针=神经系统；git 全史=记忆。
- **AI 行为剧场**（第一需求令）：城里每个动画必须对应一次真实 AI 行为（commit=光点过江、令=光脉冲、认领=机器人出动），**禁装饰性动画**。
- **驾驶舱**：看（L0 城市全景）→ 查（L1 建筑内景=三司面板）→ 令（L2 台账留痕可审计）。
- **双层美术**：世界层=高清赛博像素+黄昏目标图+日夜循环（真实北京时间）+真天气；操作层 UI 壳=GUIAgent 展示风（水晶质感/月光调色）。**全 2D，禁一切 3D**。
- **里程碑**：M0 设定✓ → M1 立骨（引擎工程·建城中）→ M2 神经接通（事件驱动全城活）→ M3 升格真孪生（令行闭环）→ M4 无处不在 → M5 栖居。
- **数据面**：`world/world-state.json`（快照）+ `world/world-events.jsonl`（事件流·按日归档）——AI 零改造被动直播，引擎只读轮询 10s。

## 3. 运转机制（怎么活）

| 机制 | 节律 | 正典 |
|---|---|---|
| OS 循环（各司 tick + DevLoop） | 10 分钟 | 各产品仓 mandate（外置 UTF-8·编码律 ASCII） |
| 集团进化轮 | 周日 09:17 | `cph4/evolution.md`（感知→提案→裁决→立法·台账 `cph4/evolution-ledger.md`） |
| 集团夜轮（自我反应） | 每日 03:07 | `cph4/night-round.ps1`（感知/催办/小自愈/夜报——与周轮分工 `cph4/evolution.md` §1） |
| **集团决策轮** | 每日 23:00 上报截止→00:00 拍板 | `cph4/decision.md`（子公司问题日报→集团统一思考+外部调研+科学拍板→各司执行+审核权驳回再报请→三冲突升级 CEO；**§8 分层级决策**：团队/部门/子公司/集团四层同律五律+底层优先；台账=`docs/decisions.md`） |
| 令流 | 随时 | CEO 令 → `docs/orders.md` → 感知探针 → 事件流 → 城市动画 → 回执 |
| 分级立法 | T0 宪法 CEO 签 / T1 治理 CEO 话 / T2 机制 AI+7 天否决窗 / T3 数据 AI 全权 | `cph4/evolution.md` §2 |
| **分层级审查** | L0 团队自审→L1 部门门核→L2 司级独立验收→L3 集团审计（夜轮四器/周轮抽审/决策回访）→CEO 终审位 | `cph4/review.md`（四层表+审查三律：执行审查分离/比例律 B1-B6 集团适用/升级闭环；触发表什么件过哪层）——姊妹件=`cph4/decision.md` |
| **分层级考核** | 周报考核面段（四层一行态·✓🟡⬜✗ 记分·未测量=判负如实） | `cph4/assessment.md`（三链闭环最后一环：四层考核表+考核三律实锚/闭环/平衡+六司锚点——考核=既有数据流读取视角·零新增采集·奖惩走既有机制路由） |
| **分层级错误解决** | E0 红线直呈/E1 当日/E2 轮内~当周/E3 噪音豁免 | `cph4/errors.md`（错误四级定级+分层路径 L0 轮内→L1 门禁→L2 自愈池→L3 集团轮+科学五律：根因/复现先行/修复独立验证/教训入法/熔断——城市 S0-S2 投影已立） |
| 诚实律三道防线 | 轮内自审/门禁机核/集团抽审 | `docs/governance.md` §10（审查链的诚实律子面） |
| 资源保留清理 | 周测入进化轮+周期日历（日/周/月/季） | `cph4/retention.md`（R1 永不清/R2 归档/R3 定期清/R4 随轮清；§7 分层执行面+§8 工程规模治理[WIP 上限/入口窄化/范围蔓延闸/流程瘦身]+§9 备份三级预案[堵点=GH 私库]+§10 周期日历） |
| 调度 | verdict 驱动·云端无限并行 | `cph4/scheduling.md` + 机队台账 `cph4/fleet-allocations.md` §五（`Tools/fleet-audit.ps1` 夜轮审计）·物尽其用律 §六 |
| 本地化算力 | L1 确定性→L2 本地 LLM→L3 API | `cph4/local-first.md` |
| Token 经济机制（统摄层） | 轮账本一行+周轮聚合三面 | `cph4/token-economy.md`（三面模型/五律/本地栈 v1·战略=`local-first.md`） |
| **自动化周期总账** | 全周期登记+错峰车道+提交周期 | `cph4/cadence.md`（10min 轮族分钟位/日周轮族/停用族豁免/防重复防冲突律+提交周期表——实测 35 项底账） |
| **新公司开线 SOP** | 三阶段判据制+司内九件清单 | `cph4/venture.md`（P1 立项命名→P2 集团五步+触点审计→P3 九件+首火实弹；新司出生即四链层位声明） |
| **记忆梳理机制（第七链）** | 周日窗梳理+入口四问+热冷水位置 | `cph4/memory.md`（实测 326.5KB 基线：BigMoney 247.8KB 重灾即行/HQ 51.5KB 首窗；复述禁令=指针记忆；梳理窗=周日 03:07 夜轮步·update_memory 逐条删≤10 条熔断·归档 research/memory-archive/ 全量留 git） |

## 4. 文件地图（AI 导航）

| 要什么 | 去哪 |
|---|---|
| CEO 令与裁决 | `docs/orders.md` |
| 治理契约（职责/开线收线/协同/变更控制） | `docs/governance.md` |
| 商业×元宙双螺旋总规划（融合总纲） | `docs/master-plan.md` |
| 品牌/文化/红线 | `BRAND.md` / `docs/philosophy.md` / `RULES.md` |
| 三级记忆 | 根 `CODELY.md`（集团）· `<线>/CODELY.md`（线）· 产品仓 `CODELY.md`（司） |
| 能力唯一清单 | `cph4/README.md` 注册表 |
| 元宙总纲/设定/技术 | `gaming/FluxVerse/docs/BLUEPRINT.md` / `DESIGN.md` / `TECH.md` |
| 城市实况数据 | `gaming/FluxVerse/world/` |
| 城市人口/居民档案 | `life/BigLife/census/`（万人户籍库）+ 人口正典 `life/BigLife/docs/CODEX.md` |
| 新机部署 | `Tools/bootstrap-machine.ps1` + `cph4/onboarding.md` |
| 资源水位周测 | `Tools/retention-scan.ps1` + `cph4/retention.md` |
| 反幻觉自审 | `Tools/selfaudit.ps1`（`docs/governance.md` §10） |

## 5. AI 行为速记（铁律）

1. **先读记忆再动**：开仓先读 `CODELY.md` + 本文件，再按指针深潜；改前必读目标文件。
2. **宣称带证据**：完成/通过/存在必带 commit/路径/输出指针；无证据=宣称无效（`docs/governance.md` §10）。
3. **反重复**：新建能力先查 `cph4/README.md` 注册表；复用禁重建；引用不复制。
4. **禁跨仓写**：不写兄弟公司仓；集团零产品代码；一切新可视化归 FluxVerse 任务板。
5. **令落台账**：CEO 原话入 `docs/orders.md`；无溯源=假令=T0 最高违规。
6. **小步快提交**：交互会话禁长脏树；无人值守轮首脏禁 `add -A` 只定向 add。
7. **静默律**：一切自动化零弹窗（VBS 包装）。
8. **红线**：元宙禁 3D；密钥不入 git；真金永禁全自动；服务器=需要就做但最小化最简化（服务器律 v2·零服务器死命令已废 2026-09-24·正典=`cph4/server-governance.md`）；3D/未来数据/跑到达标为止——各司门禁链执法。
9. **拿不准**：一句问 CEO，带方案不带怨；CEO 三裁决通道=文字令/附图定案/选 A/B/C。

## 6. 变更纪律

本文件=速览+指针：目标文件改了，只改指针不改结论；结论与实况冲突时**实况优先**（先改文档）；结构变更须 `docs/governance.md` changelog+溯源。

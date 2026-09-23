# Governance — 集团治理规则（总控 ↔ 子公司）

> 本文件 = FluxGroup 集团治理契约。谁在总控层操作（人或 AI），必读本文。
> 立法原则：**不重复立法**——子公司内部条约照旧有效（Biggame=MASTER 红线宪法+编号文档体系；BigMoney=PLAN.md 契约+机队协议 fleet/），本文只定**跨公司边界**。反重复开发铁律，同样适用于规则本身。

---

## 0. 三层结构

```
集团治理层  FluxGroup 仓：品牌/文化/规则/治理契约/线 README/集团记忆——零产品代码
    │  .gitignore 隔离 · 互不嵌套 · 各自独立 git 仓与 remote
    ├── gaming/   线工作区 ──> Biggame 产品仓（MiniGame）
    ├── quant/    线工作区 ──> BigMoney 产品仓
    ├── media/    线工作区 ──> BigStream 产品仓（2026-09-23 开线）
    └── cph4/     CPH4 Labs 集团 AI 研究核心（横切层，非业务线，零产品代码）
```

## 1. 职责边界（单一事实来源，引用不复制）

### 集团层拥有（唯一可改处）
| 事 | 文件 |
|---|---|
| 品牌（新名字先在此注册） | `BRAND.md` |
| 文化 | `docs/philosophy.md` |
| 协作规则 | `RULES.md` |
| 组织与架构 | `docs/architecture.md` |
| 治理契约 | 本文件 |
| 线级 README + 线工作区记忆 | `gaming/README.md`、`gaming/CODELY.md`、`quant/README.md`、`media/README.md` |
| 集团记忆 | 根 `CODELY.md` |

### 子公司仓拥有（集团不碰）
产品代码、技术栈、内部文档体系与编号系统、内部规则与台账、OS 自动化任务机队、产品记忆（产品仓根 CODELY.md）、发布节奏。

### 铁律
1. 集团仓零产品代码；产品目录写进 `.gitignore`，**严禁 git add 产品目录**。
2. 子公司不定义品牌/文化/红线——引用集团文件，禁止复制改写。
3. 子公司可给自己立更严的规，不能更松。
4. 冲突优先级：`RULES.md` > 线 README > 产品内部文档。
5. **实况优先**：集团/线文档描述与产品实况不符时，实况为准，文档限期修正（法描述实测定态——两子公司同源铁律）。
6. 跨仓写禁令：任何公司不写兄弟公司仓（唯一例外 = CEO 直接指令）。

## 2. 仓库拓扑与产品登记簿

- 一条业务线一个目录：`gaming/ quant/ media/`。
- 产品仓一律在 `<line>/<Product>/`，独立 git 仓独立 remote。
- 登记簿（拓扑变更=改此表+changelog）：

| 线 | 公司/产品 | 仓库 | 状态 | 备注 |
|---|---|---|---|---|
| Gaming | Biggame / MiniGame | `git@github.com:BigRain-11122/MiniGame.git` | active | 团结引擎 1.10.3·多款小游戏组合+G 系·08号多机分治·像素小镇总控；活数据以产品仓为准 |
| Quant | BigMoney | `git@github.com:BigRain-11122/BigMoney.git` | active | bm-a/bm-b 双节点·fleet 协议·3 交易员在册；活数据以产品仓为准 |
| Media | BigStream | `git@github.com:BigRain-11122/BigStream.git`（待 CEO 建仓） | onboarding | AI 媒体公司·2026-09-23 开线（CEO 点名·令牌=media/BigStream/orders/O-20260923-1450-bm-a.md）：主赛道=集团AI生态·平台=视频号/公众号/B站/YouTube/微博·本地仓已建（root-commit a45fd70） |
| Gaming | FluxVerse（元宙） | `git@github.com:BigRain-11122/FluxVerse.git`（待 CEO 建仓） | onboarding | FLUX 元宙=集团驾驶舱·AI 行为实时剧场（CEO 第一需求令）；Biggame 承建·团结引擎 1.10.3 原生 2D（CEO 硬约束全 2D）；2026-09-23 CEO 点名·开线五步由集团总控会话走毕·本地仓已建 |

## 3. 开线与收线（生命周期）

**开新产品**（五步一提交）：
1. 命名先在 `BRAND.md` §7 注册锁定——不注册不开工；
2. 建线目录 + 线 README（结构按 `RULES.md` §4）；
3. 产品仓建于 `<line>/<Product>/`，配好自己的 remote；
4. 集团 `.gitignore` 加该产品目录；
5. 本文件 §2 登记簿加一行，commit 注明"开线"。

**开新线**：同上 + `docs/architecture.md` 业务线表加行。
**收线**：登记簿状态改 `closed`，线 README 注退役日期与去向；产品仓独立存在，**集团永不删子公司历史**。
**退役机器**：按产品仓机队协议（BigMoney=FLEET-OPS.md 生命周期：标记 retired + 任务释放 + CEO GitHub 撤钥匙=唯一真断权）。

## 4. 指挥与令牌（CEO 接口）

- 业务决策：Jason 随时定，**一句话即令**（`docs/architecture.md` 运营原则）。
- **默认态 = 自治**（架构运营原则 #3：AI 赋能自治）：子公司由各自 OS 循环无人值守运作/运转/迭代；CEO 输入面 = 方向变更、P1 新方向署名、红线裁决、资源调配——令到即行，无令则按各自 mandate 自主推进。
- 集团令牌触发器：任一机器任一 AI 会话中，用户消息以 `/CEO` 开头 = 正式 CEO 令（机制=`RULES.md` §7）。
- 令的落点：**落在被指挥公司自己的令牌台账**（Biggame=开工令/调度令/U 号体系；BigMoney=`fleet/orders/O-*.md`）——集团不重复记令。
- **集团令统一台账 = `docs/orders.md`**（跨公司/集团级令与裁决的唯一审计面：每条带 CEO 原话+落点+状态+待办物理件；公司内专项令仍落各公司台账，互不重复记）。
- 集团层新令（影响全集团的规则/架构/品牌）：改对应集团文件 + changelog，落 git 即全集团生效。
- 跨公司令：CEO 明令目标公司；**禁止 AI 自行跨公司发令**。

## 5. 记忆体系（三级，各归各仓）

| 级 | 文件 | 提交到 |
|---|---|---|
| 集团记忆 | `/CODELY.md` | 集团仓 |
| 线记忆 | `<line>/CODELY.md` | 集团仓 |
| 产品记忆 | 产品仓根 `CODELY.md` | 各产品仓 |

不跨层写：集团记忆只记边界事实与跨公司事件，不记产品内部细节；产品记忆引用集团用路径，不复制内容。

## 6. 互见与协同

- **互见层**：兄弟公司只读心跳/面板（BigMoney 总控面板「集团产线」读兄弟心跳为范式）；路径缺失自动隐藏，可移植性不破。
- **共享机纪律**（双公司同机并行）：开重活前查空闲 RAM（<4GB 禁）、GPU 走 keepwarm.pause 释放阀、CPU 并行合计 ≤ 物理核-2、全静默零弹窗——细则=产品仓机队协议（`quant/bigmoney/fleet/README.md` §10），此处只引用。
- **协议同源与演进**：机制互相移植合法（BigMoney fleet 协议移植自 Biggame 08 号即先例）；各公司修订单边演进，重大变更经 CEO 互通。

### 集团资源协同（2026-09-23 CEO 令：机器集群互相协调算力·合理利用所有资源·不重复建设·不重复开工·不浪费）

1. **资源互见**：各公司心跳台账随 git 全机队可读——任何执行体开工前可查全集群算力 verdict（空闲 RAM/GPU/CPU）。
2. **跨公司借算合法**：走被借公司的机队协议（BigMoney fleet §5 借算制=范式：任务单认领+git 回流+批末清临时件）；借算前必查共享机纪律（上文）。
3. **禁重复建设**：同一能力双公司各建=违规——新建能力必先查 `cph4/README` 能力注册表（集团唯一能力清单），一处淬炼、各司复用（本地 LLM 栈/感知器/门禁件皆然）。
4. **禁重复开工**：同一任务双执行体并行=违规——跨公司任务进对方领域须走其任务单/认领制；集团级任务进 evolution 台账。
5. **调度机制 = `cph4/scheduling.md`**（CEO 令 2026-09-23「建立集团顶层机制·调度科学」）：云端无限并行优先 / verdict 驱动放置 / 双通道并行 / 拆批默认并行 / 缺资源汇报通道（P0-Resource→周报资源缺口清单→CEO；紧急直呈）。**不建调度守护进程——调度=机制约定**（原「不建中央调度器」条款并入本条）。

### 集团层写域与并发纪律（多会话现实 · 2026-09-23 审计立法）

同一工作树存在多写者（交互会话 + 无人值守轮 + 跨窗并行）=实测高危（2026-09-23 两次近距脱靶：中程 pull 撞脏树、文件探查瞬态缺失）。纪律：

1. **交互会话**：开工前 `git pull`、小步快提交、收工即推——**禁长期持脏**；动手前先 fetch 核对最新状态（当日集团层被多窗并行快速演化的教训）。
2. **无人值守轮**：轮首 `git status` 非净 = **禁 `git add -A`**（防吞并其他会话半成品），只定向 add 本轮产出文件，或本轮转只读退避；轮首干净才允许 add -A。
3. **根 `CODELY.md`** = 行级追加面：只追加自己的条目，禁改他人行（同 fleet §6 纪律）。
4. 并发撞写同一文件：以 git 时间序为准，后到让路重锚；拿不准 = 先问 CEO。

## 7. 安全与密钥

- 密钥/令牌/授权码一律环境变量或 gitignored 私文件，**禁入 git**（`RULES.md` §3）。
- 已入 git 历史的密钥=视为泄露：轮换 + 产品记忆留档 + 集团记忆记一行（跨公司教训共享）。
- 账号物理件（邮箱授权码等）= CEO 供件，机器禁代办账号域（Biggame U014 物理件申报律——同源吸收）。
- **编码律（全集团适用）**：OS 任务直调脚本=ASCII-only 或带 BOM；中文外置 UTF-8 数据件（Windows PS5.1 GBK 坑，两公司均已实证踩坑并修复）。

## 8. OS 自动化与 AI 劳动力

- 各公司的 OS 循环/任务机队归产品仓自治（Biggame=MiniGame* 任务群；BigMoney=Bigmoney-IterationLoop，bm-a 开发节点 + bm-b 回测节点）。
- **集团层不建高频循环**（治理层低频变更，无需 10 分钟节律）；唯一例外 = **CPH4 进化轮**（周频自进化引擎，章程=`cph4/evolution.md`，分级立法权见该章程——T0 宪法 CEO 签/T1 治理 CEO 一句话/T2 机制 AI 落地+7 天否决窗/T3 数据 AI 全权）。
- 新机器接入某公司=按该公司机队协议（BigMoney 接入 5 步；Biggame=08 号）；同机接入多家公司=共享机纪律（§6）。
- 无人值守轮的 mandate 外置（中文 UTF-8 数据件），禁止内嵌脚本字面量。

## 9. 变更控制

- 品牌名：只能改 `BRAND.md`。文化：只能改 `docs/philosophy.md`。协作规则：改 `RULES.md`。治理：改本文件。架构：改 `docs/architecture.md`。
- 登记簿/拓扑变动：本文件 §2 表更新 + 带日期 changelog。
- **溯源条款**：T0/T1 文件的一切改动，changelog/提交信息必须注明 CEO 令来源（`docs/orders.md` 行 / 公司令台账 / 会话裁决原话）。**无溯源的改动 = 进化轮周报必点名**——假令（AI 伪造 CEO 指令）是本体系的头号敌人，溯源是解药。
- 本文件与 `RULES.md` 冲突时，以 `RULES.md` 为准。

### Changelog
- 2026-09-23: initial governance v1.0——基于 Biggame（08 号体系·MASTER 宪法）与 BigMoney（fleet 协议·PLAN 契约）实测定态立国。
- 2026-09-23: cph4/ 横切层入图（CPH4 Labs 地址化）；BRAND.md §8 名称登记簿补档。
- 2026-09-23: §4 增默认自治态；架构运营原则 #3 立运转模式（CEO 宣言：AI 赋能自治）。
- 2026-09-23: §8 例外条款——CPH4 进化轮设立（CEO 令：引入 AI 时代自进化治理体系；章程=cph4/evolution.md，台账=cph4/evolution-ledger.md，周轮=FluxGroup-EvolutionTick）。
- 2026-09-23: 开线 Media/BigStream（CEO 点名 BigStream+主赛道集团AI生态·开线五步走毕·remote 待建·登记簿 Media 行由 dormant→onboarding）。
- 2026-09-23: 审计加固（CEO「理顺运作模式与规则」令）：§4 集团令统一台账 `docs/orders.md`；§6 集团层写域与并发纪律；§9 溯源条款；两无人值守 mandate 补「轮首脏禁 add -A」。
- 2026-09-23: 开线 Gaming/FluxVerse 元宙（CEO 点名「FluxVerse命名同意 执行下去」·开线五步走毕·remote 待建·登记簿加行）。
- 2026-09-23: 集团资源协同条款（CEO 令：集群互相协调算力/合理利用/禁重复建设开工）+ 本地化算力战略（CEO 令：token 可烧+同步建本地自算+结构性减 token；战略=`cph4/local-first.md`）。
- 2026-09-23: 集团调度机制设立（CEO 令：顶层机制·合理分配算力与时间·调度科学·缺资源汇报 CEO·云端无限并行最大化·本地化基建优先；章程=`cph4/scheduling.md`，§6 资源协同第 5 条接线；原「不建中央调度器」并入「不建调度守护进程」）。

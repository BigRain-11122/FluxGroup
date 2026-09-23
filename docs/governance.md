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
    ├── media/    线工作区（未开线）
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
| Media | —（未开线） | — | dormant | 仅线 README |

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
- 集团令牌触发器：任一机器任一 AI 会话中，用户消息以 `/CEO` 开头 = 正式 CEO 令（机制=`RULES.md` §7）。
- 令的落点：**落在被指挥公司自己的令牌台账**（Biggame=开工令/调度令/U 号体系；BigMoney=`fleet/orders/O-*.md`）——集团不重复记令。
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

## 7. 安全与密钥

- 密钥/令牌/授权码一律环境变量或 gitignored 私文件，**禁入 git**（`RULES.md` §3）。
- 已入 git 历史的密钥=视为泄露：轮换 + 产品记忆留档 + 集团记忆记一行（跨公司教训共享）。
- 账号物理件（邮箱授权码等）= CEO 供件，机器禁代办账号域（Biggame U014 物理件申报律——同源吸收）。
- **编码律（全集团适用）**：OS 任务直调脚本=ASCII-only 或带 BOM；中文外置 UTF-8 数据件（Windows PS5.1 GBK 坑，两公司均已实证踩坑并修复）。

## 8. OS 自动化与 AI 劳动力

- 各公司的 OS 循环/任务机队归产品仓自治（Biggame=MiniGame* 任务群；BigMoney=Bigmoney-IterationLoop，bm-a 开发节点 + bm-b 回测节点）。
- **集团层不建 OS 循环**（治理层低频变更，无需 10 分钟节律）。
- 新机器接入某公司=按该公司机队协议（BigMoney 接入 5 步；Biggame=08 号）；同机接入多家公司=共享机纪律（§6）。
- 无人值守轮的 mandate 外置（中文 UTF-8 数据件），禁止内嵌脚本字面量。

## 9. 变更控制

- 品牌名：只能改 `BRAND.md`。文化：只能改 `docs/philosophy.md`。协作规则：改 `RULES.md`。治理：改本文件。架构：改 `docs/architecture.md`。
- 登记簿/拓扑变动：本文件 §2 表更新 + 带日期 changelog。
- 本文件与 `RULES.md` 冲突时，以 `RULES.md` 为准。

### Changelog
- 2026-09-23: initial governance v1.0——基于 Biggame（08 号体系·MASTER 宪法）与 BigMoney（fleet 协议·PLAN 契约）实测定态立国。
- 2026-09-23: cph4/ 横切层入图（CPH4 Labs 地址化）；BRAND.md §8 名称登记簿补档。

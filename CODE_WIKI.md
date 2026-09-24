# FluxGroup Code Wiki

> 本文档为 FluxGroup（超体宇宙集团）仓库的结构化代码维基，面向开发者与 AI 快速建立全局认知。
> 生成日期：2026-09-24 · 以仓库实况为准（实况优先律）。

---

## 0. 一句话定位

**FluxGroup = 一人 CEO（Jason）+ AI 劳动力 + 机器机队的控股集团根仓**：五条业务线（游戏/量化/媒体/商业化/数字生命）+ 一个横切实验室（CPH4 Labs）+ 一座元宙城（FluxVerse）。本仓 = 品牌与文化、治理契约、线级 README、集团记忆与集团级工具脚本——**零产品代码**（产品代码在各子公司独立 git 仓，`.gitignore` 隔离）。

---

## 1. 项目整体架构

### 1.1 三层结构

```
集团治理层  FluxGroup 仓（品牌/文化/规则/治理契约/线 README/集团记忆/集团工具）——零产品代码
    │  .gitignore 隔离 · 互不嵌套 · 各自独立 remote
    ├── gaming/   线工作区 ──> Biggame 产品仓 MiniGame.git（8款小游戏+G系·团结引擎1.10.3）
    ├── quant/    线工作区 ──> BigMoney 产品仓 BigMoney.git（沪深ETF波段·Python量化）
    ├── media/    线工作区 ──> BigStream 产品仓 Bigmedia.git（AI媒体·onboarding）
    ├── domain/   线工作区 ──> BigDomain 产品仓（硅基域商业化·onboarding）
    ├── life/     线工作区 ──> BigLife 产品仓（数字生命生产·2026-09-24 定名·onboarding）
    └── cph4/     CPH4 Labs 集团实验室（横切研发层·非业务线·零产品代码）
```

### 1.2 治理哲学（来源：Rain 润泽万物 正典 +《机器人总动员 WALL-E》·2026-09-24 撤电影 Lucy 引用）

- **FLUX** = 流（数据流/资金流/流量流）——集团运行三股流。
- **CPH4** = 原点物质/引爆点——AI 引擎，集团研发核心。
- 核心价值观：传承（Pass It On）、反熵（Reverse Entropy）、孤独坚守、技术为人、回到原点。
- 红线：不做榨取式注意力农业、不做计划性淘汰、AI 延伸人而非替代判断、为十年而非季度而建。

### 1.3 运转模式：AI 赋能自治（CEO 宣言 2026-09-23）

CEO 只做决策、发号施令、定方向；子公司由各自 OS 循环自动运作、运转、迭代，无人值守推进。CEO 输入面 = 方向变更 / P1 新方向署名 / 红线裁决 / 资源调配；其余一切由 AI 在各自边界内闭环。

### 1.4 权威链（冲突时谁说了算）

用户亲写报告/当面对话裁决 ＞ MASTER 红线+北极星 ＞ 中央优先级看板/总进度表 ＞ 各款立项书/开发任务书 ＞ 手册/清单 ＞ 导航文件。

---

## 2. 主要模块职责

### 2.1 集团根层（本仓直接拥有）

| 模块/文件 | 职责 |
|---|---|
| [README.md](file:///c:/Users/sjs20/Desktop/FluxGroup/README.md) | 集团入口：身份、哲学、目录布局、读序 |
| [BRAND.md](file:///c:/Users/sjs20/Desktop/FluxGroup/BRAND.md) | 品牌唯一事实源：锁定命名、含义、视觉规则、子品牌登记簿 |
| [RULES.md](file:///c:/Users/sjs20/Desktop/FluxGroup/RULES.md) | 顶层协作规则：命名、代码、目录、红线、CEO 令触发器 `/CEO` |
| [AI.md](file:///c:/Users/sjs20/Desktop/FluxGroup/AI.md) | AI 速览正典：5 分钟全局认知入口（一句话/组织/元宙/机制/文件地图/AI 行为铁律） |
| [CODELY.md](file:///c:/Users/sjs20/Desktop/FluxGroup/CODELY.md) | 集团记忆文件（行级追加面） |
| [docs/philosophy.md](file:///c:/Users/sjs20/Desktop/FluxGroup/docs/philosophy.md) | 企业文化与北极星（Rain 润泽万物 + WALL-E） |
| [docs/architecture.md](file:///c:/Users/sjs20/Desktop/FluxGroup/docs/architecture.md) | 集团业务架构：角色、业务线、系统三层结构、机队 |
| [docs/governance.md](file:///c:/Users/sjs20/Desktop/FluxGroup/docs/governance.md) | 集团治理契约：边界/拓扑/生命周期/指挥/记忆/安全/AI 诚实律 |
| [docs/orders.md](file:///c:/Users/sjs20/Desktop/FluxGroup/docs/orders.md) | CEO 令与跨公司裁决唯一审计台账 |
| [docs/master-plan.md](file:///c:/Users/sjs20/Desktop/FluxGroup/docs/master-plan.md) | 商业×元宙双螺旋总规划（城商一体·现实链接·互相赋能） |
| [Tools/](file:///c:/Users/sjs20/Desktop/FluxGroup/Tools) | 集团级工具脚本（治理工具，非产品代码） |

### 2.2 集团级工具脚本（Tools/）

| 脚本 | 职责 | 接线章程 |
|---|---|---|
| [bootstrap-machine.ps1](file:///c:/Users/sjs20/Desktop/FluxGroup/Tools/bootstrap-machine.ps1) | 新机器一键部署编排器（六相幂等·角色化·静默律） | `cph4/onboarding.md` |
| [InvisibleRunner.vbs](file:///c:/Users/sjs20/Desktop/FluxGroup/Tools/InvisibleRunner.vbs) | 静默执行包装器（零弹窗） | 编码律 |
| [selfaudit.ps1](file:///c:/Users/sjs20/Desktop/FluxGroup/Tools/selfaudit.ps1) | 反幻觉自审：扫五仓近 24h commit 宣称词，标记证据可得性 | `docs/governance.md` §10 |
| [retention-scan.ps1](file:///c:/Users/sjs20/Desktop/FluxGroup/Tools/retention-scan.ps1) | 资源水位周测：只读扫描，入进化轮「资源健康」节 | `cph4/retention.md` |
| [secret-scan.ps1](file:///c:/Users/sjs20/Desktop/FluxGroup/Tools/secret-scan.ps1) | 密钥泄露机核：七仓扫描，P0/P2 分类 | `cph4/versioning.md` §4.2 |

### 2.3 CPH4 Labs（横切研发层 · `cph4/`）

集团实验室 = 规划大脑 + 机制淬炼工厂，**零产品代码铁律**。产出 = 机制与方法论，随各公司仓落地。

| 文件 | 职责 |
|---|---|
| [cph4/README.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/README.md) | 实验室定位 + **集团 AI 能力注册表**（唯一能力清单）+ 共享方法论 |
| [cph4/evolution.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/evolution.md) | 集团自进化治理体系章程（感知→提案→裁决→立法+瘦法） |
| [cph4/evolution-ledger.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/evolution-ledger.md) | 唯一进化台账（提案区/裁决区/报告区） |
| [cph4/evolution-tick.ps1](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/evolution-tick.ps1) | 周进化轮载体（周日 09:17 静默跑，纯 ASCII·单实例锁 120min） |
| [cph4/night-round.ps1](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/night-round.ps1) | 集团夜轮（每日 03:07 轻量自我反应：感知/催办/小自愈/夜报） |
| [cph4/onboarding.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/onboarding.md) | 新机器一键部署章程（三层模型：CEO 物理件/一键编排/各司自件） |
| [cph4/scheduling.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/scheduling.md) | 集团调度机制（verdict 驱动·云端无限并行优先） |
| [cph4/local-first.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/local-first.md) | 本地化算力战略（L1 确定性→L2 本地 LLM→L3 API） |
| [cph4/token-economy.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/token-economy.md) | Token 经济机制统摄层（三面模型/五律/本地推理栈 v1） |
| [cph4/retention.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/retention.md) | 资源保留与清理（四级保留制×五面分层+防误伤五闸） |
| [cph4/versioning.md](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/versioning.md) | git 版本与分支治理（trunk-based·tag 档案律·身份律） |
| [cph4/research/](file:///c:/Users/sjs20/Desktop/FluxGroup/cph4/research) | R- 系列研究简报（元宙规划调研，必带验证声明） |

### 2.4 业务线工作区

#### Gaming 线（`gaming/`）— FLUX Gaming / 超体游戏
- 运营主体：**Biggame**（MiniGame 组合）——AI 游戏公司，公司本体 = AI 驱动的自动开发机器。
- 技术栈：团结引擎（Tuanjie）1.10.3 · C# + PowerShell + Python · 微信/抖音小游戏 · 零服务器纯 IAA。
- 入口：[gaming/README.md](file:///c:/Users/sjs20/Desktop/FluxGroup/gaming/README.md) → [gaming/MiniGame/README.md](file:///c:/Users/sjs20/Desktop/FluxGroup/gaming/MiniGame/README.md)（仓库五区分区图）。
- 五区：①工程区（projects/packages/tools/Design）②文档区（_共享与总控/）③统计区（根级活数据）④归档区（_归档/）⑤独立项目（09_吸嘟嘟）⑥本地资源库（gitignored）。

#### Quant 线（`quant/`）— FLUX Quant / FLUX 量化
- 运营主体：**BigMoney**——量化交易公司，沪深 ETF 3-15 天日线波段交易。
- 技术栈：Python 3.10+ · 自研日线回测引擎（T+1·成本恒开·持仓铁律）· Celery + Redis 分布式 · Tailscale 组网。
- 入口：[quant/README.md](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/README.md) → [quant/bigmoney/README.md](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/README.md)。
- **本仓内最重代码模块**，详见第 3 节。

#### Media 线（`media/`）— FLUX Media / 超体自媒体
- 运营主体：**BigStream**——AI 媒体公司，主赛道 = 集团 AI 生态内容。
- 平台矩阵：微信视频号/公众号/B站/YouTube/微博（均未开，账号 = CEO 物理件）。
- 入口：[media/README.md](file:///c:/Users/sjs20/Desktop/FluxGroup/media/README.md)。

#### Domain 线（`domain/`）— BigDomain / 硅基域
- 商业化子公司，运营公众共创元宙平台「硅基域」（19.9 算力包·代币内循环·B 端入驻）。
- 前台 = BigDomain，中台 = 三司产能，底座 = FluxVerse。

#### Life 线（`life/`）— BigLife（2026-09-24 定名转正）
- 数字生命生产子公司，超体宇宙城人口与人设资产唯一生产司（万人户籍库 + 进化引擎）。

---

## 3. 关键代码：BigMoney 量化系统（quant/bigmoney/）

集团内唯一实质产品代码落在本仓工作区的 BigMoney 子目录。

### 3.1 目录结构

```
quant/bigmoney/
├── README.md              # 产品仓总览
├── requirements.txt       # Python 依赖
├── bootstrap.py           # 一键自举（依赖自装+20项自检+总控数据生成）
├── smoke_test.py          # 20 项冒烟自检
├── bigmoney.html          # 总控主界面
├── dashboard.html         # 像素风监控面板
├── config/                # 全局配置
├── engine/                # 核心引擎
├── strategies/            # 8 大流派 35 个策略
├── data/                  # 数据（48 只 ETF 日线）
├── research/              # 研究笔记
├── results/               # 回测结果（432 组参数网格）
├── screening/             # 策略筛选排名
├── tasks/                 # 分布式任务（Celery + local fallback）
├── scripts/               # 脚本
├── knowledge/             # 市场规则
├── tools/                 # 机队工具
├── fleet/                 # 机队协议
└── Money02/               # 前代系统资产库
```

### 3.2 核心引擎（engine/）

| 文件 | 关键类/函数 | 职责 |
|---|---|---|
| [backtester.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/engine/backtester.py) | `run_backtest(prices, params, ...)` · `_entry_signal(close, fast, slow)` · `_exit_signal(...)` | 回测引擎：T 信号 → T+1 开盘执行（无未来函数）· 成本恒开 · 持仓铁律 · 支持信号注入、fill_guard、cost_v2 |
| [exit_rules.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/engine/exit_rules.py) | `ExitConfig` · `ExitState` · `ExitAction` · `evaluate(state, current_price, cfg, signal_reversed)` | 持仓铁律：P1 信号反转→P2 止损（初始-8%·+5%后移动跟踪）→P3 分层止盈→P4 时间衰减→P5 亏损 8 天强平→P6 硬上限 |
| [factors.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/engine/factors.py) | 30 因子库（15 经典 + 15 特色） | 因子计算 |
| [metrics.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/engine/metrics.py) | `summarize` · `win_rate` · `profit_factor` | 回测指标汇总 |
| [futures_runner.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/engine/futures_runner.py) | — | 期货回测 runner |

### 3.3 策略层（strategies/）

8 大流派 35 个策略函数，每个模块返回 `pd.Series`（单标的 0/1 仓位）或 `pd.DataFrame`（面板权重）。

| 模块 | 流派 | 代表策略 |
|---|---|---|
| [trend.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/trend.py) | 趋势跟踪 | 唐奇安/海龟/MA/PSAR/Supertrend |
| [mean_reversion.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/mean_reversion.py) | 均值回归 | 布林/RSI/z-score/RSI-2 |
| [momentum.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/momentum.py) | 动量轮动 | 横截面/双动量/TS/RS |
| [volatility.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/volatility.py) | 波动率 | 低波/目标/突破/状态切换 |
| [sentiment.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/sentiment.py) | 情绪资金 | 放量/成交额/量价/日内/隔夜 |
| [seasonal.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/seasonal.py) | 日历季节 | 月/周末/假期 |
| [macro.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/macro.py) | 宏观过滤 | 沪深300 MA200/回撤 |
| [event.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/strategies/event.py) | 事件缺口 | 缺口回补/放量突破/双底 |

### 3.4 配置层（config/）

| 文件 | 关键类 | 职责 |
|---|---|---|
| [settings.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/config/settings.py) | `RedisConfig` · `PathConfig` · `RiskConfig` · `ScreenConfig` · 全局单例 `REDIS`/`PATHS`/`RISK`/`SCREEN` | 路径/Redis/风控/筛选参数中心配置，所有节点读此文件 |
| [param_grid.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/config/param_grid.py) | — | 回测参数网格（432 组） |
| [universe.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/config/universe.py) | — | ETF 标的池（48 只核心池） |

### 3.5 分布式任务（tasks/）

| 文件 | 职责 |
|---|---|
| [celery_app.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/tasks/celery_app.py) | Celery 应用定义 |
| [backtest_task.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/tasks/backtest_task.py) | 回测任务定义 |
| [local_runner.py](file:///c:/Users/sjs20/Desktop/FluxGroup/quant/bigmoney/tasks/local_runner.py) | 本地 fallback（无 Worker 时跑 432 组回测） |

### 3.6 网络架构（Tailscale）

```
Master (笔记本) 100.x.x.x ── Redis :6379 (bind Tailscale only)
   ├── Worker1 100.y.y.y   ── celery -Q backtest_queue
   ├── Worker2 100.z.z.z   ── celery -Q backtest_queue
   └── Worker3 100.w.w.w   ── celery -Q backtest_queue
```
实盘券商 API 走公网直连，**不经过 Tailscale**；交易指令仅 Master 本机生成。

---

## 4. 依赖关系

### 4.1 集团层文档依赖链（读序）

```
README.md → BRAND.md → docs/philosophy.md → RULES.md → docs/governance.md → AI.md → cph4/README.md → cph4/evolution.md
```

### 4.2 模块间引用关系

- **集团仓零产品代码**：产品目录写进 `.gitignore`，严禁 `git add` 产品目录。
- **子公司引用集团**：各产品仓引用集团文件用路径，不复制内容（单一事实来源）。
- **CPH4 Labs 横切**：机制淬炼工厂，产出随各公司仓落地，本身零产品代码。
- **跨仓写禁令**：任何公司不写兄弟公司仓（唯一例外 = CEO 直接指令）。
- **机队共享**：bm-a/bm-b 双节点同机纪律引用 `quant/bigmoney/fleet/README.md` §10。
- **能力复用**：新建能力先查 `cph4/README.md` 注册表，一处淬炼、各司复用。

### 4.3 BigMoney Python 依赖（requirements.txt）

| 依赖 | 用途 |
|---|---|
| pandas>=2.0 / numpy>=1.24 / scipy>=1.10 | 数据处理与科学计算核心 |
| celery>=5.3 / redis>=5.0 | 分布式任务队列 |
| akshare>=1.14 | 数据源（新浪源沪深 ETF 日线） |
| rich>=13.0 | 监控面板输出 |

### 4.4 机队（共享基础设施）

| 机 | 角色 |
|---|---|
| bm-a（DASHENG·32 核） | BigMoney 开发节点 ∥ Biggame 主机（A 机） |
| bm-b（16 核） | BigMoney 回测/数据节点（Money02 宿主） |
| Biggame B/C 机 | 游戏分机（08 号协议：认领制 + X128 机器分支） |

---

## 5. 项目运行方式

### 5.1 集团层（本仓）

本仓为治理层，无运行态代码。主要"运行"方式：
- **阅读**：按读序通读文档建立认知。
- **新机部署**：`Tools/bootstrap-machine.ps1`（六相幂等，重跑 = 全机体检）。
- **自审/周测**：`Tools/selfaudit.ps1` / `Tools/retention-scan.ps1` / `Tools/secret-scan.ps1`。
- **进化轮**：Windows 任务 `FluxGroup-EvolutionTick`（周日 09:17）→ `cph4/evolution-tick.ps1`。
- **夜轮**：Windows 任务 `FluxGroup-NightRound`（每日 03:07）→ `cph4/night-round.ps1`。
- **CEO 令**：任一 AI 会话中用户消息以 `/CEO` 开头 = 正式 CEO 令（最高优先）。

### 5.2 BigMoney 量化系统（quant/bigmoney/）

```powershell
# 1. 克隆产品仓（独立 git）
git clone git@github.com:BigRain-11122/bigmoney.git

# 2. 一条命令自举：依赖自装（清华镜像回退）→ 20 项自检 → 总控数据生成
python bootstrap.py

# 3. 打开总控界面
start bigmoney.html

# 4.（可选·Windows）装 10 分钟 AI 自迭代循环（路径自适应零改动）
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\register_loop_task.ps1
```

常用命令：
- `python -m tasks.local_runner` —— 432 组回测（本地 fallback）
- `python scripts\ce_transfer.py` —— 复现 CE 迁移
- `python -m screening.rank` —— 排名重建
- 交接指南 = `research/HANDOVER.md`

### 5.3 Biggame 游戏公司（gaming/MiniGame/）

- 打开公司看板（像素小镇）：双击 `MiniGame/像素小镇看板.bat`
- 最新状态（引擎每 10 分钟覆盖式刷新）：`MiniGame/自动化快照.md`
- 引擎 tick：Windows 计划任务 `MiniGameEngineTick` → `tools/EngineTick.ps1`

### 5.4 编码律（全集团适用）

OS 任务直调脚本 = ASCII-only 或带 BOM；中文外置 UTF-8 数据件（Windows PS5.1 GBK 坑，两公司均已实证踩坑并修复）。一切自动化零弹窗（VBS 包装）。

---

## 6. 共享方法论（两公司实证同源，集团法）

1. **修红 ＞ 开发 ＞ 优化既有**——工作模式永远这样轮换。
2. **预注册/先写死后跑数**——实验前锁门禁，禁止跑到达标为止。
3. **引用普查前置**——改名/迁移前必查引用面（RefCheck 律）。
4. **实况优先**——法描述实测定态；文档漂移 = 文档去修，不是实况让路。
5. **诚实判负**——失败留档不粉饰（零假设基线、诚实报告文化）。
6. **反重复**——先读后写、复用禁重建；规则本身也不重复立法。

---

## 7. 思维导图（简明）

```
FluxGroup（超体宇宙集团）
│
├── 治理层（本仓·零产品代码）
│   ├── 品牌/文化/规则/契约：README → BRAND → philosophy → RULES → governance
│   ├── AI 识别入口：AI.md
│   ├── CEO 令台账：docs/orders.md
│   ├── 双螺旋总规划：docs/master-plan.md
│   └── 集团工具：Tools/（bootstrap/selfaudit/retention-scan/secret-scan）
│
├── CPH4 Labs（横切层·零产品代码·机制淬炼厂）
│   ├── 能力注册表（cph4/README.md）
│   ├── 自进化治理（evolution.md + 台账 + 周轮 + 夜轮）
│   ├── 调度/算力/Token 经济（scheduling/local-first/token-economy）
│   ├── 资源保留/版本治理/新机部署（retention/versioning/onboarding）
│   └── 元宙规划研究（research/R- 系列）
│
├── 业务线 1：Gaming（游戏·Biggame）
│   ├── 产品仓：MiniGame（8款小游戏+G系·团结引擎1.10.3·零服务器）
│   ├── 元宙：FluxVerse（集团驾驶舱·对标现实·全2D·AI行为剧场）
│   └── 五区：工程/文档/统计/归档/独立项目
│
├── 业务线 2：Quant（量化·BigMoney）★唯一实质代码★
│   ├── 引擎：engine/（回测·持仓铁律·因子·指标）
│   ├── 策略：strategies/（8流派35策略）
│   ├── 配置：config/（Redis/路径/风控/筛选）
│   ├── 分布式：tasks/（Celery+本地fallback）
│   ├── 数据：48只ETF日线（新浪源）
│   └── 机队：bm-a开发 + bm-b回测（Tailscale组网）
│
├── 业务线 3：Media（媒体·BigStream·onboarding）
│   └── 主赛道=集团AI生态内容（视频号/公众号/B站/YouTube/微博）
│
├── 业务线 4：Domain（商业化·BigDomain/硅基域·onboarding）
│   └── 公众共创元宙平台（19.9算力包·代币内循环·B端入驻）
│
└── 业务线 5：Life（数字生命·BigLife·onboarding）
    └── 超体宇宙城人口与人设资产唯一生产司（万人户籍库+进化引擎）

运转模式：CEO（决策/发令/红线/资源）→ AI 劳动力 → 机器机队 24h 自治
诚实律：宣称带证据 · 新鲜验证 · 宣称分级 · 原话锚定 · 存疑即标
```

---

## 8. 当前状态速览（2026-09-24）

- ✅ 集团治理 v1.0 立国；CPH4 进化轮 + 夜轮运转
- ✅ BigMoney：48 只 ETF 真实日线 · 30 因子 IC · 8 流派 35 策略 · 回测引擎 P0 修复
- ✅ Biggame：8 款软著 IP · 像素小镇总控 · 08 号多机分治
- ⏳ BigStream/BigDomain/BigLife：onboarding 阶段（remote 待 CEO 建）
- ⏳ FluxVerse 元宙 M1 呈现层建城中（集团级最高优先·资源倾斜态）
- ❌ BigMoney 2026-09-23 实证：432 组内置均线信号全灭（策略层换血中）

> 实况以各产品仓为准；本 Wiki 仅作导航与速览。

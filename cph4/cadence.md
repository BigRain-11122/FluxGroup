# Cadence — 集团自动化周期总账（CPH4 Labs）

> 溯源：CEO 令 2026-09-24「建立起清晰的自动化任务周期，不要重复，也不要出问题。还有提交周期什么的，好好梳理一下。不止我说的这些，需要规划好所有的。」（深做授权——全盘梳理）。
> 定位：**全集团一切自动化周期与提交周期的唯一总账**——scheduling.md 管「在哪跑」，本件管「何时跑+谁跟谁错峰+怎么防重复防出错」。T2+否决窗 7 天。
> 实测底账：2026-09-24 11:47 bm-a 全机 35 项计划任务盘点（Get-ScheduledTask 实况）。

## 0. 周期总账表（bm-a 实测·2026-09-24 11:47·各分机照此格式自报入账）

| 族 | 任务（周期） | 触发 | 用途 | 护栏（既有法） |
|---|---|---|---|---|
| **10min 轮族**（错峰车道） | BigStream-OSLoop :x2｜BigLife-OSLoop :x3｜MiniGameOllamaKeepWarm :x3｜FluxVerse-DevLoop :x5｜**FluxVerseTick :x6**（本批自 :x7 迁入·原与 MiniGameEngineTick 同分钟竞写读）｜MiniGameEngineTick :x7｜Bigmoney-IterationLoop :x8｜MiniGameTickWatchdog :x8｜MiniGameEditorSentry :x9 | 每 10 分钟 | 各司 OS 迭代/心跳/保温/看门狗 | 静默律 VBS+单实例锁+轮首脏定向 add+轮账本 |
| **小时/事件族** | MiniGameCockpitBeat（5min 心跳）｜MiniGameTjcloudSync（时 :13）｜Bigmoney-LoopWatchdog（30min） | 分钟级 | 驾驶舱心跳/云同步/自愈看门狗 | watchdog 车道归属绑定（F-08：非 owner 只观测） |
| **日轮族** | **决策轮 00:00**（23:00 上报截止）｜**夜轮 03:07**（四器审计+熔断自愈）｜MiniGameRadarTick 09:52｜PolicyTick 12:52｜GateTick 14:52｜AuditTick 17:52 | 每日 | 拍板/自反应/巡检/门禁/审计 | 单轮预算 15-25min+超时优雅收尾 |
| **周轮族** | MiniGameHousekeeping 日 07:17｜RadarDeepTick 日 08:52｜**集团进化轮 日 09:17** | 周日 | 清理批/深扫/立法四步+考核面 | 轮首脏退避+法熵审视（季） |
| **登录/常驻族** | MiniGameOllamaServe（登录）｜MiniGamePopupWitness（登录常驻·弹窗见证） | 登录 | 本地模型服务/弹窗证据 | GPU/RAM 纪律 fleet §10 |
| **停用族（设计内态）** | MiniGameDailyDigest（U166 暂停·禁自愈 Enable）｜MoneyAutoGuardian（转办停用）｜GimmeAll-AutoSentinel｜CarGZH ×9（**CEO 个人域任务·非集团面·2026-09-20 起停用·未经令不动**） | — | — | E3 噪音豁免律：预期内态禁反复修 |

**B/C 机任务**：按 08 号协议自报其台账入各自正典（本表只登 bm-a）；**新机上车=bootstrap P4 注册+在本表登记簿面加行**（开线 SOP 接线）。

## 1. 防重复律（「不要重复」）

1. **同用途唯一制**：一个用途=一个任务——新任务上岗先查本总账+cph4 注册表（禁双建），发现同用途双任务=当轮收编或废一（BigStream-OSLoop 近重复教训）。
2. **周期任务认领面**（F-09 律）：跨机周期任务（核对/简报/审计类）必过认领面——错峰轮值或周期戳，他机见戳即跳（禁双机同窗同做）。
3. **停用族不可自愈复活**：Disabled=设计内态（U166 范式），任何轮禁当故障修。

## 2. 防冲突律（「不要出问题」）

1. **错峰律**：同机任务**禁同分钟触发当且仅当共享资源**（读写同文件/同仓/同锁）——10min 车道分钟位 = 稀缺资源逐一占位；**本批实证：FluxVerseTick 与 MiniGameEngineTick 同 :x7 竞写读 MiniGame 心跳 json → 已迁 :x6**（迁移=Set-ScheduledTask 单字段·幂等可回滚）。
2. **单实例锁**：一切轮任务带锁（tick 15min 陈旧接管/夜轮 60min/决策轮 30min）——防重入。
3. **并发退避**：轮首 git status 脏=只定向 add 或跳过 commit；push 被拒=pull --rebase 一次，再拒留待下轮（禁循环重试）；scan 单写者锁。
4. **熔断**：自愈两轮未愈禁硬修升级 E1（errors.md §2.5）；watchdog 非 owner 禁本地重启（F-08）。
5. **结果码抽验**：夜轮自检面=关键任务存在且非 Disabled（现有 9 项）+LastResult 非 0 抽验（267009/267011=运行中/未跑属正常码·异常码入夜报）。

## 3. 提交周期律（「提交周期什么的」）

| 面 | 周期 | 律（既有法） |
|---|---|---|
| **交互会话** | 小步快提交——每件功能/每令毕即 commit+push（禁长脏树） | versioning §4.3 四层结构+500 硬顶+[via] 尾标 |
| **10min 轮** | 轮末定向 add+commit（一 commit 一意图·轮式 `轮名 日期: 一句话`）+push 一次 | 轮首脏退避；被拒 rebase 一次 |
| **日/周轮** | 轮产出即 commit+push（夜轮/决策轮/周轮各自 mandate 已接） | 大件留周轮（夜轮预算 15min） |
| **备份节律** | 活库=每轮/每日 push（retention §9 一级）；月度恢复演练（§10 日历） | clone+bootstrap 即重建判据 |
| **tag 节律** | 里程碑/对外发布=先 tag 后发（versioning §3.4 发布锚律） | gov/vX.Y·M<x>/v1.0 模型 |

## 4. 变更控制

- 新任务/改周期/迁移车道=T2（本总账行变更+changelog）；删除任务=司内提案+台账行（可逆原则）；本表修订=T3 随实况。
- 分机任务表=各司自报（引用不复制）；集团夜轮只抽验 bm-a 面与「全机必存集」。

## 5. 验证声明

实测底账=2026-09-24 11:47 Get-ScheduledTask 35 项全量；错峰修正已实弹（FluxVerseTick :x7→:x6·NextRun 12:06 复验）；既有护栏法全部引用（静默/锁/退避/熔断/F-08/F-09/U166）；新增=总账表+防重复防冲突双律+提交周期表——回访=夜轮结果码抽验首例+各分机自报表收齐。

## 6. 监控运行机制（「确保各项任务正常运转」·CEO 令 2026-09-24 ~14:00·T2+否决窗 7 天）

**任务健康五信号**（监控器=`Tools/task-health.ps1`·只读·夜轮每夜全量跑）：

| 信号 | 判据 | 旗标 |
|---|---|---|
| ①存在性 | 在册+Enabled（停用族豁免登记对账） | **UNEXPECTED-DISABLED**（意外被禁=重点抓） |
| ②准时性 | LastRunTime ≤ 2×预期周期（防「任务在但静默不跑」=原夜轮盲区） | STALE／NEVER-RAN |
| ③结果码 | 0/RUNNING/NOT-RUN-YET 正常；**产出实据优先律：结果码异常+产出新鲜=启动器码类（观察级）；结果码异常+产出停更=真故障 E2** | CODE-n 入夜报 |
| ④产出实据 | 轮账本/state/日志时间戳新鲜（tokens 行已强制）——exit 0 但产出停更=产出断流 | 归各司自监控（L0） |
| ⑤资源面 | 心跳 verdict+机队旗标 | fleet-audit.ps1（§五台账） |

**监控分工**（谁监控谁）：L0 轮自监控（轮账本时间戳）→L2 司级看门狗（TickWatchdog/LoopWatchdog·F-08 车道归属绑定·非 owner 禁本地重启）→L3 夜轮 task-health 全量扫→CEO 面=CityWatch+黑灯区律+夜报点名行。

**处置路由**：旗标→夜报一行+E 分级（UNEXPECTED-DISABLED/NEVER-RAN/STALE→E2；连续两夜同旗=熔断升 E1[errors §2.5]）；**设计态旗标=夜轮带上下文裁决豁免登记不硬修**（E3 范式）；缺失任务按静默律重建（原夜轮自检步保留）。

**首扫实况**（2026-09-24 11:47·27 项）：0 真故障+BoardForge STALE=**设计态豁免**（空单自休眠 U175 上下文）+4 启动器码类（BigLife/Bigmoney=CODE-3·DevLoop=CODE-1·RedlineAudit=CODE-2——产出全新鲜=观察级·连续两夜未消再升 E1）。

### Changelog
- 2026-09-24: initial v1.0（35 项实测总账+防重复防冲突双律+提交周期表+错峰修正 :x7→:x6）。
- 2026-09-24: **§6 监控运行机制**（CEO 令「建立起科学的自动化任务监控和运行机制，确保各项任务正常运转」）：任务健康五信号+产出实据优先律+监控分工+处置路由（设计态豁免/熔断）+`Tools/task-health.ps1` 首扫 27 项实弹（1 设计态旗标+4 观察级码·0 真故障）。

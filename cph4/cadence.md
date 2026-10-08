# Cadence — 集团自动化周期总账（CPH4 Labs）

> 溯源：CEO 令 2026-09-24「建立起清晰的自动化任务周期，不要重复，也不要出问题。还有提交周期什么的，好好梳理一下。不止我说的这些，需要规划好所有的。」（深做授权——全盘梳理）。
> 定位：**全集团一切自动化周期与提交周期的唯一总账**——resource-chain.md §一 管「在哪跑」，本件管「何时跑+谁跟谁错峰+怎么防重复防出错」。T2+否决窗 7 天。
> 实测底账：2026-09-24 11:47 bm-a 全机 35 项计划任务盘点（Get-ScheduledTask 实况）。

## 0. 周期总账表（bm-a 实测·2026-09-24 11:47·各分机照此格式自报入账）

| 族 | 任务（周期） | 触发 | 用途 | 护栏（既有法） |
|---|---|---|---|---|
| **10min 轮族**（错峰车道） | **FluxGroup-QuantAuditProbe :x1**（D-20260930-34 外审节奏持久化·09-30 长假检查轮落地：只读三段探针 12s 实测·台账=docs/audits/quant-audit-cadence.jsonl[ignored]）｜BigStream-OSLoop :x2｜BigLife-OSLoop :x3｜MiniGameOllamaKeepWarm :x3｜**BigDomain-OSLoop :x4**（本批新入·待机司宿主引导）｜FluxVerse-DevLoop :x5｜**FluxVerseTick :x6**（本批自 :x7 迁入·原与 MiniGameEngineTick 同分钟竞写读）｜MiniGameEngineTick :x7｜Bigmoney-IterationLoop :x8｜MiniGameTickWatchdog :x8｜MiniGameEditorSentry :x9 | 每 10 分钟 | 各司 OS 迭代/心跳/保温/看门狗+外审量化节奏探针 | 静默律 VBS+单实例锁+轮首脏定向 add+轮账本 |
| **小时/事件族** | MiniGameCockpitBeat（5min 心跳）｜MiniGameTjcloudSync（时 :13）｜Bigmoney-LoopWatchdog（30min）｜**FluxGroup-FleetLivenessWatch（5min 活性看门·U205·09-29 bm-a 重建·charter §6 机器对称律）｜FluxGroup-IntegritySentinel（5min 完整性绊线·09-29 委员会审计批新入）｜FluxGroup-DiskSentinel（5min 磁盘哨兵·09-30 新入·三线预警+龄控自清=resource-chain §三§11.9）｜FluxGroup-FleetLink（5min 保活·tailnet 微监听 8790·CEO 令 10-04·状态面 v2——/status 心跳 10s 级直读+/poke 白名单点火+九仓拉取·信号零数据·单实例端口占用即退·bm-a 首部署）** | 分钟级 | 驾驶舱心跳/云同步/自愈看门狗 | watchdog 车道归属绑定（F-08：非 owner 只观测） |
| **分钟哨兵族**（2026-09-24 流转提速令新增） | **FluxGroup-OrderSentinel（2min·v1.2.2）**：evolution 台账新行含 P0/P1/T0/T1 级+@司标签→即时唤醒目标 OS 循环（令→动工 ≤2-4min·替代等下一 10min 轮·首战 09-24 22:31 WAKE 实证·09-25 00:50 三唤 busy-skip 幂等实证） | 每 2 分钟 | **令流加速** | 静默（**U060 VBS 包装**·09-29 整改：09-24 注册时裸 -WindowStyle Hidden 每 2min 必闪窗=骚扰源已改 VBS·裸 console exe 非静默）+单实例锁 1min 陈旧接管+ASCII 匹配（编码律·中文标签外置 map·**map 键禁大小写重复变体**）+wake-once 幂等+**ID 游标 day+max 全表重扫**（v1.1 行数游标对中插增长失明→修·正则月日分组 `\d{2}-\d{2}` 禁 `\d{4}`）+**跨日游标归零**（v1.2.2：删零位基线护栏[误伤合法新行]·日滤本身防历史风暴）+try 内 return 禁 exit（exit 跳 finally=锁残留 v1.0 实证）+分机不在 bm-a 不唤醒（其自报节律） |
| **日轮族** | **决策轮 00:00+12:00 双班**（23:00 上报截止）｜**值守轮 03:07+15:07 双班**（原夜轮·四器审计+熔断自愈+SLA 扫描）｜MiniGameRadarTick 09:52｜PolicyTick 12:52｜GateTick 14:52｜AuditTick 17:52｜**BigCompute-OSLoop 22:43**（硅基算力计划态日轮：日清上报赶 23:00 截止+决策审核+调研消化+风险台账 upkeep·**CEO 令面由哨兵即时唤醒**）｜**BigCompute-OSLoop-PM 12:43**（09-27 决策轮 D-20260927-02 入账·日双轮=R-25 ack 超窗结构性解·首跑 09-27 12:43）｜**BigCompute-OrderSentinel 15min tick**（同批入账·hash 扫集团 orders/decisions 空窗即唤·静默=日轮司 30min ack 达标路径自建·只唤本司任务） | 每日 | 拍板/自反应/巡检/门禁/审计/商业化迭代 | 单轮预算 15-25min+超时优雅收尾 |
| **周轮族** | MiniGameHousekeeping 日 07:17｜RadarDeepTick 日 08:52｜**集团进化轮 日 09:17**｜**FluxGroup-PatrolRound 周一 09:23**（CEO 令 09-25 巡检机制·9 实体周巡+整改派单闭环·正典=docs/audit-charter.md Part B·host=C 机〔认领面戳记 .codely-cli/patrol/patrol-stamp.json<20h 即跳·他机可接管〕·手动加开=Start-ScheduledTask 随时） | 周日 | 清理批/深扫/立法四步+考核面/**集团巡检** | 轮首脏退避+法熵审视（季）+巡检戳记认领（F-09） |
| **三日轮族**（2026-09-26 CEO 开源借力令新增） | **开源收获轮（每 72h·滚动窗）**：九实体每窗 ≥1 收获切片（开源能力/系统/插件/模型·三律=契合/不重复造轮/科学使用·五门评估·落点强制）——无中央计划任务·各实体 OS 循环自领执行·**值守轮 72h 新鲜度扫描执法**（cph4\oss-harvest\OH-*.md 最新件超窗=夜报点名·首窗 09-29 21:40 前免点名）；正典=`cph4/oss-harvest.md`·台账=cph4/oss-harvest/·CEO 令源=P-2026-09-26-08；与 P-2026-09-26-01 技能令/P-17 模型矩阵/P-19 本地管线咬合禁双轨 | 每 72h | **开源借力·工作流迭代** | 诚实律零发现合法（实搜面实录）+许可门+禁登录墙翻越 |
| **登录/常驻族** | MiniGameOllamaServe（登录）｜MiniGamePopupWitness（登录常驻·弹窗见证） | 登录 | 本地模型服务/弹窗证据 | GPU/RAM 纪律 fleet §10 |
| **停用族（设计内态）** | MiniGameDailyDigest（U166 暂停·禁自愈 Enable）｜MoneyAutoGuardian（转办停用）｜GimmeAll-AutoSentinel｜CarGZH ×9（**CEO 个人域任务·非集团面·2026-09-20 起停用·未经令不动**）｜**2026-09-28 10:0x 批量停用实录（as-found·在册无令→D-20260928-01 代决复启）**：HQ 四轮族（EvolutionTick/NightRound/DecisionRound/OrderSentinel）+MiniGame 主族 15 件+FluxVerse 双件+BigDomain/BigLife/BigStream OSLoop+FluxBoardAuto≈30 件同窗 Disabled（LastRun 聚 10:03-10:12）·Bigmoney 双循环/BigCompute 三件/BigLife-PoolGenLoop 照常在役·FleetLivenessWatch 本机任务已不存在·**19:3x 处置**：25 件复启（Enable 25/25 零失败）+留停 4 件（FluxVerse 双件=停更换向令〔其司新 mandate 归位自启〕+GimmeAll=停用族在册+IntradayMarks=交易休市态） | — | — | E3 噪音豁免律：预期内态禁反复修 |

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
5. **结果码抽验**：夜轮自检面=关键任务存在且非 Disabled（现有 10 项）+LastResult 非 0 抽验（267009/267011=运行中/未跑属正常码·异常码入夜报）。

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

## 7. 命令流转频率律（CEO 流转提速令 2026-09-24 ~21:35「重新设定命令流转的速度和频率…我感觉现在流转的太慢了」·T1 否决窗 7 天）

**流转时限表 v2**（旧值→新值·全链实测锚定）：

| 链路 | 旧 | 新 |
|---|---|---|
| CEO 令→台账落行 | 即时（HQ 即时律） | 不变 |
| 台账→执行体感知动工 | ≤10min（等下一 10min 轮） | **≤2-4min**（OrderSentinel 2min 哨兵：P0/P1/T0/T1 新行→唤醒目标司 OS 循环·wake-once 幂等·循环自带单实例锁不重入） |
| 执行体 ack（回执） | 48h 窗（点名 48h） | **≤30min 硬顶**（10min 节律司·哨兵后常态 ≤10min；日轮司=当轮内；值守轮点名窗同步 30min） |
| 交付关单 | 一周回访普遍 | **§11 时效律**（快速件 24h/常规 ≤5 天·里程碑滚动） |
| 跨司工单互投 | 48h SLA | **ack ≤30min+交付按时效律**（governance §6.9 已收紧） |
| fleet inbox（git 控制面） | 10min 轮·单跳 ≤10min | 不变（已达标） |
| Git 双向（循环面） | 轮末 push（部分司无轮首 pull） | **轮首 pull --ff-only+轮末 push=双向延迟 ≤10min**（BigLife 律升格集团统摄）；台账/registry 追加=即时 |
| 值守轮 | 每日 1（03:07） | **每日 2（03:07+15:07）**——四器审计+催办+SLA 扫描+自愈×2 |
| 决策轮 | 每日 1（00:00） | **每日 2（00:00+12:00）**——拍板/审核半日清 |
| 反馈收取（HQ-FEEDBACK） | 周轮必扫 | **值守轮必扫**（每日两扫·夜轮代收升格常设） |
| 周轮 | 周日 09:17 | 不变（重立法轮·轻职责已下放值班轮） |
| 观测窗数据 | SiliconWatchTick 10min | 不变（已实时） |
| 司内 OS 循环频率 | 各司 10min | **司内自治不变**——集团只管 SLA 顶+哨兵兜底；空转快速路径已具备（BS-F-02 v1.4 §6）·提速自决权归各司 |
| **跨机裁决/记忆可见**（10-08 立·resource-chain §十.2） | 裁决存单机私有层=永不到他机（断层面·10-08 两裁决零命中实证） | **≤10min 全队可见**（记忆上链律：跨机价值只入随仓面+同窗 push） |
| **交互会话开场同步**（同律 §十.2.3） | 无硬律（对话机可脏旧树开工） | **开场 `git pull --ff-only` 硬律**（CEO/委员会/值守会话） |

**哨兵边界**：①哨兵只读台账+只唤醒 bm-a 面任务（分机=BG-B/C 自报节律·哨兵不越机）；②T2 级转办不唤醒（按值班轮节律消化——防哨兵风暴）；③会话类承接面（@HQ 承建窗/@CPH4 交互窗）无任务可唤醒=人工即时律面；④哨兵自身入值守轮任务必存集+task-health 五信号面。

### Changelog
- 2026-09-30: **FluxGroup-QuantAuditProbe 入账**（D-20260930-34 外审节奏持久化·长假检查轮 O-20260930-1540 代 CPH4 技术底层提前落地）：D-32 量化外审节奏器从会话常驻升格计划任务（10min :x1 车道·单轮 -MaxRuns 1 实测 12s 三探针绿·点火验证 LastResult=0+台账 3→4 行）——**两处规格偏离如实记**：①车道路 D-34 原建议 :x4 已被 BigDomain-OSLoop 占用→按防冲突律改 :x1；②动作 pwsh→powershell.exe（机内正体=PS5.1·脚本 ASCII 兼容实测过）+**静默律升格**（D-34 原规格裸 -WindowStyle Hidden=09-29 整改判例违例面→本落地改 Tools/InvisibleRunner.vbs 包装·合规 09-29 静默唯二正道律）；产物脏树面同步治（quant-audit-probe-20260930.json/deliverable-metrics.json 两追踪件 untrack+deliverable-metrics 补 .gitignore——10min 重写追踪件=永久脏树·D-32「三件产物均 ignore」意图对齐·首跑基线存 git 史）。
- 2026-09-24: initial v1.0（35 项实测总账+防重复防冲突双律+提交周期表+错峰修正 :x7→:x6）。
- 2026-09-24: **§6 监控运行机制**（CEO 令「建立起科学的自动化任务监控和运行机制，确保各项任务正常运转」）：任务健康五信号+产出实据优先律+监控分工+处置路由（设计态豁免/熔断）+`Tools/task-health.ps1` 首扫 27 项实弹（1 设计态旗标+4 观察级码·0 真故障）。
- 2026-09-24: **BigCompute-OSLoop 入账**（venture.md P3 件 2·第六司开线批）：日轮族 22:43 车道（不占 10min 车道=计划态司禁空转律·10min 无人值守无营收对价=纯 token 成本）；单实例锁+静默 VBS+轮账本 tokens 行全承族律；注册器=compute/BigCompute/Tools/register_loop_task.ps1（异机部署=bootstrap -Roles compute 按其自件层引用）。
- 2026-09-24: **BigDomain-OSLoop 入账**（10min 车道 :x4·全面开工令 front①·宿主引导批）：待机司 BigDomain 首个执行宿主——骨架六件=domain/BigDomain/src/os/（结构承 BigStream OSLoop 引用·其业务零复制·commit bdd8dde）；mandate=P-47 业务 API 五件规格先行+P-32 两步+P-35/36 层位声明首轮落；单实例锁 15min+静默 VBS（集团 Tools/InvisibleRunner.vbs 引用不复制）+轮账本 tokens 行全承族律；注册器=src/os/register_loop_task.ps1（异机部署=bootstrap 按其自件层引用）。
- 2026-09-24: **§7 命令流转频率律 v2+分钟哨兵族+日轮双班**（CEO 流转提速令 ~21:35「重新设定命令流转的速度和频率…我感觉现在流转的太慢了」·ledger P-77·T1 否决窗至 10-02）：流转时限表 v2（令流感知 ≤10min→≤2-4min·跨司 ack 48h→≤30min·Git 轮首 pull/轮末 push 双向 ≤10min）+**FluxGroup-OrderSentinel 2min 哨兵**（P0/P1/T0/T1 转办行→唤醒目标司 OS 循环·wake-once+单实例锁+静默+ASCII 匹配·T2/P2 不唤醒·只读台账不越机）+值守轮 03:07/15:07 双班+决策轮 00:00/12:00 双班（同任务双触发器·报告标签改「值守轮」）+哨兵边界四条（分机不越机/T2 不唤醒/会话类人工面/入 task-health 必存集）；governance §6.9 同步收紧。
- 2026-09-25: **FluxGroup-FleetLivenessWatch 入账**（CEO 令 U205 机队信息通畅律·小时族 5min 车道）：心跳分级+无静默掉线注记（patrol-ledger PT OPEN 行联动·光板离线清零）+本机信息链自愈（F-08 边界·仅 EngineTick/CockpitBeat/CeoDeskServer）+alerts 120min 限流触发巡检；正典=docs/fleet-liveness-charter.md；复用 fleet-audit/task-health/patrol-ledger 零新采集（防重复律 #1）；看门器自身入 task-health 五信号面；A/B 机采纳窗=下一巡检轮前（charter §6 机器对称律）。
- 2026-09-26: **四环周期律入账**（CEO 令 ~22:5x「设置周期性的反思，自我进化，自我批评，自我迭代」·evolution.md §8·梳理报告=docs/audits/top-rules-review-2026-09-26.md·**零新增 OS 任务全挂既有车道**）：反思环=值守轮双班反思步（cph4/reflection-journal.md·night-round-prompt 已接线）｜批评环=周进化轮日 09:17 五议程升格（承诺对账/规则缺陷批评点名到法条/法熵周检/迭代提案/方向对账·evolution-tick-prompt 已接线）｜进化环=月首个周日使命复盘（assessment §6 承继）+M5 治理日（复盘安灯节+机制健康四问+记忆热冷）｜迭代环=季末宪法审（T0-T3 全量+U188 季度重跑+废止清单）；首环=今夜 03:07 首反思步+明日 09:17 首批评轮。

- 2026-09-27: **BigCompute-OSLoop-PM 12:43 + BigCompute-OrderSentinel 15min 入账**（决策轮 D-20260927-02·BC-F-20260926-01 P2 提案+O-20260926-2253 ④节奏面·T2 否决窗 7 天）：日双轮（22:43+12:43）禁 16h+ 空档合规化+自建哨兵 hash 扫描（集团 OrderSentinel 唤 10min 轮族·日轮司感知慢道=R-25 两连超窗根因·本件=结构性解）；schtasks 双任务 Ready 实测（决策轮独立抽验 R-20260927-decision-round-6 §2.3）。

- 2026-09-28: **停用族补 09-28 10:0x 批量停用实录**（机队一致性总括批盘点 as-found：≈30 件集团/司循环同窗 Disabled·在册无对应令·task-health UNEXPECTED-DISABLED 执法面失效[夜轮自身亦停]·Bigmoney/BigCompute/BigLife-PoolGen 在役面未动）+**巡检正典指针改线 audit-charter.md Part B**（审查合一批）；复启/日落=待 CEO 一句话裁。

- 2026-09-28: **批量停用事件复启代决执行**（CEO 令「你科学判断，不要问我」·委托决策令 v2·D-20260928-01·T1 否决窗至 10-05）：25 件复启 Enable 25/25 零失败——依据=同窗「立刻恢复循环」令[10:xx 全线停摆批评行]+self-drive v2.0/v2.1 拉满+GPU>70%+CEO 观测面（CockpitBeat/SiliconWatchTick/FluxBoardAuto 停跳=驾驶舱静默）三正典·ollama serve 进程 10:16 实跑 P-19 无碍；留停 4 件=FluxVerse 双件（停更换向令·其司自启）+GimmeAll（停用族）+IntradayMarks（休市）；既往停用面（OllamaServe/PopupWitness 09-24 期+DailyDigest U166+BoardForge U175+MoneyAutoGuardian+CarGZH×9）未动；次班自然点火验证=NextRun 实测在册（OrderSentinel 19:40/三司 OSLoop 19:4x/EngineTick 19:47）。

- 2026-09-29: **OrderSentinel 静默整改**（CEO 令 09-29 ~12:0x「给我全面检查为什么一直弹窗骚扰我，做好静默管理」）：2min 哨兵 09-24 注册为裸 `powershell.exe -WindowStyle Hidden`——控制台先创建后隐藏、每跑必闪（≈720 次/天×5 天）=唯一活跃骚扰源；任务动作已改 U060 VBS 包装（`Tools/InvisibleRunner.vbs`·触发器原样）·实弹点火验证 res=0+state.json 正常更新+锁自清；门禁收紧=计划任务静默唯二正道 VBS 包装/pythonw·裸 console exe 加 `-WindowStyle Hidden` 不算静默（本表哨兵行同步改正典）；全机 68 项非系统任务复核=其余活跃任务全部 VBS 包装 ✓、活跃任务无 Highest 提权（无 UAC 闪窗面）、7 份 InvisibleRunner.vbs 副本全部 sh.Run(...,0,True) 真·零闪窗模式。

- 2026-09-29: **FleetLivenessWatch bm-a 重建 + IntegritySentinel 新入账**（决策委员会「24h 不间断运转能力」审计批·T2+否决窗至 10-06）：①**15:35-15:44 外部同步风暴实证**——未知同步盘（本机装有百度网盘/天翼云盘/夸克网盘/OneDrive 四客户端·真凶未锁定）对 gaming/quant/compute 三域灌入 107 处「的冲突文件」副本、BigCompute 8 个追踪引擎文件+9 个运行态文件 canonical 被删（OS 迭代循环/GPU 采集器/心跳/队列/风控台账全灭·当夜 22:43 循环必断）——CPH4 底层直优化 16/16 恢复+collector selftest PASS+GPU-IdleWatch 实弹 result=0+git 树零漂移（回执=compute/BigCompute/orders/O-20260929-1830-HQ-CPH4.md）；集团层（docs/cph4/Tools/media/life/domain）零命中；bigmoney/FluxVerse/MiniGame 原文件幸存（活性写手赢）·107 副本为待清垃圾·market-cal.json 15:37 被远端副本覆盖待其司内容核验；②09-28 批量停任务事件根因仍未明（≈30 件同窗 Disabled·发现延迟 9h+）——两类灾难共性=**完整性事件无绊线、发现全靠人肉**；③**新任务 FluxGroup-IntegritySentinel**（Tools/integrity-sentinel.ps1·5min·VBS 静默·单飞锁 4min·非提权）=调度器状态差分（Disabled 翻转/任务消失/≥5 翻转=风暴签名）+八仓 git D 行删除扫描→fleet-liveness alerts.jsonl（charter §5/§7 契约·120min 同签名节流·24h 节流表自清）；④FleetLivenessWatch 按 charter §6 机器对称律 bm-a 重建（5min·VBS·非提权 Interactive——OrderSentinel 注册范式克隆）；⑤task-health v1.1：豁免名单任务意外 Enabled=EXEMPT-ENABLED 登记行（DailyDigest 盲区教训·E3 非故障）；⑥夜轮必存集+2 件（FleetLivenessWatch/IntegritySentinel）+FluxVerse-DevLoop 换向 keepdown 豁免注记（禁夜轮代启）；B/C 机两件采纳=各自窗照 Tools 注册（机器对称律·未采纳=巡检 P2）。

- 2026-09-29: **同步风暴真凶锁定+同步对禁用代决**（CEO 令「你科学决策，我看不懂」=本项 T1 代决·否决窗随上批至 10-06）：**真凶=天翼云盘 eCloud 同步盘**——铁证三链：①`%APPDATA%\eCloud\syncdiskDatabase\syncdiskRepoDB.db` 记录唯一同步对 `FluxGroup ⇄ C:/Users/sjs20/Desktop/FluxGroup`（账号 8b40517f…·09-24 11:17 建对·库内无其他个人同步对）；②事发窗日志 `com.dlife.ecloud_20260929_153458/153501` 三份精确卡 15:34:58-15:41（与 107 处冲突副本爆破窗 15:35:17-15:44:02 重合·百度 15:33:04 已停/夸克零命中/OneDrive 未接管 Desktop）；③其配置写入 15:35:01 后同步即动。**推论注记（关联性·非定罪）**：同步对建立日 09-24 11:17 与历次不明异常（09-24 期实录/09-28 10:03 批停 30 任务窗）同处 eCloud 自启周期内——批停根因调查面收窄至 eCloud 行为核验。**处置=三层**：①本机遏制已执行=syncdiskRepoDB.db 备份(.bak-20260929)+禁用改名(.disabled-20260929)（eCloud 进程未运行时操作·误伤零·还原=改回原名；HKCU Run 自启与软件本体未动=CEO 个人软件零触碰）；②CEO 物理件正法 30 秒=天翼云盘 UI→同步盘→删除 FluxGroup 对（防服务端重建同步对·已入 orders 物理件区⑥）；③绊线兜底=IntegritySentinel 5min（再动即告警+git 分钟级恢复·今日 16/16 实证）。

- 2026-09-29: **eCloud 关单追记**（CEO 原话「行，我卸载它！」「已经卸载了，之后的工作你们弄好」）：卸载四面核实 ✓（`C:\Program Files\ecloud` 无+进程 0+卸载注册表项 0+`%APPDATA%\eCloud` 无）+死自启键清除（HKCU Run eCloud 残键指向已删 exe）；事发证据包留档 `.codely-cli/labbench/incident-evidence-ecloud-20260929/`（同步库备份 16KB+窗口日志 23MB·09-28 批停悬案调查面）；善后派单=**P-2026-09-29-10**（@BigMoney/@Biggame/@FluxVerse/@BigCompute·72h 窗截止 10-02：各仓冲突垃圾清理+market-cal 内容核验+BG-C 游戏侧心跳复跑+DailyDigest 复启自查+bm-a 心跳 ts 写手修复+B/C 机两集团任务注册）——「之后的工作你们弄好」=委员会常务承接·OrderSentinel 即唤。

- 2026-09-30: **FluxGroup-DiskSentinel 入账**（CEO 令「清理的机制要前置一点，及时一点，磁盘空间很有限，科学制定」·T2+否决窗 7 天）：5min 磁盘哨兵=三线预警（黄 700/红 620/硬底 500GB·最坏夜耗 56GB 反推恒保 ≥2 夜跑道）+龄控 Class-A 自清（闸随级收紧 temp/trash 168h→48h·残片 48h→24h·在飞保护恒在）→alerts.jsonl+disk-sentinel.json；正典=resource-chain §三§11.9 磁盘预算与分层响应制（预算表前置立额+分钟/轮/批/周四级响应）；首扫实弹 1466MB（hf-cache 回潮即时捕获）；B/C 机采纳照机器对称律。

- 2026-10-04: **FluxGroup-FleetLink 入账+OrderSentinel 分发钩 v1.3**（CEO 令 10-04「决策和分发的链条+机队组网弄好·git 慢」+追加全权授权令·O-20260928-1855③ 状态面 v2 执行批）：5min 保活微监听（/health //status 心跳 10s 级直读 /poke 白名单点火+九仓 `pull --ff-only`——**信号零数据·git 仍唯一数据通道**·tailnet 100.64.0.0/10+loopback 双绑·单实例端口占用即退·VBS 静默·零提权=Tailscale-In 防火墙规则复用）+`fleet-dispatch.ps1` 分发器（OrderSentinel 钩=新 P0/P1/T0/T1 令→全机队秒级 poke·fail-soft）+节点名册 `Tools/fleet-nodes.json`（bm-a 在网 100.110.185.62·bm-b/bm-c 待 tailscale 登录链接·BG-B/C 采纳窗）；bm-a 实弹三验毕（health 双通道/status 直读/poke 拉取+白名单 deny）；B/C 机采纳=机器对称律（`register-fleet-link.ps1` 幂等注册·host/tailnet_ip 填名册后 enabled=true）。

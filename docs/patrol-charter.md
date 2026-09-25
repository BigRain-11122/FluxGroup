# Patrol Charter — 集团巡检机制正典 v1.0

> 溯源：CEO 令 2026-09-25 ~11:38「集团层面成立巡检机制，周期性巡检各个子公司实验室，并整改他们。」
> 定位：**集团层对各子公司 + CPH4 实验室 + HQ 自身的周期性运营体检与整改闭环机制**。与既有面正交不重复（cadence 防重复律#1）：
> - governance §10（AI 诚实律三道防线）= 管「说的和做的一致」；巡检 = 管「运营健康与整改闭环」，消费 §10 工具面为证据源。
> - 值守轮（03:07/15:07 四器审计）= 日频点检；巡检 = 周频深度体检+整改派单追踪，覆盖面=全部实体。
> 本文件 = 巡检机制唯一正典；巡检官会话（Tools/patrol-prompt.txt）按此执行。

## 1. 周期与触发
- **常规班**：每周一 09:23（OS 任务 `FluxGroup-PatrolRound`·零窗 InvisibleRunner·当班 host 见 §6 认领面）。
- **加开班**：CEO 可随时加开——硅基窗点任意卡片「马上办：立即跑一次集团巡检」或 `Start-ScheduledTask FluxGroup-PatrolRound`；同日戳记未过期时跳过（`-Force` 例外由 runner 参数控制）。
- 单班时间盒 25 分钟；超时先落已核验部分+残面记下轮指针。

## 2. 巡检对象（9 实体）
HQ（FluxGroup 治理层自身）· MiniGame（游戏）· FluxVerse（元宙）· BigMoney（量化金融·含 BigMoney-data 挂账面）· BigStream（媒体）· BigLife（生命）· BigDomain（域名）· BigCompute（算力）· CPH4 实验室。

## 3. 巡检七维（每实体逐维过）
1. **活性**：last commit 龄 / 7 日提交数 / 工作树脏度（probe 机械层给出）
2. **台账健康**：canonical 台账文件存在+新鲜（断更>7 天=YELLOW 起步）
3. **数据新鲜度**：状态导出（status-export）/ 心跳文件 / 世界数据龄
4. **证据链抽查**：近 3 批 commit 抽 1-2 条核证据指针真实存在（禁轻信提交信息）
5. **红线合规**：集团 governance §1-§11 + 各司自身章程红线（禁私建仓/写域越界/台账断更/停用任务复活等）
6. **整改闭环**：上轮 PT 项逐条核验——读证据指针定谳，禁轻信状态字段
7. **风险面**：调度健康（task-health）/ 机队心跳（fleet-audit）异常 + 巡检官现场发现

## 4. 判色与严重度
- **GREEN**：七维无异常或仅 P2。
- **YELLOW**：存在 P1 或台账断更或数据陈旧。
- **RED**：存在 P0（红线违规/数据面损坏/整改逾期升级）。
- 严重度与整改时限（governance §11 交付时效律）：**P0=24h / P1=72h / P2=7d**。

## 5. 整改派单（核心闭环·禁只巡不改）
每条发现 → 两处落档：
1. **docs/patrol-ledger.md** 加行（权威台账·PT-YYYYMMDD-NN 编号·字段：实体/级别/发现/要求动作/证据指针/截止/状态 OPEN）
2. **派发实体 canonical intake**（加速通道）：

| 实体 | canonical intake（只许写此处·禁碰其他面） |
|---|---|
| MiniGame | `Design/configs/GLOBAL/AI反馈队列.md`（FE 条目·C 机 tick 班 10 分钟内自消费） |
| BigMoney | `fleet/orders/` 新 O-行 |
| BigStream / BigLife / BigDomain / BigCompute | 各自 `orders/`（或 `orders.md`）区 |
| FluxVerse | `docs/` 台账面 + `watch/` 反馈面 |
| CPH4 | `cph4/registry/` + 周进化轮消化 |
| HQ | 本台账 + governance 变更控制流程 |

- **P0/P1 快唤**：额外在 `cph4/evolution-ledger.md` 追加含 `@司` 标签+级别的行 → FluxGroup-OrderSentinel（2 分钟）即时唤醒该实体 OS 循环（`Tools/order-sentinel-map.json`）。
- **实体仓写纪律**：派单落实体 intake 后由该实体自己的 lane 收口提交；巡检官会话不代司提交产品面。intake 推送失败→如实记档，HQ 台账行=唯一权威（各司 lane 经 HQ 仓亦可见）。

## 6. 防重复与认领面
- cadence.md 周轮族已注册本任务（同用途唯一制）。
- **戳记认领**（F-09 跨机周期任务认领律）：每班开跑写 `.codely-cli/patrol/patrol-stamp.json`（时间+host）；他机 runner 见戳记<20h 即跳过本班。任何机器可按 charter 接管 hosting（cadence 表改注 host）。

## 7. 产出面
- `docs/patrol/patrol-YYYY-MM-DD.md` 巡检报告（逐司判色+发现+派单指针+总评+闭环率+CEO 需拍板事项）
- `docs/patrol-ledger.md` 整改台账（唯一闭环追踪面）
- `.codely-cli/patrol/patrol-ledger.txt` 运行台账（PATROL_DONE 标记·runner 成功 oracle）

## 8. 诚实律
每句判断带证据指针；probe 未覆盖且巡检官未核验的面如实写「未覆盖」；禁编造；判色禁唯亲（子司自报≠证据）。

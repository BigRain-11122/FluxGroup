# 系统总图与去冲突（2026-11-10）

> 目的：回答一个问题——**谁在哪一层、负责哪件事、只能有一个入口**。
> 背景：主控机现有 33 个 launchd 服务、约 100 个脉阶段、257 个 Tools 工具，加上 Codely 运行时；
> 近期新增又叠了一层，出现同名/同职责。本件从顶层排到落地，给每个能力定唯一归属。

## 一、顶层：三层治理 + 一个运行时

    决策层（人/委员会）  CEO → 决策委员会（7 席）→ 台账（orders/decisions/POOL，CEO-PROXY 单写手）
    调度层（控制面）    主控脉 master_pulse（45s，只跑阶段）+ 派单单写手 master_agent
    执行层（算力面）    机队 bm-a/b/c/d + 本机 bm-m 本地模型 + Codely/Codely Bridge（对外/深判）

**Codely 的定位（关键，避免冲突）**：
- Codely 是**执行体/深度会话运行时**，不是调度器、不写集团台账；
- 程序化调用只允许走 `Tools/fleet/codely_bridge.py`（合规闸 + 路由 + 留痕）；
- 脉与车道**不得直接调 Codely**；云只做 L3 升级件；
- `.codely-cli/` 是各仓的本地配置/记忆，不是集团正典。

## 二、四张面（同一件事只在一张面上）

| 面 | 唯一载体 | 职责 | 不许做的事 |
|---|---|---|---|
| 调度面 | master_pulse + master_agent | 节拍、派单、回收、状态迁移 | 不写产品代码、不做内容生产 |
| 执行面 | lanes/<node>.json + lane_agent | 认领、执行、回执 | 不改队列（单写手）、不跨仓写 |
| 同步面 | state_sync（60s） | git 提交/拉取/推送 | 不做业务判断 |
| 观测面 | console（8787）+ 日报/看板 | 展示盘上事实 | 不只读不写、不产生新事实 |

## 三、现状清单与归属判定

### 3.1 观测/页面（冲突最重）

| 组件 | 现状 | 判定 |
|---|---|---|
| console 8787 | 实时面板 + 三级信息 | **唯一主页面（保留）** |
| dashboard / seats / fleet-console.html | 早期看板/静态快照 | 降为二级：只做链接，不重复采集 |
| webai 8088 | 本地模型对外聊天页 | 保留，定位=对外演示，不进治理 |
| DAILY-BRIEF.md / OUTPUT-BOARD.md | 我新增 | 保留，作为 console 的数据源，不再单独成页 |
| MASTER-SCREEN / CEO-THREE | 既有 | 保留（正文），console 只引用不复制 |

### 3.2 巡视（同名冲突）

| 组件 | 现状 | 判定 |
|---|---|---|
| `patrol.py`（脉阶段 patrol） | 把多报告合成一份行动清单 | 保留（**行动排序**） |
| `patrol_local.py`（launchd 名也叫 patrol） | 十域本地模型巡视 | **改名 patrol_seats**，避免与上一行同名 |
| PATROL-FLEET 蓝图 | 十域席章程/30min | 保留为章程正典；本地实现是它的 L1 替代 |

### 3.3 同步/自愈

| 组件 | 判定 |
|---|---|
| state_sync（60s，独立面） | **唯一 git 同步入口**；state_push 阶段已从脉移除 |
| state_push.py | 降为遗留工具：只允许手动/迁移用，不再挂脉 |
| watchdog（120s） | 看脉与同步面 |
| selfwatch（300s） | 看**产物新鲜度**（worker/patrol/analyst 等）——与 watchdog 分工不重叠 |
| loadwatch（60s） | 供给水位 + 补料 |
| resource_governor（60s） | 内存/swap 红线 |

### 3.4 判断/生成

| 组件 | 判定 |
|---|---|
| local_judge（4B→8B→云） | 唯一判断入口；云必须带 local_tried |
| local_worker（回执判读） | 保留：感知面，产物 LOCAL-DIGEST |
| local_analyst（8B 研判） | 保留：每小时一次，跑完即卸 |
| digest_agent / brain_service（脉慢批） | 保留：既有机队大脑；与 worker 输入不同（队列/臂） |
| loop_close（假绿/决策转卡/巡视转卡） | 保留：收口器；与 ceo_default 分工=它只转不裁 |

### 3.5 派单

| 组件 | 判定 |
|---|---|
| master_agent | 唯一派单写手（含产品优先排序） |
| promote_ready（每拍） | 补 READY→OPEN 断点，保留 |
| backlog_fill / night_fill / workgen / line_plan | 造卡器，保留；不得直接写队列 |
| cloud-smart 路由 | 必须 local_tried，否则排队 |

## 四、冲突矩阵（12 组，逐条定案）

| # | 冲突 | 定案 |
|---|---|---|
| 1 | patrol.py vs patrol_local.py 同名 | patrol_local 改名 patrol_seats；launchd 标签同步 |
| 2 | console vs dashboard/seats | console 唯一主页面；其余只做链接 |
| 3 | state_sync vs state_push | state_sync 唯一；state_push 退役出脉 |
| 4 | selfwatch vs watchdog | watchdog 管进程/心跳；selfwatch 管产物；互不越界 |
| 5 | daily_brief vs MASTER-SCREEN | 日报是聚合视图；屏幕仍是正文，日报只引用 |
| 6 | output_board vs fleet_status | 看板=产出；fleet_status=机队健康；互不复制 |
| 7 | loop_close vs ceo_default | loop_close 只转卡不裁决；裁决仍走 ceo 面 |
| 8 | local_worker vs digest_agent | 输入不同（回执 vs 队列）；产物不同；都保留 |
| 9 | local_analyst vs brain_service | analyst=小时级综述（8B）；brain=慢批判读（4B）；不合并 |
| 10 | Codely vs 脉/车道 | 只经 codely_bridge；禁止直调；不进循环 |
| 11 | 两个网关 8792 / llmgateway | 8792 是机队借算力唯一口；llmgateway 若同职责则退役 |
| 12 | fleet_selfcheck vs bootstrap-machine | selfcheck=只读体检；bootstrap=装机；不互相替代 |

## 五、从顶层到落地的整理顺序

**P0（本周，去同名/去双写）**
1. patrol_local → patrol_seats（文件/标签/selfwatch/cadence 同步）；
2. state_push 标注 LEGACY，确认不再被脉或 launchd 调用；
3. dashboard/seats 在 console 顶部只留链接，不再各自采集；
4. 所有新任务在 cadence 总账有行（已完成一批，补齐剩余）。

**P1（两周，收敛入口）**
5. 统一 LLM 网关：只保留 8792（机队）+ 11434/11436（本机），其余网关退役；
6. 观测面只留 console 一个采集器，日报/看板变成它的数据源；
7. 判断入口只留 local_judge（含 8B 二判），其余散落判断改调它。

**P2（一月，制度固化）**
8. 每个能力写一行"唯一入口 + 产物 + 失败等级"进 mechanism-map；
9. 新增工具必须先登记 cadence 与 mechanism-map，否则不进 launchd；
10. 季度审计：删掉 90 天无调用的工具与服务（法熵预算）。

## 六、验收

- 同名服务=0（launchctl 标签唯一、工具文件名不撞）；
- 双写=0（每个状态文件只有一个写手）；
- console 一页能回答：脉/队列/算力/产出/巡视/自愈；
- 任一新增能力都能在 cadence + mechanism-map 找到登记行；
- Codely 只出现在 codely_bridge 的调用链里。

# 夜间值守记录 2026-11-08（CEO 睡觉期间）

CEO 原话：「我睡觉了 你保证智能体和机队满负荷工作」

## 一、进场时"满负荷"是假的（四处结构缺陷）

| # | 症状 | 根因 | 处置 |
|---|---|---|---|
| 1 | 18 张卡永久 RUNNING、机器空转 | `lane_agent.py` 并行槽位调用 `_run_one_job`，**定义被 checkout 顶掉只剩调用点** → NameError | 补回定义，步序与单卡一致（RUNNING→run_job→RESULT）；实测一轮 6 张并行、5 张真出产物 |
| 2 | `model_plan` 每轮报 E-KEEPALIVE | 非驻留档 `keep_alive` 写 1m，而 `budget.resident_set` 只含主力+向量；**同一事实两处判据** | 策略与矩阵两处同时改 0；网关 `or "5m"` 会把 0 吞成 5m，一并修 |
| 3 | 队列 414 行非 JSON，严格解析直接崩 | `job(...): artifact` 提交**整份覆盖** `PRODUCTION-QUEUE.jsonl`，把未解决的 138 个空冲突块提交进历史（备队列 20 块） | 新增 `queue_sanitize.py`（--check/--fix，冲突块取两侧并集按 id 去重、留审计报告）；两份队列已清；RG-30 焊死 |
| 4 | 17 张纯 CPU 审计卡全压主控，bm-a/bm-c 空转 | `supply_batch` 把 `nodes` 与 `hard_nodes` 都写成 `["bm-m"]`（主控不做生产是 CEO 硬边界） | 改为按 `slots_per_node` 非主控机轮转（实测 4/4/4/4）+ 去掉 hard_nodes |

## 二、修复后实测

- 回归 **30/30 PASS**（新增 RG-30：队列禁冲突标记 + 清洗器负控）
- 主控脉 `blockers=[]`，ts 持续推进
- 在飞从「bm-m 18 独干」变为 **五台分摊**：bm-a 2 / bm-b 2 / bm-c 2 / bm-d 1 / bm-m 8
- bm-m 两分钟内消化 14 张（17→3），证明并行执行真的在跑
- 三台 FleetLink 1.9.7 全部 `health=200`，`HQ-ProductionClaim` 均为 WAKE；poke 后 bm-a/bm-c 开始领卡
- bm-b 最近回执 02:24（活着且有产物）

## 三、仍不满足"满负荷"的诚实原因

1. **供给是真瓶颈**：OPEN 常年在 2–5 张。生成器能铺的真活（软著/提审/审计/分诊）已铺完且幂等去重，再铺就是造活。`supply_batch` 现在返回 0 张可铺。
2. **bm-d 自 11-06 17:48 无心跳**，tailnet 里查不到该机（唯一在飞 1 张是历史残留）。
3. **三条子仓线（bigdomain / bigcompute / bigmoney）无"第一件真产物"定义**，属业务方向决策，不是调度能解。
4. 令牌未分发到 bm-a/b/c（无加密通道，只能带外一次性准备），跨机调网关仍不通。

## 四、值守安排

每 30 分钟一轮（cron `13,43 * * * *`，session-only）：查队列污染 / 脉推进 / 回归与模型体检 / 按机器分布查堵点；只做确定性可逆动作（补卡、改字段、推同步、重跑、重建），不对外、不花钱、不改阈值。
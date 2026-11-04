**工单预备清单**

| 车道 | 当前可派卡 (需 ≥3) | 缺口/状态 |
| :--- | :--- | :--- |
| **bm-a** | 基于 `MASTER-STATE.json` 仅含 1 张 (`open:7` 为累计，非单车道独立待办数量)，且 `bm-a` 有活跃任务 (`R-TRIAGE...`)，无独立可派单记录。 | **≥0 (无法确认)**；需读取底层 `queue-receipts` 文件确认 bm-a 单独库存。 |
| **bm-b** | 同左：`MASTER-STATE.json` 仅体现累计 open 数，未体现单车道 `need-work/*.json` 内部库存。 | **≥0 (无法确认)**；需读取 `/cph4/fleet/dispatcher/NEED-WORK/bm-b/*` 确认。 |
| **bm-c** | 同左：无独立待办数量统计，仅知系统 total 及 bm-c 正在自调度 ready cards。 | **≥0 (无法确认)**；需读取 `/cph4/fleet/dispatcher/NEED-WORK/bm-c/*` 确认。 |

**Need-Work 响应规则**
检测到 `cph4/fleet/state/need-work/*.json` 中状态为 `IDLE` 的通道卡，立即触发优先派单逻辑（P0），并在 **2s 内** 响应分配请求。

**提前备单计划**
1. **Backlog 晋升预检**：每小时轮询 `MASTER-STATE.json`，若 `open > threshold` 或特定 lane `idle_confirmed=false` 且负载异常，自动生成晋升工单。
2. **Line_plan 工序预生成**：解析 `stages` 中 `verdict: STALLED/PARKED/NO-DATA` 的阻塞点（如 `mv-kf`, `game-design`），提前调用脚本预生成分配清单至待办队列，避免静默积压。
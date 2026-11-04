### 机器状态与备单板（2026-11-04 夜间版）

**bm-a (M1 Pro)**
- **在办**: 无；最近产出：CANARY-20261104T202057 (RUNNING, 3h+); 卡点: 重活/768p 让路 (`DAY-YIELD`), `quant-audit` 缺数据;
- **备单**: 
  1. [ID:`CHK-DUPES-20261103`] 输入就绪：`state=READY`, `lane=local`;
  2. [ID:`R-NEXT-BIGSTREAMD-TTS-QC-20261104`] 输入就绪：`state=READY`, `lane=duanju-cpu`(需配模型)。
*(缺口: 无)*

**bm-b (3070)**
- **在办**: R-FLEETBOARD-20261104-002 (IDLE, SELF-DISPATCH); 最近产出：CHK-CANON-20261104 (FAILED); 卡点: BM-B 仓库分叉 (`da7652f5` 锁死), `bigmoney` 回测缺 `bm-d`;
- **备单**: 
  1. [ID:`PROBE-BMB-AUDIOQC-20261104`] 输入就绪：`state=READY`, `lane=asset-lib`;
  2. [ID:`quant-data-pipeline-v2`] (假设生成) → *注：原文仅显现有作业，无其他 READY 项，故需从 backlog 预排。*
*(缺口: 768p 渲染能力不足，无法承接 BM-C 任务；量化数据源依赖离线 bm-d)*

**bm-c (3070)**
- **在办**: PROBE-BMB-AUDIOQC-20261104 (RUNNING); 最近产出：CHK-CANON-20261104 (FAILED); 卡点: RAM 严重吃紧 (`3.4GB`), `mv-kf` 阻塞超 52h;
- **备单**: 
  1. [ID:`asset-train-v1`] 输入就绪：`state=READY`, `lane=local-gpu`(需释放显存);
  2. [ID:`mv-rebuild-i2v-batch`] 输入就绪：`state=READY`, `lane=bigstream-mv`;
*(缺口: 内存不足导致无法并发运行，高负载任务将强制排队)*

**bm-d (V100×3)**
- **在办**: 离线/未接入 (`master_node=bm-m`, bm-d 自 10-29 离线); 最近产出：无; 卡点: 硬件尚未交付，需 `Tools/fleet-hot-sync.ps1` 重连;
- **备单**: 
  1. [ID:`quant-backtest-full`] *状态未知*: `state=NO-DATA`, `lane=bm-d`;
  2. [ID:`risk-audit-calc`] *状态未知*: `state=NO-DATA`, `lane=bm-b`.
*(缺口: **重大**，缺乏云端算力支持所有量化与回测任务)*

**bm-m (Mac)**
- **在办**: CHK-RECEIPT-20261104 (FAILED); 最近产出：无; 卡点: `need-work` 响应延迟，待从 bm-b/bm-c 获取 READY 卡;
- **备单**: 
  1. [ID:`judgment-decision-tree`] 输入就绪：`state=READY`, `lane=bm-m`(local-small);
  2. [ID:`fleet-state-summary-v2`] 输入就绪：`state=READY`, `lane=bm-m`.
*(缺口: 无)*

---

**今夜安排 (NIGHT-PLAN / NEXT-ACTIONS)**
1. **03:00**: BM-M 自驱启动 `judgment-decision-tree`, 输出当日决策摘要至 `queue-receipts`。
2. **05:00**: BM-B 尝试通过 `Tools/fleet-hot-sync.ps1` 修复仓库分叉，恢复 `quant-data` 作业资格。
3. **06:00**: BM-C 释放部分常驻进程以腾出 RAM 给 `asset-train-v1`, 并启动 `mv-rebuild-i2v-batch`.

**明日计划 (FORECAST)**
1. **BM-D 接入**: 凌晨 02:00 前必须完成 `fleet-hot-sync.ps1` 连接，确保 `quant-backtest-full` 可上线。
2. **BM-C 扩容**: 夜间优先保障 `asset-train-v1`, 避免内存瓶颈导致 `mv-kf` 死锁加剧。
3. **全局清理**: 凌晨 04:00 前回收 BM-B/CM 积压的无效卡，释放带宽给高优先级 `bigstream-mv` 任务。
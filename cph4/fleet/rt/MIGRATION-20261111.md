# 存量卡迁移记录 · 2026-11-11T11:50

> 依据：`SYNC-DESIGN-v2.md` §九。来源=`origin/main:cph4/fleet/PRODUCTION-QUEUE.jsonl`（以远端为准，本地队列被多机并发重写）。
> 口径：按 `LINE-REGISTRY.owner_station` 归位；线字段缺失的按 ID 前缀推断；机制/同步类活不进产品队列。

## 一、总量

| 项 | 数 |
|---|---|
| 迁移输入（非终态卡） | 41 |
| OPEN | 6 |
| RUNNING | 2 |
| BLOCKED | 30 |
| UNVERIFIED | 3 |
| 写入分片合计 | 41（无丢失） |

## 二、分片结果

| 工位 | 行数 | 状态分布 |
|---|---|---|
| delivery 交付工厂 | 10 | OPEN 2 / BLOCKED 1 / CANCELLED 7 |
| visual 视觉工位 | 15 | OPEN 1 / UNVERIFIED 2 / CANCELLED 12 |
| audio 声音工位 | 5 | OPEN 3 / BLOCKED 2 |
| brain 大脑工位 | 2 | UNVERIFIED 1 / CANCELLED 1 |
| control 主控台 | 9 | CANCELLED 9（机制/同步类） |

## 三、处置规则（写进数据的判据）

1. **RUNNING 但无车道认领**（2 张）→ 复位为 OPEN，清 owner，记 `migration_note`。
2. **OPEN 且带 `blocked_by: no-claim-executor`**（5 张）→ 清掉该字段，按工位重新入队（新模型里执行器由工位承担）。
3. **BLOCKED 且有 `blocked_by`**（3 张）→ 原样保留原因（缺输入、主机离线、人工裁决）。
4. **BLOCKED 且无任何原因**（27 张）→ 作废并写 `cancel_reason`：
   「无 blocked_by 说明，清障条件无法判定；需要时按产品工序重开并带验收判据」。
   理由：这 27 张是队列里的黑洞——没人能执行、没人知道怎么解，留着只会继续占位。
5. **机制/同步类**（NODE-SYNC / UNBLOCK / REPAIR / CANARY / PROBE / R-TRIAGE / GAP / AUD，9 张）→ 作废，理由「v2 分片后由 state_sync --station 承担」。留在 control 分片仅供追溯。

## 四、当前可执行面（迁移后）

1. visual：1 张 OPEN（R-NEXT-BIGSTREAMM-REBUILD）+ 2 张待核（Q-MV-0001-003、asset-lib-char-gen）。
2. audio：3 张 OPEN（短剧/配音相关）+ 2 张带原因的 BLOCKED。
3. delivery：2 张 OPEN（含 bighouse 巡视处置）+ 1 张待人工裁决。
4. brain：1 张待核（C-FIN-ETF-COMPOSITE）。
5. control：0 张可执行（只有作废记录）。

## 五、下一步（batch 3）

1. `master_agent` 改为读五份分片（保留旧队列只读兜底）。
2. 旧 `PRODUCTION-QUEUE.jsonl` 停止写入，标 `frozen_at=2026-11-11`。
3. 按产品工序为各工位补第一批真卡（提审材料、MV 关键帧、配音母版），每张带验收判据。

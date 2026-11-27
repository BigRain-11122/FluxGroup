# 机队对齐回执 · bm-b（2026-10-29 23:40）

> CEO 令 2026-10-29「把整个机队配合好他的主控！」的 bm-b 侧执行回执。
> 主控 = bm-m（MacBook，`cph4/fleet/MASTER-NODE.json`）。本件只写实测，不写计划。

## 一、bm-b 侧病灶（修前）

| 项 | 实测 | 影响 |
|---|---|---|
| 工作树 | HEAD `da7652f5` vs origin `a6bbc8f1`，**落后 744 提交** | `Tools/fleet/lane_agent.py` 等新车道执行器根本不存在 |
| 认领任务 | `HQ-ProductionClaim` 跑 `queue_claim.py --pool`（旧全局队列） | 主控写的 `cph4/fleet/lanes/bm-b.json` 无人消费 |
| 主控视角 | `MASTER-LOG.md` cyc=537 `idle=bm-b:SELF-DISPATCH` | 机器活着但不接活 |

## 二、修法（不动主工作树）

主工作树仍被其它窗口使用且带 744 提交的代差，**不做 reset/checkout**。改为建独立控制面运行副本：

- 路径：`C:\Fluxgroup\FleetRuntime`（`git clone --filter=blob:none --sparse`）
- 物化器：`Tools/fleet-sync.py`（从主仓对象 `git show origin/main:<path>` 直接落 14 件，秒级；
  不走 SSH 逐 blob 稀疏检出——实测单文件一次往返，14 件要几分钟且易断）
- 认领批处理：`C:\Fluxgroup\FleetRuntime\Tools\hq-lane-claim.bat`
  顺序 = fleet-sync → fleet_hb（心跳）→ queue_claim --pool（POOL 卡）→ lane_agent（主控派活）
- 任务：`HQ-ProductionClaim` 重注册（`Tools/task-register.ps1`，S4U 静默链，every:5m）

**踩到并修掉的坑**：运行副本最初在批处理里带 `git pull`，而稀疏检出模式="/AI.md" 会在 pull 时把刚物化的 14 件当成"模式外文件"删掉 → 日志 `rc=2 / can't open file`。现改为「不 pull、只由 fleet-sync 物化」，并已 `core.sparseCheckout=false` 关掉剔除。

## 三、修后实测（2026-10-29 23:40:37）

```
SYNCED 14 / missing 0
HB bm-b seq=2 offset=948.2ms
POOL-EMPTY node=bm-b face=origin blocked=[]
LANE-IDLE bm-b :: SELF-DISPATCH: lane scans its own backlog
```

- 任务 `LastTaskResult=0`（注册工具要求"干净点火"才算部署，PASS）
- 心跳已发到 NATS hub（seq=2），主控可感知 bm-b 在线
- 车道文件读取走 origin blob，主控一派活就能领

## 四、机队其余三台（本机不可代跑，CEO 2026-10-23 令：禁跨机远程执行）

| 机 | 状态 | 已发动作 | 待其本机执行 |
|---|---|---|---|
| bm-a | `:8790` 通、poke accepted；主控日志判 OFFLINE | `MSG-20261029-2325-bmb-fleet-align-bma.md` + poke | 确认 HQ-MasterAgent/FleetDispatcher/IdleWatch 已 Disabled；`Tools\fleet-hot-sync.ps1`；lane dry |
| bm-c | `:8790` 通、poke accepted；工作树停在 `994d63ca`、RAM≈0.8G | `MSG-...-bmc.md` + poke | 同上 + `HQ-ProductionClaim` 启用 + 释放内存 |
| bm-m | 主控本体，日志 23:18 后断更（笔记本睡了/未跑一键轮） | 已补 `setup-mac.sh` 的 `git pull`（提交 `ee336b74`） | **重跑一次 `bash setup-mac.sh`** 才会重新生成带 pull 的运行器；然后 `bash tools-run-once.sh` |

## 五、验收线（下次看这三行）

1. `cph4/fleet/dispatcher/MASTER-LOG.md` 新行：`idle=bm-b:` 不再恒为 `SELF-DISPATCH`（有活时应为 RUNNING/无 idle 项）。
2. 队列出现 `R-SUBCO-20261029-00x` 且 `q=` 第一段非 0（=Mac 已拉到新规则）。
3. `cph4/fleet/queue-receipts/bm-m-subco-brief.md` 等三份产物落地（=Mac 真的在管子公司）。
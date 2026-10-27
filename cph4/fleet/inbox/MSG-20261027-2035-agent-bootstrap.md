# MSG-20261027-2035 — fleet-agent 引导（bm-b / bm-c）

**背景**：试验证明“分发到 git”≠“机器执行”。bm-a 已装 fleet-agent 并实测：命令 → NATS → agent 回 `ACK done`（含 CPU/RAM/GPU 实测），全程 5 秒内。

**Agent 边界**：只处理 `selfcheck` / `noop` 并写回执；不执行任意 shell；不停止、不重启任何现有任务。

## bm-b（必须先解分叉）

```powershell
cd <repo 根>
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-hot-sync.ps1 -Push
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\task-register.ps1 -Name FluxGroup-FleetAgent -Script "<repo 根>\Tools\fleet\fleet_agent.py" -Arg "--node bm-b --serve" -Trigger every:1m -NoFireTest
Start-ScheduledTask -TaskName FluxGroup-FleetAgent
```

## bm-c

```powershell
cd <repo 根>
git fetch origin main
git checkout origin/main -- Tools/fleet/fleet_agent.py Tools/fleet/fleet_order_bus.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\task-register.ps1 -Name FluxGroup-FleetAgent -Script "<repo 根>\Tools\fleet\fleet_agent.py" -Arg "--node bm-c --serve" -Trigger every:1m -NoFireTest
Start-ScheduledTask -TaskName FluxGroup-FleetAgent
```

## 验收

下一条机队命令后，仓库出现：

```
cph4/fleet/cmd/<cmd_id>.<node>.ack.json   status=done   stats{cpu/ram/gpu}
```

且 order-bus 的 receipt 里 `acks` 显示该节点 `done`。

## 生产领取任务（解除 no-claim-task 阻断）

bm-b 的三张卡当前被 `blocked_by: no-claim-task:bm-b` 挡住。装完 agent 后，再装领取任务：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\task-register.ps1 -Name HQ-ProductionClaim -Script "<repo 根>\Tools\queue_claim.py" -Arg "--node bm-b" -Trigger every:1m -NoFireTest
Start-ScheduledTask -TaskName HQ-ProductionClaim
```

装好后回报，主控再清 POOL 里的 `no-claim-task:bm-b`（未确认安装前不清，避免假可执行）。

## 备注

- 任务走 `task-register` 隐藏链，S4U 未提权会降级为 InteractiveToken（注销登录后不跑），已入 `task-s4u-backlog.md`。
- bm-m（Mac）到位后用 launchd 跑 `python3 Tools/fleet/fleet_agent.py --node bm-m --serve`。
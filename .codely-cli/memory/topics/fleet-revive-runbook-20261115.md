# 远程拉起机队的手册（2026-11-15 实测，CEO「你拉起他们干活」那一轮换来）

## 1. poke 契约：reason 必须含 `enable-tasks`

```
POST http://<node>:8790/poke
{"reason": "<ASCII，必须含 enable-tasks 字样>", "tasks": ["<白名单任务名>"]}
```

坑：reason 不含 `enable-tasks`（例如「CEO 令：拉起执行器干活」）时，服务端回
`{"ok":true,"accepted":true}`，但 `wakes` 永远是 `[]` —— 看起来叫过了，实际一次都没叫。
我第一次就中招，白等 30 秒。

白名单在 `Tools/fleet-nodes.json`：

- bm-a / bm-c 的 `enable_tasks` 都只有 `HQ-ProductionClaim`（v2 旧认领器）
- v3 工位执行器 `HQ-StationDrive` 在 `wake_tasks` 里，可点名唤醒
- bm-m（本机）/bm-d（算力大脑）`enabled=false`，结构性不可认领

## 2. 正门工具（不要自己拼 curl）

- `python3 Tools/fleet/executor_revive.py --check` / `--apply`
  四种判定：offline（探不到）/ closeout（pull 报 `.:fail` 分叉）/ wake（wakes 空）/ healthy。
  退出码 0 全健康 / 1 本轮做了动作 / 2 仍有节点拉不起来。
- `python3 Tools/fleet/executor_guard.py [--dry]`
  守住「任务被禁回 Disabled」：只处理 roster 的 `enable_tasks`，CEO 让路态整机跳过，
  只调 `/poke` 大众入口，不碰 OS、不杀进程。

实测（2026-11-15）：bm-a 从「执行器死 16.1h」→ healthy，wakes 出现
`HQ-ProductionClaim:WAKE`，CPU 52–62%，HEAD 持续变化。

## 3. 通道边界（当日实测，别再试错）

| 机器 | IP | 可用 | 不可用 |
|---|---|---|---|
| bm-a 公司生产力机 | 100.110.185.62 | 8790 poke / 445 SMB / 3389 RDP / 4222 NATS | 22 SSH、5985 WinRM 均关 |
| bm-c 传家宝 | 100.123.74.104 | 445 SMB / 3389 RDP | **8790 未监听**、22、5985 关 |
| bm-b 小钢炮 | 100.82.175.0 | — | 离线 4 天 |

- NATS 4222：server 活着，但 **FleetAgent 没订阅 `fleet.cmd`**。手工 `PUB fleet.cmd`
  后 60 秒收不到 `fleet.ack`，所以 NATS 现在**不是** exec 通道，别指望它。
- bm-c 只能 CEO 用远程桌面登进去启动 FleetLink/计划任务；我没有执行通道。

## 4. 「机器醒了却 no-task」≠ 复原有问题

先数分片队列里 OPEN 卡：

```
cph4/fleet/rt/<station>/queue.jsonl
```

2026-11-15 实况：delivery 15 张 = 10 DONE / 2 CANCELLED / 1 FAILED / 1 BLOCKED /
1 僵尸 RUNNING(`claimed_by=None`)，**OPEN=0** → 机器再健康也只能空转。
根因是 43 道工序里 23 道「命令未接」，SUPPLY 造不出卡。

## 5. 已知缺陷：remote_closeout_card 的卡 id 硬编码

`Tools/fleet/remote_closeout_card.py` 第 76 行卡 id 写死
`"REMOTE-CLOSEOUT-%s-20261107" % node`，一旦投过就永远判「已存在」并 skip，
`--apply` 再也投不出新卡。要重新收口必须先把 id 逻辑改成按日期生成。

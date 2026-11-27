# v3 同步与启动 · 现场清单（2026-11-12 17:5x 快照）

> 远程能做的都做了：poke 能唤醒任务、`/sync` 只能写 JSON（不能部署代码），
> 所以"代码收口 + 装执行体"这两步必须在机器上执行一次。判据只看事实，不看回执。

## 一、传家宝（bm-c / FLUXGROUP，K:/Fluxgroup/FluxGroup）

现状（实测，2026-11-12 17:53）：

| 项 | 实测值 |
|---|---|
| 机器在线 | 是（tailnet relay，ping 438ms，8790 在听） |
| `/status` 版本 | FleetLink 1.9.7 |
| 本地 HEAD | `359e11fb`（**origin 上没有这个提交**，是本机独有） |
| origin_main | `b96bd086` |
| 分叉 | 领先 1 / 落后 4（`git merge --ff-only` 不可能成功） |
| `pulls` 回执 | 写的是 `.:updated` —— **与事实不符**（假绿，已在改善台账记 IMP-SYNC-bm-c） |
| `HQ-StationDrive` | `no-task`（任务不存在，所以 poke 唤醒不了 v3） |
| 其它任务 | 12 个 Disabled，仅 `Bigmoney-IterationLoop` Running |

### 要执行的两件事

**1）收口代码（保留本地那 1 个提交，别硬 reset）**

```bat
cd /d K:\Fluxgroup\FluxGroup
git fetch origin
git log --oneline HEAD --not origin/main        :: 先看清本地那 1 个提交是什么
git rebase origin/main                          :: 有冲突就解决；不确定就先 git branch backup-20261112
git log --oneline -1                            :: 验收：应为 b96bd086 或其后代
```

如果那 1 个提交是运行时产物（日志/回执/临时文件），可以直接丢掉：

```bat
git branch backup-20261112
git reset --hard origin/main
```

**2）装 v3 执行体**

```bat
cd /d K:\Fluxgroup\FluxGroup
python Tools\fleet\install_drive_agent.py --station visual --once   :: 先看它要做什么
python Tools\fleet\install_drive_agent.py --station visual --apply  :: 生成并注册（Windows 走计划任务）
```

验收（三条都要真）：

```bat
python Tools\fleet\station_drive.py --station visual --dry
:: 期望：status_note=blocked_no_comfyui 或 ready；unknown_output 里能看见 TOOL-PENDING 明细
type cph4\fleet\rt\visual\heartbeat.json
:: 期望：有 pid/ts/round，且 ts 是刚才
```

## 二、公司生产力机（bm-a）

`/status` 显示代码也未同步到 origin。同样两步：先 `git fetch && git rebase origin/main`，
再确认 `HQ-StationDrive`（或对应任务）存在并能跑 `station_drive --station delivery --once`。
它是唯一能跑游戏产线的机器，优先修。

## 三、主控侧已经就位（不需要现场）

- 供给/回收只看本分片（本地闭环），不再代写；
- 心跳与改善台账（`IMPROVE-BACKLOG-v1.json`）已在跑，这两台机器的落后与执行体缺失已入账；
- 巡检会报 `IMP-SYNC-*` / `STATION-NO-EXECUTOR`，不会因为"回执说 updated"就变绿。

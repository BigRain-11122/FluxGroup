# 统一指令面 v1（2026-10-28·CEO 令「机队要接统一的指令，不要自己干自己的」）

> 一句话：**机器只从一条线接令、只用一个执行器干活、只往一个地方报状态；任何节点不再往组仓里写东西。**
> 现状病根（2026-10-28 实锚）：每台机都往 `docs/orders.md` 追加、把 ack 提交进 `cph4/fleet/cmd/`——工作树一分叉，`git pull` 就 `kept-local`/`fail`，新令再也进不来。bm-b/bm-c 因此停摆 11 小时，poke 三次全 `accepted` 但 HEAD 不动。

## 一、六个"唯一"

| 面 | 唯一通道 | 废止项 |
|---|---|---|
| 指令入口 | **只有 `Tools/fleet-order-bus.ps1` / `fleet_order_bus.py`**（CEO 一句话→拆车道→写 cmd→推送→NATS 发布） | 禁人肉改 orders 当派单；禁某机自己开令 |
| 指令传输 | **NATS `fleet.cmd`（主）** + `cph4/fleet/cmd/<id>.json`（权威副本，断线补捞） | `docs/orders.md` 降级为**人类台账**，机器不读它接令、不往它写 |
| 指令读取 | **从 `origin/main` 的 blob 直读**（`git fetch` + `git show origin/main:cph4/fleet/cmd/<id>.json`） | 不再依赖工作树是否干净——脏树也照样接令 |
| 执行器 | **每机一个 `fleet_agent.py` 常驻**，按 cmd 的 `actions` 白名单执行 | 禁各机 OS 循环自建活；循环只准消费 `PRODUCTION-QUEUE` 卡片 |
| 状态 | **NATS KV `fleet.nodes.<id>`**（ts/head/last_cmd/job/lease/state） | status_files 心跳文件降为离线兜底 |
| GPU | **`gpu_lease.py` 租约**（acquire→run→receipt→release） | 无租约不许起 GPU 作业 |

## 二、节点只读律（根治分叉）

1. 节点**不写** `docs/orders.md`、**不 commit** ack、**不 push** 组仓。
2. ack 走两路：NATS `fleet.ack` 实时 + 本地 `cph4/fleet/acks/`（已 gitignore）留档。
3. 节点需要上报的产物：写本地 receipt，由**派单侧**（bm-a / 未来的 bm-m）汇总，不由节点推。
4. 例外只有一个：`Tools/fleet-hot-sync.ps1` 手动收口（fetch + rebase autostash，不 hard reset）。

## 三、命令对象与状态机

```json
{ "id": "OB-YYYYMMDD-HHMMSS-nnn", "ts": "...", "text": "...",
  "lanes": ["bm-b","bm-c"],
  "actions": [ {"kind":"selfcheck"}, {"kind":"sync"}, {"kind":"kf_batch","params":{...}} ] }
```

- `actions` 是唯一可执行面：**白名单 kind**，未列 kind 一律 `queued-for-owner`（不猜、不跑任意 shell）。
- 状态机：`issued → delivered → acked → running → done | failed`。
- 无 ack 超 5 分钟 = 派单侧重投一次 + 记告警；同一 cmd 每机只执行一次（seen 去重）。
- poke 只负责**叫醒 agent**，不再携带任务清单（wake_tasks 作废为"兜底唤醒名单"）。

## 四、执行器职责（每机同一个）

1. 连 NATS，订阅 `fleet.cmd`；启动时先补扫 `origin/main` 的 cmd 目录。
2. 车道过滤（`lanes` 不含本机=跳过）。
3. 按 `actions` 调白名单 handler；GPU 类先 `gpu_lease.acquire`。
4. 每步发 ack（NATS），结束发 receipt（本地 + NATS）。
5. 每 60s 发心跳到 `fleet.nodes.<id>`（含 head/last_cmd/job/lease/state）。
6. **没有 cmd 时它就是空的**——不自己找活。要活，由派单侧开卡。

## 五、迁移（节点恢复后照做）

1. 节点本机跑一次 `Tools\fleet-hot-sync.ps1`，把工作树收到 `origin/main`。
2. 计划任务 `FluxGroup-FleetAgent` 改为 `python Tools\fleet\fleet_agent.py --node <id> --serve`（S4U、隐藏、常驻）。
3. 派单侧确认三件：agent 心跳在 KV 里 60s 内、cmd 有 ack、产物有 receipt。
4. 验收：发一条 noop 令，三机 5 分钟内 `done`；再发一条 GPU 令，只有持租约的机器跑。

## 六、与既有法的关系

- 本件只定**命令面**；派单/催办/看板照旧（`fleet-dispatch.ps1`、`fleet_reality.ps1`）。
- 与 2026-10-27「任一台机的命令必须自动分发」同源：那条定"必须分发"，本件定"怎么分发才不被节点写崩"。
- 不新增台账、不新增索引；执行细节以 `Tools/fleet/*.py` 为准。
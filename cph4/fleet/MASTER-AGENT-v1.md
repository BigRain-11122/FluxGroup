# 主 Agent + 子公司 Agent（机队调度执行闭环）v1

> CEO 令 2026-10-29「建主 Agent 和几个子公司 Agent，循环派活、盯产出、不许闲置；调度要科学，每次能调云端或本地算力看自己该做什么」。
> 上一轮复盘已定根因：机队有心跳、有队列、有认领脚本，但**没有会造活和仲裁的执行器**，所以「没 OPEN 任务」被当成正常，三台机同时健康的空转（见 2026-10-27/28 判例）。

## 一、两层结构

| 层 | 文件 | 谁跑 | 干什么 |
|---|---|---|---|
| 主 Agent | `Tools/fleet/master_agent.py` | bm-a 计划任务 `HQ-MasterAgent`（每 2 分钟） | 造活 → 路由 → 派活 → 盯租约 → 报状态 |
| 子公司 Agent | `Tools/fleet/lane_agent.py` | 各机 `HQ-ProductionClaim`（每 5 分钟，经 `queue_claim.py` 接入） | 领本机任务 → 执行 → 回执 + NATS 上报；没活时自己翻本机积压 |

单写手原则：**只有主 Agent 改队列和车道文件**，执行机只读自己的车道文件。三台机是三个 git 克隆，双写队列必然分叉（2026-10-27 已实锤）。

## 二、主 Agent 每轮五个动作

1. **感知**：读 NATS KV `FLEET_STATE.state.<node>`（心跳、CPU/RAM/GPU、快照年龄）。
2. **造活**（只造真活）：
   - `PRODUCTION-BACKLOG.jsonl`：`requires` 全在、`deliverable` 不在才入队；
   - `WORK-RULES.jsonl`：规则化派生（当前 5 条 = v718 重建 → 交付闸 → 逐镜分级 → AIGC 标识 → 保真判定），同样按文件存在性判定，不猜不编。
3. **路由**：本地优先；只有任务自带云端腿且预估 ≤500 积分才走云端，>500 标 `blocked` 等 CEO 确认（不自行授权）。
4. **派活**：按 `needs` + 实时容量 + 工作时间让路 + 优先级选车道；**每车道同时只一件**，写 `cph4/fleet/lanes/<node>.json`。
5. **盯产出**：租约到期未回执 → 重排（3 次转 FAILED）；回执说 DONE 但交付物不存在 → FAILED；被让路推迟的任务立刻释放，不占租约。

## 三、子公司 Agent 的规矩

- 只读自己的车道文件（优先读 `origin/main` blob，脏工作树也拦不住）。
- 没派活时**先扫本机积压**（`backlog_fill`），只在输入真实存在于本机时才跑——这就是「问本地算力我该干什么」。
- GPU 任务先走 `gpu_lease.py acquire`（停常驻 LLM、禁 keepwarm、等显存、起 ComfyUI），跑完 release。
- 硬红线：**禁止自动拉起已打包游戏**（CEO 2026-10-28 令）；bm-a 白天（09:00-19:00 工作日）不接重活和 GPU 活，让路给 CEO。
- 结果写本地回执 + 发 NATS KV `FLEET_STATE.lane.result.<node>`，不回写主仓。

## 四、闲置的判定（关键）

「没派活」≠「闲置」。只有车道自己上报 `IDLE` 且连续两轮无活，才算 `IDLE-CONFIRMED` 并进 `violations`。其余情况必须带原因：

- `WORKHOUR-YIELD`：任务在等夜间窗口（CEO 自己电脑的正常让路）；
- `CAPACITY-BLOCKED-RAM`：内存不足，需要释放或改派；
- `SELF-DISPATCH`：正在翻本机积压。

状态机核面：`cph4/fleet/dispatcher/MASTER-STATE.json`（每轮覆盖）+ `MASTER-LOG.md`（追加一行）。

## 五、运行与验收

```powershell
python Tools\fleet\master_agent.py                 # 跑一轮（人工）
python Tools\fleet\master_agent.py --dry --no-push # 只看决策，不落盘
python Tools\fleet\lane_agent.py --node bm-a       # 手动跑一次本机执行
```

验收判据：①队列不再长期 0 OPEN；②每台在线机的 `idle_reason` 非空且可解释；③任务从派发到回执闭环（2026-10-29 首测：smoke 任务 0.2s 完成、回执落盘、主 Agent 收口 done+1）。

## 六、首日实跑发现（2026-10-29）

1. **v718 重建规则被证伪并回撤**：`mv_rebuild_from_edl.py` 按同一 EDL 重建，产物与 v717 **逐字节相同**（MD5 均为 `B75435845FCA145DB16CFB7283F8E76B`），交付闸结论也一字不差。结论=重建不能修 D1/D2/D4（缺陷在素材镜本身），只能逐镜重烧/调色/插值。5 条规则已移到 `WORK-RULES.disabled-20261029.jsonl`，v718 母版与派生产物已删，队列行标 `INVALID`。**教训：任何“重跑就能修”的规则必须先验证产物不是副本再上生产。**
2. **白天让路的漏洞已补**：`self_dispatch` 当时只看 GPU 窗口，漏了 `heavy`，导致 10:06 在 bm-a 工作时间跑了一次重活。现已按 `heavy_allowed()` 拦截。
3. **两台远程机的结构性阻塞（需人处理）**：poke 返回 `bm-b .:updated` / `bm-c .:fail`，但两者工作树 HEAD 一直停在 `da7652f5` / `994d63ca`，拉不下新代码 → 新的 lane 执行器落不了地。各自在本机跑一次 `Tools/fleet-hot-sync.ps1` 即可解决；bm-c 另有空闲内存仅 0.8GB 的硬约束。
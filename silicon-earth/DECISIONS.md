# 裁决记录（优先于流程文档）

> 群审发现文档与代码冲突时，**以本件为准**。

---

## D1 仓库布局（新人席实证）

- **git 根是 `D:\FluxGroup`**，不是 `silicon-earth`。远程 `git@github.com:BigRain-11122/FluxGroup.git`。
- `silicon-earth/` 是子目录；所有命令先 `cd silicon-earth`。
- `git worktree` 出来的工作区包含整个 FluxGroup。**但 v1 不用 worktree**，见 D7。

## D2 运行时状态不进 git

| 文件 | 进 git？ |
|---|---|
| `events.jsonl` / `time.json` / `state.json` / `memory.json` | **否**（运行时/派生物） |
| `seed.json` | 是（源数据） |
| `TASKS.json` | 是（协作状态） |

## D3 单机单 writer 是硬约束

- `engine.lock` 只是本地文件，跨机无效。
- 只有一台机器跑 `engine.py`，其余只读。

## D4 交付只认 `tools/deliver.py`

- 非持有者拒；无 verify 拒；verify 非 0 拒；通过置 `done` 并留证。

## D5 `world_ops.py release` 不再是交付入口

- 它不跑 verify、不校验持有者，只应被理解为"放弃任务"。
- 代码层尚未强制（world_ops 文件编辑受限），进 BACKLOG B19。
- 文档层已统一：交付一律走 `deliver.py`。

## D6 崩溃重放会写重同一天

- 事件逐条 fsync，`time.json` 最后写；断电重启会把同一天再写一遍，`validate` 仍绿。
- 修法：推进前查该 day 是否已存在，有则拒绝。进 BACKLOG B18。

---

## D7 **并行撤回：v1 只支持单机、单工作区、串行**（冲突席实证）

**原因**：worktree 把目录隔开了，也把锁隔开了。`engine.lock` / `TASKS.lock` 都是各自工作区里的本地文件，跨 worktree 零共享。

实测：两份副本同时 `claim` 都成功；同时 `engine.py 3` 都成功，生成同一批事件 ID；合并时才冲突。**两个 AI 都守规矩，一样炸。**

**裁决**：在远端租约与 fencing 落地之前，**不建 worktree、不开并行会话、不用第二台机器推进**。

## D8 并行前置条件（三件齐了才解禁）

1. 远端租约：claim 推 `refs/leases/<task>`，`--force-with-lease` 抢，远端为准。
2. fencing：事件带 `(owner, lease_epoch)`，pre-push 校验。
3. 状态出仓 + 事件 ID 带节点维度。

## D9 `guard` 身份是自报，不是凭证

- `--agent 总控` 可放行一切（实测）。当前只是自检，不是门禁。
- 真门禁要挂 pre-commit/pre-push，身份来自远端任务板或凭证。进 BACKLOG B20。

---

## 现在的诚实状态

- 五席已回：**全部不通过**（流程、红队、新人、运维、冲突）。
- 已修：guard 认身份并按任务反查模块、扫描全仓与分支差异；deliver 带验收；流程收缩为串行。
- 未修：远端租约、fencing、崩溃重放、事件 ID、claim 原子写、release 门禁、文档与代码完全对齐。
- **能力边界：单机、单工作区、串行。超出这个边界的任何承诺都是假的。**

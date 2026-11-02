# 归一账 2026-11-02（一次只做减法）

> 目的：把 CEO 担心的四件事（重复指挥 / 同步失效 / 无产出 / 闲置算力）从"感觉"变成"账"，并给出唯一权威与退出名单。
> 性质：**作业单**，不是新法。执行的判据是"总数下降"，不是"文档更全"。
> 数据来源：`Tools/fleet/audit_dupes.py`（只读）、`flux_check.py`、`census.py`，均为 2026-11-02 实测。

## 一、四个数字（先看账）

| 项 | 实测 | 含义 |
|---|---|---|
| 脉冲同步 | **386 轮里 323 轮 `skipped`（84%）**，322 次因"手写文件脏" | 机队长期不同步，等于各干各的 |
| 重复指挥 | 同名 6 组（13 卡）／同 cmd 8 组（19 卡）／同交付物 3 组（6 卡） | 每日体检卡每天生成一张同 cmd 卡 |
| 无产出 | 跑完但交付物不存在 9 张；rc≠0 15 张；重试≥2 次 10 张 | "跑过了"被当成"做完了" |
| 闲置 | bm-a 空闲 20-25GB 内存，同时 4 张卡排队（都写死 bm-b/bm-c） | 不是没活，是活被钉在忙的机器上 |
| 命令台账 | orders.md 292 行；`executing/pending/待办/blocked` 命中 22 处 | 没分清"已收口"和"还开着" |

## 二、唯一权威表（其余一律降级/退出）

| 机制 | 唯一权威（留） | 退出/降级 | 理由 |
|---|---|---|---|
| 在飞卡 | `PRODUCTION-QUEUE.jsonl` | — | 唯一"正在发生"的事实 |
| 候选供给 | `PRODUCTION-BACKLOG.jsonl` | 停产卡由 workgen 单一入口写 | 候选池不是队列，只许一个生产者 |
| 人工裁决 | `dispatcher/JUDGMENT-QUEUE.jsonl` | — | 语义不同，保留但只由 master 写 |
| 机器状态 | `dispatcher/MASTER-STATE.json` + `PULSE.json` | `brain-state` / `autowork-state` / `CONTINGENCY-STATE` 降为缓存（不参与判决） | 5 套状态里只有 2 套是决策依据 |
| 车道登记 | `lanes/<node>.json` | `LANE-REGISTRY.jsonl` 归档（126 行无人读） | 两套登记必然漂移 |
| 结构闸 | `flux_check.py`（12 条不变量） | 10+ 个 gate 脚本收敛为「总闸+领域闸同一执行器」 | 现在闸多到没人敢信 |
| 派单 | `master_agent.py` | `fleet-dispatch.ps1` / `fleet-dispatcher.ps1` / `queue_claim.py` 退役 | 4 套派单必然互相抵消 |
| 记忆 | 根 `CODELY.md` + L2 topics | `cph4/fleet/memory/`、`memory-slim/` 归档为历史 | 3 个入口=3 份真相 |
| 脚本 | 一个功能一个文件 | `backlog_fill.py`（Tools/ 与 Tools/fleet/ 双份）、8 个孤儿 | 双份实现已实测漂移致饿死 |
| 命令 | `docs/orders.md` 只留 OPEN | 已收口令移 `orders-archive-*.md`（已有归档件） | 292 行里混着三年前后的令 |

## 三、今天已经改掉的两条（已入库）

1. **机器名从"硬约束"降为"偏好"**：卡写 `nodes=[bm-c]` 而 bm-c 忙时，不再判 `NO-CAPACITY`，任一合格车道可接。
   实测：dry-run 后 bm-a 接走 `R-VB-DISCOVER-R2`，bm-m 接走 `R-TTS-QC-R2`，不再空转。
2. **同 cmd 卡不再重复入队**：promote 时按 cmd 去重，跳过量进 `supply` 回执（`dedup_skipped:N`）。

## 四、七天内要清的清单（逐条带判据）

| # | 动作 | 判据 |
|---|---|---|
| 1 | 收敛队列写入口：只留 master_agent 写卡；closer/workgen/solver 改发事件 | `flux_check` I7 从 2 组违规 → 0 |
| 2 | 每日体检卡改"幂等卡"：同日同 cmd 只允许一张，跨日复用产物 | 同名/同 cmd 组数 → 0 |
| 3 | 退役 4 套派单与 2 份 backlog_fill；8 个孤儿脚本移 `_archive` | `flux_check` I12 → 0 |
| 4 | 状态 3 件降级：不再参与判决，只作展示 | `MASTER-STATE` 字段来源可追溯唯一 |
| 5 | plist 明文口令（`WEB_PASSCODE`/`ROUTER_TOKENS`）移 Keychain | plist 内零明文 |
| 6 | `docs/orders.md` 拆分：OPEN 一屏，收口入档 | OPEN 行数 ≤ 10 且每条带回执指针 |
| 7 | 无产出卡（9 张）+ 重试≥2（10 张）逐张定性：补产物 / 改卡 / 撤卡 | 关闭时必带 `error_class` 或产物 |

## 五、防复发三条（比清单更重要）

1. **查重闸**：任何新卡入队前按 (cmd, deliverable, 归一化标题) 查重，命中即拒——已实现于 promote，接下来下沉到契约校验。
2. **一进一出**：新增任何机制/规则/脚本，必须同时删或合并一个；每周归一账统计总件数，只许降。
3. **每周归一账自动出**：`audit_dupes.py` 每周一自动跑，把"重复/无产出/闲置/同步"四数写进一屏；数字不降即视为流程缺陷，当场改流程。

## 六、这份账不做什么

- 不新建注册表、不新增调度器、不新写一套规则（本件即作业单，执行完即归档）。
- 不删除任何正典：退出者先进 `_archive-<date>/`，保留可回溯。
- 不承诺"零闲置"：只承诺"有活且有机空闲"这种组合不再出现。
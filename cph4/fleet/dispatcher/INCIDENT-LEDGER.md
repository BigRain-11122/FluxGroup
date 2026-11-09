# INCIDENT-LEDGER — 运行期问题复盘（bm-m 主控自建，2026-10-31 起）

> 规则：每一条=现象 → 根因 → 修法 → 沉淀成的铁律。**只写自己跑出来的问题，不写猜的**。
> 同一条复发第二次 = 说明修法没落在判据上，必须升格为脚本断言。

| # | 现象 | 根因（真正的，不是表象） | 修法（已落地） | 铁律 |
|---|---|---|---|---|
| I-01 | bm-b/bm-c 连续整夜空转，队列全 lease-expired | **心跳任务与执行器是两个计划任务**：hb 活、claim 死，主控把"机器在线"当"执行正常" | 合并为单一 `Tools/fleet/agent.py`（pull→hb→领活→执行→回执）；`fleet_supervisor` 加 NO-EXEC（有派单 15min 无回执） | **四信号分离判健康**：hb / agent 上报 / claim / receipt，缺一不得称正常 |
| I-02 | `fleet_contingency` 偶发 FileNotFoundError 崩溃 | 多进程同写同一批状态文件 + 固定 `.tmp` 临时名，互相 rename 掉 | `fleet_lane` 唯一 tmp 名（pid+ns）；pulse 单锁 fcntl，单写手 | **一个文件只许一个写者**；跨进程临时文件必须唯一 |
| I-03 | 手改代码整天被 `git pull --rebase --autostash` 吞进 stash 且不还原 | autostash 在冲突时静默失败，pull 被 permanent 阻塞 | 改 `--no-autostash`；脏树先只提交 `cph4/fleet/` 状态白名单，手改文件一律先 commit | **改完立刻提交**；自动化里禁用 autostash |
| I-04 | 手动 rebase 必撞 pulse 的 state 快照，堆成 UU | pulse 每轮产生状态提交，与人工 rebase 竞争 | `rebase --abort` → `fetch` → `reset --hard origin/main` → 只提交手写代码 | **状态文件不进 rebase**；冲突不做手修 |
| I-05 | 自举钩子可能每 5 分钟多起一个 agent（进程风暴） | 用 `pgrep` 判存活，**Windows 上不存在**，恒判"没在跑" | 换跨平台锁文件（独占创建、10min 陈旧、无标记不启动） | **跨平台检测不能用 Unix-only 命令**；上线前必须双平台验证 |
| I-06 | 本地 4B 编造事实：说 MV"不是 AI 做的"、编"风险通报流程" | 提示词要求"别提 AI"，模型用否认来满足指令；小模型最爱编流程/制度名 | 确定性否决闸（AI 提问/身份经历→不代答）+ 软闸（素材未出现的流程词标"需复核"） | **模型的否认与承诺一律视同幻觉**；对外口径永远归人 |
| I-07 | 32k 上下文下 4B 占 8GB、内存吃紧 | KV cache 随上下文线性涨；`num_parallel=2` 再翻倍 | `CONTEXT_LENGTH=8192`、`NUM_PARALLEL=1→3`（实测 3 路各 41 tok/s、内存不变）、`mem_gate` 预算闸 | **内存按"可用−预留"分配，不按模型参数** |
| I-08 | 模型选择凭榜单，8B/30B 白占 23GB | 未做同题实测；榜单口径≠我们的延迟/内存口径 | `local_llm_bench.py` 同题三轮；实测 30B 慢 60–100 倍且思考泄漏、8B 最慢，已删 | **选型只认自己的基准，不认榜单** |

## 三条总铁律

1. **心跳不是健康**：进程活着 ≠ 有活干 ≠ 有产出。判据必须分离且各自有红灯。
2. **能由代码判定的，绝不交给模型**；模型只起草，验真由代码做，且本地/云端同一套闸。
3. **故障必须吵**：失败带 rc+报错尾部，缺证据不算失败；静默 = 最严重的缺陷。

## 复发检查

- I-01 复发 → 检查节点是否只有 hb 任务、lane 是否在跑（`last_result` 是否连续）。
- I-02 复发 → 检查是否新增了第二个写者或固定 tmp 名。
- I-03/I-04 复发 → 检查是否有人绕过"先 commit 再 pull"。
- I-06 复发 → 检查新提示词是否又允许模型"否认/承诺"。

## INC-20261110-0021 · bm-c 被停摆判据自锁（判据打架）

- 时刻：2026-11-10 00:24（CEO-PROXY 事件班）
- 现象：bm-c 名下 4 张 P0/P2 卡长期 OPEN、running=0；车道文件 idle_reason=`CAPACITY-BLOCKED-RAM EXECUTOR-DEAD (22.3h 零产出，唤醒清单空)`。
- 单一事实的两个判据：
  - `blocker_loop._node_last_output()`（停摆判据）只 glob `cph4/fleet/state/remote-receipts/*.json` —— 该目录当前 **0 文件**，于是所有机器在它眼里都"零产出"；bm-c 因此被判 22.3h。
  - `lane_trust.tier('bm-c')` 读 `cph4/fleet/queue-receipts/` —— bm-c 最近回执 2026-11-10T00:03（20 分钟前），近 7 天 120 份。
- 后果：`master_agent.lane_capacity()` 的 EXECUTOR-DEAD 分支对 bm-c 拒收全部新活，包括本该释放内存的解锁卡 → 越没产出越不给活的自锁。
- 附属证伪：`/status` 对 bm-b 与 bm-c 都不返回 `wakes` 字段，而 bm-b 仍正常领卡 ⇒「唤醒清单空」不是 bm-c 特有故障，不具判据力。
- 修法（建议·受保护件，本席不改）：①停摆判据单一源=取 `queue-receipts` 与 `state/remote-receipts` 的最新；②EXECUTOR-DEAD 对 `rescue` 卡豁免（与 RAM floor 的 rescue 豁免同构）；③lane agent 收口时统一落一份 `state/remote-receipts/<id>-<node>.json`。
- 现行缓解：解锁卡 bmc-env-unblock-2026-11-10 已在队（OPEN·owner=bm-c），一旦判据修好即第一条执行。

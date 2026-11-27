# 2026-11-11 机队架构/配置全量实测审计（为工作流大手术备底）

> 来源：CEO 令「重新了解我的集团架构，机队工作方式，同步方式」「全面了解一下我的机队架构和具体配置」。
> 方法：正典（AI.md/RULES.md/governance.md/cadence.md）+ 代码（master_pulse/master_agent/lane_agent/state_sync，逐行）+ 盘上实测（队列/归档/车道/回执/端口/launchd）。
> 用途：任何会话要做"工作流改造/收敛配置/修派单链"时先读本件，不要重新考古。

## 1. 拓扑与硬配置（实测）

- 五节点：bm-a DASHENG 100.110.185.62 `C:/Users/sjs20/Desktop/FluxGroup`；bm-b BIGMONEY 100.82.175.0 `C:/Fluxgroup/FluxGroup`；bm-c FLUXGROUP 100.123.74.104 `K:/Fluxgroup/FluxGroup`；bm-m MacBook 100.75.133.10 `/Users/junsheng.sun/FluxGroup`（名册 enabled=**false**）；bm-d PENDING-TAILNET（未入网）。
- 硬配置（`Tools/fleet/fleet_lane.py` LANES）：bm-a 94G/12G 4070S 槽8 地板1.0G 让路(9,19)；bm-b 24G/8G 槽6 地板2.0G 永不接768p；bm-c 24G/16G 槽6 地板1.0G；bm-m 32G 无CUDA 槽6 地板2.0G heavy_forbidden 磁盘留20G 单件≤20G；bm-d 256G/48G 槽8。
- 库存：每机底线 6 张、上限 40 张；元卡（CHK-/CANARY-/R-TRIAGE- 等）每机 ≤1；GPU 同刻 1 张。
- 端口：8787 console、8790 FleetLink poke/资产中继、8791 tailnet hub、8792 llm_gateway（机队借模型唯一门）、11435 model_gateway（旧门，职责重叠）、11434 本机 Ollama、8088 webai、4222 NATS（host=bm-a）。
- 卡规则（CARD-POLICY-v1）：租约 cpu45/gpu180/cloud60 分钟；心跳超时600s；握卡零输出1800s 判STALL；非终态无回执3600s 才可重排；最多3次；可重试仅 E-PATH/E-UNKNOWN/E-TIMEOUT。
- 产能（AUTONOMY-CONFIG v1-20261105c）：脉45s、106阶段、慢批300s、7阶段禁用；配额 content14/game8/strategy6/city3/platform2/enabling4 每24h；业务线占比≥0.6、fleet-ops 每机≤2张、业务停摆24h提最高优先；云端 last-resort ¥100/天硬停。
- 模型：本机 qwen3.5:4b-mlx（8k/30m/38-40tok/s）常驻；2b 快车道 keep0；8b 按需；embedding 0.6b；35b-a3b 封存未装。预算常驻20G/峰值24G。云端顺序 DeepSeek(00:30-08:30 免费窗)→Codely。

## 2. 链路真相（代码级，带行号）

- 脉：`master_pulse.py` STAGES 单表 106 项（L54-381），5 元组含 ok_rc 白名单；fast 25 / slow 81；慢批 `SLOW_EVERY=300`（L1155）；`PULSE_NO_PULL=1` 下 pull/push 记 skipped，git 只归 state_sync。
- 假绿三处：`cycle-start` 心跳先写 `ok:true`（L1171-1185），阶段异常/被 kill 后文件永久停在绿的 cycle-start；慢批 deferred 记 rc=None 仍算过（L1273-1277）；git quarantined 走 else 判 ok=True（L1282-1290）。`commit_state` 的 `last_ts/force` 是死参数（L455）。
- 派单：`master_agent.cycle()` L929-1150；单写手=声明文件 `MASTER-NODE.json` + tick 过期可 masquerade（L943-961），**不是锁**；去重按 cmd 字符串且只看 OPEN/RUNNING（L171-186、L599-617），lane 自派 L908-930 绕过；`blocked_by` 全仓只有 `fleet_board.py:72` 读（只写不读，30 张 BLOCKED 无清障路径）。
- 执行：认领=读 `lanes/<node>.json`；租约字段由 master 写；`_eff=min(max_seconds, max(5,timeout_s or 900))`；超时 kill→rc=124；回执 `queue-receipts/<id>-<node>.json` **无 sha256/大小**，master 收口只信 `deliverable_exists`。
- 重复执行路径：`lane_agent._merge_origin` 生成态冲突一律 `--theirs`（L282-284），兜底 `_local_only_cards` 只保 OPEN/READY（L206-215）→ RUNNING 的 owner/state 被抹掉。
- 同步：`state_sync.py` 60s，`add -A cph4/fleet`+仓库级 commit；`pull --ff-only`→`merge -X ours`；3 败/900s 熔断；**工作树有 Tools/ 或 docs/ 脏则整轮 skip**。`.gitattributes` 末尾 `cph4/fleet/**/*.jsonl merge=union` 与文件自身注释"状态账本绝不用 union"矛盾 → 实测 INTAKE-PENDING 16826 行 vs 唯一 id 238。
- 完整性检查盲区：`queue_integrity.py` KEY_FILES 写裸文件名 → C5 状态词表校验从未在生产队列生效；`dispatcher/*.json`（含 MASTER-STATE，comms 的 online 来源）不扫；>8MB 的 ARCHIVE 跳过。

## 3. 量级（11-11 实测）

- 队列 2500 行 + 归档 26832 行 = **全史 29372 张卡**；按线：biggame 11374、fleet-ops 7873、asset-lib 3145、bigmoney 774、fluxverse 662、bigstream-mv 577。
- 当日新建 196 张（11-10 为 199）。当前 6 OPEN / 30 BLOCKED（27 张无 blocked_by）/ 2 RUNNING（却五条车道 jobs 全 0 = 孤儿）；其中 5 张 OPEN 硬钉 bm-m 而 bm-m 无认领执行器（no-claim-executor）。
- 服务面：45 个 launchd 服务，归一化后在 `cph4/cadence.md` 查不到 24 个（含改名后未同步的 patrol_seats）。

## 4. 配置双写/冲突 8 处（手术清单）

1. 两个模型网关：`model_gateway.py:11435` 与 `llm_gateway.py:8792` 同职责；代码全指 8792，SYSTEM-MAP 措辞写反。
2. `fleet-nodes.json` bm-m enabled=false（主控不接收 poke）。
3. bm-c 内存地板：AUTONOMY 3.0G vs LANES 1.0G。
4. bm-a needs：AUTONOMY `cpu,io` vs LANES `cpu,gpu`，且 caps 无 `io` → 需 io 的卡永不匹配。
5. keep_alive：LANES bm-m 5m vs LOCAL-MODEL-POLICY resident 30m。
6. bm-a 让路三种表达：gpu_hours(9,19)/quiet_hours(9,19)/work_hours_gpu=night。
7. MODEL-POLICY.lane_local_llm 又写一遍模型名（唯一源声称在 LOCAL-MODEL-POLICY）。
8. bm-d 三处状态全过期（installing-2026-11-05 / pending / PENDING-TAILNET），而 CEO 11-05 已说当周入网。

## 5. 结论一句话

控制面极发达、生产面很薄：配置齐全且有唯一源，但同一件事被写 2–3 份（网关/地板/needs/keep_alive/让路时段），改一份另两份不跟，实测自然与文档对不上。收敛双写点即可显著减熵，不必再加机制。

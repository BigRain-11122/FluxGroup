# 指挥节奏表 v3 · 全 86 个细分阶段（2026-11-07）

> ⚠️ **状态：已退役（2026-11-11）** — 效力由 `cph4/registry/CANON-V2-20261111.md` 取代；本文仅作历史记录，不再作为执行依据。


生成方式：从主控脉 `STAGES` 逐条提取，不是手写清单。改周期只改脉，再跑 `cadence_build.py`。
校验：`python3 Tools/fleet/cadence.py --check` → 当前 **PASS（86 条 / 0 错 0 警）**。

## 值守（12 条）

| 阶段 | 周期 | 相位 | 判据（简） |
|---|---|---|---|
| executor_guard | 1m | 18s | rc 在 ok_rc 内且产出落在指定路径 |
| hb | 1m | 26s | hb_age_s < 2*period |
| qcheck | 1m | 32s | 0 坏行 |
| supply_target | 1m | 46s | 每机待派 ≥ supply.floor_cards_per_node |
| canary | 2m | 8s | rc 在 ok_rc 内且产出落在指定路径 |
| deadline | 2m | 32s | rc 在 ok_rc 内且产出落在指定路径 |
| verify_done | 2m | 104s | rc 在 ok_rc 内且产出落在指定路径 |
| card_contract_check | 3m | 0s | 无 CARD-DEFECT 新增 |
| master | 4m | 160s | 无 RUNNING 超过 lease |
| backup | 5m | 0s | rc 在 ok_rc 内且产出落在指定路径 |
| state_push | 5m | 250s | rc 在 ok_rc 内且产出落在指定路径 |
| submit_ledger | 1d | 64800s | rc 在 ok_rc 内且产出落在指定路径 |

## 派单（11 条）

| 阶段 | 周期 | 相位 | 判据（简） |
|---|---|---|---|
| ceo_queue | 45s | 9s | 队列/车道有可见变化，或明确报「无活可派」 |
| bank_autofill | 1m | 2s | 无产物已在盘却仍 pending 的条目 |
| decision_close | 1m | 12s | 队列/车道有可见变化，或明确报「无活可派」 |
| decision_router | 1m | 14s | 队列/车道有可见变化，或明确报「无活可派」 |
| next_actions | 1m | 30s | 队列/车道有可见变化，或明确报「无活可派」 |
| squeeze | 1m | 42s | 队列/车道有可见变化，或明确报「无活可派」 |
| wait_map | 1m | 50s | 队列/车道有可见变化，或明确报「无活可派」 |
| night_fill | 1m | 66s | 每机 ≥ floor |
| inventory | 2m | 40s | 队列/车道有可见变化，或明确报「无活可派」 |
| night_plan | 2m | 64s | 夜间每线 ≥1 张可跑卡 |
| workgen | 3m | 162s | 下发卡 100% 带 cmd/prompt |

## 执行（6 条）

| 阶段 | 周期 | 相位 | 判据（简） |
|---|---|---|---|
| lane | 2m | 48s | 回执含 rc/error_class/out_bytes |
| solver | 2m | 88s | 回执含 rc、耗时、产出字节；无产物即判假完成 |
| autowork | 4m | 0s | 回执含 rc、耗时、产出字节；无产物即判假完成 |
| local_tasks | 5m | 100s | 回执含 rc、耗时、产出字节；无产物即判假完成 |
| mac_farm | 7m | 0s | 回执含 rc、耗时、产出字节；无产物即判假完成 |
| asr_subs | 15m | 0s | 回执含 rc、耗时、产出字节；无产物即判假完成 |

## 线（24 条）

| 阶段 | 周期 | 相位 | 判据（简） |
|---|---|---|---|
| budget | 45s | 0s | 未超上限 |
| market | 45s | 18s | 五要素齐 |
| asset_reach | 1m | 0s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| canon | 1m | 4s | 0 漂移 |
| city | 1m | 6s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| done_audit | 1m | 16s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| forecast | 1m | 20s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| gate_rigor | 1m | 22s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| line_plan | 1m | 28s | 无悬空依赖 |
| quality | 1m | 34s | 无未过闸交付 |
| ri | 1m | 36s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| skills | 1m | 40s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| contingency | 2m | 24s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| line_agents | 2m | 56s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| skill_promote | 2m | 80s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| vault | 2m | 96s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| census | 3m | 18s | 15 条线均有 age_h |
| checkups | 3m | 36s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| gate | 3m | 72s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| radar | 3m | 126s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| inference_audit | 5m | 50s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| review_proxy | 5m | 150s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| asset_prompts | 10m | 0s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |
| biz | 10m | 150s | 产出落盘且年龄可算；rc=2 视为告警不是故障 |

## 一屏（18 条）

| 阶段 | 周期 | 相位 | 判据（简） |
|---|---|---|---|
| mem | 45s | 27s | 文件 mtime 前进且内容非空 |
| orgs | 45s | 36s | 文件 mtime 前进且内容非空 |
| decide | 1m | 10s | 文件 mtime 前进且内容非空 |
| handoff | 1m | 24s | 文件 mtime 前进且内容非空 |
| showcase | 1m | 38s | 文件 mtime 前进且内容非空 |
| supervisor | 1m | 44s | 文件 mtime 前进且内容非空 |
| surface | 1m | 48s | 文件 mtime 前进且内容非空 |
| eventlog | 1m | 0s | 文件 mtime 前进且内容非空 |
| metrics | 1m | 44s | 文件 mtime 前进且内容非空 |
| bulletin | 2m | 0s | 文件 mtime 前进且内容非空 |
| chief | 2m | 16s | 文件 mtime 前进且内容非空 |
| warm | 2m | 112s | 文件 mtime 前进且内容非空 |
| judge | 3m | 90s | 每条有 class 且在五类白名单内 |
| master_loop | 3m | 108s | 文件 mtime 前进且内容非空 |
| social | 3m | 144s | 文件 mtime 前进且内容非空 |
| digest | 3m | 0s | 四线各一句且每句带证据指针 |
| brain | 4m | 80s | 文件 mtime 前进且内容非空 |
| memory_nightly | 15m | 300s | 文件 mtime 前进且内容非空 |

## 方向（6 条）

| 阶段 | 周期 | 相位 | 判据（简） |
|---|---|---|---|
| commander | 3m | 54s | 无僵尸线 |
| ceo_pilot | 30m | 0s | 有 top 且带 why/action/done_check 三段 |
| model_plan | 1h | 1200s | 结论带证据指针，否则视为未出结论 |
| ceo_three | 1d | 0s | ≤3 条，每条带文件证据 |
| demand_audit | 1d | 21600s | 结论带证据指针，否则视为未出结论 |
| fact_check | 1d | 43200s | 每条越界候选有 VERIFIED/STALE 回执 |

## 两条注记

1. `*` 表示产物路径由命令行推断（48 条），尚未逐条核实；核实后去掉标记即可。
2. 周期 <45s 的阶段统一按 45s 计——脉的基础节拍是 45 秒，更快的设置实际每轮都会跑。
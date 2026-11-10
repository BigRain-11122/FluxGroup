# 阶段自证（每个登记阶段是否真的在跑）2026-11-10T21:34:12

判据：最后一次**真跑**（rc 非空）距今 ≤ 周期×2 与 600 秒的较大者。「PULSE 里没显示」不等于没跑——慢批 300 秒节流是设计态。

共 106 个阶段：新鲜 46 · 超期 52 · 从未跑 0 · 瘦身跳过 8

**52 个超期未跑 / 0 个从未跑过。**

| 阶段 | 状态 | 距今 | 周期 | 返回码 |
|---|---|---|---|---|
| executor_guard | 超期 | 658s | 60.0s | 0 |
| market | 超期 | 658s | 45.0s | 0 |
| quality | 超期 | 658s | 60.0s | 2 |
| ossradar | 超期 | 658s | 120.0s | 0 |
| inventory | 超期 | 658s | 120.0s | 0 |
| census | 超期 | 658s | 180.0s | 0 |
| card_contract_check | 超期 | 658s | 180.0s | 0 |
| mem_guard | 超期 | 658s | 120.0s | 0 |
| quality_agents | 超期 | 658s | 300.0s | 0 |
| ri | 超期 | 658s | 60.0s | 2 |
| canon | 超期 | 658s | 60.0s | 0 |
| city | 超期 | 658s | 60.0s | 1 |
| skills | 超期 | 658s | 60.0s | 0 |
| skill_promote | 超期 | 658s | 120.0s | 0 |
| backup | 超期 | 658s | 300.0s | 0 |
| next_actions | 超期 | 658s | 60.0s | 0 |
| ceo_queue | 超期 | 658s | 45.0s | 2 |
| bulletin | 超期 | 658s | 120.0s | 0 |
| wait_map | 超期 | 658s | 60.0s | 0 |
| supply_target | 超期 | 658s | 60.0s | 1 |
| radar | 超期 | 658s | 180.0s | 0 |
| budget | 超期 | 658s | 45.0s | 0 |
| gate | 超期 | 658s | 180.0s | 0 |
| checkups | 超期 | 658s | 180.0s | 2 |
| review_proxy | 超期 | 658s | 300.0s | 0 |
| inference_audit | 超期 | 658s | 300.0s | 0 |
| vault | 超期 | 658s | 120.0s | 0 |
| asset_reach | 超期 | 658s | 60.0s | 0 |
| done_audit | 超期 | 658s | 60.0s | 0 |
| handoff | 超期 | 658s | 60.0s | 0 |
| chief | 超期 | 658s | 120.0s | 0 |
| health | 超期 | 658s | 90.0s | 0 |
| contingency | 超期 | 658s | 120.0s | 0 |
| local_tasks | 超期 | 658s | 300.0s | 0 |
| decision_close | 超期 | 658s | 60.0s | 0 |
| capabilities | 超期 | 658s | Nones | 0 |
| cloud_run | 超期 | 658s | Nones | 0 |
| judge | 超期 | 658s | 180.0s | 0 |
| brain | 超期 | 658s | 240.0s | 0 |
| social | 超期 | 658s | 180.0s | 0 |
| mem | 超期 | 658s | 45.0s | 0 |
| squeeze | 超期 | 658s | 60.0s | 1 |
| autowork | 超期 | 658s | 240.0s | 0 |
| closer | 超期 | 658s | 60.0s | 0 |
| master_loop | 超期 | 658s | 180.0s | 0 |
| decision_router | 超期 | 658s | 60.0s | 0 |
| deadline | 超期 | 658s | 120.0s | 0 |
| supervisor | 超期 | 658s | 60.0s | 0 |
| brain_brief | 超期 | 658s | 60.0s | 0 |
| digest | 超期 | 658s | 200.0s | 0 |
| solver | 超期 | 658s | 120.0s | 0 |
| line_agents | 超期 | 658s | 120.0s | 0 |

## 瘦身跳过（设计态，不是缺陷）

- canary、decide、forecast、gate_rigor、orgs、showcase、surface、warm

## 已知长期不跑（外因，不是缺陷）

- executor_guard：远端探针，机器不在线时如实记 unreachable
- eventlog：NATS 总线不可达时按熔断跳过（可达即跑）

---
_这份屏只回答问题「它到底跑没跑过」；跑得对不对由各席自己的判据管_

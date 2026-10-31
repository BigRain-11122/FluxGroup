# bigcompute — NEED-JUDGMENT 台账

> 域标：**bigcompute**（巡视席·BigCompute 硅基算力）。本件只记需裁决项，裁决权=枢纽；本席不直写 orders/decisions/POOL/DEADLINES。
> 格式：`- [状态] 条目` + 证据指针 + 候选处置（不代决）。章程=cph4/fleet/dispatcher/PATROL-FLEET/CHARTERS.md §6。

- [OPEN 2026-11-01 06:2x][P1] **风险台账入档滞后：10-31~11-01 新增面零入档，队列三件 FAILED 无结案，bm-b 执行腿静默 41.4h**
  - 事实（06:13-06:17 直读）：`compute/BigCompute/docs/risk-register.md` 最后写入 **2026-10-30 21:00**、末条 R-61——其后 1.5 日零行。
  - 期间三件队列 FAILED 仍挂着（`cph4/fleet/PRODUCTION-QUEUE.jsonl` 直读）：
    - `Q-AUD-1002` rc=4294967294 / attempts=0 / `requeued_at` 10-31T02:57:39 之后零新认领；注称根因=bm-b 缺 ffmpeg、lane 有 env_selfheal winget 自装路径。
    - `Q-TTS-1202` failure=`lease-expired-5-attempts`（5 次租约到期零回执）——已被 `Q-TTS-1202R`（P0·bm-b 05:26:55 认领·lease 180min→08:26 到期）**事实取代**，但原卡仍留 FAILED，未按取代结案。
    - `R-LLM-BMC-PROBE` `cmd=null`（作者 stub，非可执行件），其自陈 `retry_reason="cmd is null = authored stub, not runnable; needs a real command before requeue"`。
  - 供给地板（`state/idle_selfcheck.json` 06:05:59）：`breach_effective=true`、`effective_ignitable=0`、`ready_total=4`/`ready_ignitable=2`、`self_stale`=backlog#8,#11（3.0 日）、`lane_mismatch=2`、`takeover_candidate`=backlog#10,#15（需佐证）、`silent_owners` bm-b=2482.8min（41.4h）。
  - 旁证：`dispatcher/SUPERVISOR.md` 06:14 自陈「失败件 3 个：Q-AUD-1002,Q-TTS-1202,R-LLM-BMC-PROBE —— 要么重派要么改卡，不能挂着」+「bm-b 有派单但 ? 分钟无执行回执」，但无处置行落账。
  - 候选处置（择一，候枢纽；本席只登记不代改队列）：①`Q-TTS-1202` 记为 CLOSED-SUPERSEDED（被 Q-TTS-1202R 取代）；②`R-LLM-BMC-PROBE` 补真命令重派，或按 commandless-stub 关线；③`Q-AUD-1002` 交一次真实认领取证（env_selfheal 是否自装成功）或改由树内有 ffmpeg 的机承接；④bm-b 执行腿按 SUPERVISOR 建议由机队席在本机跑 `Tools/fleet/lane_agent.py --node bm-b`；⑤上述四件结案后补一条 risk-register 维护注记（R-61 之后首行）。

- [OPEN 2026-11-01 06:2x][P2] **V100 采购判据执行面零凭证：到货验收三关（身份/性能/物理+ECC/Retired Pages）与 72h 换退计时无任何回执件**
  - 事实：`cph4/fleet/hardware/V100-RIG-BOM-20261014.md`（10-20 15:35）+ `V100-EXPANSION-SPEC-20261014.md` 载明判据；采购 10-14 已由 CEO 执行（R-55 行）。但 `compute/BigCompute/state/` 内 `v100-*` 全部停在 **2026-10-14**（P0 preflight/夜间测量/verdict），此后**零到货验收凭证**：无三关回执、无 ECC/Retired Pages 读数、无「到货起算 72h 换退窗」计时件。bm-d 侧为装机中状态。
  - 判读：缺凭证≠未验收（可能记在他司/枢纽台账，本席视野不可见）；但按 §6③「判据执行漂移=旗」，域内可检面为零凭证，故登记不代决。
  - 候选处置（候枢纽）：①在硬件/枢纽台账补验收回执指针并回链本节（本席只读不代验）；②若 72h 窗已过而定谳不可换退，落「窗过」明示行（属 CEO/委员会面，本席零催办）；③后续同型采购把「验收回执落 state/v100-accept-<ts>.txt」写进 BOM 判据节，免重演凭证空窗。

- [STANDING 已承载·不新立] 商业化出口连续零实绩（§6①）、LLM-35B :8090 消费率 0%（§6⑤）、GPU 利用率 R-45 对标差距线（§6④）
  - 出口：`state/delivery-ledger.jsonl` 仅 3 行 DV-20261025-1（`mock:true`/`live:false`·10-25 22:39）→ 真出口零实绩，已超 3 日线；承载=R-45「商业消费四源全零=失分结构态」+ R-28/R-08（开店物理件未通·CEO 保留面零催办）。
  - 35B：`state/lane8090-probe-log.jsonl` 10-31 18:08→11-01 06:05 连续 5 探 DARK[DOWN]（最近 06:05:57）；承载=R-58 open + D-20261031-05 判定窗 11-02 03:07。
  - GPU：日均 10-29 68.5% / 10-30 89.3% / 10-31 55.8% 三日站上 50% 对标线（正面），11-01 夜窗 06:08/06:13 util=1.0% 空转待盯；承载=R-45 open。
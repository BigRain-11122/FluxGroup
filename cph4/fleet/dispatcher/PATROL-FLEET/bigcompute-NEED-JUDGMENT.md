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
- [CLOSED 2026-11-02 00:2x（本席核收）] **风险台账滞后项已修**：`compute/BigCompute/docs/risk-register.md` mtime = **2026-11-01 22:49:57**，末条 R-62（写入面编码事故·修复后 CLEAN），「R-61 之后零行」状态结束。上轮 P1 的「台账滞后」半边闭环；余「队列 FAILED 结案」未执行，见本件 P2·二轮项。

- [OPEN 2026-11-02 00:2x][P1·二轮] **L1 :8090（35B coder）结构性缺席，本班三证排除「CEO 让路/暂停」解释**
  - 新证（00:16-00:18 直读本机）：①`Get-NetTCPConnection -LocalPort 8090 -State Listen` 计数 = **0**（端口无人持，当前不是 eCloud 抢占态）；②`state/lane8090-probe-log.jsonl` 尾四探全 `DARK[DOWN]`（10-31 18:10:56 / 11-01 12:43:07 / 11-01 22:43:07 / **11-02 00:05:57**）；③`.codely-cli/machine-state.flag` = `resumed 2026-10-31T17:47:19+08:00` → **非让路窗**（R-56 型 pause 解释不成立）。
  - 判读：R-58 三案（eCloud 占端口 / 权重与二进制缺失 / 看门狗假绿 exit 0）未见修复，`lane8090` 侧已连续 ≥30h 零服务。§6⑤「35B 消费率 <1%」由偶发升级为**结构性**；同时是本域唯一「算力商品」服务面后端。
  - 候选（候枢纽·本席零催办）：①按 R-58 的 BC-P-101 三案定夺（改端口 / 补资产 / 看门狗改真判）；②若 35B 已实质上弃用，落一行「服务下线」明示并停 8090 探针，免每日 DARK 噪声；③修好前把四个消费面（BigLife 年轮 / MV 分镜 / 8792 QA / BigMoney advisor）显式 reroute 到 `:11434` 4B，避免上游静默降级。

- [OPEN 2026-11-02 00:2x][P1·新] **bm-a 夜间生产窗被常驻 4B 挤出：GPU 3% / 9821MiB 已占 / 剩 ≈2461MiB，768P 生产车道物理上无法点火（2026-10-28 判例复发，占用由 7.3G 升至 9.8G）**
  - 新证（00:18 本机 nvidia-smi + Win32_Process）：`utilization.gpu=3%`、`memory.used=9821 / 12282 MiB`；占卡进程 = `llama-server.exe` pid **54636**（起 2026-10-31 17:51:52，即 machine-state resumed 后 4 分钟自起），命令行 `--model sha256-85e4…（Ollama 4B 档） -c 32768 -np 2 --flash-attn auto`。
  - 判读：00:18 属 bm-a 夜窗（quiet_hours 09:00-19:00 之外），按律应为满载生产窗；实测 GPU 3%、显存被常驻推理吃掉 80%。bm-a 侧 768P 车道（ComfyUI krea2 int8 / h3 int4）需 ~10G 级显存，free 2.4G 下**不可点火**——这是「算力在役、产能为零」的成本空转，也是 GPU 卡被迫外投 bm-b（8G，显存更小）的结构性原因。
  - 与 10-28 判例差别：那轮是「4B 常驻 7.3G + keepwarm 反复拉回」；本轮 keepwarm 已非主导，单件常驻（ctx 32768 / `-np 2`）本身就吃 80%。
  - 候选（候枢纽）：①夜窗把常驻 4B 降到 `num_ctx 8192` / `-np 1`，或按 5m 短租卸载，让出 ≥8G 给生产车道（`Tools/fleet/gpu_lease.py` 现有租约未覆盖 Ollama runner，属缺口）；②`dispatch_precheck` 链上补 `free_vram` 门（R-61 同族：读数有、裁判无）；③若不改，则 bm-a 夜窗产能须按「仅小件」重算，不得在排产表按满卡记。

- [OPEN 2026-11-02 00:2x][P2·二轮] **队列簿记未结案：FAILED 2 件挂账 + UNVERIFIED 8 件 + MASTER-STATE 计数与 jsonl 口径不一致**
  - 事实（`cph4/fleet/PRODUCTION-QUEUE.jsonl` 逐行统计，共 72 行）：`DONE 54 / UNVERIFIED 8 / OPEN 3 / RUNNING 1 / FAILED 2 / CANCELLED 4`。
  - FAILED 仍为 `Q-AUD-1002`（10-31T02:58:59）与 `Q-TTS-1202`（10-31T12:41:37，已被 `Q-TTS-1202R` 取代却仍留 FAILED）；上轮 NJ（11-01 06:2x）建议的两项零执行（`R-LLM-BMC-PROBE` 已从队列消失，`Q-TTS-1202→CLOSED-SUPERSEDED` 未翻）。
  - 新面：`UNVERIFIED` 8 件（MV-NEWPROC-PACKET / R-NEXT-BIGSTREAMM-GATE-20261101 / R-NEXT-BIGSTREAMM-AUDIT-20261101 / C-VB-DISCOVER-V02 / V03 / KN-FILM-GATE-LATEST / LINE-TRIAGE-MV / Q-TRIAGE-BIGSTREAMDUANJU），均 `result.rc=0 + deliverable_exists=true` 但无 receipt/audit 收口 → 属「产能已消耗、成果未验收」，直接压低 §6④ 对账面可信度。
  - 口径不一致：`MASTER-STATE.json` queue = `open 16 / running 2 / failed 2`，与 jsonl 实盘 `OPEN 3 / RUNNING 1 / FAILED 2` 不符（差 13），簿记面已失真。
  - 候选（候枢纽）：①`Q-TTS-1202` 翻 CLOSED-SUPERSEDED（一句话）；②UNVERIFIED 8 件按行内已有 rc/deliverable 批量补 receipt；③MASTER-STATE 的 queue 计数改为由 jsonl 派生，单一真源。
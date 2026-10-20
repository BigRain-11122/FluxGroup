# NEED-JUDGMENT — bigmoney（巡视席呈枢纽）

> 写手=bigmoney 巡视席 R21（只读只议）。台账 orders/decisions/POOL 未直写。班时=2026-10-20 17:12。

## NJ[bigmoney#R21-1] 弱传感只读 main → bm-b fallback 推送不可见（机制）
- 事实：本班触发旗 quant/bigmoney/fleet/machines/bm-b.json: stale 154min > 150min。实核 bm-b 活着：poke 监听 http://100.82.175.0:8790/status 17:02:59 应答（ram_free 8.6GB·cpu 19%·gpu RTX3070 3639MiB free）；其内部心跳 clock_read=16:51:29、round r1076 closed、idle_rounds=0、agenda_starved=false。
- 根因：bm-b 自 r1074（14:22）起主推延后（pre-push claw 因陈旧基线 fail-closed，防误删他机 shard，行为正确），r1075/r1076 落在 origin/machine/bm-b-r1075（15:14:16）/ origin/machine/bm-b-r1076（16:51:50）；而弱传感只读 main 上的 fleet/machines/*.json。
- 建议（候裁）：传感器增读 origin/machine/bm-b-* tip 提交时间作退化保底，或 bm-b 写心跳旁路件（非 main 路径）。
- 判据：git for-each-ref 分支时间戳 + /status 双证（两证一致）。

## NJ[bigmoney#R21-2] bm-b 主推收口待排（运维）
- 事实：origin/main 上 bm-b 心跳自 14:22 后无增量；r1075/r1076 仅 fallback。本班未触碰 bm-b 工作树，其树干净度未核。
- 建议：枢纽给 bm-b 排一次干净树 rebase+push 收口轮；收口前读 bm-b 状态一律走 /status 或 fallback 分支，勿以 main 心跳判死。

## NJ[bigmoney#R21-3] PATROL-FLEET/LOG.md 工作树含未解 stash 冲突块（横切完整性）
- 事实：工作树 LOG.md=783 行，含 <<<<<<< Updated upstream(L471) / =======(L473) / >>>>>>> Stashed changes(L782)；HEAD 版 464 行零标记；git status=M，diff +782/-311，未提交。
- 影响：任何班次追加行都落在冲突块之后；若后续按 upstream 侧解块将丢约 308 行班志。
- 建议（候裁）：由 group 横切席或枢纽按「保两侧·按时间序拼接」法定点解块并即时提交。本席未直改（只读只议）。

## 域观察（非 NJ·仅留痕）
- 供给水位：bm-a 引擎 last_tick 17:09 verdict=idle·queue_depth=0·claimable_n=0（引擎活着但供给薄）；bm-b next=W21 generate 补 ≥3 ready。
- 波链：bm-c r1159→r1162 W289 PREREG FREEZE + 五面 splice 连续（42nd/43rd A-hop），链序未断。
- 资金安全：r1073 fund P2 revival pair 双诚实判负且两池单已 done——无「判负策略保载续烧」。
- RAM-GATE：bm-c 16:06 健康面 ram_free 0.6GB 偏紧；后续 16:31/16:38/16:57 提交照常，未见中断。
- 本班机制修补：Tools/patrol-fleet-carrier.ps1 L84 snooze 解析加容错解包（PS5.1 ConvertFrom-Json 顶层数组返单对象致多条目静默塌缩为 1·实测复证）；改后 parse_errors=0，snooze 双条目命中实测通过。备份=.bak-20261020-1715。
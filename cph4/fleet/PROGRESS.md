# 自动推进事实页

> 生成：2026-11-06T10:49:42（每轮主控脉自动刷新；只列盘上事实，无结论、无自评）

## 一、现在在跑（队列 RUNNING）

（无）

待派 OPEN：22 张

## 二、机队实况（每机最后一次心跳 + 最后产出）

| 机器 | 心跳状态 | 在跑的卡 | out_bytes | 心跳龄 | 最后产出 |
|---|---|---|---|---|---|
| bm-a | RUNNING | R-MODEL-RADAR-BMA-20261106 | None | 7s | 4.9h |
| bm-b | DONE | R-CROSSTALK-POST-20261106-001 | None | 93s | 11.2h |
| bm-c | DONE | OPS-CLOCK-RESYNC-BMC-20261105 | None | 14s | 10.4h |
| bm-m | DONE | R-CROSSTALK-SWEEP-20261105-001 | None | 229s | 0.1h |

## 三、最近完成（含谁跑的）

| 卡 | 机器 | 时间 | 产物 |
|---|---|---|---|
| R-CROSSTALK-POST-20261106-001 | - | 2026-11-06T10:46:25 | - |
| OPS-CLOCK-RESYNC-BMC-20261105 | - | 2026-11-06T10:46:14 | - |
| R-CROSSTALK-SWEEP-20261105-001 | bm-m | 2026-11-06T10:45:53 | /Users/junsheng.sun/FluxGroup/cph4/fleet/queue-receipts/bm-m-crosstalk-sweep.md |
| asset-lib-char-prompts-2026-11-06 | bm-m | 2026-11-06T10:43:36 | cph4/fleet/queue-receipts/char-gen-plan-2026-11-06.json |
| R-TRIAGE-BIGSTREAMMV-BMA-20261104 | bm-b | 2026-11-06T10:41:41 | cph4/fleet/queue-receipts/triage-bigstream-mv-20261104.md |
| fleet-node-sync-report-bm-b-2026-11-05 | - | 2026-11-06T10:41:41 | cph4/fleet/queue-receipts/node-sync-bm-b-2026-11-05.txt |
| fleet-node-sync-report-bm-c-2026-11-05 | bm-c | 2026-11-06T10:41:41 | cph4/fleet/queue-receipts/node-sync-bm-c-2026-11-05.txt |
| R-GPUWORK-20261105-001 | bm-m | 2026-11-06T10:41:41 | /Users/junsheng.sun/FluxGroup/cph4/fleet/queue-receipts/bm-m-gpuwork-reply.md |
| CANARY-20261103T200141 | bm-b | 2026-11-06T10:41:38 | cph4/fleet/state/canary/RUN-20261103T200141.txt |
| Q-TRIAGE-BIGSTREAMMV-20261104 | bm-c | 2026-11-06T10:41:38 | cph4/fleet/queue-receipts/triage-bigstream-mv-20261104.md |
| asset-lib-asset-gen-scenes-2026-11-05 | bm-c | 2026-11-06T10:41:38 | cph4/fleet/queue-receipts/asset-gen-scenes-2026-11-05.json |
| C-TTS-QC-ALL | - | 2026-11-06T10:41:37 | cph4/fleet/queue-receipts/tts-qc-all.json |
| QUEUE-CARD-AUDIT-20261106 | bm-a | 2026-11-06T02:57:45 | cph4/fleet/queue-receipts/queue-card-audit-20261106.json |
| R-NEXT-BIGSTREAMM-GATE-20261105 | bm-m | 2026-11-06T01:31:38 | cph4/fleet/queue-receipts/mv-gate-20261105.json |
| R-NEXT-BIGSTREAMM-AUDIT-20261105 | - | 2026-11-06T01:31:38 | cph4/fleet/queue-receipts/mv-full-audit-20261105.json |

## 四、最近失败（附原因原文）

| 卡 | 机器 | rc | 定性 | 原因（原文截断） |
|---|---|---|---|---|
| CNV-20261105T174044-2 | bm-m | None | - | - |
| SIM-20261105T160855-01-infra | - | None | - | - |
| SIM-20261105T155828-01-infra | bm-m | None | - | - |
| CHT-20261105T134829-99 | bm-m | None | - | - |
| SIM-20261105T151259-01-0 | - | None | E-NO-RECEIPT | - |
| B-QNT-SIGNAL-20261105 | - | None | E-NO-RECEIPT | - |
| CHT-20261105T134950-99 | - | 7 | E-UNKNOWN | rc=7, no output captured |
| CHT-20261105T134821-03 | - | None | E-NO-RECEIPT | - |
| B-MV-AUDIT-20261105 | - | None | E-ROOTCAUSE-3X | - |
| biggame-playable-2026-11-03 | bm-m | 0 | E-CONTRACT | rc=0, no output captured |
| R-MODEL-RADAR-BMC-20261103 | - | None | E-CONTRACT | - |
| ART-PUSH-BMA-20261104 | - | None | E-ROOTCAUSE-3X | - |
| asset-lib-face-caption-2026-11-04 | bm-c | None | E-NO-RECEIPT | - |
| asset-lib-face-caption-2026-11-03 | - | None | E-CMD-MISSING | - |
| asset-lib-voice-corpus-bmc-2026-11-03 | bm-c | None | E-BLOCKED-INPUT | - |

## 五、远端回执（失败原因能不能回到主控）

| 回执 | 状态 | rc | 定性 | 命令 | stderr |
|---|---|---|---|---|---|
| asset-lib-env-check-2026-11-06-bm-m.json | FAILED | 1 | E-UNKNOWN | python3 Tools/fleet/asset_env_check.py --out cph4/fleet/queu | - |
| Q-VCORP-PREP-e01-R3-20261105-bm-a.json | FAILED | 2 | E-INPUT | - | - |
| CHK-RECEIPT-20261103-bm-m.json | FAILED | 2 | E-CONTRACT | python3 Tools/fleet/receipt_attrib.py --out cph4/fleet/queue | - |
| R-GPUWORK-20261105-001-bm-m.json | DONE | 0 | - | - | - |
| Q-MV-ANCHOR-WORDS-DRAIN-20261106-bm-b.json | FAILED | 2 | E-INPUT | - | - |
| asset-lib-env-check-2026-11-06-bm-c.json | FAILED | 1 | E-UNKNOWN | - | - |
| asset-lib-face-dataset-2026-11-06-bm-c.json | FAILED | 1 | E-UNKNOWN | - | - |
| asset-lib-char-prompts-2026-11-06-bm-m.json | DONE | 0 | - | python3 Tools/fleet/char_plan.py | - |
| asset-lib-library-check-2026-11-06-bm-b.json | FAILED | 2 | E-INPUT | - | - |
| bigstream-mv-gate-2026-11-06-bm-m.json | FAILED | 1 | E-UNKNOWN | python3 Tools/mv_delivery_gate.py cph4/fleet/mv0001-handover | Traceback (most recent call last):   File "/Users/junsheng.sun/FluxGroup/Tools/mv_delivery_gate.py", |
| asset-lib-char-gen-2026-11-06-bm-c.json | DONE | 0 | - | - | - |
| MV-ANCHOR-BATCH3-20261106-bm-a.json | FAILED | 0 | E-ARTIFACT | - | - |
| R-CROSSTALK-SWEEP-20261105-001-bm-m.json | DONE | 0 | - | - | - |
| R-CROSSTALK-POST-20261106-001-bm-b.json | DONE | 0 | - | - | - |
| OPS-CLOCK-RESYNC-BMC-20261105-bm-c.json | DONE | 0 | - | - | - |

## 六、最近退回的卡（谁退的、为什么）

| 卡 | 退回者 | 原因 |
|---|---|---|
| FREE-MEM-DIAG-bm-c-20261106 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |
| Q-MV-ANCHOR-WORDS-DRAIN-20261106 | fleet_status | owner heartbeat stale 227s (aging 0min) |
| Q-MV-ANCHOR-WORDS-DRAIN-BMA-20261106 | fleet_status | owner heartbeat stale 190s (aging 0min) |
| R-MODEL-RADAR-BMA-20261106 | fleet_status | owner heartbeat stale 23s (aging 0min) |
| asset-lib-env-check-2026-11-06 | fleet_status | owner is stale-worker (>6h no output) (aging 1min) |
| bigstream-mv-gate-2026-11-06 | fleet_status | owner heartbeat stale 74s (aging 0min) |
| biggame-pack-scan-2026-11-06 | fleet_status | owner heartbeat stale 126s (aging 0min) |
| R-CROSSTALK-POST-20261106-001 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |
| asset-lib-voice-corpus-2026-11-06 | fleet_status | owner heartbeat stale 131s (aging 0min) |
| asset-lib-face-dataset-2026-11-06 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |
| asset-lib-library-check-2026-11-06 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |
| bigmoney-backtest-2026-11-06 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |
| asset-lib-char-gen-2026-11-06 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |
| asset-lib-asset-gen-2026-11-06 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |
| asset-lib-asset-gen-scenes-2026-11-06 | fleet_status | owner is stale-worker (>6h no output) (aging 0min) |

## 七、24h 运转探针

- 结论：GREEN｜绿 73.9%｜采样 3757 次｜够不够判 24h：否
- 当前红项：无

---
查看面板：http://127.0.0.1:8787/ （首页含本页链接）

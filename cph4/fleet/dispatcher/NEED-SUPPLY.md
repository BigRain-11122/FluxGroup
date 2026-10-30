# NEED-SUPPLY - why lanes and business lines are not running (#regenerated)

- ts: 2026-10-30T21:17:10
- queue: open=4 running=2 done=38 failed=2
- open jobs by need: cpu=3 gpu=1

- bm-a: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-b: RUNNING Q-AUD-1002
- bm-c: RUNNING R-LLM-BMC-PROBE
- bm-m: CAPACITY-BLOCKED-RAM ram 1.9/2.0 GB -> free memory on that box (gpu_lease --acquire reclaims it)

Rules pack: cph4/fleet/WORK-RULES.jsonl (empty = every job must be declared by a producing seat; the master will not invent work).

## 业务条线（正身 cph4/fleet/LINE-REGISTRY.json）

| 条线 | 判 | 最近产出 | 阈值 | 卡在 | 负责人 |
|---|---|---|---|---|---|
| BigStream·漫剧 | BLOCKED | - | 48.0h | - | 漫剧席 |
| BigStream·MV 41 曲 | WAITING | - | 24.0h | - | 导演席（CEO 终审） |
| BigStream·短剧 | WAITING | - | 72.0h | - | 短剧席 |
| Biggame·游戏 | WAITING | - | 24.0h | - | 游戏席 |
| FluxVerse·元宙城 | WAITING | - | 36.0h | - | 城市线 |
| BigMoney·量化 | WAITING | - | 24.0h | - | 量化席 |
| BigDomain·硅基域商业化 | WAITING | - | 36.0h | - | 域运营席 |
| BigCompute·硅基算力 | WAITING | - | 36.0h | - | 算力中枢席 |
| BigLife·数字生命 | WAITING | - | 48.0h | - | 生命生产席 |
| BigHouse·城市安家 | WAITING | - | 72.0h | - | 生态运营席 |
| 车机游戏 BU | WAITING | - | 72.0h | - | 车机 BU |
| RECON·竞品拆解 | WAITING | - | 72.0h | - | 拆解部 |
| BigStream·短视频/切片 | PARKED | - | 168.0h | - | 短视频席 |

- PARKED=CEO 令停，不计闲置；WAITING=没活但未过期；STALE=超过阈值无产出；BLOCKED=有活但无可用车道；卡在=最早断供的工段。

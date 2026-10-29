# NEED-SUPPLY - why lanes and business lines are not running (#regenerated)

- ts: 2026-10-29T14:54:03
- queue: open=0 running=0 done=25 failed=0
- open jobs by need: cpu=0 gpu=0

- bm-a: DAY-YIELD: work machine, takes over at 19:00 -> assign a card or declare work
- bm-b: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-c: CAPACITY-BLOCKED-RAM ram 1.1/3.0 GB -> free memory on that box (gpu_lease --acquire reclaims it)

Rules pack: cph4/fleet/WORK-RULES.jsonl (empty = every job must be declared by a producing seat; the master will not invent work).

## 业务条线（正身 cph4/fleet/LINE-REGISTRY.json）

| 条线 | 判 | 最近产出 | 阈值 | 卡在 | 负责人 |
|---|---|---|---|---|---|
| BigStream·漫剧 | BLOCKED | - | 48.0h | 剧本/编剧席 | 漫剧席 |
| BigHouse·城市安家 | STALE | 271.5h | 72.0h | - | 生态运营席 |
| BigStream·MV 41 曲 | STALLED-STAGE | - | 24.0h | 关键帧/导演席·美术 | 导演席（CEO 终审） |
| BigStream·短剧 | STALLED-STAGE | - | 72.0h | 剧本/编剧席 | 短剧席 |
| 车机游戏 BU | STALLED-STAGE | - | 72.0h | 市场/立项/车机 BU | 车机 BU |
| RECON·竞品拆解 | STALLED-STAGE | - | 72.0h | 扒榜/拆包/拆解部 | 拆解部 |
| Biggame·游戏 | WAITING | 0.2h | 24.0h | - | 游戏席 |
| FluxVerse·元宙城 | WAITING | 1.5h | 36.0h | - | 城市线 |
| BigMoney·量化 | WAITING | 5.9h | 24.0h | - | 量化席 |
| BigDomain·硅基域商业化 | WAITING | 0.3h | 36.0h | - | 域运营席 |
| BigCompute·硅基算力 | WAITING | 8.7h | 36.0h | - | 算力中枢席 |
| BigLife·数字生命 | WAITING | 33.8h | 48.0h | - | 生命生产席 |
| BigStream·短视频/切片 | PARKED | - | 168.0h | - | 短视频席 |

- PARKED=CEO 令停，不计闲置；WAITING=没活但未过期；STALE=超过阈值无产出；BLOCKED=有活但无可用车道；卡在=最早断供的工段。

# NEED-SUPPLY - why lanes and business lines are not running (#regenerated)

<<<<<<< HEAD
- ts: 2026-10-31T14:44:38
- queue: open=1 running=1 done=44 failed=5
- open jobs by need: cpu=1 gpu=0

- bm-a: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-b: RUNNING Q-TTS-1202R
- bm-c: CAPACITY-BLOCKED-RAM ram 1.6/3.0 GB -> free memory on that box (gpu_lease --acquire reclaims it)
=======
- ts: 2026-10-31T14:11:50
- queue: open=0 running=0 done=44 failed=6
- open jobs by need: cpu=0 gpu=0

- bm-a: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-b: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-c: CAPACITY-BLOCKED-RAM ram 1.0/3.0 GB -> free memory on that box (gpu_lease --acquire reclaims it)
>>>>>>> 8d72eaea (pulse: state snapshot [via bm-m])
- bm-m: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card

Rules pack: cph4/fleet/WORK-RULES.jsonl (empty = every job must be declared by a producing seat; the master will not invent work).

## 业务条线（正身 cph4/fleet/LINE-REGISTRY.json）

| 条线 | 判 | 最近产出 | 阈值 | 卡在 | 负责人 |
|---|---|---|---|---|---|
<<<<<<< HEAD
| BigStream·漫剧 | BLOCKED | - | 48.0h | 剧本/编剧席 | 漫剧席 |
| BigLife·数字生命 | STALE | 81.7h | 48.0h | - | 生命生产席 |
| BigHouse·城市安家 | STALE | 319.4h | 72.0h | - | 生态运营席 |
| BigStream·MV 41 曲 | STALLED-STAGE | - | 24.0h | 质检/交付/质检席 | 导演席（CEO 终审） |
| BigStream·短剧 | STALLED-STAGE | - | 72.0h | 剧本/编剧席 | 短剧席 |
| FluxVerse·元宙城 | STALLED-STAGE | 0.0h | 36.0h | 场景装配/地编席 | 城市线 |
| 车机游戏 BU | STALLED-STAGE | - | 72.0h | 市场/立项/车机 BU | 车机 BU |
| RECON·竞品拆解 | STALLED-STAGE | - | 72.0h | 扒榜/拆包/拆解部 | 拆解部 |
| Biggame·游戏 | WAITING | 0.5h | 24.0h | - | 游戏席 |
| BigMoney·量化 | WAITING | 0.2h | 24.0h | - | 量化席 |
| BigDomain·硅基域商业化 | WAITING | 0.2h | 36.0h | - | 域运营席 |
| BigCompute·硅基算力 | WAITING | 1.4h | 36.0h | - | 算力中枢席 |
=======
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
>>>>>>> 8d72eaea (pulse: state snapshot [via bm-m])
| BigStream·短视频/切片 | PARKED | - | 168.0h | - | 短视频席 |

- PARKED=CEO 令停，不计闲置；WAITING=没活但未过期；STALE=超过阈值无产出；BLOCKED=有活但无可用车道；卡在=最早断供的工段。

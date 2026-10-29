# NEED-SUPPLY - why lanes and business lines are not running (#regenerated)

- ts: 2026-10-29T10:46:02
- queue: open=0 running=0 done=25 failed=0
- open jobs by need: cpu=0 gpu=0

- bm-a: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-b: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-c: CAPACITY-BLOCKED-RAM ram 1.0/3.0 GB -> free memory on that box (gpu_lease --acquire reclaims it)

Rules pack: cph4/fleet/WORK-RULES.jsonl (empty = every job must be declared by a producing seat; the master will not invent work).

## 业务条线（正身 cph4/fleet/LINE-REGISTRY.json）

| 条线 | 判 | 最近产出 | 阈值 | 活 | 负责人 |
|---|---|---|---|---|---|
| BigStream·漫剧 | BLOCKED | 47.3h | 48.0h | none | 漫剧席 @bm-b |
| BigStream·短剧 | STALE | 280.4h | 72.0h | none | 短剧席 |
| BigHouse·城市安家 | STALE | 267.4h | 72.0h | none | 生态运营席 |
| RECON·竞品拆解 | STALE | 119.8h | 72.0h | none | 拆解部 |
| BigStream·MV 41 曲 | WAITING | 7.2h | 24.0h | none | 导演席（CEO 终审） |
| Biggame·游戏 | WAITING | 0.0h | 24.0h | none | 游戏席 |
| FluxVerse·元宙城 | WAITING | 21.4h | 36.0h | none | 城市线（CEO 第一检查入口） |
| BigMoney·量化 | WAITING | 1.8h | 24.0h | none | 量化席 @bm-b/bm-d |
| BigDomain·硅基域商业化 | WAITING | 0.3h | 36.0h | none | 域运营席 |
| BigCompute·硅基算力 | WAITING | 4.6h | 36.0h | none | 算力中枢席 |
| BigLife·数字生命 | WAITING | 29.7h | 48.0h | none | 生命生产席 |
| 车机游戏 BU | WAITING | 71.9h | 72.0h | none | 车机 BU |
| BigStream·短视频/切片 | PARKED | 208.5h | 168.0h | none | 短视频席 |

- PARKED=CEO 令停，不计闲置；WAITING=没活但未过期；STALE=超过阈值无产出；BLOCKED=有活但无可用车道。

# NEED-SUPPLY - why lanes and business lines are not running (#regenerated)

- ts: 2026-10-30T16:27:55
- queue: open=0 running=0 done=36 failed=1
- open jobs by need: cpu=0 gpu=0

- bm-a: DAY-YIELD: work machine, takes over at 19:00 -> assign a card or declare work
- bm-b: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-c: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card
- bm-m: SELF-DISPATCH: lane scans its own backlog -> lane is scanning its own backlog; if this persists >2 rounds the box has no declared work and needs a new card

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


## 2026-10-30 16:40 bm-m 主控：高清音色库（60席矩阵）唯一缺口 = 候选视频清单
- 正典 VOICE-BANK-PLAN.md v1 已定标准（44.1kHz/降噪/F0闸/20epoch），vb_worker.py 全节点 CPU 分片构建器就绪（实参 --voice --bvids-file --minutes）。
- 但仓内除已收的芯龙门（mid 696523981）外**没有任何 bvid 清单**；侯卫东类/方言/老年/童声缺口席位的候选清单只有 CEO 能定（B站手选或给关键词由 bm-m 35B 初筛）。
- 待 CEO 给清单 → bm-b 主机跑 xlm-hq 续训 + bm-m/bm-a 夜跑 vb_worker 分片，音色库即可满负荷推进。

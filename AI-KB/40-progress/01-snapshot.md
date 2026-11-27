---
id: progress.snapshot
title: 进度快照（事实）
layer: progress
questions: ["现在做到哪", "哪条停了"]
facts: ["state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
当前进度以磁盘事实为准：队列 1385 张，状态分布 DONE=517，CANCELLED=611，FAILED=2，ARCHIVED=227，UNVERIFIED=6，OPEN=9，NONE=3，RUNNING=10。

## 全景
| 线 | 声明 | 观测 | 产物年龄(h) | DONE | 总卡 |
|---|---|---|---|---|---|
| BigStream·MV 41 曲 | ACTIVE | OBSERVED | 2.4 | 115 | 131 |
| BigStream·漫剧 | PARKED | OBSERVED | 0.4 | 15 | 25 |
| BigStream·短剧 | PARKED | OBSERVED | 198.2 | 6 | 19 |
| BigStream·短视频/切片 | PARKED | OBSERVED | 131.7 | 未测 | 0 |
| Biggame·游戏 | ACTIVE | OBSERVED | 103.5 | 74 | 232 |
| FluxVerse·元宙城 | ACTIVE | OBSERVED | 105.8 | 5 | 7 |
| BigMoney·量化 | ACTIVE | OBSERVED | 84.8 | 86 | 94 |
| BigDomain·硅基域商业化 | ACTIVE | OBSERVED | 103.4 | 5 | 8 |
| BigCompute·硅基算力 | ACTIVE | OBSERVED | 103.4 | 4 | 5 |
| BigLife·数字生命 | ACTIVE | EMPTY | 未测 | 3 | 5 |
| BigHouse·城市安家 | PARKED | NO-DISK | 未测 | 未测 | 0 |
| 车机游戏 BU | PARKED | OBSERVED | 124.9 | 未测 | 0 |
| RECON·竞品拆解 | ACTIVE | OBSERVED | 12.2 | 3 | 6 |
| 机队运维·端到端自检（平台服务线） | ACTIVE | BOOKKEEPING | 未测 | 123 | 362 |
| 资产储备·角色 LoRA 与音色库 | ACTIVE | OBSERVED | 5.3 | 44 | 79 |

## 判断规则
声明 ACTIVE 但盘上无产物 = 纸面；产物年龄超阈值 = 停摆；有卡在飞且回执新鲜 = 真在推进。

## 我不知道的
远端产物未回传时无法判定。

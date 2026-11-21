# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-21T22:06:17 ｜ 语料 8788 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 11 | 300 | 96% | - | 0 | - | collect |
| requester | 38 | 400 | 90% | - | 0 | - | collect |
| ai_creator | 58 | 400 | 86% | - | 0 | - | collect |
| student | 78 | 400 | 80% | - | 0 | - | collect |
| critic | 99 | 400 | 75% | - | 0 | - | collect |
| beginner | 110 | 400 | 72% | - | 0 | - | collect |
| music_seeker | 400 | 600 | 33% | BLOCKED | 0 | 2.6 | collect |
| tech_nerd | 469 | 600 | 22% | BLOCKED | 0 | 2.7 | collect |
| feeler | 476 | 600 | 21% | BLOCKED | 0 | 2.4 | collect |
| peer_pro | 506 | 600 | 16% | BLOCKED | 0 | 2.5 | collect |
| craft_learner | 1425 | 800 | 0% | TRAIN-FAIL | 0 | 1.6 | - |
| memer | 1874 | 600 | 0% | KEEP | 10 | 0.4 | verify |
| shallow | 1533 | 600 | 0% | KEEP | 10 | 2.0 | verify |

**本拍派工**：`collect` / `peer_pro` —— 缺 94 行（16%）；可定向视频 3 条
**结果**：NOPROGRESS（24.8s，本段净增 +0 行）

```
[定向 3 条已知视频]
sweep] 完成：视频 1（跳过 2）评论新 289 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=104778 → 入库62780（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

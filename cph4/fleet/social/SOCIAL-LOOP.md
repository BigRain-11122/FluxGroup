# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-21T00:39:07 ｜ 语料 11848 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 2 | 300 | 99% | - | 0 | - | collect |
| family | 14 | 300 | 95% | - | 0 | - | collect |
| ai_creator | 69 | 400 | 83% | - | 0 | - | collect |
| requester | 83 | 400 | 79% | - | 0 | - | collect |
| student | 107 | 400 | 73% | - | 0 | - | collect |
| critic | 119 | 400 | 70% | - | 0 | - | collect |
| beginner | 152 | 400 | 62% | - | 0 | - | collect |
| music_seeker | 437 | 600 | 27% | SUPPLY | 0 | 6.2 | collect |
| feeler | 546 | 600 | 9% | REJECT | 10 | 1.8 | - |
| tech_nerd | 565 | 600 | 6% | TRAIN-FAIL | 0 | 6.3 | - |
| peer_pro | 598 | 600 | 0% | KEEP | 30 | 4.1 | - |
| craft_learner | 1986 | 800 | 0% | REJECT | 10 | 1.1 | - |
| memer | 2136 | 600 | 0% | KEEP | 30 | 8.0 | - |
| shallow | 2990 | 600 | 0% | TRAIN-FAIL | 0 | 4.1 | - |

**本拍派工**：`collect` / `critic` —— 缺 281 行（70%）；可定向视频 0 条
**结果**：NOPROGRESS（330.4s，本段净增 +0 行）

```
[该段无已知视频，退回按评论数总榜]
weep] 完成：视频 6（跳过 45）评论新 850 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=101419 → 入库61651（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T23:57:12 ｜ 语料 10941 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 12 | 300 | 96% | - | 0 | - | collect |
| requester | 63 | 400 | 84% | - | 0 | - | collect |
| ai_creator | 67 | 400 | 83% | - | 0 | - | collect |
| student | 103 | 400 | 74% | - | 0 | - | collect |
| critic | 109 | 400 | 73% | - | 0 | - | collect |
| beginner | 143 | 400 | 64% | - | 0 | - | collect |
| music_seeker | 421 | 600 | 30% | SUPPLY | 0 | 5.5 | collect |
| tech_nerd | 522 | 600 | 13% | TRAIN-FAIL | 0 | 5.6 | - |
| feeler | 525 | 600 | 12% | REJECT | 10 | 1.1 | - |
| peer_pro | 552 | 600 | 8% | KEEP | 30 | 3.4 | - |
| craft_learner | 1695 | 800 | 0% | REJECT | 10 | 0.4 | - |
| memer | 2051 | 600 | 0% | KEEP | 30 | 7.3 | - |
| shallow | 2730 | 600 | 0% | TRAIN-FAIL | 0 | 3.4 | - |

**本拍派工**：`collect` / `ai_creator` —— 缺 333 行（83%）；可定向视频 0 条
**结果**：NOPROGRESS（330.0s，本段净增 +0 行）

```
[该段无已知视频，退回按评论数总榜]
eep] 完成：视频 6（跳过 32）评论新 1120 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=96160 → 入库59211（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T23:02:02 ｜ 语料 10161 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 11 | 300 | 96% | - | 0 | - | collect |
| requester | 60 | 400 | 85% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 85 | 400 | 79% | - | 0 | - | collect |
| critic | 104 | 400 | 74% | - | 0 | - | collect |
| beginner | 122 | 400 | 70% | - | 0 | - | collect |
| music_seeker | 412 | 600 | 31% | SUPPLY | 0 | 4.6 | collect |
| tech_nerd | 497 | 600 | 17% | TRAIN-FAIL | 0 | 4.7 | collect |
| feeler | 500 | 600 | 17% | REJECT | 10 | 0.1 | collect |
| peer_pro | 532 | 600 | 11% | KEEP | 30 | 2.5 | - |
| craft_learner | 1505 | 800 | 0% | REJECT | 30 | 6.4 | - |
| memer | 1968 | 600 | 0% | KEEP | 30 | 6.3 | - |
| shallow | 2503 | 600 | 0% | TRAIN-FAIL | 0 | 2.5 | - |

**本拍派工**：`collect` / `requester` —— 缺 340 行（85%）；可定向视频 0 条
**结果**：NOPROGRESS（815.3s，本段净增 +0 行）

```
[该段无已知视频，退回按评论数总榜]
weep] 完成：视频 5（跳过 88）评论新 878 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=90097 → 入库56283（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

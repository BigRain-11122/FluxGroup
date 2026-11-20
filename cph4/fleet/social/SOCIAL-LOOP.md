# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-21T00:54:42 ｜ 语料 12067 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 2 | 300 | 99% | - | 0 | - | collect |
| family | 16 | 300 | 95% | - | 0 | - | collect |
| ai_creator | 72 | 400 | 82% | - | 0 | - | collect |
| requester | 86 | 400 | 78% | - | 0 | - | collect |
| student | 107 | 400 | 73% | - | 0 | - | collect |
| critic | 120 | 400 | 70% | - | 0 | - | collect |
| beginner | 154 | 400 | 62% | - | 0 | - | collect |
| music_seeker | 438 | 600 | 27% | SUPPLY | 0 | 6.5 | collect |
| feeler | 550 | 600 | 8% | REJECT | 10 | 2.0 | - |
| tech_nerd | 569 | 600 | 5% | TRAIN-FAIL | 0 | 6.6 | - |
| craft_learner | 2009 | 800 | 0% | REJECT | 10 | 1.4 | - |
| memer | 2155 | 600 | 0% | KEEP | 30 | 8.2 | - |
| peer_pro | 600 | 600 | 0% | KEEP | 30 | 4.3 | - |
| shallow | 3122 | 600 | 0% | TRAIN-FAIL | 0 | 4.4 | - |

**本拍派工**：`collect` / `music_seeker` —— 缺 162 行（27%）；可定向视频 0 条
**结果**：NOPROGRESS（336.2s，本段净增 +0 行）

```
[该段无已知视频，退回按评论数总榜]
weep] 完成：视频 6（跳过 49）评论新 689 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=102884 → 入库62299（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

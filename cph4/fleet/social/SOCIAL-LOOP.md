# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-21T00:23:28 ｜ 语料 11298 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 2 | 300 | 99% | - | 0 | - | collect |
| family | 12 | 300 | 96% | - | 0 | - | collect |
| ai_creator | 67 | 400 | 83% | - | 0 | - | collect |
| requester | 67 | 400 | 83% | - | 0 | - | collect |
| student | 103 | 400 | 74% | - | 0 | - | collect |
| critic | 112 | 400 | 72% | - | 0 | - | collect |
| beginner | 146 | 400 | 64% | - | 0 | - | collect |
| music_seeker | 427 | 600 | 29% | SUPPLY | 0 | 5.9 | collect |
| feeler | 529 | 600 | 12% | REJECT | 10 | 1.5 | - |
| tech_nerd | 535 | 600 | 11% | TRAIN-FAIL | 0 | 6.0 | - |
| peer_pro | 580 | 600 | 3% | KEEP | 30 | 3.8 | - |
| craft_learner | 1852 | 800 | 0% | REJECT | 10 | 0.8 | - |
| memer | 2088 | 600 | 0% | KEEP | 30 | 7.7 | - |
| shallow | 2787 | 600 | 0% | TRAIN-FAIL | 0 | 3.8 | - |

**本拍派工**：`collect` / `critic` —— 缺 288 行（72%）；可定向视频 0 条
**结果**：NOPROGRESS（333.8s，本段净增 +0 行）

```
[该段无已知视频，退回按评论数总榜]
eep] 完成：视频 6（跳过 40）评论新 1134 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=98905 → 入库60875（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

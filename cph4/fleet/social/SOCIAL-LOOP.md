# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T22:46:05 ｜ 语料 9922 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 11 | 300 | 96% | - | 0 | - | collect |
| requester | 59 | 400 | 85% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 80 | 400 | 80% | - | 0 | - | collect |
| critic | 100 | 400 | 75% | - | 0 | - | collect |
| beginner | 119 | 400 | 70% | - | 0 | - | collect |
| music_seeker | 404 | 600 | 33% | SUPPLY | 0 | 4.3 | collect |
| tech_nerd | 483 | 600 | 20% | TRAIN-FAIL | 0 | 4.4 | collect |
| feeler | 490 | 600 | 18% | - | 0 | - | collect |
| peer_pro | 523 | 600 | 13% | KEEP | 30 | 2.2 | - |
| craft_learner | 1458 | 800 | 0% | REJECT | 30 | 6.1 | - |
| memer | 1919 | 600 | 0% | KEEP | 30 | 6.1 | - |
| shallow | 2467 | 600 | 0% | TRAIN-FAIL | 0 | 2.2 | - |

**本拍派工**：`collect` / `traditional` —— 缺 299 行（100%）；可定向视频 0 条
**结果**：NOPROGRESS（349.2s，本段净增 +0 行）

```
[该段无已知视频，退回按评论数总榜]
eep] 完成：视频 6（跳过 13）评论新 1522 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=88390 → 入库55696（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

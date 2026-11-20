# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T20:49:47 ｜ 语料 9641 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 10 | 300 | 97% | - | 0 | - | collect |
| requester | 57 | 400 | 86% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 66 | 400 | 84% | - | 0 | - | collect |
| critic | 98 | 400 | 76% | - | 0 | - | collect |
| beginner | 113 | 400 | 72% | - | 0 | - | collect |
| music_seeker | 401 | 600 | 33% | SUPPLY | 0 | 2.4 | collect |
| feeler | 460 | 600 | 23% | - | 0 | - | collect |
| tech_nerd | 478 | 600 | 20% | TRAIN-FAIL | 0 | 2.5 | collect |
| peer_pro | 520 | 600 | 13% | KEEP | 30 | 0.3 | - |
| craft_learner | 1424 | 800 | 0% | REJECT | 30 | 4.2 | - |
| memer | 1837 | 600 | 0% | KEEP | 30 | 4.1 | - |
| shallow | 2409 | 600 | 0% | TRAIN-FAIL | 0 | 0.3 | - |

**本拍派工**：`collect` / `beginner` —— 缺 287 行（72%）；可定向视频 3 条
**结果**：NOPROGRESS（96.4s，本段净增 +0 行）

```
[定向 3 条已知视频]
sweep] 完成：视频 3（跳过 0）评论新 411 / 弹幕新 0 → /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[sweep] 下一步：python3 Tools/fleet/human_corpus.py --from-dir /Users/junsheng.sun/FluxGroup/cph4/fleet/social/raw
[human] 自有采集 'in'=83217 → 入库53291（use=train）→ /Users/junsheng.sun/FluxGroup/cph4/fleet/social/corpus/human/own_collected.jsonl
```

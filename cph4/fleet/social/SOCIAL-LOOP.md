# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-21T00:34:05 ｜ 语料 11848 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 2 | 300 | 99% | - | 0 | - | collect |
| family | 14 | 300 | 95% | - | 0 | - | collect |
| ai_creator | 69 | 400 | 83% | - | 0 | - | collect |
| requester | 83 | 400 | 79% | - | 0 | - | collect |
| student | 107 | 400 | 73% | - | 0 | - | collect |
| critic | 119 | 400 | 70% | - | 0 | - | collect |
| beginner | 152 | 400 | 62% | - | 0 | - | collect |
| music_seeker | 437 | 600 | 27% | SUPPLY | 0 | 6.1 | collect |
| feeler | 546 | 600 | 9% | REJECT | 10 | 1.7 | - |
| tech_nerd | 565 | 600 | 6% | TRAIN-FAIL | 0 | 6.2 | - |
| peer_pro | 598 | 600 | 0% | KEEP | 30 | 4.0 | - |
| craft_learner | 1986 | 800 | 0% | REJECT | 10 | 1.0 | - |
| memer | 2136 | 600 | 0% | KEEP | 30 | 7.9 | - |
| shallow | 2990 | 600 | 0% | TRAIN-FAIL | 0 | 4.0 | - |

**本拍派工**：`tune` / `__all__` —— 各段无缺料、无待验件，做参数复检
**结果**：OK（0.4s）

```
（min_human 固定 8）
   maxlen=45   通过  388（21.1%）
   maxlen=60   通过  414（22.5%）
   maxlen=75   通过  434（23.6%）
   maxlen=90   通过  447（24.3%）←当前
   maxlen=120  通过  465（25.3%）

[scan] min_human（maxlen 固定 90，仅可信型语料）
   min_human=0  通过 1152 / 1200（96.0%）
   min_human=4  通过  896 / 1200（74.7%）
   min_human=8  通过  373 / 1200（31.1%）←当前
   ⚠ min_human=0 能让通过数 373→1152，但通过率不是质量：需下游评测才可改

[tune] 无参数越过边际（5%），保持现状
```

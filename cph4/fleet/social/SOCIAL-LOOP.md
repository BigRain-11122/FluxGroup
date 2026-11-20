# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T23:20:41 ｜ 语料 10396 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 12 | 300 | 96% | - | 0 | - | collect |
| requester | 62 | 400 | 84% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 88 | 400 | 78% | - | 0 | - | collect |
| critic | 104 | 400 | 74% | - | 0 | - | collect |
| beginner | 140 | 400 | 65% | - | 0 | - | collect |
| music_seeker | 415 | 600 | 31% | SUPPLY | 0 | 4.9 | collect |
| tech_nerd | 501 | 600 | 16% | TRAIN-FAIL | 0 | 5.0 | collect |
| feeler | 503 | 600 | 16% | REJECT | 10 | 0.5 | collect |
| peer_pro | 538 | 600 | 10% | KEEP | 30 | 2.8 | - |
| craft_learner | 1574 | 800 | 0% | REJECT | 30 | 6.7 | - |
| memer | 1990 | 600 | 0% | KEEP | 30 | 6.7 | - |
| shallow | 2579 | 600 | 0% | TRAIN-FAIL | 0 | 2.8 | - |

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

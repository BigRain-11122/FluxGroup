# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-21T22:36:54 ｜ 语料 11084 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 3 | 300 | 99% | - | 0 | - | collect |
| family | 17 | 300 | 94% | - | 0 | - | collect |
| requester | 62 | 400 | 84% | - | 0 | - | collect |
| ai_creator | 64 | 400 | 84% | - | 0 | - | collect |
| student | 105 | 400 | 74% | - | 0 | - | collect |
| critic | 125 | 400 | 69% | - | 0 | - | collect |
| beginner | 150 | 400 | 62% | - | 0 | - | collect |
| music_seeker | 441 | 600 | 26% | BLOCKED | 0 | 3.1 | collect |
| feeler | 550 | 600 | 8% | BLOCKED | 0 | 2.9 | - |
| tech_nerd | 570 | 600 | 5% | REJECT | 10 | 0.3 | - |
| craft_learner | 2138 | 800 | 0% | TRAIN-FAIL | 0 | 2.1 | - |
| memer | 2157 | 600 | 0% | KEEP | 10 | 0.9 | verify |
| peer_pro | 603 | 600 | 0% | BLOCKED | 0 | 3.0 | - |
| shallow | 1948 | 600 | 0% | KEEP | 10 | 2.5 | verify |

**本拍派工**：`tune` / `__all__` —— 各段无缺料、无待验件，做参数复检
**结果**：OK（0.6s）

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

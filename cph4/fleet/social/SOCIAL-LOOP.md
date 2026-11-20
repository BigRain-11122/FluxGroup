# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T22:56:58 ｜ 语料 10161 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 11 | 300 | 96% | - | 0 | - | collect |
| requester | 60 | 400 | 85% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 85 | 400 | 79% | - | 0 | - | collect |
| critic | 104 | 400 | 74% | - | 0 | - | collect |
| beginner | 122 | 400 | 70% | - | 0 | - | collect |
| music_seeker | 412 | 600 | 31% | SUPPLY | 0 | 4.5 | collect |
| tech_nerd | 497 | 600 | 17% | TRAIN-FAIL | 0 | 4.6 | collect |
| feeler | 500 | 600 | 17% | REJECT | 10 | 0.1 | collect |
| peer_pro | 532 | 600 | 11% | KEEP | 30 | 2.4 | - |
| craft_learner | 1505 | 800 | 0% | REJECT | 30 | 6.3 | - |
| memer | 1968 | 600 | 0% | KEEP | 30 | 6.3 | - |
| shallow | 2503 | 600 | 0% | TRAIN-FAIL | 0 | 2.4 | - |

**本拍派工**：`tune` / `__all__` —— 各段无缺料、无待验件，做参数复检
**结果**：OK（0.8s）

```
（min_human 固定 8）
   maxlen=45   通过  387（21.1%）
   maxlen=60   通过  412（22.4%）
   maxlen=75   通过  431（23.4%）
   maxlen=90   通过  445（24.2%）←当前
   maxlen=120  通过  464（25.2%）

[scan] min_human（maxlen 固定 90，仅可信型语料）
   min_human=0  通过 1149 / 1200（95.8%）
   min_human=4  通过  894 / 1200（74.5%）
   min_human=8  通过  371 / 1200（30.9%）←当前
   ⚠ min_human=0 能让通过数 371→1149，但通过率不是质量：需下游评测才可改

[tune] 无参数越过边际（5%），保持现状
```

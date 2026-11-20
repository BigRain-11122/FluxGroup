# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T22:03:55 ｜ 语料 9647 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 10 | 300 | 97% | - | 0 | - | collect |
| requester | 57 | 400 | 86% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 66 | 400 | 84% | - | 0 | - | collect |
| critic | 98 | 400 | 76% | - | 0 | - | collect |
| beginner | 114 | 400 | 72% | - | 0 | - | collect |
| music_seeker | 401 | 600 | 33% | SUPPLY | 0 | 3.6 | collect |
| feeler | 460 | 600 | 23% | - | 0 | - | collect |
| tech_nerd | 478 | 600 | 20% | TRAIN-FAIL | 0 | 3.7 | collect |
| peer_pro | 520 | 600 | 13% | KEEP | 30 | 1.5 | - |
| craft_learner | 1428 | 800 | 0% | REJECT | 30 | 5.4 | - |
| memer | 1837 | 600 | 0% | KEEP | 30 | 5.4 | - |
| shallow | 2410 | 600 | 0% | TRAIN-FAIL | 0 | 1.5 | - |

**本拍派工**：`tune` / `__all__` —— 各段无缺料、无待验件，做参数复检
**结果**：OK（0.4s）

```
（min_human 固定 8）
   maxlen=45   通过  365（19.9%）
   maxlen=60   通过  394（21.4%）
   maxlen=75   通过  417（22.7%）
   maxlen=90   通过  428（23.3%）←当前
   maxlen=120  通过  445（24.2%）

[scan] min_human（maxlen 固定 90，仅可信型语料）
   min_human=0  通过 1157 / 1200（96.4%）
   min_human=4  通过  891 / 1200（74.2%）
   min_human=8  通过  354 / 1200（29.5%）←当前
   ⚠ min_human=0 能让通过数 354→1157，但通过率不是质量：需下游评测才可改

[tune] 无参数越过边际（5%），保持现状
```

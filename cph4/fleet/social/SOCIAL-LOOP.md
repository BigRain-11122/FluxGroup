# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T22:41:02 ｜ 语料 9922 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 11 | 300 | 96% | - | 0 | - | collect |
| requester | 59 | 400 | 85% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 80 | 400 | 80% | - | 0 | - | collect |
| critic | 100 | 400 | 75% | - | 0 | - | collect |
| beginner | 119 | 400 | 70% | - | 0 | - | collect |
| music_seeker | 404 | 600 | 33% | SUPPLY | 0 | 4.2 | collect |
| tech_nerd | 483 | 600 | 20% | TRAIN-FAIL | 0 | 4.3 | collect |
| feeler | 490 | 600 | 18% | - | 0 | - | collect |
| peer_pro | 523 | 600 | 13% | KEEP | 30 | 2.1 | - |
| craft_learner | 1458 | 800 | 0% | REJECT | 30 | 6.0 | - |
| memer | 1919 | 600 | 0% | KEEP | 30 | 6.0 | - |
| shallow | 2467 | 600 | 0% | TRAIN-FAIL | 0 | 2.1 | - |

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

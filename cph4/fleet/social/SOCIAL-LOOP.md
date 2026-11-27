# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-27T21:30:24 ｜ 语料 18670 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 4 | 300 | 99% | - | 0 | - | collect |
| family | 39 | 300 | 87% | - | 0 | - | collect |
| requester | 68 | 400 | 83% | - | 0 | - | collect |
| ai_creator | 105 | 400 | 74% | - | 0 | - | collect |
| student | 148 | 400 | 63% | - | 0 | - | collect |
| beginner | 193 | 400 | 52% | - | 0 | - | collect |
| craft_learner | 2595 | 800 | 0% | REJECT | 10 | 10.6 | - |
| critic | 439 | 400 | 0% | REJECT | 10 | 21.4 | - |
| feeler | 1106 | 600 | 0% | REJECT | 10 | 17.7 | - |
| memer | 4493 | 600 | 0% | REJECT | 30 | 3.6 | - |
| music_seeker | 1647 | 600 | 0% | KEEP | 30 | 4.1 | - |
| peer_pro | 656 | 600 | 0% | REJECT | 10 | 20.8 | - |
| shallow | 3220 | 600 | 0% | REJECT | 30 | 1.5 | - |
| tech_nerd | 778 | 600 | 0% | REJECT | 30 | 3.0 | - |

**本拍派工**：`tune` / `__all__` —— 各段无缺料、无待验件，做参数复检
**结果**：OK（0.4s）

```
xlen=60   通过  413（22.5%）
   maxlen=75   通过  438（23.8%）
   maxlen=90   通过  454（24.7%）←当前
   maxlen=120  通过  478（26.0%）

[scan] min_human（maxlen 固定 90，仅可信型语料）
   min_human=0  通过 1130 / 1200（94.2%）
   min_human=4  通过  898 / 1200（74.8%）
   min_human=8  通过  380 / 1200（31.7%）←当前
   ⚠ min_human=0 能让通过数 380→1130，但通过率不是质量：需下游评测才可改

[tune] 建议改：
   maxlen → 120（通过率 24.7% → 26.0%（+5%））
[tune] 未改（加 --apply 生效）
```

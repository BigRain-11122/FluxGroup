# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-20T16:40:06 ｜ 语料 8893 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 1 | 300 | 100% | - | 0 | - | collect |
| family | 9 | 300 | 97% | - | 0 | - | collect |
| student | 56 | 400 | 86% | - | 0 | - | collect |
| requester | 57 | 400 | 86% | - | 0 | - | collect |
| ai_creator | 64 | 400 | 84% | - | 0 | - | collect |
| critic | 94 | 400 | 76% | - | 0 | - | collect |
| beginner | 113 | 400 | 72% | - | 0 | - | collect |
| music_seeker | 397 | 600 | 34% | KEEP | 10 | 5.5 | collect |
| feeler | 417 | 600 | 30% | - | 0 | - | collect |
| tech_nerd | 471 | 600 | 22% | KEEP | 10 | 5.5 | collect |
| peer_pro | 493 | 600 | 18% | KEEP | 10 | 0.9 | collect |
| craft_learner | 1308 | 800 | 0% | REJECT | 30 | 0.0 | - |
| memer | 1521 | 600 | 0% | KEEP | 10 | 4.0 | verify |
| shallow | 2294 | 600 | 0% | - | 0 | - | train |

**本拍派工**：`verify` / `memer` —— 判 KEEP 只用了 n=10，功率不足（目标 30）
**结果**：OK（58.8s）

```
[verify] KEEP（n=30）：均分 +27.5 / 人味 +7.6
```

# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-23T11:28:59 ｜ 语料 11277 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 3 | 300 | 99% | - | 0 | - | collect |
| family | 17 | 300 | 94% | - | 0 | - | collect |
| requester | 62 | 400 | 84% | - | 0 | - | collect |
| ai_creator | 65 | 400 | 84% | - | 0 | - | collect |
| student | 107 | 400 | 73% | - | 0 | - | collect |
| critic | 129 | 400 | 68% | - | 0 | - | collect |
| beginner | 152 | 400 | 62% | - | 0 | - | collect |
| music_seeker | 447 | 600 | 26% | KEEP | 10 | 0.2 | collect |
| feeler | 551 | 600 | 8% | REJECT | 10 | 5.6 | - |
| tech_nerd | 592 | 600 | 1% | REJECT | 10 | 4.4 | - |
| craft_learner | 2206 | 800 | 0% | REJECT | 10 | 5.0 | - |
| memer | 2207 | 600 | 0% | KEEP | 10 | 6.2 | verify |
| peer_pro | 606 | 600 | 0% | TRAIN-FAIL | 0 | 2.8 | - |
| shallow | 1955 | 600 | 0% | BLOCKED | 0 | 0.5 | - |

**本拍派工**：`verify` / `memer` —— 判 KEEP 只用了 n=10，功率不足（目标 30）
**结果**：OK（27.7s）

```
[verify] REJECT（n=30）：均分只 +0.5（需 ≥5.0）
```

# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-22T02:35:03 ｜ 语料 11085 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 3 | 300 | 99% | - | 0 | - | collect |
| family | 17 | 300 | 94% | - | 0 | - | collect |
| requester | 62 | 400 | 84% | - | 0 | - | collect |
| ai_creator | 64 | 400 | 84% | - | 0 | - | collect |
| student | 105 | 400 | 74% | - | 0 | - | collect |
| critic | 125 | 400 | 69% | - | 0 | - | collect |
| beginner | 150 | 400 | 62% | - | 0 | - | collect |
| music_seeker | 441 | 600 | 26% | KEEP | 10 | 2.3 | collect |
| feeler | 550 | 600 | 8% | REJECT | 10 | 1.1 | - |
| tech_nerd | 570 | 600 | 5% | KEEP | 10 | 0.0 | verify |
| craft_learner | 2139 | 800 | 0% | REJECT | 10 | 0.6 | - |
| memer | 2157 | 600 | 0% | KEEP | 30 | 3.5 | - |
| peer_pro | 603 | 600 | 0% | REJECT | 10 | 1.7 | - |
| shallow | 1948 | 600 | 0% | KEEP | 30 | 3.4 | - |

**本拍派工**：`verify` / `tech_nerd` —— 判 KEEP 只用了 n=10，功率不足（目标 30）
**结果**：OK（61.6s）

```
[verify] REJECT（n=30）：均分只 +3.7（需 ≥5.0）
```

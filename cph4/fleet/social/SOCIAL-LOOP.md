# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-23T23:26:01 ｜ 语料 12060 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 3 | 300 | 99% | - | 0 | - | collect |
| family | 19 | 300 | 94% | - | 0 | - | collect |
| requester | 64 | 400 | 84% | - | 0 | - | collect |
| ai_creator | 85 | 400 | 79% | - | 0 | - | collect |
| student | 109 | 400 | 73% | - | 0 | - | collect |
| critic | 136 | 400 | 66% | - | 0 | - | collect |
| beginner | 163 | 400 | 59% | - | 0 | - | collect |
| music_seeker | 465 | 600 | 22% | KEEP | 10 | 4.4 | collect |
| craft_learner | 2334 | 800 | 0% | REJECT | 10 | 0.9 | - |
| feeler | 613 | 600 | 0% | REJECT | 10 | 2.6 | - |
| memer | 2264 | 600 | 0% | KEEP | 10 | 3.8 | verify |
| peer_pro | 621 | 600 | 0% | KEEP | 10 | 5.5 | verify |
| shallow | 2152 | 600 | 0% | REJECT | 10 | 5.0 | - |
| tech_nerd | 650 | 600 | 0% | KEEP | 10 | 3.2 | verify |

**本拍派工**：`collect` / `student` —— 缺 291 行（73%）；可定向视频 38 条
**结果**：FAIL（0.1s）

```
[定向 6 条已知视频] [sweep] BLOCKED 学习循环正在用 profile（pid 73504），本轮跳过
```

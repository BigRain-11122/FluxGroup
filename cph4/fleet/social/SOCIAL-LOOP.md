# 养号自驱环路（SOCIAL-LOOP）

> 更新时间 2026-11-23T21:06:31 ｜ 语料 3952 行 ｜ 每段评测目标 n=30

| 段 | 可用行 | 目标 | 缺口 | 最近判词 | n | 龄期(h) | 下一步 |
|---|---|---|---|---|---|---|---|
| traditional | 0 | 300 | 100% | - | 0 | - | collect |
| family | 7 | 300 | 98% | - | 0 | - | collect |
| student | 28 | 400 | 93% | - | 0 | - | collect |
| requester | 29 | 400 | 93% | - | 0 | - | collect |
| critic | 41 | 400 | 90% | - | 0 | - | collect |
| ai_creator | 43 | 400 | 89% | - | 0 | - | collect |
| beginner | 45 | 400 | 89% | - | 0 | - | collect |
| peer_pro | 103 | 600 | 83% | KEEP | 10 | 3.2 | collect |
| music_seeker | 131 | 600 | 78% | KEEP | 10 | 2.1 | collect |
| feeler | 261 | 600 | 56% | REJECT | 10 | 0.2 | collect |
| tech_nerd | 326 | 600 | 46% | KEEP | 10 | 0.9 | collect |
| craft_learner | 524 | 800 | 34% | REJECT | 10 | 3.9 | collect |
| memer | 906 | 600 | 0% | KEEP | 10 | 1.5 | verify |
| shallow | 851 | 600 | 0% | REJECT | 10 | 2.6 | - |

**本拍派工**：`collect` / `student` —— 缺 372 行（93%）；可定向视频 38 条
**结果**：FAIL（0.1s）

```
[定向 6 条已知视频] [sweep] BLOCKED 学习循环正在用 profile（pid 22661），本轮跳过
```

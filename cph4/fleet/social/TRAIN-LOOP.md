# 7×24 训练循环（2026-11-21T14:16:33）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| shallow | 3217 | 是 | 配方更新 v3-natural-dist（3217 行） |
| craft_learner | 2124 | 是 | 配方更新 v3-natural-dist（2124 行） |
| peer_pro | 622 | 是 | 配方更新 v3-natural-dist（622 行） |
| tech_nerd | 574 | 是 | 配方更新 v3-natural-dist（574 行） |
| feeler | 558 | 是 | 配方更新 v3-natural-dist（558 行） |
| music_seeker | 442 | 是 | 配方更新 v3-natural-dist（442 行） |
| memer | 2191 | 否 | 冷却中（0.0h 前刚训过，语料 2191→2191 未涨 10%） |
| beginner | 162 | 否 | 语料 162 < 200 |
| critic | 122 | 否 | 语料 122 < 200 |
| student | 108 | 否 | 语料 108 < 200 |
| requester | 91 | 否 | 语料 91 < 200 |
| ai_creator | 72 | 否 | 语料 72 < 200 |
| family | 17 | 否 | 语料 17 < 200 |
| traditional | 3 | 否 | 语料 3 < 200 |

## 补料清单（训练线的真实瓶颈）

有 7 个段低于 200 行，合计还差 **825 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| beginner | 162 | 38 |
| critic | 122 | 78 |
| student | 108 | 92 |
| requester | 91 | 109 |
| ai_creator | 72 | 128 |
| family | 17 | 183 |
| traditional | 3 | 197 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-20T15:47 | peer_pro | 10 | 493 | 3.338 | 300 | 53.0 | 73.6 | 2.0 | KEEP |
| 11-20T16:39 | craft_learner | 30 | None | None | None | 81.4 | 78.2 | None | REJECT |
| 11-20T16:41 | memer | 30 | None | None | None | 49.0 | 76.5 | None | KEEP |
| 11-20T18:21 | tech_nerd | 0 | 471 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-20T18:26 | music_seeker | 0 | 386 | None | None | None | None | None | SUPPLY（样本不足） |
| 11-20T20:33 | shallow | 0 | 2294 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-20T20:34 | peer_pro | 30 | None | None | None | 50.3 | 57.4 | None | KEEP |
| 11-20T22:53 | feeler | 10 | 460 | 3.449 | 200 | 56.5 | 59.4 | -7.0 | REJECT |
| 11-20T23:32 | craft_learner | 10 | 1505 | 3.606 | 500 | 85.5 | 77.8 | -1.0 | REJECT |
| 11-21T14:16 | memer | 10 | 2191 | 3.337 | 400 | 38.7 | 73.4 | 10.0 | KEEP |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

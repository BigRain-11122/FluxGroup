# 7×24 训练循环（2026-11-21T16:19:51）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| memer | 217 | 是 | 配方更新 v3-natural-dist（217 行） |
| shallow | 557 | 否 | 冷却中（0.0h 前刚训过，语料 557→557 未涨 10%） |
| craft_learner | 176 | 否 | 语料 176 < 200 |
| tech_nerd | 106 | 否 | 语料 106 < 200 |
| feeler | 84 | 否 | 语料 84 < 200 |
| peer_pro | 48 | 否 | 语料 48 < 200 |
| music_seeker | 45 | 否 | 语料 45 < 200 |
| ai_creator | 36 | 否 | 语料 36 < 200 |
| requester | 20 | 否 | 语料 20 < 200 |
| student | 9 | 否 | 语料 9 < 200 |
| critic | 8 | 否 | 语料 8 < 200 |
| beginner | 6 | 否 | 语料 6 < 200 |

## 补料清单（训练线的真实瓶颈）

有 10 个段低于 200 行，合计还差 **1462 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| craft_learner | 176 | 24 |
| tech_nerd | 106 | 94 |
| feeler | 84 | 116 |
| peer_pro | 48 | 152 |
| music_seeker | 45 | 155 |
| ai_creator | 36 | 164 |
| requester | 20 | 180 |
| student | 9 | 191 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-20T16:41 | memer | 30 | None | None | None | 49.0 | 76.5 | None | KEEP |
| 11-20T18:21 | tech_nerd | 0 | 471 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-20T18:26 | music_seeker | 0 | 386 | None | None | None | None | None | SUPPLY（样本不足） |
| 11-20T20:33 | shallow | 0 | 2294 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-20T20:34 | peer_pro | 30 | None | None | None | 50.3 | 57.4 | None | KEEP |
| 11-20T22:53 | feeler | 10 | 460 | 3.449 | 200 | 56.5 | 59.4 | -7.0 | REJECT |
| 11-20T23:32 | craft_learner | 10 | 1505 | 3.606 | 500 | 85.5 | 77.8 | -1.0 | REJECT |
| 11-21T14:16 | memer | 10 | 2191 | 3.337 | 400 | 38.7 | 73.4 | 10.0 | KEEP |
| 11-21T15:16 | tech_nerd | 10 | 574 | 4.214 | 200 | 54.0 | 77.0 | 5.0 | KEEP |
| 11-21T16:19 | shallow | 10 | 557 | 3.156 | 400 | 54.3 | 75.4 | 9.0 | KEEP |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

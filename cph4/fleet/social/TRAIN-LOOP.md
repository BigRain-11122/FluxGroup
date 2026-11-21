# 7×24 训练循环（2026-11-22T00:54:15）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| memer | 2157 | 是 | 配方更新 v5-shape-quota（2157 行） |
| craft_learner | 2139 | 是 | 配方更新 v5-shape-quota（2139 行） |
| shallow | 1948 | 是 | 配方更新 v5-shape-quota（1948 行） |
| tech_nerd | 570 | 是 | 配方更新 v5-shape-quota（570 行） |
| feeler | 550 | 是 | 配方更新 v5-shape-quota（550 行） |
| music_seeker | 441 | 是 | 配方更新 v5-shape-quota（441 行） |
| peer_pro | 603 | 否 | 冷却中（0.0h 前刚训过，语料 603→603 未涨 10%） |
| beginner | 150 | 否 | 语料 150 < 200 |
| critic | 125 | 否 | 语料 125 < 200 |
| student | 105 | 否 | 语料 105 < 200 |
| ai_creator | 64 | 否 | 语料 64 < 200 |
| requester | 62 | 否 | 语料 62 < 200 |
| family | 17 | 否 | 语料 17 < 200 |
| traditional | 3 | 否 | 语料 3 < 200 |

## 补料清单（训练线的真实瓶颈）

有 7 个段低于 200 行，合计还差 **874 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| beginner | 150 | 50 |
| critic | 125 | 75 |
| student | 105 | 95 |
| ai_creator | 64 | 136 |
| requester | 62 | 138 |
| family | 17 | 183 |
| traditional | 3 | 197 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-21T19:35 | peer_pro | 0 | 603 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-21T19:41 | feeler | 0 | 364 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-21T20:06 | shallow | 10 | 1948 | 3.584 | 400 | 54.3 | 69.3 | 7.0 | KEEP |
| 11-21T20:29 | craft_learner | 0 | 2138 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-21T21:40 | memer | 10 | 2157 | 3.346 | 300 | 38.7 | 50.3 | 3.0 | KEEP |
| 11-21T22:17 | tech_nerd | 10 | 570 | 3.638 | 300 | 54.0 | 50.8 | -1.0 | REJECT |
| 11-21T23:02 | memer | 30 | None | None | None | 49.0 | 54.7 | None | KEEP |
| 11-21T23:08 | shallow | 30 | None | None | None | 44.1 | 61.3 | None | KEEP |
| 11-22T00:19 | music_seeker | 10 | 441 | 2.913 | 400 | 37.5 | 60.3 | 6.0 | KEEP |
| 11-22T00:54 | peer_pro | 10 | 603 | 3.783 | 400 | 51.8 | 51.8 | -1.0 | REJECT |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

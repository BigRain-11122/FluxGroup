# 7×24 训练循环（2026-11-23T02:13:22）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| memer | 2207 | 是 | 配方更新 v5-shape-quota（2207 行） |
| craft_learner | 2206 | 是 | 配方更新 v5-shape-quota（2206 行） |
| shallow | 1955 | 是 | 配方更新 v5-shape-quota（1955 行） |
| peer_pro | 606 | 是 | 配方更新 v5-shape-quota（606 行） |
| tech_nerd | 592 | 是 | 配方更新 v5-shape-quota（592 行） |
| music_seeker | 447 | 是 | 配方更新 v5-shape-quota（447 行） |
| feeler | 551 | 否 | 冷却中（0.0h 前刚训过，语料 551→551 未涨 10%） |
| beginner | 152 | 否 | 语料 152 < 200 |
| critic | 129 | 否 | 语料 129 < 200 |
| student | 107 | 否 | 语料 107 < 200 |
| ai_creator | 65 | 否 | 语料 65 < 200 |
| requester | 62 | 否 | 语料 62 < 200 |
| family | 17 | 否 | 语料 17 < 200 |
| traditional | 3 | 否 | 语料 3 < 200 |

## 补料清单（训练线的真实瓶颈）

有 7 个段低于 200 行，合计还差 **865 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| beginner | 152 | 48 |
| critic | 129 | 71 |
| student | 107 | 93 |
| ai_creator | 65 | 135 |
| requester | 62 | 138 |
| family | 17 | 183 |
| traditional | 3 | 197 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-22T20:17 | music_seeker | 10 | 447 | 2.913 | 400 | 37.5 | 63.5 | 6.0 | KEEP |
| 11-22T20:25 | memer | 30 | None | None | None | 49.0 | 40.0 | None | REJECT |
| 11-22T20:56 | feeler | 10 | 551 | 3.322 | 400 | 56.5 | 49.3 | -5.0 | REJECT |
| 11-22T21:30 | craft_learner | 10 | 2204 | 3.478 | 200 | 85.5 | 81.5 | 2.0 | REJECT |
| 11-22T22:36 | tech_nerd | 0 | 591 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-22T23:57 | peer_pro | 10 | 606 | 3.783 | 400 | 51.8 | 52.8 | -1.0 | REJECT |
| 11-23T00:33 | shallow | 10 | 1955 | 3.663 | 400 | 54.3 | 58.0 | 4.0 | REJECT |
| 11-23T00:49 | music_seeker | 0 | 447 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-23T01:36 | memer | 10 | 2207 | 2.99 | 400 | 38.7 | 42.4 | 2.0 | REJECT |
| 11-23T02:13 | feeler | 10 | 551 | 3.322 | 400 | 56.5 | 43.1 | -6.0 | REJECT |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

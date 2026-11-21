# 7×24 训练循环（2026-11-22T03:45:25）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| memer | 2157 | 是 | 配方更新 v5-shape-quota（2157 行） |
| craft_learner | 2139 | 是 | 配方更新 v5-shape-quota（2139 行） |
| shallow | 1948 | 是 | 配方更新 v5-shape-quota（1948 行） |
| peer_pro | 603 | 是 | 配方更新 v5-shape-quota（603 行） |
| tech_nerd | 570 | 是 | 配方更新 v5-shape-quota（570 行） |
| feeler | 550 | 是 | 配方更新 v5-shape-quota（550 行） |
| music_seeker | 441 | 否 | 冷却中（0.0h 前刚训过，语料 441→441 未涨 10%） |
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
| 11-21T23:08 | shallow | 30 | None | None | None | 44.1 | 61.3 | None | KEEP |
| 11-22T00:19 | music_seeker | 10 | 441 | 2.913 | 400 | 37.5 | 60.3 | 6.0 | KEEP |
| 11-22T00:54 | peer_pro | 10 | 603 | 3.783 | 400 | 51.8 | 51.8 | -1.0 | REJECT |
| 11-22T01:28 | feeler | 10 | 550 | 3.322 | 400 | 56.5 | 57.5 | -2.0 | REJECT |
| 11-22T02:00 | craft_learner | 10 | 2139 | 3.478 | 200 | 85.5 | 76.8 | 0.0 | REJECT |
| 11-22T02:33 | tech_nerd | 10 | 570 | 3.522 | 400 | 54.0 | 67.0 | 3.0 | KEEP |
| 11-22T02:36 | tech_nerd | 30 | None | None | None | 56.7 | 60.4 | None | REJECT |
| 11-22T02:38 | memer | 0 | 2157 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-22T03:13 | shallow | 10 | 1948 | 3.663 | 400 | 54.3 | 43.8 | 1.0 | REJECT |
| 11-22T03:45 | music_seeker | 10 | 441 | 2.913 | 400 | 37.5 | 72.0 | 8.0 | KEEP |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

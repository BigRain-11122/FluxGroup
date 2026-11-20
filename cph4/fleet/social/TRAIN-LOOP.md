# 7×24 训练循环（2026-11-20T22:53:30）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| shallow | 2410 | 是 | 配方更新 v3-natural-dist（2410 行） |
| memer | 1837 | 是 | 配方更新 v3-natural-dist（1837 行） |
| craft_learner | 1428 | 是 | 配方更新 v3-natural-dist（1428 行） |
| peer_pro | 520 | 是 | 配方更新 v3-natural-dist（520 行） |
| tech_nerd | 478 | 是 | 配方更新 v3-natural-dist（478 行） |
| music_seeker | 401 | 是 | 配方更新 v3-natural-dist（401 行） |
| feeler | 460 | 否 | 冷却中（0.0h 前刚训过，语料 460→460 未涨 10%） |
| beginner | 114 | 否 | 语料 114 < 200 |
| critic | 98 | 否 | 语料 98 < 200 |
| student | 66 | 否 | 语料 66 < 200 |
| ai_creator | 65 | 否 | 语料 65 < 200 |
| requester | 57 | 否 | 语料 57 < 200 |
| family | 10 | 否 | 语料 10 < 200 |
| traditional | 1 | 否 | 语料 1 < 200 |

## 补料清单（训练线的真实瓶颈）

有 7 个段低于 200 行，合计还差 **989 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| beginner | 114 | 86 |
| critic | 98 | 102 |
| student | 66 | 134 |
| ai_creator | 65 | 135 |
| requester | 57 | 143 |
| family | 10 | 190 |
| traditional | 1 | 199 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-20T13:49 | peer_pro | 10 | 493 | 3.375 | 300 | 47.6 | 87.3 | 9.0 | KEEP |
| 11-20T14:16 | __all__ | 10 | 0 | 3.42 | 100 | 49.2 | 70.0 | 8.5 | KEEP |
| 11-20T15:47 | peer_pro | 10 | 493 | 3.338 | 300 | 53.0 | 73.6 | 2.0 | KEEP |
| 11-20T16:39 | craft_learner | 30 | None | None | None | 81.4 | 78.2 | None | REJECT |
| 11-20T16:41 | memer | 30 | None | None | None | 49.0 | 76.5 | None | KEEP |
| 11-20T18:21 | tech_nerd | 0 | 471 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-20T18:26 | music_seeker | 0 | 386 | None | None | None | None | None | SUPPLY（样本不足） |
| 11-20T20:33 | shallow | 0 | 2294 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-20T20:34 | peer_pro | 30 | None | None | None | 50.3 | 57.4 | None | KEEP |
| 11-20T22:53 | feeler | 10 | 460 | 3.449 | 200 | 56.5 | 59.4 | -7.0 | REJECT |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

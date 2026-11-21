# 7×24 训练循环（2026-11-21T18:17:37）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| memer | 2143 | 是 | 配方更新 v4-clean-corpus（2143 行） |
| craft_learner | 2071 | 是 | 配方更新 v4-clean-corpus（2071 行） |
| shallow | 1894 | 是 | 配方更新 v4-clean-corpus（1894 行） |
| peer_pro | 602 | 是 | 配方更新 v4-clean-corpus（602 行） |
| tech_nerd | 557 | 是 | 配方更新 v4-clean-corpus（557 行） |
| feeler | 545 | 是 | 配方更新 v4-clean-corpus（545 行） |
| music_seeker | 436 | 是 | 配方更新 v4-clean-corpus（436 行） |
| beginner | 149 | 否 | 语料 149 < 200 |
| critic | 122 | 否 | 语料 122 < 200 |
| student | 105 | 否 | 语料 105 < 200 |
| ai_creator | 64 | 否 | 语料 64 < 200 |
| requester | 62 | 否 | 语料 62 < 200 |
| family | 17 | 否 | 语料 17 < 200 |
| traditional | 3 | 否 | 语料 3 < 200 |

## 补料清单（训练线的真实瓶颈）

有 7 个段低于 200 行，合计还差 **878 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| beginner | 149 | 51 |
| critic | 122 | 78 |
| student | 105 | 95 |
| ai_creator | 64 | 136 |
| requester | 62 | 138 |
| family | 17 | 183 |
| traditional | 3 | 197 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-20T20:33 | shallow | 0 | 2294 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-20T20:34 | peer_pro | 30 | None | None | None | 50.3 | 57.4 | None | KEEP |
| 11-20T22:53 | feeler | 10 | 460 | 3.449 | 200 | 56.5 | 59.4 | -7.0 | REJECT |
| 11-20T23:32 | craft_learner | 10 | 1505 | 3.606 | 500 | 85.5 | 77.8 | -1.0 | REJECT |
| 11-21T14:16 | memer | 10 | 2191 | 3.337 | 400 | 38.7 | 73.4 | 10.0 | KEEP |
| 11-21T15:16 | tech_nerd | 10 | 574 | 4.214 | 200 | 54.0 | 77.0 | 5.0 | KEEP |
| 11-21T16:19 | shallow | 10 | 557 | 3.156 | 400 | 54.3 | 75.4 | 9.0 | KEEP |
| 11-21T17:19 | music_seeker | 10 | 442 | 3.323 | 200 | 37.5 | 67.6 | 7.0 | KEEP |
| 11-21T18:12 | peer_pro | 10 | 622 | 3.237 | 400 | 51.8 | 71.5 | 6.0 | KEEP |
| 11-21T18:17 | feeler | 0 | 545 | None | None | None | None | None | EVAL-MISSING（样本不足） |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

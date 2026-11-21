# 7×24 训练循环（2026-11-21T21:45:25）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| shallow | 159 | 否 | 语料 159 < 200 |
| craft_learner | 129 | 否 | 语料 129 < 200 |
| memer | 104 | 否 | 语料 104 < 200 |
| tech_nerd | 56 | 否 | 语料 56 < 200 |
| feeler | 41 | 否 | 语料 41 < 200 |
| peer_pro | 41 | 否 | 语料 41 < 200 |
| music_seeker | 33 | 否 | 语料 33 < 200 |
| requester | 13 | 否 | 语料 13 < 200 |
| student | 9 | 否 | 语料 9 < 200 |
| ai_creator | 7 | 否 | 语料 7 < 200 |
| critic | 6 | 否 | 语料 6 < 200 |
| beginner | 4 | 否 | 语料 4 < 200 |

## 补料清单（训练线的真实瓶颈）

有 12 个段低于 200 行，合计还差 **1798 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| shallow | 159 | 41 |
| craft_learner | 129 | 71 |
| memer | 104 | 96 |
| tech_nerd | 56 | 144 |
| peer_pro | 41 | 159 |
| feeler | 41 | 159 |
| music_seeker | 33 | 167 |
| requester | 13 | 187 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-21T18:22 | craft_learner | 0 | 2071 | None | None | None | None | None | SUPPLY（样本不足） |
| 11-21T19:02 | shallow | 10 | 3217 | 3.347 | 500 | 54.3 | 58.7 | 5.0 | REJECT |
| 11-21T19:19 | memer | 0 | 2143 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-21T19:24 | tech_nerd | 0 | 557 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-21T19:30 | music_seeker | 0 | 439 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-21T19:35 | peer_pro | 0 | 603 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-21T19:41 | feeler | 0 | 364 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-21T20:06 | shallow | 10 | 1948 | 3.584 | 400 | 54.3 | 69.3 | 7.0 | KEEP |
| 11-21T20:29 | craft_learner | 0 | 2138 | None | None | None | None | None | TRAIN-FAIL（样本不足） |
| 11-21T21:40 | memer | 10 | 2157 | 3.346 | 300 | 38.7 | 50.3 | 3.0 | KEEP |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

# 7×24 训练循环（2026-11-22T07:02:13）

> 调度：`com.fluxgroup.trainloop` 每 300s · 当前 running

## 队列

| 段 | 可用行数 | 可训 | 判据 |
|---|---|---|---|
| memer | 2181 | 是 | 配方更新 v5-shape-quota（2181 行） |
| craft_learner | 2170 | 是 | 配方更新 v5-shape-quota（2170 行） |
| shallow | 1952 | 是 | 配方更新 v5-shape-quota（1952 行） |
| peer_pro | 605 | 是 | 配方更新 v5-shape-quota（605 行） |
| feeler | 550 | 是 | 配方更新 v5-shape-quota（550 行） |
| music_seeker | 445 | 是 | 配方更新 v5-shape-quota（445 行） |
| tech_nerd | 579 | 否 | 冷却中（0.0h 前刚训过，语料 579→579 未涨 10%） |
| beginner | 151 | 否 | 语料 151 < 200 |
| critic | 127 | 否 | 语料 127 < 200 |
| student | 107 | 否 | 语料 107 < 200 |
| ai_creator | 65 | 否 | 语料 65 < 200 |
| requester | 62 | 否 | 语料 62 < 200 |
| family | 17 | 否 | 语料 17 < 200 |
| traditional | 3 | 否 | 语料 3 < 200 |

## 补料清单（训练线的真实瓶颈）

有 7 个段低于 200 行，合计还差 **868 行**才够开训：

| 段 | 现有 | 差 |
|---|---|---|
| beginner | 151 | 49 |
| critic | 127 | 73 |
| student | 107 | 93 |
| ai_creator | 65 | 135 |
| requester | 62 | 138 |
| family | 17 | 183 |
| traditional | 3 | 197 |

## 最近 10 轮

| 时间 | 段 | n | 行数 | val 最低 | 步 | 基座 | 候选 | 人味Δ | 判词 |
|---|---|---|---|---|---|---|---|---|---|
| 11-22T04:54 | feeler | 10 | 550 | 3.322 | 400 | 56.5 | 46.6 | -6.0 | REJECT |
| 11-22T05:00 | craft_learner | 0 | 2139 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-22T05:06 | tech_nerd | 0 | 570 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-22T05:07 | peer_pro | 30 | None | None | None | 50.3 | 57.2 | None | KEEP |
| 11-22T05:11 | memer | 0 | 2157 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-22T05:17 | shallow | 0 | 1948 | None | None | None | None | None | BLOCKED（样本不足） |
| 11-22T05:24 | music_seeker | 0 | 441 | None | None | None | None | None | SUPPLY（样本不足） |
| 11-22T05:58 | feeler | 10 | 550 | 3.322 | 400 | 56.5 | 43.4 | -6.0 | REJECT |
| 11-22T06:29 | craft_learner | 10 | 2170 | 3.478 | 200 | 85.5 | 80.3 | 1.0 | REJECT |
| 11-22T07:02 | tech_nerd | 10 | 579 | 3.522 | 400 | 54.0 | 68.0 | 3.0 | KEEP |

> 判据：段内均分 ≥ 基座+5、PASS 不降、人味(human) 不降 2；同段冷却 6h；被否段语料需涨 15% 才重训。

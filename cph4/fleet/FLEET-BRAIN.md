# 机队决策（常驻模型在候选里挑）2026-11-14T13:27:21

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：有空车道且待派卡多，优先派单
- 执行：已执行 rc=0   LINES: PARKED=4, STALLED-STAGE=6, WAITING=5

## 事实（规则算出来的）

- 队列：待派 6 / 在飞 4
- 车道：bm-a 3，bm-b 0，bm-c 0，bm-m 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 61 / 待升级 0

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 3 台空转而待派只有 6 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 6 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 61 项命中
- `A_ASSIGN` 定责：给无主活卡按 nodes 指定承办机 — 5 张活卡没有 owner
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 09:35:39 | A_NIGHT_PLAN | model | 是 |
| 10:09:55 | A_NIGHT_PLAN | model | 是 |
| 10:41:46 | A_NIGHT_PLAN | model | 是 |
| 11:13:29 | A_NIGHT_PLAN | model | 是 |
| 11:45:28 | A_NIGHT_PLAN | model | 是 |
| 12:20:22 | A_DISPATCH | model | 是 |
| 12:53:26 | A_DISPATCH | model | 是 |
| 13:27:21 | A_DISPATCH | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

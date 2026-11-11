# 机队决策（常驻模型在候选里挑）2026-11-11T08:59:14

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：有空车道且待派卡多，优先派单
- 执行：已执行 rc=0   LINES: PARKED=5, STALLED-STAGE=4, WAITING=5, WORKING=1

## 事实（规则算出来的）

- 队列：待派 5 / 在飞 2
- 车道：bm-a 1，bm-b 0，bm-c 0，bm-m 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 89 / 待升级 0

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 2 台空转而待派只有 5 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 5 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 89 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 08:19:06 | A_DISPATCH | model | 否 |
| 08:22:25 | A_DISPATCH | model | 否 |
| 08:26:03 | A_DISPATCH | model | 否 |
| 08:31:34 | A_DISPATCH | model | 否 |
| 08:34:43 | A_DISPATCH | model | 否 |
| 08:40:18 | A_DISPATCH | model | 否 |
| 08:44:24 | A_DISPATCH | model | 否 |
| 08:59:14 | A_DISPATCH | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

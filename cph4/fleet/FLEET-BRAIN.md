# 机队决策（常驻模型在候选里挑）2026-11-11T03:46:37

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：有空车道且待派卡多，优先派单
- 执行：已执行 rc=0   LINES: PARKED=5, STALLED-STAGE=4, WAITING=4, WORKING=2

## 事实（规则算出来的）

- 队列：待派 6 / 在飞 3
- 车道：bm-a 2，bm-b 0，bm-c 1，bm-m 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 3 / 待升级 1

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 2 台空转而待派只有 6 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 6 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 3 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 02:42:16 | A_DISPATCH | fallback | 是 |
| 02:54:38 | A_FILL | fallback | 是 |
| 03:05:07 | A_FILL | fallback | 是 |
| 03:13:25 | A_DISPATCH | model | 是 |
| 03:19:20 | A_DISPATCH | model | 否 |
| 03:24:09 | A_FILL | fallback | 是 |
| 03:36:15 | A_NIGHT_PLAN | model | 是 |
| 03:46:37 | A_DISPATCH | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

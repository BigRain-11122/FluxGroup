# 机队决策（常驻模型在候选里挑）2026-11-10T00:48:38

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：有空车道且待派卡充足
- 执行：已执行 rc=0   LINES: PARKED=5, STALLED-STAGE=2, WAITING=6, WORKING=2

## 事实（规则算出来的）

- 队列：待派 4 / 在飞 4
- 车道：bm-a 3，bm-b 0，bm-c 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 0 / 待升级 0

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 1 台空转而待派只有 4 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 4 张待派且有机器空着
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 00:38:03 | A_CLOSE_LOOP | model | 否 |
| 00:39:54 | A_CLOSE_LOOP | model | 否 |
| 00:41:27 | A_CLOSE_LOOP | model | 否 |
| 00:42:56 | A_CLOSE_LOOP | model | 否 |
| 00:44:22 | A_CLOSE_LOOP | model | 否 |
| 00:45:41 | A_NIGHT_PLAN | model | 否 |
| 00:47:09 | A_NIGHT_PLAN | model | 否 |
| 00:48:38 | A_DISPATCH | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

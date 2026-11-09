# 机队决策（常驻模型在候选里挑）2026-11-10T02:53:35

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：有空车道且待派卡多，优先派单
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 4 / 在飞 0
- 车道：bm-a 0，bm-b 0，bm-c 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 1 / 待升级 0

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 2 台空转而待派只有 4 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 4 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 1 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 02:43:39 | A_CLOSE_LOOP | model | 是 |
| 02:44:56 | A_DISPATCH | model | 否 |
| 02:46:15 | A_DISPATCH | model | 否 |
| 02:48:07 | A_DISPATCH | model | 否 |
| 02:49:24 | A_DISPATCH | model | 否 |
| 02:50:44 | A_DISPATCH | model | 否 |
| 02:52:01 | A_DISPATCH | model | 否 |
| 02:53:35 | A_DISPATCH | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

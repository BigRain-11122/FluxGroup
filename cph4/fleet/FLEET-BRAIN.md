# 机队决策（常驻模型在候选里挑）2026-11-10T10:42:31

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：有空车道且待派卡可立即处理
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 2 / 在飞 1
- 车道：bm-a 1，bm-b 0，bm-c 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 8 / 待升级 0

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 2 台空转而待派只有 2 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 2 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 8 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 10:32:05 | A_DISPATCH | model | 否 |
| 10:33:52 | A_DISPATCH | model | 否 |
| 10:35:11 | A_DISPATCH | model | 否 |
| 10:36:28 | A_DISPATCH | model | 否 |
| 10:37:49 | A_DISPATCH | model | 否 |
| 10:39:39 | A_DISPATCH | model | 否 |
| 10:41:03 | A_DISPATCH | model | 否 |
| 10:42:31 | A_DISPATCH | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

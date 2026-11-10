# 机队决策（常驻模型在候选里挑）2026-11-10T09:51:31

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：3 台空机匹配 3 张待派卡，立即派单最优先
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 3 / 在飞 0
- 车道：bm-a 0，bm-b 0，bm-c 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 12 / 待升级 1

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 3 台空转而待派只有 3 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 3 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 12 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 09:40:11 | A_DISPATCH | model | 否 |
| 09:41:44 | A_DISPATCH | model | 否 |
| 09:43:09 | A_DISPATCH | model | 否 |
| 09:44:48 | A_DISPATCH | model | 否 |
| 09:46:10 | A_DISPATCH | model | 否 |
| 09:47:36 | A_DISPATCH | model | 否 |
| 09:48:59 | A_DISPATCH | model | 否 |
| 09:51:31 | A_DISPATCH | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

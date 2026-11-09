# 机队决策（常驻模型在候选里挑）2026-11-10T00:03:19

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：7 项堵点待闭环，优先解决
- 执行：已执行 rc=0 [blocker] throttled: last full run 31s ago (<300s)

## 事实（规则算出来的）

- 队列：待派 18 / 在飞 14
- 车道：bm-a 8，bm-b 6，bm-c 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 7 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 18 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 7 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 23:52:09 | A_DISPATCH | model | 否 |
| 23:53:32 | A_DISPATCH | model | 否 |
| 23:54:59 | A_DISPATCH | model | 否 |
| 23:56:38 | A_DISPATCH | model | 否 |
| 23:58:05 | A_DISPATCH | model | 否 |
| 23:59:30 | A_DISPATCH | model | 否 |
| 00:00:56 | A_DISPATCH | model | 否 |
| 00:03:19 | A_CLOSE_LOOP | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

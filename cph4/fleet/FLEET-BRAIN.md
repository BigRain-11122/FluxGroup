# 机队决策（常驻模型在候选里挑）2026-11-10T06:27:07

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：堵点闭环命中 10 项需优先处理
- 执行：已执行 rc=0 [blocker] throttled: last full run 95s ago (<300s)

## 事实（规则算出来的）

- 队列：待派 1 / 在飞 4
- 车道：bm-a 1，bm-b 1，bm-c 2
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 10 / 待升级 0

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 10 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 06:16:21 | A_DISPATCH | model | 否 |
| 06:17:45 | A_DISPATCH | model | 否 |
| 06:19:23 | A_DISPATCH | model | 否 |
| 06:20:56 | A_DISPATCH | model | 否 |
| 06:22:17 | A_DISPATCH | model | 否 |
| 06:23:52 | A_DISPATCH | model | 否 |
| 06:25:43 | A_DISPATCH | model | 否 |
| 06:27:07 | A_CLOSE_LOOP | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

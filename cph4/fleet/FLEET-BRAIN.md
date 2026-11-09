# 机队决策（常驻模型在候选里挑）2026-11-10T02:00:56

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：闭环上次命中 1 项需优先处理
- 执行：已执行 rc=0 [blocker] throttled: last full run 169s ago (<300s)

## 事实（规则算出来的）

- 队列：待派 3 / 在飞 3
- 车道：bm-a 1，bm-b 1，bm-c 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 1 / 待升级 0

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 1 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 01:50:49 | A_DISPATCH | model | 否 |
| 01:52:31 | A_DISPATCH | model | 否 |
| 01:53:55 | A_DISPATCH | model | 否 |
| 01:55:19 | A_DISPATCH | model | 否 |
| 01:56:56 | A_DISPATCH | model | 否 |
| 01:58:18 | A_DISPATCH | model | 否 |
| 01:59:37 | A_DISPATCH | model | 否 |
| 02:00:56 | A_CLOSE_LOOP | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

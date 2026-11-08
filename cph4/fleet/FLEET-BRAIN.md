# 机队决策（常驻模型在候选里挑）2026-11-08T12:00:31

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：闭环上次命中 1 项需优先处理
- 执行：已执行 rc=0 [blocker] 命中 0 · 已解 0 · 升级 0 · 分类表缺口 0

## 事实（规则算出来的）

- 队列：待派 3 / 在飞 7
- 车道：bm-a 1，bm-b 2，bm-c 3
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 1 / 待升级 0

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 1 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 11:42:57 | A_DISPATCH | model | 否 |
| 11:43:57 | A_DISPATCH | model | 否 |
| 11:46:31 | A_DISPATCH | model | 否 |
| 11:49:21 | A_DISPATCH | model | 否 |
| 11:52:10 | A_DISPATCH | model | 否 |
| 11:54:49 | A_DISPATCH | model | 否 |
| 11:57:20 | A_DISPATCH | model | 否 |
| 12:00:31 | A_CLOSE_LOOP | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

# 机队决策（常驻模型在候选里挑）2026-11-08T03:21:22

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：闭环上次命中 1 项需优先处理
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 3 / 在飞 8
- 车道：bm-a 5，bm-b 1，bm-c 2
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 1 / 待升级 0

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 1 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 03:10:11 | A_NIGHT_PLAN | model | 否 |
| 03:11:54 | A_NIGHT_PLAN | model | 否 |
| 03:13:29 | A_CLOSE_LOOP | model | 否 |
| 03:15:13 | A_NIGHT_PLAN | model | 否 |
| 03:16:47 | A_NIGHT_PLAN | model | 否 |
| 03:18:47 | A_CLOSE_LOOP | model | 否 |
| 03:20:20 | A_CLOSE_LOOP | model | 否 |
| 03:21:22 | A_CLOSE_LOOP | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

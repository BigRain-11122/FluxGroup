# 机队决策（常驻模型在候选里挑）2026-11-10T01:28:31

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：优先处理 26 个命中堵点
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 8 / 在飞 2
- 车道：bm-a 3，bm-b 1，bm-c 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 26 / 待升级 0

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 26 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 01:17:36 | A_CLOSE_LOOP | model | 否 |
| 01:18:58 | A_CLOSE_LOOP | model | 否 |
| 01:20:24 | A_NIGHT_PLAN | model | 是 |
| 01:21:57 | A_CLOSE_LOOP | model | 否 |
| 01:23:24 | A_CLOSE_LOOP | model | 否 |
| 01:24:42 | A_CLOSE_LOOP | model | 否 |
| 01:26:01 | A_DISPATCH | model | 否 |
| 01:28:31 | A_CLOSE_LOOP | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

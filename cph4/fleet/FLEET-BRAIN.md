# 机队决策（常驻模型在候选里挑）2026-11-10T01:17:36

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：9 项堵点待闭环，优先处理
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 6 / 在飞 7
- 车道：bm-a 5，bm-b 2，bm-c 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 9 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 6 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 9 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 01:07:01 | A_CLOSE_LOOP | model | 否 |
| 01:08:25 | A_NIGHT_PLAN | model | 否 |
| 01:10:01 | A_CLOSE_LOOP | model | 否 |
| 01:11:31 | A_CLOSE_LOOP | model | 否 |
| 01:12:54 | A_CLOSE_LOOP | model | 否 |
| 01:14:18 | A_DISPATCH | model | 是 |
| 01:16:19 | A_DISPATCH | model | 否 |
| 01:17:36 | A_CLOSE_LOOP | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

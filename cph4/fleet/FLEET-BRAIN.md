# 机队决策（常驻模型在候选里挑）2026-11-10T00:13:14

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：3 项堵点命中，优先闭环
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 20 / 在飞 18
- 车道：bm-a 8，bm-b 6，bm-c 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 3 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 20 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 3 项命中
- `A_ASSIGN` 定责：给无主活卡按 nodes 指定承办机 — 1 张活卡没有 owner
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 00:00:56 | A_DISPATCH | model | 否 |
| 00:03:19 | A_CLOSE_LOOP | model | 是 |
| 00:05:01 | A_CLOSE_LOOP | model | 否 |
| 00:06:36 | A_NIGHT_PLAN | model | 是 |
| 00:08:03 | A_CLOSE_LOOP | model | 否 |
| 00:09:44 | A_NIGHT_PLAN | model | 否 |
| 00:11:15 | A_NIGHT_PLAN | model | 否 |
| 00:13:14 | A_CLOSE_LOOP | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

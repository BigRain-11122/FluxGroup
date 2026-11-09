# 机队决策（常驻模型在候选里挑）2026-11-10T00:18:05

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型选择）
- 理由：有空车道且待派卡多，优先派单
- 执行：已执行 rc=0   LINES: PARKED=5, STALLED-STAGE=2, WAITING=1, WORKING=7

## 事实（规则算出来的）

- 队列：待派 21 / 在飞 14
- 车道：bm-a 8，bm-b 6，bm-c 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 19 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 21 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 19 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_DEDUPE` 按交付物撤重复活卡（保留跑得最远的那张） — 1 组同交付物多张活卡，两台机在互相覆盖回执
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 00:06:36 | A_NIGHT_PLAN | model | 是 |
| 00:08:03 | A_CLOSE_LOOP | model | 否 |
| 00:09:44 | A_NIGHT_PLAN | model | 否 |
| 00:11:15 | A_NIGHT_PLAN | model | 否 |
| 00:13:14 | A_CLOSE_LOOP | model | 否 |
| 00:15:04 | A_CLOSE_LOOP | model | 否 |
| 00:16:31 | A_CLOSE_LOOP | model | 否 |
| 00:18:05 | A_DISPATCH | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

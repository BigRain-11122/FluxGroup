# 机队决策（常驻模型在候选里挑）2026-11-11T00:10:42

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：8 项堵点待闭环优先处理
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 9 / 在飞 19
- 车道：bm-a 8，bm-b 5，bm-c 6，bm-m 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 8 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 9 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 8 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_DEDUPE` 按交付物撤重复活卡（保留跑得最远的那张） — 1 组同交付物多张活卡，两台机在互相覆盖回执
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 23:47:20 | A_DISPATCH | model | 否 |
| 23:50:01 | A_DISPATCH | model | 否 |
| 23:52:44 | A_DISPATCH | model | 否 |
| 23:55:14 | A_DISPATCH | model | 否 |
| 23:59:02 | A_FILL | fallback | 是 |
| 00:03:06 | A_DISPATCH | model | 否 |
| 00:06:28 | A_CLOSE_LOOP | fallback | 是 |
| 00:10:42 | A_CLOSE_LOOP | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

# 机队决策（常驻模型在候选里挑）2026-11-11T00:06:28

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：已执行 rc=0 [blocker] throttled: last full run 257s ago (<300s)

## 事实（规则算出来的）

- 队列：待派 7 / 在飞 20
- 车道：bm-a 8，bm-b 5，bm-c 6，bm-m 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 11 / 待升级 0

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 11 项命中
- `A_ASSIGN` 定责：给无主活卡按 nodes 指定承办机 — 1 张活卡没有 owner
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_DEDUPE` 按交付物撤重复活卡（保留跑得最远的那张） — 1 组同交付物多张活卡，两台机在互相覆盖回执
- `A_REVIVE` 唤醒停摆执行者：poke 显式启用 / 发收口卡 — 1 台机器 FleetLink 活着但不唤醒任务
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 23:44:36 | A_DISPATCH | model | 否 |
| 23:47:20 | A_DISPATCH | model | 否 |
| 23:50:01 | A_DISPATCH | model | 否 |
| 23:52:44 | A_DISPATCH | model | 否 |
| 23:55:14 | A_DISPATCH | model | 否 |
| 23:59:02 | A_FILL | fallback | 是 |
| 00:03:06 | A_DISPATCH | model | 否 |
| 00:06:28 | A_CLOSE_LOOP | fallback | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

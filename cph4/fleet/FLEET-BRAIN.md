# 机队决策（常驻模型在候选里挑）2026-11-11T00:54:58

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_DISPATCH**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：已执行 rc=0   LINES: PARKED=5, STALLED-STAGE=4, WAITING=4, WORKING=2

## 事实（规则算出来的）

- 队列：待派 9 / 在飞 8
- 车道：bm-a 6，bm-b 1，bm-c 3，bm-m 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 94 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 9 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 94 项命中
- `A_ASSIGN` 定责：给无主活卡按 nodes 指定承办机 — 1 张活卡没有 owner
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 00:03:06 | A_DISPATCH | model | 否 |
| 00:06:28 | A_CLOSE_LOOP | fallback | 是 |
| 00:10:42 | A_CLOSE_LOOP | model | 否 |
| 00:16:20 | A_CLOSE_LOOP | model | 否 |
| 00:20:49 | A_CLOSE_LOOP | fallback | 否 |
| 00:33:25 | A_CLOSE_LOOP | fallback | 是 |
| 00:39:53 | A_CLOSE_LOOP | fallback | 否 |
| 00:54:58 | A_DISPATCH | fallback | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

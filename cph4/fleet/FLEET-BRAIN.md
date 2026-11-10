# 机队决策（常驻模型在候选里挑）2026-11-10T23:20:26

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_FILL**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：已执行 rc=0 候选卡为 0（README 里没活可补）——这属于供给缺口，不是调度故障

## 事实（规则算出来的）

- 队列：待派 5 / 在飞 5
- 车道：bm-a 3，bm-b 1，bm-c 1，bm-m 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 14 / 待升级 0

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 1 台空转而待派只有 5 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 5 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 14 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 22:55:24 | A_DISPATCH | model | 否 |
| 22:59:54 | A_DISPATCH | fallback | 否 |
| 23:04:56 | A_CLOSE_LOOP | fallback | 是 |
| 23:07:27 | A_CLOSE_LOOP | model | 否 |
| 23:09:43 | A_DISPATCH | model | 否 |
| 23:15:50 | A_DISPATCH | model | 否 |
| 23:17:44 | A_CLOSE_LOOP | fallback | 是 |
| 23:20:26 | A_FILL | fallback | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

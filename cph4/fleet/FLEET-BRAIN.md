# 机队决策（常驻模型在候选里挑）2026-11-10T23:59:02

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_FILL**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：已执行 rc=0 候选卡为 0（README 里没活可补）——这属于供给缺口，不是调度故障

## 事实（规则算出来的）

- 队列：待派 5 / 在飞 6
- 车道：bm-a 1，bm-b 0，bm-c 1，bm-m 4
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 8 / 待升级 0

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 1 台空转而待派只有 5 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 5 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 8 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 23:38:17 | A_DISPATCH | model | 否 |
| 23:40:38 | A_DISPATCH | model | 否 |
| 23:44:36 | A_DISPATCH | model | 否 |
| 23:47:20 | A_DISPATCH | model | 否 |
| 23:50:01 | A_DISPATCH | model | 否 |
| 23:52:44 | A_DISPATCH | model | 否 |
| 23:55:14 | A_DISPATCH | model | 否 |
| 23:59:02 | A_FILL | fallback | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

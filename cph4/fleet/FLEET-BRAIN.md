# 机队决策（常驻模型在候选里挑）2026-11-10T21:26:54

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_FILL**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：已执行 rc=0 队列已有 7 张待领，够用，不灌

## 事实（规则算出来的）

- 队列：待派 7 / 在飞 4
- 车道：bm-a 1，bm-b 2，bm-c 1，bm-m 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 89 / 待升级 1

## 候选（模型只能从这里挑）

- `A_FILL` 补供给：night_fill + workgen + supply_batch — 1 台空转而待派只有 7 张
- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 7 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 89 项命中
- `A_ASSIGN` 定责：给无主活卡按 nodes 指定承办机 — 2 张活卡没有 owner
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 20:50:56 | A_DISPATCH | fallback | 是 |
| 20:54:06 | A_DISPATCH | model | 否 |
| 20:59:19 | A_CLOSE_LOOP | fallback | 是 |
| 21:03:25 | A_FILL | fallback | 是 |
| 21:08:26 | A_DISPATCH | fallback | 是 |
| 21:12:31 | A_DISPATCH | fallback | 否 |
| 21:23:06 | A_CLOSE_LOOP | fallback | 是 |
| 21:26:54 | A_FILL | fallback | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

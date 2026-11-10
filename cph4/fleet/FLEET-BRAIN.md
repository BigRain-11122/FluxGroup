# 机队决策（常驻模型在候选里挑）2026-11-11T00:33:25

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：已执行 rc=0 [blocker] throttled: last full run 62s ago (<300s)

## 事实（规则算出来的）

- 队列：待派 16 / 在飞 9
- 车道：bm-a 4，bm-b 1，bm-c 1，bm-m 3
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 97 / 待升级 1

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 97 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 23:55:14 | A_DISPATCH | model | 否 |
| 23:59:02 | A_FILL | fallback | 是 |
| 00:03:06 | A_DISPATCH | model | 否 |
| 00:06:28 | A_CLOSE_LOOP | fallback | 是 |
| 00:10:42 | A_CLOSE_LOOP | model | 否 |
| 00:16:20 | A_CLOSE_LOOP | model | 否 |
| 00:20:49 | A_CLOSE_LOOP | fallback | 否 |
| 00:33:25 | A_CLOSE_LOOP | fallback | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

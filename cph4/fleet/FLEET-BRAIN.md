# 机队决策（常驻模型在候选里挑）2026-11-08T00:31:12

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_NIGHT_PLAN**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：已执行 rc=0 [night_plan] cards=3 waiting=0

## 事实（规则算出来的）

- 队列：待派 10 / 在飞 14
- 车道：bm-a 5，bm-b 4，bm-c 3
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 0 / 待升级 0

## 候选（模型只能从这里挑）

- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 00:09:40 | A_DISPATCH | model | 是 |
| 00:12:29 | A_CLOSE_LOOP | fallback | 否 |
| 00:14:34 | A_NIGHT_PLAN | model | 是 |
| 00:18:17 | A_CLOSE_LOOP | fallback | 否 |
| 00:21:46 | A_CLOSE_LOOP | fallback | 否 |
| 00:24:25 | A_CLOSE_LOOP | model | 否 |
| 00:27:50 | A_CLOSE_LOOP | model | 否 |
| 00:31:12 | A_NIGHT_PLAN | fallback | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

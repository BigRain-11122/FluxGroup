# 机队决策（常驻模型在候选里挑）2026-11-10T21:53:24

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型越权/乱答→回落规则）
- 理由：模型未给出合法候选（空），回落规则首选
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 7 / 在飞 6
- 车道：bm-a 4，bm-b 3，bm-c 1，bm-m 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 8 / 待升级 0

## 候选（模型只能从这里挑）

- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 8 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 21:12:31 | A_DISPATCH | fallback | 否 |
| 21:23:06 | A_CLOSE_LOOP | fallback | 是 |
| 21:26:54 | A_FILL | fallback | 是 |
| 21:32:44 | A_CLOSE_LOOP | fallback | 否 |
| 21:42:13 | A_DISPATCH | fallback | 是 |
| 21:46:01 | A_DISPATCH | fallback | 否 |
| 21:49:11 | A_CLOSE_LOOP | fallback | 是 |
| 21:53:24 | A_CLOSE_LOOP | fallback | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

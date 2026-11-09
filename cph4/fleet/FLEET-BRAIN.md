# 机队决策（常驻模型在候选里挑）2026-11-10T03:47:17

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_NIGHT_PLAN**（模型选择）
- 理由：5 条线停摆超 72 小时需补卡
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 1 / 在飞 1
- 车道：bm-a 1，bm-b 1，bm-c 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 0 / 待升级 0

## 候选（模型只能从这里挑）

- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 03:37:31 | A_DISPATCH | model | 否 |
| 03:38:48 | A_DISPATCH | model | 否 |
| 03:40:29 | A_DISPATCH | model | 否 |
| 03:41:59 | A_DISPATCH | model | 否 |
| 03:43:15 | A_DISPATCH | model | 否 |
| 03:44:30 | A_CLOSE_LOOP | model | 是 |
| 03:45:48 | A_NIGHT_PLAN | model | 是 |
| 03:47:17 | A_NIGHT_PLAN | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

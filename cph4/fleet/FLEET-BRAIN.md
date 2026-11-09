# 机队决策（常驻模型在候选里挑）2026-11-10T01:02:06

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_NIGHT_PLAN**（模型选择）
- 理由：5 条线停摆超 72 小时需补卡
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 4 / 在飞 6
- 车道：bm-a 3，bm-b 2，bm-c 2
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 0 / 待升级 0

## 候选（模型只能从这里挑）

- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 00:51:59 | A_CLOSE_LOOP | model | 否 |
| 00:53:18 | A_CLOSE_LOOP | model | 否 |
| 00:54:38 | A_CLOSE_LOOP | model | 否 |
| 00:56:02 | A_NIGHT_PLAN | model | 否 |
| 00:57:41 | A_NIGHT_PLAN | model | 否 |
| 00:59:14 | A_NIGHT_PLAN | model | 否 |
| 01:00:46 | A_NIGHT_PLAN | model | 否 |
| 01:02:06 | A_NIGHT_PLAN | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

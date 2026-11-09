# 机队决策（常驻模型在候选里挑）2026-11-10T00:50:05

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_NIGHT_PLAN**（模型选择）
- 理由：5 条线停摆超 72 小时需补卡
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 4 / 在飞 1
- 车道：bm-a 3，bm-b 1，bm-c 1
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute
- 堵点命中 0 / 待升级 0

## 候选（模型只能从这里挑）

- `A_ASSIGN` 定责：给无主活卡按 nodes 指定承办机 — 1 张活卡没有 owner
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 5 条 ACTIVE 线已停 ≥72h
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 00:39:54 | A_CLOSE_LOOP | model | 否 |
| 00:41:27 | A_CLOSE_LOOP | model | 否 |
| 00:42:56 | A_CLOSE_LOOP | model | 否 |
| 00:44:22 | A_CLOSE_LOOP | model | 否 |
| 00:45:41 | A_NIGHT_PLAN | model | 否 |
| 00:47:09 | A_NIGHT_PLAN | model | 否 |
| 00:48:38 | A_DISPATCH | model | 是 |
| 00:50:05 | A_NIGHT_PLAN | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

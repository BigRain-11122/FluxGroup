# 机队决策（常驻模型在候选里挑）2026-11-10T20:42:25

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：堵点闭环上次命中 2 项，优先处理
- 执行：未执行 rc=0 冷却中（600s 内已执行过同一动作）

## 事实（规则算出来的）

- 队列：待派 10 / 在飞 10
- 车道：bm-a 2，bm-b 0，bm-c 6，bm-m 2
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 2 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 10 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 2 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_REVIVE` 唤醒停摆执行者：poke 显式启用 / 发收口卡 — 1 台机器 FleetLink 活着但不唤醒任务
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 20:20:16 | A_CLOSE_LOOP | model | 是 |
| 20:22:45 | A_FILL | fallback | 否 |
| 20:25:09 | A_FILL | fallback | 否 |
| 20:28:36 | A_FILL | fallback | 否 |
| 20:32:29 | A_FILL | fallback | 否 |
| 20:37:39 | A_DISPATCH | fallback | 是 |
| 20:40:13 | A_CLOSE_LOOP | model | 是 |
| 20:42:25 | A_CLOSE_LOOP | model | 否 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

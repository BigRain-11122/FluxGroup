# 机队决策（常驻模型在候选里挑）2026-11-11T10:04:54

分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**（4B 级算术不可信，所以数字从不交给模型）。

## 本轮

- 决策：**A_CLOSE_LOOP**（模型选择）
- 理由：闭环上次命中 24 项，优先处理
- 执行：已执行 rc=0 [blocker] throttled: last full run 27s ago (<300s)

## 事实（规则算出来的）

- 队列：待派 25 / 在飞 1
- 车道：bm-a 1，bm-b 0，bm-c 0，bm-m 0
- 停摆线：biggame,fluxverse,bigmoney,bigdomain,bigcompute,recon
- 堵点命中 24 / 待升级 0

## 候选（模型只能从这里挑）

- `A_DISPATCH` 派单：master_agent 把队列里的卡装进空车道 — 有 25 张待派且有机器空着
- `A_CLOSE_LOOP` 跑堵点闭环：按分类表检测并自动解 — 闭环上次报 24 项命中
- `A_NIGHT_PLAN` 按声明补卡：night_plan 派各线唯一下一步 — 6 条 ACTIVE 线已停 ≥72h
- `A_DEDUPE` 按交付物撤重复活卡（保留跑得最远的那张） — 1 组同交付物多张活卡，两台机在互相覆盖回执
- `A_NOOP` 什么都不做，保持现状 — 没有值得动的事，别为动而动

## 最近决策

| 时间 | 决策 | 来源 | 执行 |
|---|---|---|---|
| 09:30:03 | A_DISPATCH | model | 否 |
| 09:33:35 | A_DISPATCH | model | 否 |
| 09:42:01 | A_DISPATCH | model | 否 |
| 09:48:02 | A_DISPATCH | model | 否 |
| 09:51:31 | A_DISPATCH | model | 否 |
| 09:55:09 | A_DISPATCH | model | 否 |
| 09:58:58 | A_DISPATCH | model | 否 |
| 10:04:54 | A_CLOSE_LOOP | model | 是 |

---
_模型没有发明动作的权力：候选外的 id 一律回落规则首选_

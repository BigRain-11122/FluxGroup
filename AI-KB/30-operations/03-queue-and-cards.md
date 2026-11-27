---
id: ops.queue
title: 队列、卡与状态机
layer: operations
questions: ["一张卡长什么样", "状态怎么流转", "怎么验收"]
facts: ["cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/CARD-POLICY-v1.json"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
卡是唯一的工作单元；队列是唯一权威，回执是唯一验收凭据。

## 结构（有哪些层/进程/目录）
`PRODUCTION-QUEUE.jsonl`（一行一卡）→ `lanes/<node>.json`（派单）→ `queue-receipts/`（回执）→ 状态机。

## 数据怎么流
OPEN → RUNNING（owner + lease）→ DONE/FAILED/BLOCKED；CANCELLED 与 ARCHIVED 是终态，只有显式 requeued_by 能重开。

## 关键约定（不许违反的）
交付物必须与 cmd 真实产出路径一致；同一命令同一刻只派一张；坏卡要归档不要反复重试。

## 怎么验证它在工作
近期状态分布与在飞卡：DONE=517，CANCELLED=611，FAILED=2，ARCHIVED=227，UNVERIFIED=6，OPEN=9，NONE=3，RUNNING=10。

## 我不知道的
历史卡里仍有个别空壳。

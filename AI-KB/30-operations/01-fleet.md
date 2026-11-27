---
id: ops.fleet
title: 机队与跨机执行
layer: operations
questions: ["有几台机器", "怎么给机器派活", "怎么判断机器真在干活"]
facts: ["Tools/fleet-nodes.json", "cph4/fleet/lanes/", "cph4/fleet/queue-receipts/"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: local-llm
---
## 一句话
系统由 bm-a、bm-b、bm-c 三个节点组成，当前脉冲阶段为 92。部分节点如 bm-m 和 bm-d 处于空闲状态，原因均为自我调度。队列中 OPEN 任务数为 9，RUNNING 任务数为 10。

## 结构（有哪些层/进程/目录）
系统包含 fleet 与 queue 两大核心层级。fleet 下管理 nodes 节点及 slots 槽位资源。queue 下统计 DONE、CANCELLED 等状态的任务数据。节点 bm-a 位于 DASHENG，bm-b 位于 BIGMONEY。

## 数据怎么流
任务在 OPEN 状态进入系统，随后转为 RUNNING。完成的任务归入 DONE 列表，失败则进入 FAILED。未验证任务暂存于 UNVERIFIED 队列中。

## 关键约定（不许违反的）
节点 bm-a 拥有 5 条车道，bm-b 和 bm-c 各有 3 条与 2 条。所有节点的 idle_reason 字段必须保持为空字符串。脉冲时间戳 pulse_ts 格式需包含时区偏移。

## 怎么验证它在工作
检查 fleet.nodes 中是否存在 id 为 bm-a、bm-b、bm-c 的条目。确认 pulse_stages 数值等于 92。核对 queue.RUNNING 数量是否大于 0。

## 我不知道的
未测/未知：节点 bm-m 和 bm-d 的具体运行状态。未测/未知：当前系统总任务数的精确总和。未测/未知：未来脉冲阶段的预计数值。

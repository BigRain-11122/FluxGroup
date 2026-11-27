---
id: eng.architecture
title: 系统架构与数据流
layer: engineering
questions: ["系统由什么组成", "数据怎么流", "关键约定"]
facts: ["Tools/fleet/master_pulse.py", "Tools/fleet-nodes.json", "cph4/fleet/AUTONOMY-CONFIG.json"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: local-llm
---
## 一句话
系统由 228 个工具节点组成，核心调度脉冲为 92 秒。所有进程均位于指定目录如 .codely-cli 或 Tools 下运行。当前状态显示部分节点处于空闲等待中。

## 结构（有哪些层/进程/目录）
顶层包含 bm-a、bm-b、bm-c 等关键节点。底层目录涵盖 compute、gaming 及 soft-pat 申请材料区。系统分层为 nodes、slots 与 pulse_stages 三组。

## 数据怎么流
数据从 bm-a 的 5 条车道流向 bigstream-mv 阶段。bm-b 和 bm-c 分别处理 6 个槽位的流量。93.7 秒内完成一次完整脉冲循环。

## 关键约定（不许违反的）
严禁跨节点直接写入未授权目录。所有时间戳必须对齐至 2026-11-08 基准。bm-m 和 bm-d 禁止自我分发扫描。

## 怎么验证它在工作
检查 fleet 中 nodes 列表是否包含 bm-a。确认 pulse_stages 数值等于 92。查看 top_dirs 中是否存在 .git 文件夹。

## 我不知道的
未测/未知节点状态变化频率。未测/未知未来脉冲周期调整规则。未测/未知自我分发机制的具体延迟值。

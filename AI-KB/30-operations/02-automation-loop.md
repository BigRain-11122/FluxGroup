---
id: ops.loop
title: 主控脉与节奏
layer: operations
questions: ["自动化怎么跑起来", "怎么判断脉健康"]
facts: ["Tools/fleet/master_pulse.py", "cph4/fleet/dispatcher/PULSE.json", "cph4/fleet/state/stage-last.json"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
主控脉是唯一的常驻身体：按节奏跑 92 个阶段，出卡、派单、验收、出屏。

## 结构（有哪些层/进程/目录）
master_pulse（launchd 常驻）→ 各阶段脚本 → state/ 下的机读状态 + 根目录的一屏 markdown。

## 数据怎么流
节奏表（cadence）定周期 → 阶段执行 → 写 PULSE.json/stage-last.json → 看板与 CEO-NEXT 汇总。

## 关键约定（不许违反的）
阶段必须留下「最后一次真跑」记录；同一工具不得被两个阶段重复登记；阈值只在 cph4/fleet/*.json 里改。

## 怎么验证它在工作
`PULSE.json.ts` 在推进，且 `state/stage-last.json` 里各阶段时间在更新；launchctl 的 PID 不可信。

## 我不知道的
慢批阶段单轮耗时会超过标称节拍。

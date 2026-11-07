---
id: line.biglife
title: BigLife·数字生命
layer: business
questions: ["这条线做什么", "谁负责", "做到哪了", "怎么验证"]
facts: ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template+local-llm
---
## 一句话
当前 BigLife·数字生命业务状态为活跃，优先级标记为 P2。
## 谁负责 / 怎么判
负责人：生命生产席；判新鲜度阈值：48 小时。
## 工序与用哪台机
人设生产（生命生产席，local-llm）；生命体征闸（质检席，none）。
## 现在的产出
盘上最近产物时间 未测（距今 未测 小时，状态 EMPTY）；队列累计 5 张，其中完成 3 张。
## 怎么验证
看产物文件的 mtime 与队列回执是否同时更新；只有回执没有产物 = 假完成。
## 下一步
该线若 age_h 超过阈值，先查卡是否在飞、输入是否到位，再谈新内容。
## 我不知道的
本页数字取自注册表与磁盘普查；远端机器上的产物本机看不到，标为远端待查。

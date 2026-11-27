---
id: line.bigstream-duanju
title: BigStream·短剧
layer: business
questions: ["这条线做什么", "谁负责", "做到哪了", "怎么验证"]
facts: ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template+local-llm
---
## 一句话
BigStream·短剧（P0）业务已停摆，最新观测时间为 2026 年 10 月 30 日。
## 谁负责 / 怎么判
负责人：短剧席；判新鲜度阈值：72 小时。
## 工序与用哪台机
剧本（编剧席，cloud-smart）；试构图（短剧席，local-gpu）。
## 现在的产出
盘上最近产物时间 2026-10-30T18:42:56（距今 198.2 小时，状态 OBSERVED）；队列累计 19 张，其中完成 6 张。
## 怎么验证
看产物文件的 mtime 与队列回执是否同时更新；只有回执没有产物 = 假完成。
## 下一步
该线若 age_h 超过阈值，先查卡是否在飞、输入是否到位，再谈新内容。
## 我不知道的
本页数字取自注册表与磁盘普查；远端机器上的产物本机看不到，标为远端待查。

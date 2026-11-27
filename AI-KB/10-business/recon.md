---
id: line.recon
title: RECON·竞品拆解
layer: business
questions: ["这条线做什么", "谁负责", "做到哪了", "怎么验证"]
facts: ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template+local-llm
---
## 一句话
RECON·竞品拆解业务事实，当前状态为 P3 级且处于活跃中。
## 谁负责 / 怎么判
负责人：拆解部；判新鲜度阈值：72 小时。
## 工序与用哪台机
扒榜/拆包（拆解部，none）；48h 原型（拆解部，cloud-smart）。
## 现在的产出
盘上最近产物时间 2026-11-07T12:38:24（距今 12.2 小时，状态 OBSERVED）；队列累计 6 张，其中完成 3 张。
## 怎么验证
看产物文件的 mtime 与队列回执是否同时更新；只有回执没有产物 = 假完成。
## 下一步
该线若 age_h 超过阈值，先查卡是否在飞、输入是否到位，再谈新内容。
## 我不知道的
本页数字取自注册表与磁盘普查；远端机器上的产物本机看不到，标为远端待查。

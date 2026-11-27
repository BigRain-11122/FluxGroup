---
id: line.bigstream-mv
title: BigStream·MV 41 曲
layer: business
questions: ["这条线做什么", "谁负责", "做到哪了", "怎么验证"]
facts: ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template+local-llm
---
## 一句话
BigStream·MV 41 曲为 P0 级活跃业务，已观测且持续运行。
## 谁负责 / 怎么判
负责人：导演席（自决推进，CEO 巡视可随时否决）；判新鲜度阈值：24 小时。
## 工序与用哪台机
立意/分镜（导演席，cloud-smart）；关键帧（导演席·美术，local-gpu）；出片（导演席，local-gpu）；剪辑/装配（剪辑席，none）；质检/交付（质检席，none）；呈审（导演席（自决放行），none）。
## 现在的产出
盘上最近产物时间 2026-11-07T22:27:30（距今 2.4 小时，状态 OBSERVED）；队列累计 131 张，其中完成 115 张。
## 怎么验证
看产物文件的 mtime 与队列回执是否同时更新；只有回执没有产物 = 假完成。
## 下一步
该线若 age_h 超过阈值，先查卡是否在飞、输入是否到位，再谈新内容。
## 我不知道的
本页数字取自注册表与磁盘普查；远端机器上的产物本机看不到，标为远端待查。

---
id: line.biggame
title: Biggame·游戏
layer: business
questions: ["这条线做什么", "谁负责", "做到哪了", "怎么验证"]
facts: ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template+local-llm
---
## 一句话
Biggame·游戏为 P0 级业务，当前状态活跃且已被观测。
## 谁负责 / 怎么判
负责人：游戏席；判新鲜度阈值：24 小时。
## 工序与用哪台机
玩法/数值（游戏席，cloud-smart）；美术资产（美术席，local-gpu）；构建/打包（工程席，none）。
## 现在的产出
盘上最近产物时间 2026-11-03T17:19:36（距今 103.5 小时，状态 OBSERVED）；队列累计 232 张，其中完成 74 张。
## 怎么验证
看产物文件的 mtime 与队列回执是否同时更新；只有回执没有产物 = 假完成。
## 下一步
该线若 age_h 超过阈值，先查卡是否在飞、输入是否到位，再谈新内容。
## 我不知道的
本页数字取自注册表与磁盘普查；远端机器上的产物本机看不到，标为远端待查。

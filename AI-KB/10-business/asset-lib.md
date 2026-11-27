---
id: line.asset-lib
title: 资产储备·角色 LoRA 与音色库
layer: business
questions: ["这条线做什么", "谁负责", "做到哪了", "怎么验证"]
facts: ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template+local-llm
---
## 一句话
资产储备·角色 LoRA 与音色库，P0 级业务事实。
## 谁负责 / 怎么判
负责人：资产席；判新鲜度阈值：72 小时。
## 工序与用哪台机
训练环境自检（资产席，rule）；数据集准入闸（资产席，rule）；LoRA/音色训练（资产席，local-gpu）。
## 现在的产出
盘上最近产物时间 2026-11-07T19:32:03（距今 5.3 小时，状态 OBSERVED）；队列累计 79 张，其中完成 44 张。
## 怎么验证
看产物文件的 mtime 与队列回执是否同时更新；只有回执没有产物 = 假完成。
## 下一步
该线若 age_h 超过阈值，先查卡是否在飞、输入是否到位，再谈新内容。
## 我不知道的
本页数字取自注册表与磁盘普查；远端机器上的产物本机看不到，标为远端待查。

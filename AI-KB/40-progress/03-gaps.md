---
id: progress.gaps
title: 缺口与堵点
layer: progress
questions: ["哪里断了", "为什么断"]
facts: ["state/lines.json", "cph4/fleet/BLOCKERS.md"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
缺口分两类：声明在做但盘上没产物（2 条），以及已知结构性堵点。

## 纸面业务
- BigLife·数字生命（声明 ACTIVE，观测 EMPTY）
- 机队运维·端到端自检（平台服务线）（声明 ACTIVE，观测 BOOKKEEPING）

## 已知堵点形态
1) 卡指向的输入不存在（目录/成片/语料）→ 天天重试空转；
2) 三个生成器发同一命令的重复卡 → 多机做同一件事；
3) 归档不是终态时死卡会被旧 claim 复活；
4) 远端产物被本机判成缺失（假红）；
5) 节点仓库分叉导致改码到不了机器。

## 怎么验证
每条缺口都要能回答「现在还能不能修、谁来修、缺什么输入」。
## 我不知道的
本页只覆盖仓库里可核验的事实；各机运行时状态、商业数据与对外承诺不在本页。

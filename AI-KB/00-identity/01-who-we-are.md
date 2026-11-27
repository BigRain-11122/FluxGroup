---
id: identity.who
title: 集团与业务总览
layer: identity
questions: ["这家在做什么", "有几条线", "谁决策"]
facts: ["LINE-REGISTRY.json", "state/lines.json", "PRODUCTION-QUEUE.jsonl"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 这是什么组织
一个由 CEO 定方向、AI 机队执行的内容与游戏集团，仓库根目录 `/Users/junsheng.sun/FluxGroup`。
## 现在同时在做的业务（按优先级）
共 15 条业务线：BigStream·MV 41 曲(P0/ACTIVE)；BigStream·漫剧(P0/PARKED)；BigStream·短剧(P0/PARKED)；BigStream·短视频/切片(P0/PARKED)；Biggame·游戏(P0/ACTIVE)；FluxVerse·元宙城(P2/ACTIVE)；BigMoney·量化(P1/ACTIVE)；BigDomain·硅基域商业化(P1/ACTIVE)；BigCompute·硅基算力(P3/ACTIVE)；BigLife·数字生命(P2/ACTIVE)；BigHouse·城市安家(P2/PARKED)；车机游戏 BU(P3/PARKED)；RECON·竞品拆解(P3/ACTIVE)；机队运维·端到端自检（平台服务线）(P3/ACTIVE)；资产储备·角色 LoRA 与音色库(P0/ACTIVE)。
## 谁做决定、谁执行
CEO 只做方向、红线、花钱三类决定；其余由主控与各线自决推进。执行落在机队（bm-a、bm-b、bm-c、bm-m、bm-d）与各业务目录。
## 三条最容易被误解的地方
1) 「卡完成」不等于产物在盘；2) 主控不做生产，只出卡/裁决/告警/一屏；3) 远端机器上的产物主控看不到，不能判成缺失。
## 怎么快速判断一条业务是真的在做还是在纸面上
看该线最新产物 mtime + 队列里是否有在飞卡 + 回执是否带 rc 与字节数，三者同时更新才算真做。
## 我不知道的
各线商业目标与实际营收不在本仓，未测。

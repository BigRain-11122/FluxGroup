---
id: business.portfolio
title: 业务组合总表
layer: business
questions: ["一共有哪些线", "哪条快断了"]
facts: ["LINE-REGISTRY.json", "state/lines.json"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
15 条业务线，按 P0 内容 / P1 战略 / P2 城市 / P3 平台分组。

## 全景表
| 线 | 名称 | 优先级 | 声明 | 产物年龄(h) | DONE | OPEN |
|---|---|---|---|---|---|---|
| bigstream-mv | BigStream·MV 41 曲 | P0 | ACTIVE | 2.4 | 115 | 未测 |
| bigstream-drama | BigStream·漫剧 | P0 | PARKED | 0.4 | 15 | 1 |
| bigstream-duanju | BigStream·短剧 | P0 | PARKED | 198.2 | 6 | 2 |
| bigstream-shortvideo | BigStream·短视频/切片 | P0 | PARKED | 131.7 | 未测 | 未测 |
| biggame | Biggame·游戏 | P0 | ACTIVE | 103.5 | 74 | 1 |
| fluxverse | FluxVerse·元宙城 | P2 | ACTIVE | 105.8 | 5 | 未测 |
| bigmoney | BigMoney·量化 | P1 | ACTIVE | 84.8 | 86 | 未测 |
| bigdomain | BigDomain·硅基域商业化 | P1 | ACTIVE | 103.4 | 5 | 未测 |
| bigcompute | BigCompute·硅基算力 | P3 | ACTIVE | 103.4 | 4 | 未测 |
| biglife | BigLife·数字生命 | P2 | ACTIVE | 未测 | 3 | 未测 |
| bighouse | BigHouse·城市安家 | P2 | PARKED | 未测 | 未测 | 未测 |
| car-gaming | 车机游戏 BU | P3 | PARKED | 124.9 | 未测 | 未测 |
| recon | RECON·竞品拆解 | P3 | ACTIVE | 12.2 | 3 | 未测 |
| fleet-ops | 机队运维·端到端自检（平台服务线） | P3 | ACTIVE | 未测 | 123 | 1 |
| asset-lib | 资产储备·角色 LoRA 与音色库 | P0 | ACTIVE | 5.3 | 44 | 4 |

## 怎么读这张表
产物年龄超过该线阈值或声明 ACTIVE 但 observed 不是 OBSERVED，就是「纸面在做」，要去看卡和输入。

## 我不知道的
远端产物本机不可见，按远端待查处理。

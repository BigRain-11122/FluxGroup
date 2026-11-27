---
id: skills.seats
title: 席位与工序分工
layer: skills
questions: ["谁负责哪道工序", "哪台机跑"]
facts: ["LINE-REGISTRY.json(stages)", "cph4/agents/AGENT-LIBRARY.md"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
常驻角色不是人，是分工：每条线的工序都标了 owner 与用哪台机。

## 角色清单（取自线注册表 stages）
- BigStream·MV 41 曲：立意/分镜(导演席)；关键帧(导演席·美术)；出片(导演席)；剪辑/装配(剪辑席)；质检/交付(质检席)；呈审(导演席（自决放行）)
- BigStream·漫剧：剧本(编剧席)；画面/分镜(漫剧席)；配音(声音席)；混音/合成(声音席)
- BigStream·短剧：剧本(编剧席)；试构图(短剧席)
- BigStream·短视频/切片：选题/脚本(短视频席)；剪辑(剪辑席)
- Biggame·游戏：玩法/数值(游戏席)；美术资产(美术席)；构建/打包(工程席)
- FluxVerse·元宙城：场景装配(地编席)；数据面(城市线)；可视化(城市线)
- BigMoney·量化：数据(数据席)；回测(量化席)；审计/闸(风控席)
- BigDomain·硅基域商业化：引流线索(域运营席)；订单簿记(域运营席)
- BigCompute·硅基算力：成交环(算力中枢席)
- BigLife·数字生命：人设生产(生命生产席)；生命体征闸(质检席)
- BigHouse·城市安家：安家(生态运营席)；邻里/共长(生态运营席)
- 车机游戏 BU：市场/立项(车机 BU)；研发/适配闸(工程席)
- RECON·竞品拆解：扒榜/拆包(拆解部)；48h 原型(拆解部)
- 机队运维·端到端自检（平台服务线）：端到端自检(中枢)
- 资产储备·角色 LoRA 与音色库：训练环境自检(资产席)；数据集准入闸(资产席)；LoRA/音色训练(资产席)

## 怎么用
派活时按 stage 找 owner；owner 不等于机器，lane 才是机器。

## 我不知道的
各席的决策权限细节分散在 cph4/council 与 docs/decisions.md。

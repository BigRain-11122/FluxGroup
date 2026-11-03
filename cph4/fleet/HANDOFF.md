# 交接一屏（2026-11-03 20:20）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（3 张）

- `biggame-playable-2026-11-03` [游戏（可上线清单 → 一款可玩包 → 提审材料）] 一款可玩包（3 关 60–90 秒，2D，儿童不作失败）（bm-m，45 分钟租约）
- `asset-lib-face-caption-2026-11-03` [资产储备（角色 LoRA / 音色库）] 人脸数据集打标（vision 草稿，人只校对）（bm-a，180 分钟租约）
- `asset-lib-asset-gen-2026-11-03` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（bm-c，180 分钟租约）

## 二、待判（17 张在队列等机器）

- `Q-TRIAGE-ASSETLIB-20261103` asset-lib 线级体检（本机证据目录实况）（无归属）
- `asset-lib-voice-corpus-bmb-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 1/4（bm-b，纯 CPU）（asset-lib）
- `CHK-RECEIPT-20261103` 回执卫生体检（rc 缺失/error_class 缺失出表）（bm-m 兜底体检）（fleet-ops）
- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（fleet-ops）
- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `CANARY-20261103T154230` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261103T160731` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-MODEL-RADAR-BMB-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-b）（无归属）
- `R-MODEL-RADAR-BMC-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-c）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）

## 三、阻塞（7 项断言红 / 3 台机不一致）

- 断言 I1：2 条
- 断言 I2：138 条
- 断言 I3：19 条
- 断言 I4：10 条
- 断言 I12：4 条
- 断言 I13：1 条
- 断言 I14：2 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：IDLE-WITH-QUEUE
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 83.7，返工 7，产出年龄 7.6
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.4
- bigstream-duanju：过闸率 62.5，返工 3，产出年龄 97.5
- biggame：过闸率 100.0，返工 0，产出年龄 2.9
- asset-lib：过闸率 35.7，返工 8，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

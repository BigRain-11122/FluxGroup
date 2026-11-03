# 交接一屏（2026-11-03 21:15）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（3 张）

- `biggame-playable-2026-11-03` [游戏（可上线清单 → 一款可玩包 → 提审材料）] 一款可玩包（3 关 60–90 秒，2D，儿童不作失败）（bm-m，45 分钟租约）
- `asset-lib-char-prompts-2026-11-03` [资产储备（角色 LoRA / 音色库）] 角色包出图计划（8 原创角色 × 6 视角提示词包）（bm-a，45 分钟租约）
- `asset-lib-char-gen-2026-11-03` [资产储备（角色 LoRA / 音色库）] 角色包出图（本机 ComfyUI，1024²，同 seed 组）（bm-c，180 分钟租约）

## 二、待判（16 张在队列等机器）

- `Q-TRIAGE-ASSETLIB-20261103` asset-lib 线级体检（本机证据目录实况）（无归属）
- `asset-lib-voice-corpus-bmb-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 1/4（bm-b，纯 CPU）（asset-lib）
- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（fleet-ops）
- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `CANARY-20261103T154230` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `asset-lib-char-probe-2026-11-03` [资产储备（角色 LoRA / 音色库）] 角色出图模型探针（问本机 ComfyUI 有哪些模型，不出图）（asset-lib）
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
- 机器 bm-a：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-b：HB-SILENT、IDLE-WITH-QUEUE
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 81.8，返工 7，产出年龄 8.5
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 1.3
- bigstream-duanju：过闸率 62.5，返工 3，产出年龄 98.4
- biggame：过闸率 100.0，返工 0，产出年龄 3.8
- asset-lib：过闸率 46.2，返工 6，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

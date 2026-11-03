# 交接一屏（2026-11-03 15:37）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `asset-lib-voice-corpus-bmb-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 1/4（bm-b，纯 CPU）（bm-a，45 分钟租约）
- `asset-lib-voice-corpus-bmc-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 2/4（bm-c，纯 CPU）（bm-m，45 分钟租约）
- `asset-lib-index-2026-11-03` [资产储备（角色 LoRA / 音色库）] 入库登记（没过闸的不许进资产库）（bm-c，45 分钟租约）
- `asset-lib-face-caption-2026-11-03` [资产储备（角色 LoRA / 音色库）] 人脸数据集打标（vision 草稿，人只校对）（bm-b，180 分钟租约）

## 二、待判（4 张在队列等机器）

- `bigstream-duanju-remux-2026-11-03` [短剧（配音质检→带声合流→可发集数）] 带声合流（三层混音 → 成片，loudnorm -14）（bigstream-duanju）
- `Q-TRIAGE-ASSETLIB-20261103` asset-lib 线级体检（本机证据目录实况）（无归属）
- `CHK-RECEIPT-20261103` 回执卫生体检（rc 缺失/error_class 缺失出表）（bm-m 兜底体检）（fleet-ops）
- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（fleet-ops）

## 三、阻塞（6 项断言红 / 2 台机不一致）

- 断言 I1：2 条
- 断言 I2：125 条
- 断言 I3：19 条
- 断言 I4：11 条
- 断言 I12：1 条
- 断言 I14：2 条
- 机器 bm-b：HB-SILENT
- 机器 bm-c：HB-SILENT

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 81.8，返工 7，产出年龄 2.9
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.0
- bigstream-duanju：过闸率 62.5，返工 3，产出年龄 92.8
- biggame：过闸率 75.0，返工 0，产出年龄 None
- asset-lib：过闸率 62.5，返工 3，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

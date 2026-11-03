# 交接一屏（2026-11-03 14:27）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `bigstream-mv-gate-2026-11-03` [MV·爱在西元前（v721 终版）] 交付闸（重复/静止/抖动/闪烁）（bm-a，45 分钟租约）
- `asset-lib-env-check-2026-11-03` [资产储备（角色 LoRA / 音色库）] 训练环境自检（这台机能不能烧）（bm-m，45 分钟租约）
- `asset-lib-face-dataset-2026-11-03` [资产储备（角色 LoRA / 音色库）] 人脸数据集准入（反 AI 脸的第一道门）（bm-b，45 分钟租约）
- `asset-lib-voice-corpus-bmm-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 3/4（bm-m，纯 CPU）（bm-c，45 分钟租约）

## 二、待判（8 张在队列等机器）

- `biggame-playable-2026-11-03` [游戏（可上线清单 → 一款可玩包 → 提审材料）] 一款可玩包（3 关 60–90 秒，2D，儿童不作失败）（biggame）
- `bigstream-duanju-remux-2026-11-03` [短剧（配音质检→带声合流→可发集数）] 带声合流（三层混音 → 成片，loudnorm -14）（bigstream-duanju）
- `Q-TRIAGE-ASSETLIB-20261103` asset-lib 线级体检（本机证据目录实况）（无归属）
- `asset-lib-voice-dataset-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色数据集准入（反播音腔的第一道门）（asset-lib）
- `asset-lib-voice-corpus-bmb-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 1/4（bm-b，纯 CPU）（asset-lib）
- `asset-lib-voice-corpus-bmc-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 2/4（bm-c，纯 CPU）（asset-lib）
- `CHK-RECEIPT-20261103` 回执卫生体检（rc 缺失/error_class 缺失出表）（bm-m 兜底体检）（无归属）
- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（无归属）

## 三、阻塞（7 项断言红 / 3 台机不一致）

- 断言 I1：5 条
- 断言 I2：111 条
- 断言 I3：18 条
- 断言 I4：9 条
- 断言 I12：4 条
- 断言 I13：2 条
- 断言 I14：2 条
- 机器 bm-b：IDLE-WITH-QUEUE
- 机器 bm-c：NO-RECEIPT-1H
- 机器 bm-m：IDLE-WITH-QUEUE

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 83.7，返工 8，产出年龄 1.7
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 2.2
- bigstream-duanju：过闸率 62.5，返工 3，产出年龄 91.6
- biggame：过闸率 100.0，返工 0，产出年龄 None
- asset-lib：过闸率 None，返工 0，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

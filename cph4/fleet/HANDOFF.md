# 交接一屏（2026-11-03 14:40）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `biggame-playable-2026-11-03` [游戏（可上线清单 → 一款可玩包 → 提审材料）] 一款可玩包（3 关 60–90 秒，2D，儿童不作失败）（bm-c，45 分钟租约）
- `asset-lib-voice-corpus-bma-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 0/4（bm-a，纯 CPU）（bm-a，45 分钟租约）
- `asset-lib-voice-corpus-bmb-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 1/4（bm-b，纯 CPU）（bm-b，45 分钟租约）
- `C-INFRA-AUDIT-BM-B-20261103` 本地推理栈体检（bm-b）：引擎/端口归属/环境变量/速度/向量层（bm-m，45 分钟租约）

## 二、待判（5 张在队列等机器）

- `bigstream-duanju-remux-2026-11-03` [短剧（配音质检→带声合流→可发集数）] 带声合流（三层混音 → 成片，loudnorm -14）（bigstream-duanju）
- `Q-TRIAGE-ASSETLIB-20261103` asset-lib 线级体检（本机证据目录实况）（无归属）
- `CHK-RECEIPT-20261103` 回执卫生体检（rc 缺失/error_class 缺失出表）（bm-m 兜底体检）（无归属）
- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（无归属）
- `C-INFRA-AUDIT-BM-C-20261103` 本地推理栈体检（bm-c）：引擎/端口归属/环境变量/速度/向量层（fleet-ops）

## 三、阻塞（6 项断言红 / 3 台机不一致）

- 断言 I1：5 条
- 断言 I2：125 条
- 断言 I3：19 条
- 断言 I4：9 条
- 断言 I12：4 条
- 断言 I14：2 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 81.8，返工 7，产出年龄 1.8
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 2.3
- bigstream-duanju：过闸率 62.5，返工 3，产出年龄 91.8
- biggame：过闸率 100.0，返工 0，产出年龄 None
- asset-lib：过闸率 25.0，返工 3，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

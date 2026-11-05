# 交接一屏（2026-11-05 14:04）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `ART-PUSH-BMA-20261104` bm-a 产物回传（artifact_push 全量）（bm-a，45 分钟租约）
- `asset-lib-env-check-2026-11-05` [资产储备（角色 LoRA / 音色库）] 训练环境自检（这台机能不能烧）（bm-b，45 分钟租约）
- `bigstream-mv-gate-2026-11-05` [MV·爱在西元前（v721 终版）] 交付闸（重复/静止/抖动/闪烁）（bm-m，45 分钟租约）
- `asset-lib-voice-assemble-2026-11-05` [资产储备（角色 LoRA / 音色库）] 音色数据集装配（授权核查→voices/<组> 准入）（bm-c，45 分钟租约）

## 二、待判（17 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `CHT-20261105T132722-01` 全链路自测 1（fleet-ops）
- `LINE-TRIAGE-MV-20261105` MV 线证据陈旧扫描（line_triage·本机可判面）（fleet-ops）
- `asset-lib-face-dataset-2026-11-05` [资产储备（角色 LoRA / 音色库）] 人脸数据集准入（反 AI 脸的第一道门）（asset-lib）
- `asset-lib-asset-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（asset-lib）
- `asset-lib-asset-gen-scenes-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图·场景（竖屏底图）（asset-lib）
- `CHT-20261105T134645-01` 全链路自测 1（fleet-ops）
- `CHT-20261105T134647-02` 全链路自测 2（fleet-ops）
- `CHT-20261105T134717-01` 全链路自测 1（fleet-ops）
- `CHT-20261105T134725-02` 全链路自测 2（fleet-ops）

## 三、阻塞（8 项断言红 / 3 台机不一致）

- 断言 I1：3 条
- 断言 I2：162 条
- 断言 I3：11 条
- 断言 I4：14 条
- 断言 I6：1 条
- 断言 I7：2 条
- 断言 I12：15 条
- 断言 I14：4 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 75.0，返工 13，产出年龄 25.9
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 1.3
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 139.3
- biggame：过闸率 71.4，返工 2，产出年龄 44.6
- asset-lib：过闸率 37.5，返工 22，产出年龄 18.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

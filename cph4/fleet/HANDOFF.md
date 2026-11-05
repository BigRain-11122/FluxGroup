# 交接一屏（2026-11-05 14:59）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `asset-lib-env-check-2026-11-05` [资产储备（角色 LoRA / 音色库）] 训练环境自检（这台机能不能烧）（bm-b，45 分钟租约）
- `asset-lib-voice-assemble-2026-11-05` [资产储备（角色 LoRA / 音色库）] 音色数据集装配（授权核查→voices/<组> 准入）（bm-m，45 分钟租约）
- `asset-lib-asset-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（bm-c，180 分钟租约）
- `CHT-20261105T134821-03` 全链路自测 3（bm-a，45 分钟租约）

## 二、待判（6 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `CHT-20261105T134829-99` 全链路自测 99 (负向)（fleet-ops）
- `CHT-20261105T134950-99` 全链路自测 99 (负向)（fleet-ops）
- `R-NEXT-FLUXVERSE-CITY-STA-20261105` 元宙城 12 面状态实盘（在役/受阻/空白逐面点名）（fluxverse）
- `R-TRIAGE-BIGLIFE-BMA-20261105` BigLife·数字生命 线证据扫描（bm-a 本机可判面）（无归属）
- `CANARY-20261105T145926` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 3 台机不一致）

- 断言 I1：3 条
- 断言 I2：156 条
- 断言 I3：11 条
- 断言 I4：15 条
- 断言 I6：1 条
- 断言 I7：2 条
- 断言 I12：16 条
- 断言 I14：4 条
- 机器 bm-a：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：BUSY-NO-REPORT、NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 72.0，返工 13，产出年龄 26.7
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 2.2
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 140.1
- biggame：过闸率 71.4，返工 2，产出年龄 45.5
- asset-lib：过闸率 35.3，返工 23，产出年龄 18.9

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

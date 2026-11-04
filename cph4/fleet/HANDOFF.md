# 交接一屏（2026-11-04 20:04）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（3 张）

- `CHK-RECEIPT-20261103` 回执卫生体检（rc 缺失/error_class 缺失出表）（bm-m 兜底体检）（bm-c，45 分钟租约）
- `R-MODEL-RADAR-BMB-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-b）（bm-m，45 分钟租约）
- `ART-PUSH-BMA-20261104` bm-a 产物回传（artifact_push 全量）（bm-a，45 分钟租约）

## 二、待判（6 张在队列等机器）

- `asset-lib-voice-corpus-bmb-2026-11-03` [资产储备（角色 LoRA / 音色库）] 音色语料工程·分片 1/4（bm-b，纯 CPU）（asset-lib）
- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T175030` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 2 台机不一致）

- 断言 I1：3 条
- 断言 I2：158 条
- 断言 I3：3 条
- 断言 I4：11 条
- 断言 I7：1 条
- 断言 I12：12 条
- 断言 I13：1 条
- 断言 I14：3 条
- 机器 bm-b：IDLE-WITH-QUEUE
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 75.0，返工 12，产出年龄 7.8
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.4
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 121.2
- biggame：过闸率 66.7，返工 2，产出年龄 26.6
- asset-lib：过闸率 40.0，返工 19，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

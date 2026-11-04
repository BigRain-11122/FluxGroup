# 交接一屏（2026-11-04 19:29）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（bm-c，45 分钟租约）
- `Q-TRIAGE-BIGMONEY-20261104` bigmoney 线级体检（本机证据目录实况）（bm-m，45 分钟租约）
- `R-MODEL-RADAR-BMC-20261104` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-c）（bm-a，45 分钟租约）
- `bigstream-mv-stability-2026-11-04` [MV·爱在西元前（v721 终版）] 稳定性闸（seam / freeze 双 0）（bm-b，45 分钟租约）

## 二、待判（17 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMB-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-b）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T125141` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T125241` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T131747` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-PLAN-BIGGAME-20261104` Biggame·游戏 线级体检与缺口清单（biggame）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 2 台机不一致）

- 断言 I1：2 条
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

- bigstream-mv：过闸率 76.6，返工 10，产出年龄 7.2
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 7.2
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 120.6
- biggame：过闸率 60.0，返工 1，产出年龄 26.0
- asset-lib：过闸率 38.7，返工 18，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

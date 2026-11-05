# 交接一屏（2026-11-05 11:36）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（1 张）

- `asset-lib-asset-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（bm-c，180 分钟租约）

## 二、待判（19 张在队列等机器）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（fleet-ops）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `bigstream-mv-gate-2026-11-05` [MV·爱在西元前（v721 终版）] 交付闸（重复/静止/抖动/闪烁）（bigstream-mv）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T202057` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261105T061408` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-TRIAGE-BIGSTREAMMV-BMA-20261104` BigStream·MV 41 曲 线证据扫描（bm-a 本机可判面）（无归属）
- `R-TRIAGE-FLEETOPS-BMA-20261104` 机队运维·端到端自检（平台服务线） 线证据扫描（bm-a 本机可判面）（无归属）
- `R-PLAN-BIGDOMAIN-20261105` BigDomain·硅基域商业化 线级体检与缺口清单（bigdomain）
- `Q-TRIAGE-BIGSTREAMMV-20261105` bigstream-mv 线级体检（本机证据目录实况）（无归属）

## 三、阻塞（8 项断言红 / 4 台机不一致）

- 断言 I1：4 条
- 断言 I2：174 条
- 断言 I3：10 条
- 断言 I4：13 条
- 断言 I6：1 条
- 断言 I7：1 条
- 断言 I12：15 条
- 断言 I14：3 条
- 机器 bm-a：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-b：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H
- 机器 bm-m：BUSY-NO-REPORT

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 13，产出年龄 23.5
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 5.3
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 136.8
- biggame：过闸率 57.1，返工 2，产出年龄 42.2
- asset-lib：过闸率 35.3，返工 24，产出年龄 15.6

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

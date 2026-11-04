# 交接一屏（2026-11-05 06:14）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（bm-m，45 分钟租约）
- `CANARY-20261104T125141` 端到端自检：投卡→领取→执行→回执→产物（bm-a，45 分钟租约）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（bm-c，45 分钟租约）
- `MV-NEWPROC-PACKET-20261104` 导演席新流程卷：四曲立意/分镜/合规矩阵一页卷（bm-b，45 分钟租约）

## 二、待判（12 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGGAME-20261105` Biggame·游戏 线级体检与缺口清单（biggame）
- `bigstream-mv-gate-2026-11-05` [MV·爱在西元前（v721 终版）] 交付闸（重复/静止/抖动/闪烁）（bigstream-mv）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `R-PLAN-BIGMONEY-20261104` BigMoney·量化 线级体检与缺口清单（bigmoney）
- `CANARY-20261104T140742` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T175030` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T201032` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 4 台机不一致）

- 断言 I1：3 条
- 断言 I2：136 条
- 断言 I3：10 条
- 断言 I4：12 条
- 断言 I6：1 条
- 断言 I7：1 条
- 断言 I12：15 条
- 断言 I14：3 条
- 机器 bm-a：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-b：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-c：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-m：BUSY-NO-REPORT

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 13，产出年龄 18.0
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 2.2
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 131.4
- biggame：过闸率 66.7，返工 2，产出年龄 36.8
- asset-lib：过闸率 38.7，返工 19，产出年龄 0.1

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

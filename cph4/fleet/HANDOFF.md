# 交接一屏（2026-11-04 21:05）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（bm-m，45 分钟租约）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（bm-b，45 分钟租约）
- `R-PLAN-BIGMONEY-20261104` BigMoney·量化 线级体检与缺口清单（bm-c，45 分钟租约）
- `MV-NEWPROC-PACKET-20261104` 导演席新流程卷：四曲立意/分镜/合规矩阵一页卷（bm-a，45 分钟租约）

## 二、待判（8 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `ART-PUSH-BMA-20261104` bm-a 产物回传（artifact_push 全量）（fleet-ops）
- `CANARY-20261104T175030` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T202057` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T210515` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（7 项断言红 / 3 台机不一致）

- 断言 I1：3 条
- 断言 I2：156 条
- 断言 I3：3 条
- 断言 I4：11 条
- 断言 I7：1 条
- 断言 I12：12 条
- 断言 I14：3 条
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H
- 机器 bm-m：BUSY-NO-REPORT

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 75.0，返工 12，产出年龄 8.9
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 1.5
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 122.3
- biggame：过闸率 66.7，返工 2，产出年龄 27.6
- asset-lib：过闸率 38.7，返工 19，产出年龄 0.1

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

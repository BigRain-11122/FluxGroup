# 交接一屏（2026-11-05 01:27）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `MV-NEWPROC-PACKET-20261104` 导演席新流程卷：四曲立意/分镜/合规矩阵一页卷（bm-m，45 分钟租约）
- `fleet-node-sync-report-bm-c-2026-11-05` [机队] bm-c 仓面自报：分支/HEAD/origin/main/领先落后/脏文件（纯 git，不依赖仓内脚本）（bm-c，10 分钟租约）
- `Q-VCORP-PREP-e01-R3-20261105` 音色语料切片·e01（LibriTTS → voices/e01/sliced，纯 CPU）（bm-a，60 分钟租约）
- `Q-VCORP-TRAIN-PILOT-libritts-e01-R3-20261105` 音色微调试点·libritts-e01（语料→SoVITS s2→权重，DE-AI-SPEC A8 批前抽检）（bm-b，240 分钟租约）

## 二、待判（32 张在队列等机器）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（fleet-ops）
- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T125141` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-PLAN-BIGMONEY-20261104` BigMoney·量化 线级体检与缺口清单（bigmoney）
- `CANARY-20261104T140742` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T175030` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 2 台机不一致）

- 断言 I1：4 条
- 断言 I2：180 条
- 断言 I3：9 条
- 断言 I4：11 条
- 断言 I6：1 条
- 断言 I7：1 条
- 断言 I12：14 条
- 断言 I14：3 条
- 机器 bm-b：HB-SILENT
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 12，产出年龄 13.3
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.2
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 126.6
- biggame：过闸率 62.5，返工 3，产出年龄 32.0
- asset-lib：过闸率 35.9，返工 22，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

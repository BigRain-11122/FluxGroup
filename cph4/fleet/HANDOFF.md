# 交接一屏（2026-11-05 03:59）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（5 张）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（bm-m，45 分钟租约）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（bm-c，45 分钟租约）
- `MV-NEWPROC-PACKET-20261104` 导演席新流程卷：四曲立意/分镜/合规矩阵一页卷（bm-b，45 分钟租约）
- `asset-lib-face-dataset-2026-11-05` [资产储备（角色 LoRA / 音色库）] 人脸数据集准入（反 AI 脸的第一道门）（bm-c，45 分钟租约）
- `Q-VCORP-TRAIN-PILOT-libritts-e01-R3-20261105` 闊宠壊寰�璋冭瘯鐐孤穕ibritts-e01锛堣��鏂欌啋SoVITS s2鈫掓潈閲嶏紝DE-AI-SPEC A8 鎵瑰墠鎶芥��锛�（bm-b，240 分钟租约）

## 二、待判（29 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T125141` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-PLAN-BIGMONEY-20261104` BigMoney·量化 线级体检与缺口清单（bigmoney）
- `CANARY-20261104T140742` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T175030` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T201032` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T202057` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（7 项断言红 / 2 台机不一致）

- 断言 I1：2 条
- 断言 I2：122 条
- 断言 I3：4 条
- 断言 I4：9 条
- 断言 I7：1 条
- 断言 I12：12 条
- 断言 I14：3 条
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 13，产出年龄 15.7
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.2
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 129.1
- biggame：过闸率 71.4，返工 3，产出年龄 34.5
- asset-lib：过闸率 37.8，返工 23，产出年龄 0.1

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

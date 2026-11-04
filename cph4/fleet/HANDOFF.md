# 交接一屏（2026-11-05 04:26）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（bm-m，45 分钟租约）
- `R-NEXT-BIGSTREAMM-GATE-20261105` MV 浜や粯闂稿�嶈窇锛氬綋鍓嶆瘝鐗堝洓闂稿叏楠岋紙鏀跺彛鍓嶇疆锛�（bm-a，45 分钟租约）
- `Q-VCORP-TRAIN-PILOT-libritts-e01-R3-20261105` 闊宠壊寰�璋冭瘯鐐孤穕ibritts-e01锛堣��鏂欌啋SoVITS s2鈫掓潈閲嶏紝DE-AI-SPEC A8 鎵瑰墠鎶芥��锛�（bm-b，240 分钟租约）
- `asset-lib-asset-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（bm-c，180 分钟租约）

## 二、待判（31 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T125141` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-PLAN-BIGMONEY-20261104` BigMoney·量化 线级体检与缺口清单（bigmoney）
- `CANARY-20261104T140742` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T175030` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T201032` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 1 台机不一致）

- 断言 I1：4 条
- 断言 I2：198 条
- 断言 I3：10 条
- 断言 I4：14 条
- 断言 I6：1 条
- 断言 I7：1 条
- 断言 I12：15 条
- 断言 I14：3 条
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 72.0，返工 13，产出年龄 16.2
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.3
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 129.5
- biggame：过闸率 71.4，返工 3，产出年龄 34.9
- asset-lib：过闸率 36.8，返工 24，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

# 交接一屏（2026-11-05 06:31）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `asset-lib-face-dataset-2026-11-05` [资产储备（角色 LoRA / 音色库）] 人脸数据集准入（反 AI 脸的第一道门）（bm-a，45 分钟租约）
- `Q-VCORP-PREP-e01-R3-20261105` 音色语料切片·e01（LibriTTS → voices/e01/sliced，纯 CPU）（bm-m，60 分钟租约）
- `asset-lib-asset-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（bm-b，180 分钟租约）
- `asset-lib-char-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 角色包出图（本机 ComfyUI，1024²，同 seed 组）（bm-c，180 分钟租约）

## 二、待判（29 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGGAME-20261105` Biggame·游戏 线级体检与缺口清单（biggame）
- `bigstream-mv-gate-2026-11-05` [MV·爱在西元前（v721 终版）] 交付闸（重复/静止/抖动/闪烁）（bigstream-mv）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T125141` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-PLAN-BIGMONEY-20261104` BigMoney·量化 线级体检与缺口清单（bigmoney）
- `CANARY-20261104T140742` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 0 台机不一致）

- 断言 I1：3 条
- 断言 I2：156 条
- 断言 I3：10 条
- 断言 I4：12 条
- 断言 I6：1 条
- 断言 I7：1 条
- 断言 I12：15 条
- 断言 I14：3 条

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 13，产出年龄 18.3
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.2
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 131.7
- biggame：过闸率 66.7，返工 2，产出年龄 37.1
- asset-lib：过闸率 38.7，返工 19，产出年龄 0.1

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

# 交接一屏（2026-11-05 06:57）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `MV-NEWPROC-PACKET-20261104` 导演席新流程卷：四曲立意/分镜/合规矩阵一页卷（bm-a，45 分钟租约）
- `Q-VCORP-PREP-e01-R3-20261105` 音色语料切片·e01（LibriTTS → voices/e01/sliced，纯 CPU）（bm-m，60 分钟租约）
- `Q-VCORP-TRAIN-PILOT-libritts-e01-R3-20261105` 音色微调试点·libritts-e01（语料→SoVITS s2→权重，DE-AI-SPEC A8 批前抽检）（bm-b，240 分钟租约）
- `asset-lib-char-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 角色包出图（本机 ComfyUI，1024²，同 seed 组）（bm-c，180 分钟租约）

## 二、待判（23 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-PLAN-BIGGAME-20261105` Biggame·游戏 线级体检与缺口清单（biggame）
- `R-PLAN-BIGSTREAMDUA-20261104` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `CANARY-20261104T140742` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T175030` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T201032` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T202057` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261105T061408` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 3 台机不一致）

- 断言 I1：4 条
- 断言 I2：168 条
- 断言 I3：10 条
- 断言 I4：13 条
- 断言 I6：1 条
- 断言 I7：1 条
- 断言 I12：15 条
- 断言 I14：3 条
- 机器 bm-a：BUSY-NO-REPORT
- 机器 bm-b：BUSY-NO-REPORT
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 72.0，返工 13，产出年龄 18.8
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.7
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 132.1
- biggame：过闸率 66.7，返工 2，产出年龄 37.5
- asset-lib：过闸率 36.4，返工 20，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

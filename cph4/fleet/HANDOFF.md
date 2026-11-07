# 交接一屏（2026-11-07 14:45）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（1 张）

- `asset-lib-asset-gen-2026-11-07` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（bm-c，180 分钟租约）

## 二、待判（3 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `MOB-DRAMA-TTSQC-20261106T162309` 短剧配音批质检（在持料机上跑，出可发布集数清单）（bigstream-drama）
- `CANARY-20261107T144524` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 4 台机不一致）

- 断言 I1：5 条
- 断言 I2：1 条
- 断言 I3：36 条
- 断言 I4：20 条
- 断言 I7：3 条
- 断言 I12：30 条
- 断言 I13：2 条
- 断言 I14：3 条
- 机器 bm-a：IDLE-WITH-QUEUE
- 机器 bm-b：IDLE-WITH-QUEUE
- 机器 bm-c：NO-RECEIPT-1H
- 机器 bm-m：IDLE-WITH-QUEUE

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 87.1，返工 18，产出年龄 18.5
- bigstream-drama：过闸率 75.0，返工 7，产出年龄 12.3
- bigstream-duanju：过闸率 44.4，返工 3，产出年龄 185.7
- biggame：过闸率 28.8，返工 78，产出年龄 91.1
- asset-lib：过闸率 35.0，返工 29，产出年龄 18.5

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

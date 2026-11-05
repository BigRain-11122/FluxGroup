# 交接一屏（2026-11-05 16:29）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `asset-lib-voice-assemble-2026-11-05` [资产储备（角色 LoRA / 音色库）] 音色数据集装配（授权核查→voices/<组> 准入）（bm-b，45 分钟租约）
- `asset-lib-char-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 角色包出图（本机 ComfyUI，1024²，同 seed 组）（bm-c，180 分钟租约）
- `SIM-20261105T155828-01-1` 演练·量化信号（bm-a，45 分钟租约）
- `SIM-20261105T161648-03-0` 演练·MV闸（bm-m，45 分钟租约）

## 二、待判（5 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `SIM-20261105T155828-01-infra` 演练·机制卡（应被配额拦）（fleet-ops）
- `SIM-20261105T160855-01-infra` 演练·机制卡（应被配额拦）（fleet-ops）
- `R-NEXT-BIGSTREAMD-EVIDENCE-20261105` 漫剧证据目录补齐判定：画面/配音工段为何为空（一页含根因与补法）（bigstream-drama）
- `CANARY-20261105T162939` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（7 项断言红 / 3 台机不一致）

- 断言 I2：2 条
- 断言 I3：9 条
- 断言 I4：17 条
- 断言 I6：1 条
- 断言 I7：2 条
- 断言 I12：18 条
- 断言 I14：4 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 84.5，返工 16，产出年龄 28.3
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 3.7
- bigstream-duanju：过闸率 57.1，返工 3，产出年龄 141.7
- biggame：过闸率 71.4，返工 2，产出年龄 47.1
- asset-lib：过闸率 46.4，返工 22，产出年龄 0.5

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

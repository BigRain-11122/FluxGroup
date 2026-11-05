# 交接一屏（2026-11-05 14:49）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `C-TTS-QC-ALL` 短剧配音全量质检（逐集时长/静音/体积 → 可发布集数清单）（bm-a，45 分钟租约）
- `asset-lib-voice-assemble-2026-11-05` [资产储备（角色 LoRA / 音色库）] 音色数据集装配（授权核查→voices/<组> 准入）（bm-b，45 分钟租约）
- `asset-lib-face-dataset-2026-11-05` [资产储备（角色 LoRA / 音色库）] 人脸数据集准入（反 AI 脸的第一道门）（bm-c，45 分钟租约）
- `B-MV-AUDIT-20261105` MV 逐镜体检：6 对重复镜 + 24 个近静止镜的具体镜号与时间码（修片前置）（bm-m，45 分钟租约）

## 二、待判（11 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `asset-lib-char-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 角色包出图（本机 ComfyUI，1024²，同 seed 组）（asset-lib）
- `asset-lib-asset-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图（道具/场景，吃 ASSET-PROMPTS 规格）（asset-lib）
- `CHT-20261105T134821-03` 全链路自测 3（fleet-ops）
- `CHT-20261105T134829-99` 全链路自测 99 (负向)（fleet-ops）
- `CHT-20261105T134950-99` 全链路自测 99 (负向)（fleet-ops）
- `R-TRIAGE-BIGLIFE-BMB-20261105` BigLife·数字生命 线证据扫描（bm-b 本机可判面）（无归属）
- `R-TRIAGE-RECON-BMB-20261105` RECON·竞品拆解 线证据扫描（bm-b 本机可判面）（无归属）
- `R-TRIAGE-FLEETOPS-BMA-20261105` 机队运维·端到端自检（平台服务线） 线证据扫描（bm-a 本机可判面）（无归属）
- `B-QNT-SIGNAL-20261105` 量化：下月持仓信号（含因子值与输入指纹）（bigmoney）

## 三、阻塞（8 项断言红 / 3 台机不一致）

- 断言 I1：3 条
- 断言 I2：156 条
- 断言 I3：11 条
- 断言 I4：15 条
- 断言 I6：1 条
- 断言 I7：2 条
- 断言 I12：16 条
- 断言 I14：4 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 13，产出年龄 26.6
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 2.1
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 140.0
- biggame：过闸率 71.4，返工 2，产出年龄 45.4
- asset-lib：过闸率 36.4，返工 23，产出年龄 18.7

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

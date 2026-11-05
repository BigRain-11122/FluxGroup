# 交接一屏（2026-11-05 13:57）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `ART-PUSH-BMA-20261104` bm-a 产物回传（artifact_push 全量）（bm-a，45 分钟租约）
- `asset-lib-env-check-2026-11-05` [资产储备（角色 LoRA / 音色库）] 训练环境自检（这台机能不能烧）（bm-b，45 分钟租约）
- `asset-lib-voice-assemble-2026-11-05` [资产储备（角色 LoRA / 音色库）] 音色数据集装配（授权核查→voices/<组> 准入）（bm-c，45 分钟租约）
- `asset-lib-face-dataset-2026-11-05` [资产储备（角色 LoRA / 音色库）] 人脸数据集准入（反 AI 脸的第一道门）（bm-m，45 分钟租约）

## 二、待判（31 张在队列等机器）

- `C-TTS-QC-ALL` 短剧配音全量质检（逐集时长/静音/体积 → 可发布集数清单）（无归属）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `R-MODEL-RADAR-BMM-20261105` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `Q-TRIAGE-RECON-20261105` recon 线级体检（本机证据目录实况）（无归属）
- `R-MODEL-RADAR-BMB-20261105` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-b）（无归属）
- `R-TRIAGE-BIGGAME-BMB-20261105` Biggame·游戏 线证据扫描（bm-b 本机可判面）（无归属）
- `R-TRIAGE-FLUXVERSE-BMB-20261105` FluxVerse·元宙城 线证据扫描（bm-b 本机可判面）（无归属）
- `CHT-20261105T132722-01` 全链路自测 1（fleet-ops）
- `CANARY-20261105T133235` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CHK-RECEIPT-20261104` 回执卫生体检（rc 缺失/error_class 缺失出表）（bm-m 兜底体检）（fleet-ops）

## 三、阻塞（8 项断言红 / 4 台机不一致）

- 断言 I1：3 条
- 断言 I2：162 条
- 断言 I3：11 条
- 断言 I4：14 条
- 断言 I6：1 条
- 断言 I7：2 条
- 断言 I12：15 条
- 断言 I14：4 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H
- 机器 bm-m：HB-SILENT

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 13，产出年龄 25.8
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 1.2
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 139.1
- biggame：过闸率 71.4，返工 2，产出年龄 44.5
- asset-lib：过闸率 38.7，返工 20，产出年龄 17.9

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

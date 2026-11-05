# 交接一屏（2026-11-05 14:10）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（4 张）

- `C-TTS-QC-ALL` 短剧配音全量质检（逐集时长/静音/体积 → 可发布集数清单）（bm-m，45 分钟租约）
- `ART-PUSH-BMA-20261104` bm-a 产物回传（artifact_push 全量）（bm-a，45 分钟租约）
- `asset-lib-char-gen-2026-11-05` [资产储备（角色 LoRA / 音色库）] 角色包出图（本机 ComfyUI，1024²，同 seed 组）（bm-b，180 分钟租约）
- `asset-lib-asset-gen-scenes-2026-11-05` [资产储备（角色 LoRA / 音色库）] 通用资产出图·场景（竖屏底图）（bm-c，180 分钟租约）

## 二、待判（14 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `CHT-20261105T132722-01` 全链路自测 1（fleet-ops）
- `LINE-TRIAGE-MV-20261105` MV 线证据陈旧扫描（line_triage·本机可判面）（fleet-ops）
- `asset-lib-face-dataset-2026-11-05` [资产储备（角色 LoRA / 音色库）] 人脸数据集准入（反 AI 脸的第一道门）（asset-lib）
- `CHT-20261105T134645-01` 全链路自测 1（fleet-ops）
- `CHT-20261105T134647-02` 全链路自测 2（fleet-ops）
- `CHT-20261105T134717-01` 全链路自测 1（fleet-ops）
- `CHT-20261105T134725-02` 全链路自测 2（fleet-ops）
- `CHT-20261105T134733-03` 全链路自测 3（fleet-ops）
- `CHT-20261105T134806-01` 全链路自测 1（fleet-ops）

## 三、阻塞（8 项断言红 / 3 台机不一致）

- 断言 I1：3 条
- 断言 I2：156 条
- 断言 I3：11 条
- 断言 I4：14 条
- 断言 I6：1 条
- 断言 I7：2 条
- 断言 I12：15 条
- 断言 I14：4 条
- 机器 bm-a：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-b：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-c：BUSY-NO-REPORT、NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 73.5，返工 13，产出年龄 26.0
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 1.4
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 139.4
- biggame：过闸率 71.4，返工 2，产出年龄 44.7
- asset-lib：过闸率 35.3，返工 22，产出年龄 18.1

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

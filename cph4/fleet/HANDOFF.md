# 交接一屏（2026-11-05 13:15）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（0 张）


## 二、待判（7 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `ART-PUSH-BMA-20261104` bm-a 产物回传（artifact_push 全量）（fleet-ops）
- `MV-NEWPROC-PACKET-20261104` 导演席新流程卷：四曲立意/分镜/合规矩阵一页卷（无归属）
- `R-NEXT-BIGGAME-SUBMIT-P-20261105` 游戏提审·真实缺件重盘（隐私已齐，重算图标/截图/台账/包体）（biggame）
- `asset-lib-env-check-2026-11-05` [资产储备（角色 LoRA / 音色库）] 训练环境自检（这台机能不能烧）（asset-lib）
- `bigstream-mv-gate-2026-11-05` [MV·爱在西元前（v721 终版）] 交付闸（重复/静止/抖动/闪烁）（bigstream-mv）
- `CANARY-20261105T131519` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（8 项断言红 / 4 台机不一致）

- 断言 I1：3 条
- 断言 I2：156 条
- 断言 I3：10 条
- 断言 I4：13 条
- 断言 I6：1 条
- 断言 I7：1 条
- 断言 I12：14 条
- 断言 I14：4 条
- 机器 bm-a：BUSY-NO-REPORT
- 机器 bm-b：BUSY-NO-REPORT
- 机器 bm-c：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-m：BUSY-NO-REPORT

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 75.0，返工 12，产出年龄 25.0
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.5
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 138.4
- biggame：过闸率 66.7，返工 2，产出年龄 43.8
- asset-lib：过闸率 38.7，返工 19，产出年龄 17.2

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

# 交接一屏（2026-11-03 14:21）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（2 张）

- `bigstream-mv-gate-2026-11-03` [MV·爱在西元前（v721 终版）] 交付闸（重复/静止/抖动/闪烁）（bm-a，45 分钟租约）
- `asset-lib-env-check-2026-11-03` [资产储备（角色 LoRA / 音色库）] 训练环境自检（这台机能不能烧）（bm-c，45 分钟租约）

## 二、待判（3 张在队列等机器）

- `biggame-playable-2026-11-03` [游戏（可上线清单 → 一款可玩包 → 提审材料）] 一款可玩包（3 关 60–90 秒，2D，儿童不作失败）（biggame）
- `bigstream-duanju-remux-2026-11-03` [短剧（配音质检→带声合流→可发集数）] 带声合流（三层混音 → 成片，loudnorm -14）（bigstream-duanju）
- `R-TRIAGE-ASSETLIB-BMA-20261103` 资产储备·角色 LoRA 与音色库 线证据扫描（bm-a 本机可判面）（无归属）

## 三、阻塞（6 项断言红 / 3 台机不一致）

- 断言 I1：5 条
- 断言 I2：111 条
- 断言 I3：18 条
- 断言 I4：9 条
- 断言 I12：4 条
- 断言 I14：2 条
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H
- 机器 bm-m：IDLE-WITH-QUEUE

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 83.7，返工 8，产出年龄 1.7
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 2.2
- bigstream-duanju：过闸率 62.5，返工 3，产出年龄 91.6
- biggame：过闸率 100.0，返工 0，产出年龄 None
- asset-lib：过闸率 None，返工 0，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

# 交接一屏（2026-11-05 18:31）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（28 张）

- `CHK-DUPES-20261103` 重复派单向量重扫（bm-m 兜底体检）（bm-m，45 分钟租约）
- `CANARY-20261104T132721` 端到端自检：投卡→领取→执行→回执→产物（bm-c，45 分钟租约）
- `MV-NEWPROC-PACKET-20261104` 导演席新流程卷：四曲立意/分镜/合规矩阵一页卷（bm-b，45 分钟租约）
- `AUD-SOFT-20261105T181824-09` 软著材料清点：G15_PetWorkCrew（bm-c，45 分钟租约）
- `AUD-SOFT-20261105T181824-10` 软著材料清点：G15_萌宠开店啦_CCPC提交格式（bm-c，45 分钟租约）
- `AUD-SOFT-20261105T181824-11` 软著材料清点：G16_CrazyEstate（bm-c，45 分钟租约）
- `AUD-SOFT-20261105T181824-12` 软著材料清点：G16_我有一栋楼_CCPC提交格式（bm-c，45 分钟租约）
- `AUD-SOFT-20261105T181824-14` 软著材料清点：G18_PalacePlunder（bm-b，45 分钟租约）
- `AUD-SOFT-20261105T181824-15` 软著材料清点：G19_BloomHaven（bm-b，45 分钟租约）
- `AUD-SOFT-20261105T181824-17` 软著材料清点：G20_MonsterInn（bm-b，45 分钟租约）

## 二、待判（16 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `CANARY-20261104T201032` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261104T202057` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `AUD-GAME-20261105T181824-25` 提审缺口落单：MonsterInn（biggame）
- `AUD-GAME-20261105T181824-26` 提审缺口落单：CardRogue（biggame）
- `AUD-GAME-20261105T181824-27` 提审缺口落单：ExileFarm（biggame）
- `AUD-GAME-20261105T181824-29` 提审缺口落单：LanternSlayer（biggame）
- `AUD-GAME-20261105T181824-30` 提审缺口落单：FateGate（biggame）
- `AUD-GAME-20261105T181824-31` 提审缺口落单：StrategistDefense（biggame）
- `AUD-GAME-20261105T181824-32` 提审缺口落单：DemonTamer（biggame）

## 三、阻塞（7 项断言红 / 2 台机不一致）

- 断言 I1：2 条
- 断言 I2：126 条
- 断言 I3：4 条
- 断言 I4：9 条
- 断言 I7：1 条
- 断言 I12：15 条
- 断言 I14：4 条
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 86.3，返工 16，产出年龄 30.4
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 0.0
- bigstream-duanju：过闸率 57.1，返工 3，产出年龄 143.8
- biggame：过闸率 66.7，返工 41，产出年龄 49.1
- asset-lib：过闸率 57.1，返工 24，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

# 交接一屏（2026-11-04 18:00）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（3 张）

- `biggame-playable-2026-11-03` [游戏（可上线清单 → 一款可玩包 → 提审材料）] 一款可玩包（3 关 60–90 秒，2D，儿童不作失败）（bm-m，45 分钟租约）
- `R-MODEL-RADAR-BMC-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-c）（bm-a，45 分钟租约）
- `bigstream-mv-transition-2026-11-04` [MV·爱在西元前（v721 终版）] 转场审计（逐切点方向余弦，OPPOSE 必须 0）（bm-c，45 分钟租约）

## 二、待判（33 张在队列等机器）

- `R-MODEL-RADAR-BMA-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-a）（无归属）
- `R-MODEL-RADAR-BMB-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-b）（无归属）
- `R-MODEL-RADAR-BMM-20261103` 本地模型日报：扫上游新档+实测+按两条判据决定是否换档（bm-m）（无归属）
- `CANARY-20261103T200141` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261103T201026` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `CANARY-20261103T221514` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）
- `R-PLAN-BIGCOMPUTE-20261104` BigCompute·硅基算力 线级体检与缺口清单（bigcompute）
- `R-PLAN-BIGDOMAIN-20261104` BigDomain·硅基域商业化 线级体检与缺口清单（bigdomain）
- `R-PLAN-BIGLIFE-20261104` BigLife·数字生命 线级体检与缺口清单（biglife）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）

## 三、阻塞（8 项断言红 / 3 台机不一致）

- 断言 I1：2 条
- 断言 I2：158 条
- 断言 I3：2 条
- 断言 I4：11 条
- 断言 I7：1 条
- 断言 I12：12 条
- 断言 I13：1 条
- 断言 I14：3 条
- 机器 bm-a：BUSY-NO-REPORT
- 机器 bm-b：IDLE-WITH-QUEUE
- 机器 bm-c：BUSY-NO-REPORT

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 76.6，返工 10，产出年龄 5.8
- bigstream-drama：过闸率 73.3，返工 7，产出年龄 5.8
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 119.2
- biggame：过闸率 75.0，返工 1，产出年龄 24.6
- asset-lib：过闸率 38.7，返工 20，产出年龄 0.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

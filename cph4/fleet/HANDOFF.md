# 交接一屏（2026-11-02 22:31）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（1 张）

- `R-TTS-QC-R2-20261102` 短剧配音全量质检（出可发布集数清单）（bm-b，45 分钟租约）

## 二、待判（2 张在队列等机器）

- `R-TRIAGE-BIGSTREAMDRAMA-BMC-20261102` BigStream·漫剧 线证据扫描（bm-c 本机可判面）（无归属）
- `CANARY-20261102T223137` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（5 项断言红 / 4 台机不一致）

- 断言 I1：6 条
- 断言 I2：118 条
- 断言 I3：18 条
- 断言 I4：12 条
- 断言 I14：2 条
- 机器 bm-a：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-b：BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-c：OFFLINE、BUSY-NO-REPORT、NO-RECEIPT-1H
- 机器 bm-m：IDLE-WITH-QUEUE

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 83.3，返工 7，产出年龄 3.0
- bigstream-drama：过闸率 71.4，返工 7，产出年龄 75.7
- bigstream-duanju：过闸率 100.0，返工 2，产出年龄 75.7

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

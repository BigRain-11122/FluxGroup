# 交接一屏（2026-11-03 00:08）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（3 张）

- `R-PLAN-BIGMONEY-20261103` BigMoney·量化 线级体检与缺口清单（bm-a，45 分钟租约）
- `R-PLAN-RECON-20261103` RECON·竞品拆解 线级体检与缺口清单（bm-b，45 分钟租约）
- `R-TRIAGE-BIGSTREAMMV-BMC-20261103` BigStream·MV 41 曲 线证据扫描（bm-c 本机可判面）（bm-m，45 分钟租约）

## 二、待判（11 张在队列等机器）

- `R-TRIAGE-BIGSTREAMDRAMA-BMC-20261102` BigStream·漫剧 线证据扫描（bm-c 本机可判面）（无归属）
- `Q-TRIAGE-BIGSTREAMDUANJU-20261103` bigstream-duanju 线级体检（本机证据目录实况）（无归属）
- `Q-TRIAGE-BIGGAME-20261103` biggame 线级体检（本机证据目录实况）（无归属）
- `Q-TRIAGE-FLUXVERSE-20261103` fluxverse 线级体检（本机证据目录实况）（无归属）
- `R-TRIAGE-BIGSTREAMDUANJU-BMM-20261103` BigStream·短剧 线证据扫描（bm-m 本机可判面）（无归属）
- `R-TRIAGE-BIGGAME-BMM-20261103` Biggame·游戏 线证据扫描（bm-m 本机可判面）（无归属）
- `R-TRIAGE-FLUXVERSE-BMM-20261103` FluxVerse·元宙城 线证据扫描（bm-m 本机可判面）（无归属）
- `R-PLAN-BIGSTREAMDRA-20261103` BigStream·漫剧 线级体检与缺口清单（bigstream-drama）
- `R-PLAN-BIGSTREAMDUA-20261103` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `R-TRIAGE-BIGMONEY-BMM-20261103` BigMoney·量化 线证据扫描（bm-m 本机可判面）（无归属）

## 三、阻塞（5 项断言红 / 3 台机不一致）

- 断言 I1：6 条
- 断言 I2：118 条
- 断言 I3：18 条
- 断言 I4：12 条
- 断言 I14：2 条
- 机器 bm-a：IDLE-WITH-QUEUE
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-m：IDLE-WITH-QUEUE

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 83.3，返工 7，产出年龄 4.6
- bigstream-drama：过闸率 62.5，返工 7，产出年龄 77.3
- bigstream-duanju：过闸率 50.0，返工 2，产出年龄 77.3
- biggame：过闸率 0.0，返工 0，产出年龄 None

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

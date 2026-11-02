# 交接一屏（2026-11-03 00:38）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（2 张）

- `C-TTS-QC-ALL` 短剧配音全量质检（逐集时长/静音/体积 → 可发布集数清单）（bm-a，45 分钟租约）
- `R-TRIAGE-BIGGAME-BMM-20261103` Biggame·游戏 线证据扫描（bm-m 本机可判面）（bm-m，45 分钟租约）

## 二、待判（8 张在队列等机器）

- `R-TRIAGE-BIGSTREAMDRAMA-BMC-20261102` BigStream·漫剧 线证据扫描（bm-c 本机可判面）（无归属）
- `R-TRIAGE-FLUXVERSE-BMM-20261103` FluxVerse·元宙城 线证据扫描（bm-m 本机可判面）（无归属）
- `R-PLAN-BIGSTREAMDRA-20261103` BigStream·漫剧 线级体检与缺口清单（bigstream-drama）
- `R-PLAN-BIGSTREAMDUA-20261103` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `R-TRIAGE-BIGMONEY-BMM-20261103` BigMoney·量化 线证据扫描（bm-m 本机可判面）（无归属）
- `R-TRIAGE-BIGDOMAIN-BMA-20261103` BigDomain·硅基域商业化 线证据扫描（bm-a 本机可判面）（无归属）
- `R-TRIAGE-FLEETOPS-BMA-20261103` 机队运维·端到端自检（平台服务线） 线证据扫描（bm-a 本机可判面）（无归属）
- `CANARY-20261103T003807` 端到端自检：投卡→领取→执行→回执→产物（fleet-ops）

## 三、阻塞（6 项断言红 / 2 台机不一致）

- 断言 I1：6 条
- 断言 I2：118 条
- 断言 I3：18 条
- 断言 I4：12 条
- 断言 I13：1 条
- 断言 I14：2 条
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：IDLE-WITH-QUEUE

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 83.3，返工 7，产出年龄 5.2
- bigstream-drama：过闸率 75.0，返工 7，产出年龄 77.8
- bigstream-duanju：过闸率 50.0，返工 3，产出年龄 77.8
- biggame：过闸率 100.0，返工 0，产出年龄 None

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

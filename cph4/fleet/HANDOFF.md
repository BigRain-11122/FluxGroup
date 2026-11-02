# 交接一屏（2026-11-03 00:32）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（2 张）

- `C-TTS-QC-ALL` 短剧配音全量质检（逐集时长/静音/体积 → 可发布集数清单）（bm-a，45 分钟租约）
- `R-NEXT-BIGSTREAMD-TTS-QC-20261103` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bm-b，45 分钟租约）

## 二、待判（10 张在队列等机器）

- `R-TRIAGE-BIGSTREAMDRAMA-BMC-20261102` BigStream·漫剧 线证据扫描（bm-c 本机可判面）（无归属）
- `Q-TRIAGE-FLUXVERSE-20261103` fluxverse 线级体检（本机证据目录实况）（无归属）
- `R-TRIAGE-BIGSTREAMDUANJU-BMM-20261103` BigStream·短剧 线证据扫描（bm-m 本机可判面）（无归属）
- `R-TRIAGE-BIGGAME-BMM-20261103` Biggame·游戏 线证据扫描（bm-m 本机可判面）（无归属）
- `R-TRIAGE-FLUXVERSE-BMM-20261103` FluxVerse·元宙城 线证据扫描（bm-m 本机可判面）（无归属）
- `R-PLAN-BIGSTREAMDRA-20261103` BigStream·漫剧 线级体检与缺口清单（bigstream-drama）
- `R-PLAN-BIGSTREAMDUA-20261103` BigStream·短剧 线级体检与缺口清单（bigstream-duanju）
- `R-TRIAGE-BIGMONEY-BMM-20261103` BigMoney·量化 线证据扫描（bm-m 本机可判面）（无归属）
- `R-TRIAGE-BIGDOMAIN-BMA-20261103` BigDomain·硅基域商业化 线证据扫描（bm-a 本机可判面）（无归属）
- `R-TRIAGE-FLEETOPS-BMA-20261103` 机队运维·端到端自检（平台服务线） 线证据扫描（bm-a 本机可判面）（无归属）

## 三、阻塞（5 项断言红 / 2 台机不一致）

- 断言 I1：5 条
- 断言 I2：118 条
- 断言 I3：18 条
- 断言 I4：9 条
- 断言 I14：2 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：NO-RECEIPT-1H

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 83.3，返工 7，产出年龄 5.0
- bigstream-drama：过闸率 75.0，返工 7，产出年龄 77.7
- bigstream-duanju：过闸率 66.7，返工 2，产出年龄 77.7
- biggame：过闸率 0.0，返工 0，产出年龄 None

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

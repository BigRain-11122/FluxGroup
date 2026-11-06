# 交接一屏（2026-11-06 16:53）

> 新会话先读这一页，再看具体文件。四段：在产 / 待判 / 阻塞 / 下一步。

## 一、在产（0 张）


## 二、待判（13 张在队列等机器）

- `R-NEXT-BIGSTREAMD-TTS-QC-20261104` 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）（bigstream-duanju）
- `OPS-CLOCK-RESYNC-BMB-20261105` None（无归属）
- `FREE-MEM-DIAG-bm-c-20261106` None（无归属）
- `Q-MV-ANCHOR-WORDS-DRAIN-20261106` None（无归属）
- `R-NEXT-BIGSTREAMD-EVIDENCE-20261106` 漫剧证据目录补齐判定：画面/配音工段为何为空（一页含根因与补法）（bigstream-drama）
- `biggame-pack-scan-2026-11-06` None（无归属）
- `asset-lib-voice-corpus-2026-11-06` None（无归属）
- `bigmoney-backtest-2026-11-06` None（无归属）
- `asset-lib-asset-gen-2026-11-06` None（无归属）
- `asset-lib-asset-gen-scenes-2026-11-06` None（无归属）

## 三、阻塞（8 项断言红 / 4 台机不一致）

- 断言 I1：5 条
- 断言 I3：55 条
- 断言 I4：18 条
- 断言 I6：7 条
- 断言 I7：3 条
- 断言 I12：27 条
- 断言 I13：1 条
- 断言 I14：3 条
- 机器 bm-a：NO-RECEIPT-1H
- 机器 bm-b：NO-RECEIPT-1H
- 机器 bm-c：NO-RECEIPT-1H
- 机器 bm-m：IDLE-WITH-QUEUE

## 四、下一步（P0 两线）

- bigstream-mv：过闸率 87.0，返工 15，产出年龄 6.1
- bigstream-drama：过闸率 53.3，返工 7，产出年龄 6.1
- bigstream-duanju：过闸率 71.4，返工 3，产出年龄 166.1
- biggame：过闸率 82.9，返工 47，产出年龄 71.5
- asset-lib：过闸率 62.2，返工 17，产出年龄 6.0

## 五、已发布（0 条）

- 还没有任何发布

---
生成：`Tools/fleet/handoff.py`；数据来源：队列/断言/通信/计分/发布台账。

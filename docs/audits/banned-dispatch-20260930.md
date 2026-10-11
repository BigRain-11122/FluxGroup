# 禁开方向命中件派工单（D-20260930-41 §1.2）

> 生成 2026-09-30 17:45｜窗口 30 天｜命中 18 件
> **裁定（外审拍板）**：命中不等于判死。每件有 **7 天**补例外论证（**新数据** 或 **新机制论证** ＋引用 BAN 编号）。到期未补 = 判不受理，已烧格数计入浪费。
> 理由：直接判死会把真创新一起误杀。

## 汇总

| 方向 | 命中件数 |
|---|---|
| BAN-01 ETF cross-sectional momentum | 7 |
| BAN-04 Grid trading | 3 |
| BAN-07 Small-cap / low-price factor | 3 |
| BAN-03 Single-name timing reversal or momentum at 5/10/20 days | 2 |
| BAN-02 ETF cross-sectional reversal | 1 |
| BAN-05 Market-temperature / breadth timing as a precondition | 1 |
| BAN-09 Style persistence / chasing the prior year's winning style | 1 |

## 派工明细

| 件 | 命中 | 需补 | 时限 |
|---|---|---|---|
| `quant/bigmoney/research/FACTOR_BLEND.md` | BAN-01 | supply exception statement: new_data or new_mechanism + cite BAN-01 | 7 天 |
| `quant/bigmoney/research/FACTOR_BLEND_V2.md` | BAN-01 | supply exception statement: new_data or new_mechanism + cite BAN-01 | 7 天 |
| `quant/bigmoney/research/RETAIL_QUANT_TRACK.md` | BAN-01 | supply exception statement: new_data or new_mechanism + cite BAN-01 | 7 天 |
| `quant/bigmoney/research/STRATEGY_SYSTEM_V3.md` | BAN-01 | supply exception statement: new_data or new_mechanism + cite BAN-01 | 7 天 |
| `quant/bigmoney/research/SYSTEM_LOGIC.md` | BAN-01 | supply exception statement: new_data or new_mechanism + cite BAN-01 | 7 天 |
| `quant/bigmoney/research/digests/DIGEST-20260925-ssrn-crossref-academic-sweep.md` | BAN-01 | supply exception statement: new_data or new_mechanism + cite BAN-01 | 7 天 |
| `quant/bigmoney/research/shortline/ASTYLE_ZOO.md` | BAN-01 | supply exception statement: new_data or new_mechanism + cite BAN-01 | 7 天 |
| `quant/bigmoney/research/RETAIL_QUANT_TRACK.md` | BAN-02 | supply exception statement: new_data or new_mechanism + cite BAN-02 | 7 天 |
| `quant/bigmoney/research/digests/DIGEST-20260925-wave7-slice5.md` | BAN-03 | supply exception statement: new_data or new_mechanism + cite BAN-03 | 7 天 |
| `quant/bigmoney/research/digests/DIGEST-20260925-wave8-slice2.md` | BAN-03 | supply exception statement: new_data or new_mechanism + cite BAN-03 | 7 天 |
| `quant/bigmoney/research/EXIT_OVERLAY_P1.md` | BAN-04 | supply exception statement: new_data or new_mechanism + cite BAN-04 | 7 天 |
| `quant/bigmoney/research/ORDERS_INDEX.md` | BAN-04 | supply exception statement: new_data or new_mechanism + cite BAN-04 | 7 天 |
| `quant/bigmoney/research/shortline/P4_BATCH2A.md` | BAN-04 | supply exception statement: new_data or new_mechanism + cite BAN-04 | 7 天 |
| `quant/bigmoney/research/RETAIL_QUANT_TRACK.md` | BAN-05 | supply exception statement: new_data or new_mechanism + cite BAN-05 | 7 天 |
| `quant/bigmoney/research/digests/DIGEST-20260924-wave3.md` | BAN-07 | supply exception statement: new_data or new_mechanism + cite BAN-07 | 7 天 |
| `quant/bigmoney/research/digests/DIGEST-20260925-wave4-slice10.md` | BAN-07 | supply exception statement: new_data or new_mechanism + cite BAN-07 | 7 天 |
| `quant/bigmoney/research/digests/DIGEST-20260925-wave5-slice2.md` | BAN-07 | supply exception statement: new_data or new_mechanism + cite BAN-07 | 7 天 |
| `quant/bigmoney/research/RETAIL_QUANT_TRACK.md` | BAN-09 | supply exception statement: new_data or new_mechanism + cite BAN-09 | 7 天 |

## 复跑

```
python Tools/banned_dispatch.py --days 30
```

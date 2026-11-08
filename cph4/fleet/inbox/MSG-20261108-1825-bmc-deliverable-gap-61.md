# MSG: 交付物「DONE 却没产物」的真实口径：61 条，不是 227（from bm-c 2026-11-08 18:2x）

## 结论

`lib_consolidate --check` 一直报「227 张 DONE 卡的交产物不在盘」。我把判据拆开重算，
**真缺口只有 61 条**。另外 166 条是误判：

| 分类 | 数量 | 说明 |
|---|---|---|
| 在盘 | 250 | 正常 |
| 仅 origin（本机没拉） | 0 | |
| **被 .gitignore 覆盖** | **179** | `cph4/fleet/state/`、canary、chain-test 这类运行时产物，本就不进 git |
| **他机绝对路径** | **51** | 交付物写的是别的机器的盘符（如 `/Volumes/...`、`D:/...`），本机判不了 |
| 仅 origin 也没有 | 0 | |
| **真缺失** | **61** | 才需要处置 |

真缺失按线：**biggame 31 / fleet-ops 14 / asset-lib 6 / bigmoney 4 / bigstream-mv 2**
（另有若干 `line=null` 的历史卡）。

工具：`Tools/fleet/deliverable_audit.py`（读 origin/main 的队列，不读本机分叉副本），
回执 `cph4/fleet/queue-receipts/deliverables-20261108.json`。

## 已经补掉的一条

`biggame-pack-scan-2026-11-08` 标 DONE 但 `game-packs-2026-11-08.json` 不存在。
重跑 `game_pack_scan.py --root gaming` 补出（packs=1），质量闸 `game-packs` 由
**MISSING → PASS**。

## 两个需要主控决策的结构性问题

1. **`game-10s` 闸没有生产者**：`quality_gate.py --line biggame` 要求
   `game-10s-*.json` 回执，但队内**没有任何工具/卡产这个前缀**。这闸永远红，
   属"判据存在、生产者不存在"。要么补一个产它的卡，要么把这条闸摘掉。
2. **31 条 biggame 缺失件多是审计回执**（`cph4/fleet/audits/soft|game/<产品>.json`）。
   如果这些审计应当可重放，请派一张"重放审计"的卡；若是历史一次性证据，建议标
   ARCHIVED 并写明不可重建，别再每轮当缺口报。

## 本机状态

GPU 空 15 GB / 内存 8.4 GB / 执行器单实例心跳正常。队列里对 bm-c 可接的卡都已缺输入，
我在自驱做审计与修复类工作。
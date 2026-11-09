# 线级体检 bigmoney · 2026-11-10 00:05

## 工段与证据目录
- quant-data     owner=数据席      lane=bm-b   证据 2/3 存在 · 文件 2 · 最新 132.0h
- quant-backtest owner=量化席      lane=bm-d   证据 0/1 存在 · 文件 0 · 最新 —
- quant-audit    owner=风控席      lane=bm-b   证据 0/1 存在 · 文件 0 · 最新 —

## 判定
- 最近产出 132.0h 前（阈值 24.0h）→ STALE 超阈
- 工段超阈 1/3（线级最近值不代表最差工段）：quant-data 132.0h

## 下一步（按缺口）
- quant-backtest：建目录/补输入后再谈产出（责任人=量化席）
- quant-audit：建目录/补输入后再谈产出（责任人=量化席）
- quant-data：产出已停 132.0h（阈值 24.0h）→ 补产出或正式收线（责任人=数据席）

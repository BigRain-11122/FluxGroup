# 线级体检 bigmoney · 2026-11-15 01:05

## 工段与证据目录
- quant-data     owner=数据席      lane=bm-b   证据 3/3 存在 · 文件 18619 · 最新 28.8h
- quant-backtest owner=量化席      lane=bm-d   证据 1/1 存在 · 文件 25769 · 最新 0.9h
- quant-audit    owner=风控席      lane=bm-b   证据 1/1 存在 · 文件 1 · 最新 529.8h

## 判定
- 最近产出 0.9h 前（阈值 24.0h）→ FRESH 在阈内
- 工段超阈 2/3（线级最近值不代表最差工段）：quant-data 28.8h、quant-audit 529.8h

## 下一步（按缺口）
- quant-data：产出已停 28.8h（阈值 24.0h）→ 补产出或正式收线（责任人=数据席）
- quant-audit：产出已停 529.8h（阈值 24.0h）→ 补产出或正式收线（责任人=风控席）

# m-w3-settle · 状态结算

- **域**：世界　**状态**：building　**owner**：未指派
- **职责**：从事件流回放，算出每块区域的 positivity 与状态；可随时重建
- **输入**：events.jsonl
- **输出**：state.json
- **独占写**：modules/m-w3-settle/data/state.json
- **怎么跑**：`python modules/m-w3-settle/settle.py`
- **怎么验**：`python tools/world_ops.py validate`
- **下一步**：把年龄/人口变化也纳入结算

## 不许做
- 不改其他模块目录（只写上面「独占写」里的路径）
- 不私改 `CONTRACTS/`
- 不用手写结果冒充跑出来的结果

## 交接
三行：改了哪些文件 / 一条命令怎么跑 / 一条命令怎么验（贴退出码）。

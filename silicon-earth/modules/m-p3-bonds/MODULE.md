# m-p3-bonds · 关系与相助

- **域**：人　**状态**：usable　**owner**：bm-c（v0.1 · 2026-11-27）
- **职责**：谁帮过谁、谁欠谁、谁会来
- **输入**：帮助类事件（help / teach / repair）
- **输出**：bonds.json —— 成对关系账，**欠与还分开记，不互相抵消**
- **独占写**：`modules/m-p3-bonds/data/bonds.json`、`bonds.py`、`check.py`
- **怎么跑**：`python modules/m-p3-bonds/bonds.py`
- **怎么验**：`python modules/m-p3-bonds/check.py`（rc=0 才算过）
- **下一步**：加「谁会来」——净欠方在缺人时先被求助

## 口径（改口径＝改契约，须走总控）

| 项 | 规则 |
|---|---|
| 谁的活 | `help` / `teach` / `repair`，且 `actors` 至少两人 |
| 谁给谁 | `actors[0]` 出手（给），`actors[1]` 受助（收） |
| 记法 | 一对人一条账；两个方向各记次数，**不抵消** |
| 净欠 | `net_creditor` = 净给出更多的一方；两边一样多＝`null`（平账） |
| 覆盖 | 每次帮助事件恰好记进一条账，事件 id 留指针（每对最多 20 条） |
| 不信自己 | `check.py` **独立重算**事件流再对账，不复用 `bonds.py` 的代码 |

## 不许做
- 不改其他模块目录（只写上面「独占写」里的路径）
- 不私改 `CONTRACTS/`
- 不手写 `bonds.json` 冒充跑出来的结果

## 交接
三行：改了哪些文件 / 一条命令怎么跑 / 一条命令怎么验（贴退出码）。

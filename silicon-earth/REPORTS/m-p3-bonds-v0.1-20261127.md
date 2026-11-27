# m-p3-bonds v0.1 交付记录（2026-11-27 · bm-c）

## 一 改了哪些文件

| 文件 | 性质 | 说明 |
|---|---|---|
| `modules/m-p3-bonds/bonds.py` | 新增 | 相助记账：从 events.jsonl 回放，`actors[0]` 给 `actors[1]`，欠与还分开记 |
| `modules/m-p3-bonds/check.py` | 新增 | 验收闸：**独立重算**事件流再对账（不复用 bonds.py 的实现） |
| `modules/m-p3-bonds/module.json` | 改 | `status: empty → usable`，补 run/verify/owner/next，writes 扩到三件 |
| `modules/m-p3-bonds/MODULE.md` | 改 | 口径表 + 独写路径 + 交接三行 |
| `TASKS.json` | 改 | 新增 **T13 相助记账从事件流可重算**（P1，todo，待总控领取或并入） |
| `CONTRACTS/verify.json` | 改 | T13 权威验收命令 |
| `CONTRACTS/acceptance.json` | 改 | T13 权威验收标准（与任务板逐字一致，否则 validate 拦） |

数据产物 `modules/m-p3-bonds/data/bonds.json` **不提交**：它是派生件，与 state/memory 同口径（由脚本重建，不入库）。

## 二 一条命令怎么跑

```
python modules/m-p3-bonds/bonds.py
```
第 573 天实跑输出：`315 次出手 · 289 对关系（还过 12 / 单向 277）`；常出手 P0702 / P0801 / P20164 各 5 次。

## 三 一条命令怎么验

```
python modules/m-p3-bonds/check.py
```
rc=0 才算过。判据六条：覆盖（每次帮助事件恰好记进一条账）· 外键（两人都在 people.json）· 事件锚（引用的事件 id 真实存在）· 逐条重算一致 · net/net_creditor/repaid 自洽 · 无自指无重复对。

本次实测：`PASS 关系账 · 315 次出手 · 289 对 · 还过 12 · 单向 277 · 覆盖 315/315` → **rc=0**

## 四 负控（证明闸不是摆设）

| 负控 | 造假手法 | 结果 |
|---|---|---|
| 1 | 把某对关系的一方次数 +1（与事件流不符） | **rc=1**：`['P0101','P0102'] 计数与事件流不符：账 2/0 vs 重算 1/0` |
| 2 | 把一对外键改成 `P99999` | **rc=1**：`账里的外键不存在：['P0101','P99999']` |
| 复原 | 换回真账 | rc=0 PASS |

## 五 回归面

- `python tools/ready.py` → 10/10 全过
- `python tools/world_ops.py validate` → rc=0（22 模块 · 契约 · 单写者 · 外键 · 事件流全过；可执行模块 11 → **12**）
- `python tools/sim_test.py` → 10/10 PASS（T7「非空模块 run/verify 齐备」仍过）

## 六 口径备忘（改口径＝改契约，须走总控）

- 帮助类 = `help` / `teach` / `repair`，且 `actors` 至少两人
- `actors[0]` 出手、`actors[1]` 受助；一对人一条账，两个方向**不抵消**
- `net_creditor` = 净给出更多的一方；平账为 `null`
- 每对最多留 20 条事件指针，账本不复制事件全文（引用不复制）

## 七 待办 / 边界

- T13 在板上是 `todo`，本次未走 claim/deliver 仪式（本机是镜像工作树 + 非本仓分支树，`deliver.py` 的 git 改动面判据在此形态下会误判），故以「分支 + 本记录」交付；总控领取后可直接跑上面两条命令复核。
- 世界仍是**单写者**：本机只跑只读派生（bonds），不推进 `engine.py`；advance 世界仍归 delivery。

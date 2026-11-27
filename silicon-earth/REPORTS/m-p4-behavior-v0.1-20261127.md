# m-p4-behavior v0.1 交付记录（2026-11-27 · bm-c）

## 一 改了哪些文件

| 文件 | 性质 | 说明 |
|---|---|---|
| `modules/m-p4-behavior/behavior.py` | 新增 | 规则版行为：修 > 还 > 帮 > 守 |
| `modules/m-p4-behavior/check.py` | 新增 | 验收闸：**独立重算**每人动作与目标，逐人比对 |
| `modules/m-p4-behavior/module.json` | 改 | `empty → usable`，补 run/verify/owner/next |
| `modules/m-p4-behavior/MODULE.md` | 改 | 规则表 + ties 规则 + 独写路径 |
| `TASKS.json` | 改 | 新增 **T14 行为规则版可重算可对账**（P1，依赖 T13） |
| `CONTRACTS/verify.json` | 改 | T14 权威验收命令 |
| `CONTRACTS/acceptance.json` | 改 | T14 权威验收标准（与任务板逐字一致） |

`modules/m-p4-behavior/data/behavior.json` 是派生件，**不入库**（同 bonds/state 口径）。

## 二 一条命令怎么跑

```
python modules/m-p4-behavior/behavior.py
```
第 573 天实跑：`12361 人 → 修 21 · 还 209 · 帮 205 · 守 11926`

## 三 一条命令怎么验

```
python modules/m-p4-behavior/check.py
```
判据：全量覆盖（每人恰好一条）· 动作四类限定 · **与独立重算逐人比对（动作 + 目标人）** · 还/帮的目标必须真实存在于关系账 · 四类计数与 summary 自洽。

本次实测：`PASS 行为 · 12361 人全覆盖 · 修 21 · 还 209 · 帮 205 · 守 11926` → **rc=0**

## 四 负控（三条都实打实被拦）

| 负控 | 造假手法 | 结果 |
|---|---|---|
| 1 | 把一个「守」改成「修」（他没有 lost 记忆） | **rc=1** `P0602: 判了修但其实没有 lost 记忆` |
| 2 | 把某条「还」的目标人换成另一个没有给过他的人 | **rc=1** `P0102: 还 的目标 P0102 并没有给过他` |
| 3 | 删掉最后一个人的行为 | **rc=1** `有 1 人没有任何行为（例：['P22334']）` |

负控 2 第一版（只查方向）没拦住——当时换的目标恰好就是原目标；正是这次空转促成了「逐人比对独立重算结果」这条更硬的判据。

## 五 回归面

- `python tools/world_ops.py validate` → rc=0（可执行模块 12 → **13**）
- `python tools/sim_test.py` → 10/10 PASS

## 六 口径备忘

| 动作 | 条件 | 目标 |
|---|---|---|
| 修 | 有 `lost` 记忆 | — |
| 还 | 收 − 给 ≥ 1 | 给过他的最多的那个人 |
| 帮 | 给 − 收 ≥ 1 | 他帮过的最多的那个人 |
| 守 | 其余 | —（理由=未了的事） |

ties：次数多者优先、同次数按 id 字典序 → 同输入必同输出。

## 七 边界

- 规则版**不接模型**；要接须新开契约（BACKLOG B8 只要求规则版先行）。
- 世界仍单写者：本机只跑只读派生，不推进 `engine.py`。

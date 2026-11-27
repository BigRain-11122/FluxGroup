# m-w4-history v0.1 交付记录（2026-11-27 · bm-c）

## 一 改了哪些文件

| 文件 | 性质 | 说明 |
|---|---|---|
| `modules/m-w4-history/history.py` | 新增 | 纪年：用 blackout/breach 划界，按段内主导区域命名 |
| `modules/m-w4-history/check.py` | 新增 | 验收闸：覆盖连续性、边界合法性、计数、可查证性 |
| `modules/m-w4-history/module.json` | 改 | `empty → usable`，补 run/verify/owner/next |
| `modules/m-w4-history/MODULE.md` | 改 | 口径表 + 实跑样本 + 独写路径 |
| `TASKS.json` | 改 | 新增 **T15 纪年可查可对账** |
| `CONTRACTS/verify.json` | 改 | T15 权威验收命令 |
| `CONTRACTS/acceptance.json` | 改 | T15 权威验收标准 |

`modules/m-w4-history/data/history.json` 为派生件，不入库。

## 二 一条命令怎么跑

```
python modules/m-w4-history/history.py
```
第 573 天实跑：`25 纪 · 573 条事件 · 24 个大事`；首纪 `1-11 1·裂谷的开城`，末纪 `565-573 25·协议洲的失守后`。

## 三 一条命令怎么验

```
python modules/m-w4-history/check.py
```
判据六条：首纪从第 1 天起、末纪到 time.day、纪间无缝无重、非首纪起点必须是黑屏/失守日、各纪事件数与实算一致、`dominant_region` 与名字里的区域名可查证、无空段无重名。

本次实测：`PASS 纪年 · 25 纪 · 覆盖 573/573 事件 · 末纪 25·协议洲的失守后` → **rc=0**

## 四 负控（三条都拦）

| 负控 | 造假手法 | 结果 |
|---|---|---|
| 1 | 把第 2 纪起点挪到不是大事的一天 | **rc=1** 事件数不符 + 起点非大事日 |
| 2 | 改第 3 纪的 dominant_region | **rc=1** `第 3 纪 dominant_region 应为 R02，实为 R09` |
| 3 | 给首纪事件数 +3 | **rc=1** `第 1 纪事件数 14 与实算 11 不符` |

## 五 回归面

- `python tools/world_ops.py validate` → rc=0（可执行模块 13 → **14**）
- `python tools/sim_test.py` → 10/10 PASS

## 六 边界

- 纪元名是**从事件流查出来的**（段号 + 主导区域 + 触发类型），不许另编故事；要写「这一纪留下什么」须另开一步，从该纪事件里挑代表事件。
- 世界单写者不变：本机只跑只读派生。

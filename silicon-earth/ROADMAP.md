# 推进路线（自动循环读这张表）

> 每行是一个可自动执行的步骤：`run` 干活，`verify` 判成败。
> 谁说下一步做什么？这张表。`tools/autoloop.py` 从上往下取第一个 `todo`。
> 一次只做一件；verify 不过就停，标 blocked，不硬闯。

| id | 标题 | run | verify | status |
|---|---|---|---|---|
| S1 | 户籍按区拆分，大文件出仓 | `python tools/split_census.py` | `python tools/world_ops.py validate` | done |
| S2 | 世界推进一天并刷新派生与总览 | `python tools/advance.py 1` | `python tools/world_ops.py validate` | done |
| S3 | 推进 200 天，让更多居民进入历史 | `python tools/advance.py 200` | `python tools/world_ops.py validate` | done |
| S4 | 日报改为按势力叙事 | 需要改 `m-b1-output/make.py` | `python modules/m-b1-output/check.py` | blocked |
| S5 | 覆盖率提升到 30% 以上 | `python tools/grow_coverage.py` | `python tools/check_coverage.py` | blocked |

说明：
- S4 需要写代码，留给交互会话或授权代理，自动循环不擅自改逻辑。
- S5 的上游是先有 `grow_coverage.py` 与 `check_coverage.py`；没有脚本就是 blocked，不是失败。

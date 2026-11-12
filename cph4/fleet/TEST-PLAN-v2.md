# 测试目录与缺口（TEST-PLAN v2）· 2026-11-12

> 生成物：`python3 Tools/fleet/test_catalog.py --write`。改测试请改模块，不要手改本文件。
> 跑法：`python3 Tools/fleet/run_all_tests.py`（全量）｜`python3 Tools/fleet/quality_score.py`（算分）

## 一、分层面（跑什么）

| 层 | 内容 |
|---|---|
| L0 回归用例 | 回归用例 RG-* |
| L1 单元自检 | shards 分片/锁、drive 自驱、panel 评审团、agent 席位、local loop 本地闭环、view 一屏、cmd 命令面、work matrix 颗粒度、drama rules 漫剧闸、voice gate 语感、make index 索引、os matrix 跨系统、cpu alloc 分配、env probe 环境采集、env align 环境对齐、fleet doc 文档生成、compute alloc 算力调度、brain stress 端点阶梯、quality score 评分器、self loop 回环、condition matrix 环境矩阵、parallel sim 并发模型、cmd latency 命令通道、docs curate 文档整理、automation plan 排班校验、identity 身份唯一权威、state machine 状态机权威、drive agent 执行体生成 |
| L2 场景与条件 | 工况 QA 12 例、鲁棒性 10 例、条件矩阵 80 格、并发争用模型、命令下发延迟、预演 14 场景 |
| L3 一致性/文档 | 一致性 17 项、情况台账、文档库/正典指针、深度审计（P0 才判红）、测试目录新鲜、文档与配置一致 |
| L4 总评分 | 总评分 |

## 二、用例面（各多少例）

| 模块 | 例数 | 覆盖什么 |
|---|---|---|
| `regression.CASES` | 38 | 历史故障固化的回归断言（每条带负控） |
| `station_qa.CASES` | 12 | 机内执行工况：停/离线/无命令/人判/低盘/坏卡 |
| `fleet_rehearsal.SCEN` | 14 | 跨机流转预演：交接/重复/离线/回执/漂移 |
| `robustness_suite.CASES` | 17 | 存储与数据面：并发写/崩溃/坏行/状态机/数量级 |
| `condition_matrix`（生成） | 80（环境 55 / 核力 10 / 系统 15） | 5 台机 × 环境偏差 × 核力禁区 |
| `parallel_sim`（生成） | 4 组合 | 单端点平摊/突发 × 有/无深席上升 |

## 三、还没覆盖的（缺口，按优先级）

| # | 缺口 | 为什么重要 |
|---|---|---|
| 1 | 真 Windows 执行 | 三台生产机的命令只在沙箱里模拟过，没有一次真机跑通用例 |
| 2 | 真 GPU 出片 | ComfyUI/i2v 链路没有端到端跑过（无在线 GPU 机） |
| 3 | 真实网络分区 | 只模拟了端点不可达，没测过 tailnet 抖动/半连通下的重试风暴 |
| 4 | 长跑 24h | 所有用例都是秒级；没有 24h 稳定性（内存泄漏/句柄泄漏）观测 |
| 5 | 断电恢复 | 只测了半截文件，没测过 fsync 掉电后分片与回执的一致性 |
| 6 | 大素材 IO | 1000 张卡测了，但没测 GB 级产物搬运与哈希的时间预算 |
| 7 | 多机并发写同一分片 | 单机并发测了；跨机同写不该发生，但没有闸去拦 |
| 8 | 权限与越权 | 只测了「不对外」的字面约束，没测凭据文件权限与越权路径 |

## 四、循环与迭代（怎么转起来）

1. `run_all_tests.py` 全量跑一遍（层内失败继续跑完再汇总）。
2. 失败项先分「真故障」与「状态未达标」，后者不改口径不刷分。
3. 真故障走：定根因 → 改成断言 → 加负控（能判「该红必须红」）→ 重跑全量。
4. `self_loop.py` 自动修登记过的确定性项（文档漂移、本机探针），其余留给人判。
5. 每轮分数与残余阻塞写 `state/quality-history.jsonl`，趋势可查。

**退出条件**：全量 0 失败且 `quality_score` 只剩外部阻塞（服务暂停／机器离线／未装机）。

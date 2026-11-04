# OH-20261104-bigcompute — 开源收获轮（D-20261104-06 派单·本司断供 15 天后补件）

- 实体：BigCompute（硅基算力）
- 派单依据：`docs/decisions.md` D-20261104-06（2026-11-04 09:1x 夜轮补班）→「其余七实体 11-06 12:00 前各一件，四栏齐」
- 本司上一件：`OH-20261020-bigcompute.md`（10-20 03:24），其后零件
- 窗口：2026-11-04 19:0x（窗内提前 ≈17h）
- 写作纪律：D-20260927-03 唯一许可写盘面（本目录 append）；零商业动作；判负项留痕不删

---

## 一、实搜面（3 查·A 级 API 读取）

| # | 查询 | 结果 |
|---|---|---|
| Q1 | `psutil`（按星序） | total=1984；top: `shirou/gopsutil` 11,939★（Go 版 psutil·语言面判负）／`giampaolo/psutil` 11,316★／`amanusk/s-tui` 5,119★（GPL-2.0） |
| Q2 | `gpustat nvidia gpu monitoring` | total=2；`henry0312/datadog-gpustat` 7★（2019 停更）／`OpenMandrivaAssociation/python-gpustat` 0★（打包壳·3KB）——**真实 gpustat 主仓未被本查询命中**，如实记录检索面局限，不据此判负主仓 |
| Q3 | `gpu monitoring nvidia smi python stars:>500` | total=0（qualifier 组合语法无效）——**判负自身检索式**，不当作「无此类项目」的证据 |

> 检索面自评：3 查中 1 查有效、1 查偏、1 查语法失败。本件结论只建立在 **LICENSE 原文直验 + 本机实跑** 上，不建立在星数排序上。

---

## 二、切片一：`giampaolo/psutil`（复用面·非新采用）

| 栏 | 内容 |
|---|---|
| **发现** | 本司 `Tools/gpu_idle_collector.py` L699-702 / L934-936 **已在用** `psutil.cpu_percent(interval=1)` + `virtual_memory()`；同一台机的 `Tools/idle_selfcheck.py` L189-191 却走 `powershell → Get-CimInstance Win32_Processor → LoadPercentage`。**同一物理量在司内有两把尺子**，而 `py_cpu` 字段正是 O-20261013-2215「py≥70% 验收线」哨兵的数据源 |
| **星数** | 11,316★／fork 1,539／open issues 286／pushed 2026-11-04（当日活跃）／Python |
| **许可** | `BSD-3-Clause`（GitHub license API 直读 `spdx_id=bsd-3-clause`）。五门过：契合（系统读数）✓／反重复（已在本司依赖树，**复用非新增**）✓／许可（BSD-3 商用可·需保留版权声明）✓／健康（当日提交·主仓维护中）✓／成本安全（纯本地进程内读取·零网络零上传）✓ |
| **接入结论** | **复用（无需新增依赖）**。本轮增量不是「引入库」，而是把两通道拉到同一张桌上实测——见第三节 |

---

## 三、切片一的可跑验证件（本件实际交付物）

`Tools/cpu_read_ab_probe.py`（selftest 11/11 PASS；实跑证据 `state/cpu-read-ab-20261104.json`）

- 设计三律：psutil 缺失 → `PSUTIL-ABSENT` 不判负；子进程失败 → `SHELL-FAILED` 显式点名 rc；任一通道 None → `READ-UNAVAILABLE`，**禁止用 0 填充后参与比较**
- 实跑（bm-a·19:0x·5 轮·psutil 采样窗 1.0s）：

| 通道 | 中位读数 | 中位耗时 |
|---|---|---|
| PowerShell `LoadPercentage` | **64.0%** | 1.415 s |
| `psutil.cpu_percent(1.0)` | **20.6%** | 1.001 s |

  → `verdict=DIVERGENT` delta=**43.4pp**（阈 15pp），加速比 1.4×；逐轮 shell `[52,67,68,64,45]` / psutil `[30.9,20.6,34.5,16.6,17.0]`

- **如实边界（三条，缺一条即结论无效）**：
  1. 两通道**语义本就不同**：`LoadPercentage` 为瞬时值，`psutil.cpu_percent(interval)` 为区间均值。差 43pp 不证明任何一方「错」。
  2. 存在**自干扰候选解释**：powershell.exe 冷启本身占用 CPU，恰好落在 `LoadPercentage` 的瞬时采样窗内，可能抬高读数。本轮未做隔离实验，故**不作因果断言**。
  3. 结论**不跨机外推**：单机单窗 5 轮，静置与满载两种工况都未覆盖。

- 对判据面的直接含义（只提问题，不改判据）：O-2215 的 `py_cpu` 若换通道，同一台机的「繁忙度」读数可位移 40pp 量级——**70% 这条线挂在哪把尺子上，必须先钉死再谈验收**。已登记提案 BC-P-189（通道单源化 + 双通道并排读数 + 隔离实验预注册），本件不改代码。

---

## 四、切片二/三：判负留痕

| 候选 | 星数 | 许可 | 接入结论 |
|---|---|---|---|
| `shirou/gopsutil` | 11,939★ | license=Other/NOASSERTION（**未断言**，需人工读原文） | **不接入**：Go 实现，本司工具链为 Python；语言面判负，且许可未断言不支持自动采信 |
| `amanusk/s-tui` | 5,119★ | `GPL-2.0` | **不接入**：TUI 交互工具，非库形态；GPL-2.0 传染性对闭源产线不友好；能力面（终端压测+监控界面）与本司「静默无人值守」相悖 |
| `henry0312/datadog-gpustat` | 7★ | MIT | **不接入**：2019-10 停更（7 年）、依赖 Datadog Agent 与 python2 语境；健康门判负 |
| `OpenMandrivaAssociation/python-gpustat` | 0★ / 3KB | 未读（体量过小无实质） | **不接入**：发行版打包壳，非源仓；0★ 零社区信号 |

---

## 五、验证声明

- 星数/许可/活跃度：GitHub REST API 实读（3 查·A 级），非记忆转述。
- 许可：psutil 走 GitHub license API `spdx_id`；判负项同样按 API 字段落栏，未断言项如实标 `NOASSERTION`。
- 本机读数：`Tools/cpu_read_ab_probe.py run` 实跑 5 轮，输出全量落 `state/cpu-read-ab-20261104.json`（UTF-8 无 BOM）。
- **未做**：pynvml/nvidia-ml-py 方向（本机未装，且 nvidia-smi 单源为 O-20261006-2358 已定谳，不在本窗翻案）；gpustat 主仓（检索未命中，不臆测其许可与状态）。
- 判负项一律保留，不因「本轮没接入」删除条目。

---

## 六、应用表（可执行下游）

| # | 落点 | 动作 | 归属 |
|---|---|---|---|
| 1 | `Tools/cpu_read_ab_probe.py` | 已落盘·可复跑（`run`/`selftest`） | BigCompute |
| 2 | `state/cpu-read-ab-20261104.json` | A/B 原始读数证据 | BigCompute |
| 3 | BC-P-189 | `py_cpu` 通道单源化提案（并排读数 + 隔离实验 + 阈值标定前置） | 提案面候批 |
| 4 | 本件 §三 表 | 供 O-2215 满载哨兵判据面复核时直引 | HQ/委员会 |
| 5 | 派单回执 | D-20261104-06「其余七实体各一件」本司侧交付 | 已交本件 |
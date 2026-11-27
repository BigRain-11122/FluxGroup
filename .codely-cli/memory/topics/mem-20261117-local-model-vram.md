# 本地模型 / 显存 定案 · 2026-11-17

## 一、12G 卡（RTX 4070 SUPER）本地模型标定

同一提示词、`think=false`、UTF-8 直传（PowerShell `ConvertTo-Json` + `Invoke-RestMethod` 会吃掉中文，必须 `[Text.Encoding]::UTF8.GetBytes()`）。

| 配置 | 显存净占 | 解码速度 |
|---|---|---|
| qwen3.5:9b @16K 全 GPU | 6.6 G | 60.8 tok/s |
| qwen3.5:9b @8K 全 GPU | 6.1 G | 60+ tok/s |
| qwen3.5:9b @16K，28 层 GPU | — | 28.4 tok/s |
| qwen3.5:9b @16K，20 层 GPU | — | 14.1 tok/s |

**定案：全 GPU + `num_ctx=8192`。** 部分层落内存掉速一半以上，内存再充足也不划算。
（居民档案 2.3 KB、prompt 实测 4939 字符，8K 足够。）

## 二、Ollama `keep_alive=Forever` 的真实成因

`ollama ps` 显示 `UNTIL: Forever`，而用户环境变量 `OLLAMA_KEEP_ALIVE=5m` 管不住——**请求级参数覆盖服务端默认**。

根因不在调用方写死，而是一条兜底链：
1. BigLife 生成器 `evolve_citizen.seat()` 优先用 `BIGLIFE_LLM_URL`（默认 `:8090`）
2. 本机 `:8090` **无监听** → 落到 `_ollama_model()`
3. `_ollama_model()` 首选 `qwen3:4b-instruct`
4. 该模型在 16K 上下文下 2.5G 本体撑到 **7.5 GB**

同轮确认：`:8792` 是 BigCompute 的 `resident_qa_server`，**`Tools/fleet/llm_gateway.py` 本体未运行**（与 2026-11-16 那条「8792 端口表过期」一致）。

## 三、阈值定案：闸门必须给桌面留余量

`state/vram-gate.jsonl` 显示过去整天都在 **89–94%** 占用下判 `degraded` 并放行（`limit=0.90`），
即系统长期在「没有余量」的状态下硬跑——这会让所有需要 GPU 渲染的桌面应用不稳定。

改法：`vram_guard()` 默认值改为读 `BIGLIFE_VRAM_LIMIT`（默认仍 0.90，向后兼容），本机设 **0.82**。

## 四、配置清单（已落地）

| 位置 | 键 | 值 |
|---|---|---|
| `~/.codely-cli/settings.json` | `flashModel` | `qwen3.5:4b`（后台杂活走轻量档） |
| 用户环境变量 | `BIGLIFE_MODEL` | `qwen3.5:9b` |
| 用户环境变量 | `BIGLIFE_LLM_URL` | `http://127.0.0.1:11434/v1/chat/completions`（绕过已死的 8090） |
| 用户环境变量 | `BIGLIFE_VRAM_LIMIT` | `0.82` |

## 五、让路守护

`life/BigLife/Tools/wait_then_produce.py`（`pythonw` 静默无窗）：
按命令行匹配 `*_train_network.py` → 连续 3 轮无匹配判训练结束 → 等 120s → `free ≥ 6000 MiB` 才开跑，否则退避 10 分钟×8 次，**绝不硬挤**。
回执 `state/wait-produce.json`，日志 `state/wait-produce.log`。

## 六、工具坑（本次踩到）

1. **按进程拆显存只有一条路**：`Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory`（`Get-CimInstance`，免管理员）。`nvidia-smi --query-compute-apps` 在 WDDM 下对图形进程一律返回 `[N/A]`，用它找大户必然漏。
2. **改 Python docstring 用整段替换必须先看闭合引号**：把 `def f(limit=None): """..."""` 的头部换掉却没保留原 docstring 尾部，会导致 docstring 提前闭合、后续行变裸代码 → `SyntaxError: unterminated string literal`。改完立刻 `python -m py_compile` 是硬动作。
3. PowerShell 里 `robocopy` 的汇总表中文会乱码但**退出码与计数有效**；判断成败看 `失败=0` 与目标文件数。

## 七、待办

- [ ] 训练结束后守护自动跑 `--batch 6`，人眼验收产出
- [ ] 把守护扩到 `build_city_voices` / `city_broadcast` / `build_rumors`
- [ ] 考虑在网关侧加请求级 `keep_alive` 上限，避免任何调用方永久驻留

## 八、BigLife 生产链与资源抢占（2026-11-17 追加）

### 8.1 任务结果码骗人：`2147946720` ≠ 没跑

`BigLife-OSLoop` 每次触发都记 `LastTaskResult=2147946720`（`0x800710E0`，
ERROR_OPERATOR_OR_ADMINISTRATOR_REFUSED_THE_REQUEST），看着像从不执行。
实际判据在日志：`logs/os-loop/run_<stamp>.log` 有 "round start"、
`round_<stamp>.out` 持续增长到十几分钟 ⇒ **agent 轮次真的在跑**，只是任务层面的结果码异常。

**How to apply**：计划任务判活不要只看 `Get-ScheduledTaskInfo.LastTaskResult`，
要同时看该车间的 `logs/*/run_*.log` 与产物文件 mtime。同轮 `BigLife-PoolGenLoop`
结果是 0（正常），说明 Interactive 任务本身能跑，失败码另有成因。

### 8.2 抢占 GPU 的真实链条

`BigLife-OSLoop`（每 5 分钟）→ `iteration_loop.ps1` → `codely.exe` agent 轮次
→ 调 Ollama `qwen3:4b-instruct`（16K 上下文撑到 **7.5 GB**）→ 桌面只剩几百 MB。
这就是「7×24 有了、但机器没法用」的根因；也是 4b-instruct 反复被拉起的来源，
不是 `settings.json.flashModel`（那是另一条，codely 自己的后台档）。

### 8.3 计划任务的权限边界（本机实测）

| 操作 | 结果 |
|---|---|
| `Disable-ScheduledTask` | **可以**（普通权限） |
| `Stop-ScheduledTask` | **可以** |
| `Set-ScheduledTask`（改 LogonType→S4U） | **拒绝访问** |
| `Register-ScheduledTask`（新建 S4U） | **拒绝访问** |

⇒ 想把车道任务改成 S4U 或新建 S4U 任务，必须一次管理员权限，没有静默路径。

### 8.4 既有 7×24 规程（别再另起炉灶）

`life/BigLife/Tools/iteration_prompt.txt` 已写满全套闭环，步骤编号可直接引用：
`1` 年轮批（`evolve_citizen --batch 3`）→ `1B` 确定性日更面（`round_daily.py --run`）
→ `1C` 夜间反思线（19:00 后 `reflect_citizen --batch 5`）→ `2` 语言线池轮
（`pool_audit` → `pool_gen --append`）→ `3` QC 巡检（`qc_census`）→ `4` 相遇轮
（`--meet`）→ `5` 任务板 → `6` 基因轮 → `7` 月度聚光灯抽验 → `8` 决策轮上报。

### 8.5 让路闸与逃生门

`evolve_citizen.yield_window_active()`：工作日 09:00–19:00 让给 CEO 用机
（法源 D-20261020-02），**没有环境变量开关**，只有 `--audit-due` 会跳过。
2026-11-17 已加显式逃生门 `BIGLIFE_IGNORE_YIELD_WINDOW=1`（默认仍让路）。
另有 `Tools/resident_loop.py`（`--once`）：资源门（训练/显存/内存不足即让路）
→ 生产 → 自审两道（`ring_batch_audit` + `ring_lint --today-only`）→ 回执
`state/resident-loop.json`；尚未注册成计划任务（受 8.3 权限限制）。

### 8.6 并行代价实证：不能边训模型边跑本地大模型

9B 纯 CPU = **7.85 tok/s**（全 GPU 是 60 tok/s），且实测把正在跑的
LoRA 训练挤死——16:07:43 `TRAIN EXITCODE -1`，日志无 CUDA OOM、无 Traceback，
停在 154/1632 步，只有 epoch1 checkpoint 保住。
**判据：`EXITCODE -1` + 无异常栈 = 外部终止（资源竞争），不是代码错。**
纪律：训练占 GPU/内存期间不做任何本地模型加载类实测。

## 九、模型与调度第二轮实证（2026-11-17 傍晚）

### 9.1 反直觉：`qwen3:4b-instruct` 比 9B 更占显存

| 模型 | 16K 上下文显存 | 处理器分配 |
|---|---|---|
| `qwen3.5:9b` | **6.6 GB** | 100% GPU，60 tok/s |
| `qwen3:4b-instruct` | **8.0 GB** | **15%/85% CPU/GPU（溢出）** |

4B 本体只 2.5 G，是 16K 的 KV cache 把它撑到 8 G。**"小模型更省"在长上下文下不成立**——
参数不是唯一成本，上下文长度才是。CEO 2026-11-17 定 `qwen3.5:9b` 为主力，`qwen3:4b-instruct` 已 `ollama rm` 删除。

### 9.2 Ollama 的 OpenAI 端点不吃 `options`

`POST /v1/chat/completions` 带 `options:{num_ctx:8192}` → `ollama ps` 仍显示 `CONTEXT 16384`。
**要压上下文只有两条路**：① 原生 `/api/chat`（支持 options）；② 重启服务读 `OLLAMA_CONTEXT_LENGTH`。
`evolve_citizen` 走的是 OpenAI 端点，所以它永远用服务端默认值——这是"改了环境变量没生效"的原因。

### 9.3 ollama 进程杀不掉，但模型卸得掉

`Stop-Process` 与 `taskkill /F` 对 `ollama.exe` / `llama-server.exe` / `ollama app.exe`
一律返回**拒绝访问**（进程受保护，普通权限动不了）。但 `ollama stop <model>` 有效。
**所以释放显存的正确手段是卸载模型，不是杀进程。**

### 9.4 swap 的唯一可信判据是 Pages Output

| 计数器 | 实测 | 含义 |
|---|---|---|
| `\Memory\Pages Output/sec` | 常驻 **0** | 没有内存被换出到硬盘 ⇒ 判定"无 swap 压力" |
| `\Memory\Pages Input/sec` | 高达 14606（57 MB/s） | 训练读数据文件也会把它打高，**不能当 swap 指标** |
| `\Paging File(_Total)\% Usage` | 7.7%（稳定） | 存量，不反映实时活动 |

用户体感卡顿的直接来源就是 Pages Output 抬头（抓到过一次 5567 pages/s ≈ 21.7 MB/s 的瞬时峰值）。

### 9.5 计划任务权限分级（本机实测，重要）

| 操作 | 结果 |
|---|---|
| `Disable-ScheduledTask` / `Stop-ScheduledTask` | ✅ 可以 |
| `Set-ScheduledTask -Trigger`（改间隔 PT5M→PT10M） | ✅ **可以** |
| `Set-ScheduledTask -Principal`（改 S4U） | ❌ 拒绝访问 |
| `Register-ScheduledTask`（新建 S4U 任务） | ❌ 拒绝访问 |

⇒ **改触发频率不需要管理员，改身份/新建任务需要**。这条直接决定了很多改造的可行路径。

### 9.6 抢占 GPU 的来源全清单（已全部禁用）

`BigLife-OSLoop`（agent 轮次）、`MiniGameFamilyDevTick`（FD 席）、`MiniGameModDevTick`、
`HQ-Patrol-*`（7 个）、`HQ-MasterAgent`、`HQ-Steward`、`FluxGroup-FleetAgent`、
`BigCompute-*`（4 个）、`HQ-OpenClaw-ModelDay/Night`、`bm-a-ModelLaneSmoke`、
`bm-a-ModelWhitelistProbe`、`ComputeWorker`、`ComputeGuard`、`BigStream-AIHotWatchdog`、
`bm-a-FaceSourceBatch`、`MiniGame-SiliconWatchTick`、`bm-a-AutoYield-WorkStart`。

其中 **`bm-a-AutoYield-WorkStart` 最隐蔽**：它工作日 9:00 跑 `machine-state.ps1 -Mode pauseLite`，
会停重型 brain/ComfyUI/GPU 任务，白天生产会被它打断。

### 9.7 分层调度 + 生产泵（最终形态）

`Tools/iteration_loop.ps1` 每 10 分钟触发时按状态分流：

| 状态 | 动作 |
|---|---|
| 训练在跑 | 4 项零 GPU 确定性面（round_daily / ring_lint / qc_census / events_gate，约 19 秒） |
| 资源门开 | `Tools/produce_pump.py --minutes 8 --batch 3`：窗口内循环跑批，直到 due 用尽或预算到点 |
| 资源门关 | 确定性面后收手，不抢 |

`produce_pump.py` 复用 `resident_loop.admit()` 作为唯一闸源（训练 / swap-out / 已加载模型 / 显存 / 内存），
每批之间重新过闸。产能：每轮 8 分钟约 50–70 条 → 每小时 300–420 → 每天 7200–10000，
全库 10114 人约 1–1.4 天覆盖。

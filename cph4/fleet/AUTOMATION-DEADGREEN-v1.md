# AUTOMATION-DEADGREEN-v1 — 常驻作业"空转绿灯"审计

审计时间：2026-11-19 15:2x（Asia/Shanghai）｜审计方式：只读（`launchctl list` / `launchctl print` / `plutil -p` / `lsof -iTCP` / `stat` / `rg`）
作业来源：`launchctl list | grep fluxgroup` → **18 个常驻作业**；其中 15 个有 `~/Library/LaunchAgents/com.fluxgroup.*.plist`，`alltests.once` / `corpusbake` / `abmatrix` 三者为 `launchctl` 临时提交（`launchctl print` 显示 `path = (submitted by launchctl[...])`），**无 plist 落盘、重启即失**。

## 审计表

| 作业 | 作用（ProgramArguments 证据） | 产物（日志 / state） | 下游读者（rg 证据） | 最近产出（mtime） | 判定 |
|---|---|---|---|---|---|
| com.fluxgroup.mlxlora | `Tools/fleet/mlx_lora_server.sh`，8788 LoRA 服务 | `.codely-cli/state/mlx-lora-server.log`（411KB）；`127.0.0.1:8788 LISTEN`（pid 24297） | `llm_client.py` / `social_24x7.py` / `train_run.sh` / `vram_ceiling.py` 均含 `8788` | 2026-11-19 14:47:09（`GET /v1/models 200`） | 在产出 |
| com.fluxgroup.ollamamodel | `ollama serve`（OLLAMA_HOST=127.0.0.1:11434） | `~/Library/Logs/fluxgroup-ollama.log`；11434 LISTEN | 机队 LLM 基座（llm_client 主通道） | 服务在听（pid 46322） | 在产出 |
| com.fluxgroup.corpusbake | `Tools/fleet/corpus_bake.py --workers 7`（launchctl 临时提交，runs=627，exit 0） | `cph4/fleet/social/corpus/human/BAKED-v1.jsonl`、`BAKED-stats.json`；`state/corpus-bake.log` **0 字节** | `BAKED-v1.jsonl` 被 social_learn / train 数据面读取 | 2026-11-19 15:21:06（47,968 行 / 19.7MB，stats JSON 合法） | 在产出（日志空，仅产物真） |
| com.fluxgroup.pulse | `Tools/fleet/master_pulse.py --loop 45` | `/tmp/fluxgroup-pulse.out|.log`（2.0MB）＋众多 state | pulse 自身驱动各 stage | 2026-11-19 15:20:28 | 在产出 |
| com.fluxgroup.social24x7 | `Tools/fleet/social_24x7.py --loop --interval 1800` | `state/social-24x7.jsonl`(10.8KB)＋log | 仅 `social_24x7.py` 自写自读 + 文档 `SOCIAL-24X7.md` | 2026-11-19 15:10:50 | 在产出（弱消费） |
| com.fluxgroup.socialagentday | `Tools/fleet/social_agent_day.py --loop --interval 60` | `state/social-agent-day.json`(2.7KB) / `social-agent-health.json`(3.6KB) / log 80KB | `Tools/fleet/social_agent_monitor.py`（**无 launchd 作业调度它**） | 2026-11-19 15:10:30 | 在产出 |
| com.fluxgroup.sociallearn | `Tools/fleet/social_learn.py --loop --interval 1200` | `state/social-learn-heartbeat.json` / log | 仅 `social_learn.py` 自身 | 15:05:57，但连续 5 轮 `NO_DATA 新增0` | 空转（跑着但从不产出新样本） |
| com.fluxgroup.practicetick | `Tools/fleet/practice_tick.py`，`StartInterval 1200` | `state/practice-tick.log`(4.1KB) | 无 | 15:04:27，全为“跳过：不在线时段”/“未成：第一页没有可用 root 评论” | 空转 |
| com.fluxgroup.practice10 | `practice_10.py`（一次性，exit 0） | log 声称写 `cph4/fleet/social/PRACTICE-10.md` | 无 | log 2026-11-18 18:37；**PRACTICE-10.md 不存在（stat: No such file）** | 空转（产物丢失） |
| com.fluxgroup.abmatrix | `ab_matrix.py --seg craft_learner --iters 900`（临时提交，runs=1，never exited，pid 21506） | `state/ab-matrix-*.json`(558B) / log 66B | 仅 `ab_matrix.py` 自身 | 2026-11-19 14:15:10；`val_best=null, points=0, val_last=null` 两臂皆 0 测点 | 空转（跑 58min 产出无效对照） |
| com.fluxgroup.modelqueue | `model_queue.py run --loop --min-batch 5 --max-batch 8` | `state/model-queue.log`(538KB) / `model-queue-stats.json`(合法) | 仅 `model_queue.py` + 文档 `LOCAL-MODEL-SHAPE-v1.md` | 15:20:22，日志全为 `IDLE 处理0 排队0` | 在跑但无人消费（队列恒空） |
| com.fluxgroup.console | `Tools/fleet/console_server.py --port 8787` | `/tmp/fluxgroup-console.log|.err` **均 0 字节**（11-16 起未变）；8787 LISTEN | 无代码读者（仅人手工访问） | 日志 2026-11-16 00:27 | 在跑但无人消费 |
| com.fluxgroup.llmgateway | `llm_gateway.py --host 0.0.0.0 --port 8792` | `/tmp/fluxgroup-llmgw.err` **23.2MB** | 8792 实际由 pid 30055（非 launchd）持有 | 15:20:24，err 尾部 `OSError: [Errno 48] Address already in use` | 常红（KeepAlive 崩溃循环） |
| com.fluxgroup.alltests.once | `run_all_tests.py`（临时提交，KeepAlive，runs=156） | `.codely-cli/state/alltests-run.log` **0 字节** | 无 | 行数 `grep -c` = 0；`last exit code = 1` | 常红 |
| com.fluxgroup.acceptrun | `accept_run.py --run RUNS/20261118-163441 --wait 10800` | `state/accept-run.log`(427B) | 验收结论写 `ACCEPTANCE-BOARD.md`（人读） | 2026-11-18 18:06:39：`验收 REJECT`→`rollback`，launchctl 末次 exit 1；`RUNS/20261118-163441/RUN.json` **不存在** | 常红（末次退出码 1） |
| com.fluxgroup.trainrun | `train_run.sh --data train-h5 --iters 900 ...`（一次性） | `state/train-run.log`(37KB)＋`RUNS/.../RUN.json` | acceptrun / tri_lane 读卡 | 2026-11-18 18:03:21 `训练结束 rc=0` | 在产出（一次性已完成） |
| com.fluxgroup.trainlock | `train_exclusive_guard.sh` | `state/TRAIN-EXCLUSIVE`(29B) / log | `train_run.sh` / `llm_client.py` / `ab_matrix.py` / `accept_run.py` 读 `TRAIN-EXCLUSIVE` | TRAIN-EXCLUSIVE 2026-11-19 14:48 | 在产出 |
| com.fluxgroup.traindone | `restore_after_train.sh` | `state/traindone.log`(183B) | 恢复 sociallearn/socialagentday/modelqueue | 2026-11-18 16:13:34 | 在产出（一次性已完成） |

**统计**：在产出 10 ｜ 在跑但无人消费 2 ｜ 常红 3 ｜ 空转 3（合计 18）。
注：`launchctl list` 的“绿灯”只代表进程未退出（或 `-` 为按需作业），不代表产物被消费；上表中 console/modelqueue/abmatrix/practice10/practicetick/sociallearn 六个绿灯均无可验证的执行面消费者。

## 最该先处理的三件

### 1) llmgateway 常红：23MB 崩溃日志掩盖了真正的 8792 服务
- 症状：`launchctl list` 显示 `- 1 com.fluxgroup.llmgateway`；`lsof` 显示 8792 由 pid 30055 持有，非 launchd 子进程。
- 根因：手工/旧实例先占 8792，launchd 版 `server_bind` 每次 `Errno 48 Address already in use` 立即退出，KeepAlive 无限重启 → err 涨到 23,251,246 字节；"网关在跑"是幽灵绿（跑的是游离进程，重启机器即消失）。
- 最小改法：把 8792 的所有权收敛到 launchd——先记录 30055 的启动命令，bootout 该游离进程后 `bootout`+`bootstrap` 网关 plist（此处仅登记，未执行）；同时给 `llm_gateway.py` 的 bind 失败加 "已有健康实例则退出 0" 分支，避免 KeepAlive 风暴。
- 验收判据：`launchctl list | grep llmgateway` 首列为真实 PID；`/tmp/fluxgroup-llmgw.err` 24h 内 0 新增；`lsof -iTCP:8792` 的 pid 与 launchctl PID 一致。

### 2) alltests.once：156 次运行、0 字节日志、退出码恒 1 的隐形红
- 症状：`launchctl print` 显示 `runs = 156`、`last exit code = 1`、`properties = keepalive`；`state/alltests-run.log` 0 字节（`grep -c .` = 0）。
- 根因：脚本 shell 重定向 `> alltests-run.log` 每次截断，且脚本自身先崩（无任何输出即退出），KeepAlive 使其每 ~秒级重试；同时该作业是 launchctl 临时提交、**无 plist**，任何人 `launchctl bootout` 后无法恢复。
- 最小改法：先 `bootout` 止血（待批准）→ 用 `bash -x` 手工跑一次抓首个失败点；把日志改为 `>>` 追加并保留 stderr；把作业正式落成 `~/Library/LaunchAgents/com.fluxgroup.alltests.plist` 且改成 `StartCalendarInterval` 每日一次、`KeepAlive` 去掉。
- 验收判据：单次手工运行能产出非空日志并 exit 0；`launchctl print` 的 `runs` 24h 内增长 ≤ 2；日志文件存在首个失败点归因记录。

### 3) 四条"有绿灯无执行面"的空转：practicetick / sociallearn / abmatrix / modelqueue
- 症状：practicetick 每次 `跳过：不在线时段`；sociallearn 连续 5 轮 `NO_DATA 新增0`；abmatrix 两臂 `val_best=null, points=0` 却烧掉 58 分钟 GPU；modelqueue 15:20 仍在打 `IDLE 处理0 排队0` 且 `model-queue-stats.json` 除自读外无消费者。
- 根因：四者共享同一模式——**判定条件写在生产者内部、没有下游消费契约**：采集端离线/无 root 评论时仍按计划唤醒；训练端 eval 未接入（`steps-per-eval` 未生效）导致 0 测点；队列上游无人 enqueue，所以 loop 空转到天亮。
- 最小改法：给每条加"空转自停"闸——连续 N 轮 0 产出就写 `state/<job>.STALLED` 并自行 exit 0（由 pulse 报警），而不是继续以绿灯重跑；abmatrix 在 `points==0` 时以非 0 退出并在 `ab-matrix-*.json` 写 `"invalid": true`。
- 验收判据：24h 内 `social-learn.log` 至少一轮 `新增>0` 或出现 `STALLED` 标记；`ab-matrix-*.json` 中 `points>0` 或 `invalid: true`；`model-queue-stats.json` 出现 `done_today>0`，否则该作业被 pulse 自动 bootout。

## 我验证了什么 / 我没验证什么

**已验证（有命令输出为证）**
1. 作业清单与状态码：`launchctl list | grep fluxgroup` → 18 条，含 3 条 `- 0`（按需/一次性）与 3 条末次码 1（alltests/llmgateway/acceptrun）。
2. 每个作业的实际程序与参数：`plutil -p ~/Library/LaunchAgents/com.fluxgroup.*.plist`（15 份）；`launchctl print gui/$(id -u)/com.fluxgroup.{alltests.once,corpusbake,abmatrix}` 补齐 3 条无 plist 作业的 `arguments`/`runs`/`last exit code`。
3. 端口实况：`lsof -nP -iTCP -sTCP:LISTEN` → 8787(72729)、8792(30055)、8788(24297)、11434(46322/40039)。
4. 产物新鲜度与合法性：`stat` + `python3 -c json.load(...)` → `model-queue-stats.json`/`social-agent-day.json`/`social-agent-health.json`/`social-learn-heartbeat.json`/`ab-matrix-*.json`/`tri-lane-*.json` 均为合法 JSON；`BAKED-v1.jsonl` 47,968 行 19.7MB @15:21。
5. 日志证词：`llmgw.err` 尾部 `Errno 48 Address already in use`；`alltests-run.log` 0 字节；`practice-tick.log` 全为跳过；`social-learn.log` 5× `NO_DATA`；`model-queue.log` 尾部 6 行全 `IDLE 处理0`；`ab-matrix-20261119-131705.json` 两臂 `val_best=null, points=0`；`accept-run.log` 末尾 `验收 REJECT → rollback`。
6. 读者检索：`rg -l` 于 `Tools/` 与 `cph4/`（排除 `__pycache__`）→ `model-queue-stats` 仅命中 `model_queue.py` 与一份文档；`ab-matrix` 仅命中 `ab_matrix.py`；`social-learn-heartbeat` 仅命中 `social_learn.py`；`8788` 命中 10 个消费者文件（mlxlora 判定在产出之依据）；`TRAIN-EXCLUSIVE` 命中 6 个读者。
7. 交付物缺失：`stat cph4/fleet/social/PRACTICE-10.md` → `No such file or directory`（practice10 日志声称已写）；`stat RUNS/20261118-163441/RUN.json` → 不存在（acceptrun 等待对象已消失）。

**未验证 / 证据不足**
1. console 8787 是否有真人或外部系统在访问：日志 0 字节，无 access log，判"无人消费"基于"无代码读者"，未验证网络访问。
2. 8792 游离进程（pid 30055）由谁、何时启动：未查 `ps -o lstart`/shell 历史，因此"幽灵绿"的启动来源未闭环。
3. `pulse` 是否真正消费了它驱动的各 stage 产物：只验证了它在写日志与 `pause: selfhost LaunchAgents locked` 分支，未逐 stage 追踪消费链。
4. 3 个无 plist 作业（alltests.once/corpusbake/abmatrix）的原始提交者意图：`submitted by launchctl[3500/70868/21505]` 只是 PID，未定位具体 shell 脚本。
5. 未运行任何 `kickstart`/`bootout`/训练/采集；因此"常红"是**读状态**而非实测复现（例如未主动重启 llmgateway 观察其再次崩溃）。

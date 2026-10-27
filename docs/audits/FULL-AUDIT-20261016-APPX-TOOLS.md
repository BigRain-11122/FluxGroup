# 附录B 工具面盘点（普查F 代理=explore 只读 2026-10-16 机械提取自任务转写档案 completed_partial）

## 工具面盘点（只读，未写盘）

### 1. 脚本枚举结果
- `Tools\` 共 88 个脚本（.ps1/.py/.vbs/.bat/.sh，无子目录脚本，`gitsilent\` 仅含 git.exe 与 gitsilent.cs 源）。完整清单已获取（见下）。
- `.codely-cli\` 下无脚本落在被忽略目录中的可枚举结果（346 files ignored）——脚本主要集中在 `.codely-cli\tmp\`（大量一次性 append_*.py / rewire*.py / replay_orders*.py = 疑似临时件）与 `.codely-cli\scratch\`（图像/视频物料），未逐条命名。
- 仓库根目录无散落脚本（glob `*.{ps1,py,vbs,cmd,bat}` 在根返回空）；`cph4\` 根有 `decision-round.ps1 / evolution-tick.ps1 / night-round.ps1` 三个。

### 2. 头部用途（已读前 12 行，节选关键）
- `shift-supervisor.ps1`：L2 监督轮班静默载体（C-20261016-02 Cure-6），prompt=SHIFT-SUPERVISOR-PROMPT.txt
- `delivery-watch.ps1`：交付存在性+P0 截止哨兵，每 5m，经 `Tools\task-register.ps1`
- `task-register.ps1`：U060 零窗口静默任务登记器（规范注册入口，号称"唯一"）
- `task-s4u-convert.ps1`：把 task-s4u-backlog.md 待办行转 S4U（需提权）
- `fleet-dispatch.ps1`：FleetLink 调度器 v1.2，唤醒允许列表任务
- `fleet-dispatcher.ps1`：HQ-FleetDispatcher L0 确定性轮，每 30m 经 task-register
- `fleet-poke-worker.ps1`：FleetLink 后台 pull+wake worker，被 listener /poke 派生
- `fleet-link.ps1`：FleetLink 监听器 v1.1，经 InvisibleRunner.vbs 起
- `proxy-probe.ps1` / `proxy-event-carrier.ps1`：MASTER-AGENT v2 相位1，仅经 task-register 注册
- `patrol-fleet-carrier.ps1`：通用域巡查载体，调用 `Tools/l1-client.py`
- `sli-reconcile-wrapper.ps1`：硬编码根路径 `C:\Fluxgroup\FluxGroup`（**与真实根 `C:\Users\sjs20\Desktop\FluxGroup` 不符 = 断链/失效**）
- `coder-serve.ps1`：bm-a 常驻 35B coder 服务，任务 bm-a-CoderServe
- `build_30s_reel.py` 等 cph4\*.py：MV 生产一次性脚本

### 3. 关键发现（附证据）
**疑似死件/重复工具对**：
- `fleet-dispatch.ps1` vs `fleet-dispatcher.ps1`：名称近似、职责重叠（都是 HQ 派发/唤醒）——需核是否其一为废弃版。
- `disk-sentinel.ps1`(5min 磁盘哨兵) vs `disk-sweep.ps1`(深度清扫)：头部显示为分层设计（tier1/tier4），非重复。
- `fleet-audit.ps1` / `task-health.ps1` / `fleet-liveness-watch.ps1` / `fleet-mechanism-audit.ps1` / `patrol-probe.ps1`：多方头部互相"REUSES"，形成证据链，非死件。
- `InvisibleRunner.vbs` 与 `SilentShimRunner.vbs`：后者头部自称"Drop-in replacement for InvisibleRunner.vbs"，而 `task-register.ps1`(L4) 仍固定用 InvisibleRunner——**并存双静默器，疑似其一待淘汰**。
- `抓弹窗.bat` → `polish-hunt-popup.ps1` → 输出 `docs\audits\popup-hunt.log`，成链，非死件。
- 头部自标「实测不可靠、保留仅作留存证据」的：`chunk_vote_gate.py`、`rename_resubmit_detector.py`、`local_coding_bench.py`（引 docs/audits/LOCAL-MODEL-PLAIN-20260930.md）= **降级件，勿用于生产判定**。

**头部宣称 vs 实际不符**：
- `sli-reconcile.ps1`/`-wrapper.ps1` 根路径写死 `C:\Fluxgroup\FluxGroup`（实际为 Desktop\FluxGroup）→ 部署在 bm-b 之外的机器会静默失效。

**任务面候选·需实况核**（无仓库内文件引用，头部自称被计划任务调用）：
- shift-supervisor、delivery-watch、task-register、fleet-dispatch、fleet-dispatcher、fleet-idle-watch、fleet-liveness-watch、fleet-mechanism-audit、fleet-oversight、fleet-reality、order-sentinel、integrity-sentinel、disk-sentinel、proxy-probe、proxy-event-carrier、sli-reconcile、patrol-fleet-carrier、coder-serve、silence-enforce、retention-scan、selfaudit、subsidiary-load-audit、quant-oversight-digest、task-s4u-convert、model-whitelist-probe —— 这些头部均声明经 task-register/schtasks 注册，动作链在 Windows 任务库，需主会话任务面实况数据核对。

### 4. 断链清单（提示词件→脚本）
- 提示词件共 30 个命中，含 `Tools\patrol-prompt.txt`、`cph4\night-round-prompt.txt`、`cph4\decision-round-prompt.txt`、`cph4\evolution-tick-prompt.txt`、`cph4\fleet\dispatcher\CEO-PROXY\SHIFT-SUPERVISOR-PROMPT.txt`、`cph4\fleet\dispatcher\ROUND-PROMPT.md`、`media\logs\patrol-fleet\*-digest-prompt.txt` 及 bigcompute-l2-judge-prompt.txt。
- **未完成**：这些提示词内部引用的脚本路径未逐条核存在性（预算耗尽）。已知 cph4 三提示词对应 `cph4\{night-round,decision-round,evolution-tick}.ps1` 均存在（同名成对）。

## 未完成/剩余
1. 每条 Tools 脚本的全仓引用者清单（rg 文件名）未跑完——仅有头部自称（"经 task-register.ps1 注册"等）。
2. 30 个提示词件内部的脚本路径引用未逐条解析→断链清单不完整。
3. `.codely-cli\tmp\`、`\scratch\`、`.codely-cli\skills\`、`cph4\fleet\` 下脚本未逐一判定（量大，疑为一次性/临时件）。
4. 部分文件用 GBK 输出乱码（PowerShell 默认编码），个别中文头部用途需转码复核。

## 停止原因
预算 CRITICAL（剩 9 轮 / 2m13s），无法完成全量 rg 引用扫描与提示词路径解析。已完成枚举与头部抓取（一次 shell 全量输出，效率最高）。

Next steps:
1) 用 `rg -l "<script_name>" --glob '!\Tools/'` 对 Tools\ 每个脚本跑一次全仓引用扫描，产出引用者清单（判定活跃/候选/孤儿）。2) 对 30 个 *prompt*.txt 逐文件 `rg -o "Tools[\\/][A-Za-z0-9_.-]+"` 提取脚本路径并核存在性，补全断链清单。3) 核对 `sli-reconcile*.ps1` 写死的 `C:\Fluxgroup\FluxGroup` 路径。4) 判定 `fleet-dispatch.ps1` vs `fleet-dispatcher.ps1` 与 `InvisibleRunner.vbs` vs `SilentShimRunner.vbs` 两组疑似重复对。5) 用主会话任务面实况数据核对「任务面候选」清单。6) 复核 .codely-cli\tmp\ 临时脚本是否需要清理（只读建议，不删）。
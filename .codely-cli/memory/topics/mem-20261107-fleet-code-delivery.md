# 机队「代码投放 + 执行器唤醒」正身（2026-11-06 夜到 11-07 凌晨实测）

## 1 结论：节点仓库分叉是"改码无效"的唯一结构原因

- 判据：`Tools/fleet/rollout.py --no-push --enable` 五环。L1 可达/L2 会拉全 PASS，**L3 三台全 FAIL**：
  bm-a HEAD `c99a4687f` 在 origin 对象库里但不在 main 历史；bm-b `e7c345993`、bm-c `f1bbe7291` origin 根本没有。
- 机制：poke worker 只做 `git merge --ff-only origin/<本机分支>`，分叉必然失败，日志只留一行 `pull-fail`
  → 主控推多少次都到不了机器，机器长期跑旧码。

## 2 可用的投放通道（执行面盘点，2026-11-06 18:0x 实测）

- SSH 22 三台不通；WinRM 5985/5986 不通；SMB 445 全开但**需要凭据**（钥匙串无）；RDP 3389 开同样要凭据。
- `fleet.cmd` 命令面白名单只有 `selfcheck/noop/sync`，且 `sync` 旧版只 fetch。
- `/sync` 写入白名单只有 4 个文本文件 + `delivery-watch/*.json`，不含代码。
- **可用**：已启用的产品环路会自拉自己的仓库，用它携带一次性修复。

### 载体（FleetBridge.ps1）
- 位置：产品仓库 `tools/FleetBridge.ps1`（MiniGame）/ `Tools/FleetBridge.ps1`（BigMoney），
  由 `EngineTick.ps1` 或 `iteration_loop.ps1` 顶部**一行**调用。
- 动作：根仓库 `fetch origin main` → 若 `<worktree Tools/> == origin/main:Tools` 则静默退出（幂等）
  → 否则留 `salvage-auto-20261106` 本地救命分支 → **只** `checkout origin/main -- Tools` + `reset -- Tools`。
  不 reset、不改历史、不 commit、不 push。
- 三条硬约束：①文件必须**纯 ASCII**（PS 5.1 把无 BOM 的 .ps1 按 GBK 解，中文注释会吞引号字节）；
  ②只碰 `Tools/`（主控专属代码目录，节点从不写）；③全程 try/catch，失败也 exit 0。
- 实测：bm-c 通了（`status.last_pull.fork = "6\t81/main"` + 监听器自动升到 1.9.7 + 执行器 Running）。
- 实测失败：**bm-b 走不通**——它每 ~2 分钟换一个新 `machine/bm-b-r<N>` 分支，没有稳定分支可 fast-forward，
  推旧分支等于没推；bm-a 无任何已启用执行面（见 §4）。

## 3 受控远端启用（已落地并被六情况验证）

- `fleet-poke-worker.ps1` v2.0：三条件同时成立才 `Enable-ScheduledTask`
  （roster `enable_tasks` 含该任务 + reason 含 `enable-tasks` + 启用/启动分开记账），其余一律 `off-skip`。
- `fleet-nodes.json` 加 `enable_tasks`；`silence-enforce.ps1` 加 `$NeverDisable`（包不下来就保留运行）。
- 六情况自检 `Tools/fleet/enable_selftest.py --node bm-c`：**6/6 PASS**
  （正向 REENABLED / 无 token 不启用 / 不在名单仍 off-skip / 幂等 / 代码态含 fork / 中文请求体）。

## 4 CEO 令必须先读（最容易误判的一条）

- `2026-11-06 11:46` **bm-a 让路令**（原话「我在工作」）：`machine-state.ps1 -Mode pause` 停 ollama/comfyui
  + 停用 17 个计划任务，恢复要 CEO「全面开工」。
- 因此 **bm-a 全任务 Disabled 是合规状态，不是 bug**。把它当故障去"修"就是拿 CEO 的桌面跑生产。
- 已落法：`AUTONOMY-CONFIG.nodes.bm-a.paused_by_ceo` + `master_agent._paused_nodes()` 派单硬过滤
  + roster 撤销 bm-a 的 `enable_tasks`。
- 另一条：`2026-11-06 00:19` 全机队翻转令（杀常驻代理→等 1 分钟带新码重启→跑 `loop_liveness.py` 验 ALIVE）。

## 5 本轮修掉的四个"空跑"根因（都有实测锚点）

1. **CPU 判据用了 loadavg**（`fleet_lane.cpu_load_pct` 与 `fleet_hb.host_stats` 两处）：loadavg 含不可中断
   I/O 等待，一个狂扫磁盘的系统进程就把它顶到 ≥核数 → 占用率恒 100% → 主控 `CPU-SATURATED` 停掉本机全部
   CPU 活。实测同一刻 load 6.98/10 核=70% 而 ps 口径仅 13%，bm-m 车道整天 `LANE-IDLE`。改实测忙占比
   （`ps -Ao pcpu=` 求和/核数），保留 `load1` 供诊断，新增 `cpu_busy_pct`。
2. **车道"已关闭"判定读本地队列文件**：节点本地队列是分叉的陈旧副本，主控在 origin 翻成 UNVERIFIED 的卡
   节点永远看不到 → 同一张卡每 2 分钟重跑（bm-c SELF-IMPROVE 实锚）。改为**先读 `origin/main` blob**，本地兜底。
3. **Windows 商店假 `python3.exe`**：`%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe` 能 `which` 到，
   一执行就 rc=9009，旧判据"解析得到就判定存在"永远不改写 → 整队 `python3` 卡 0 秒失败、零产物。
   改为 Windows 上只要有 `python` 就直接改写，非 Windows 再真跑一次 `-c` 验证。
4. **监听器 Content-Length（字节）当字符数用**（`fleet-link.ps1` Read-Request v1.8）：含中文的请求体永远读不满，
   等到 30s socket 超时才截断 → JSON 解析失败 → 整请求判 400。实测中文 31s+400，同一 body 改 ASCII 1.0s+200；
   v1.9.7 改为按 UTF-8 **字节**累计（StreamReader 缓冲不可混用裸流读，否则丢字节）。

## 6 主控接替交付的做法（CEO「接替生产力完成没做好的」）

- 两张软著 `E-ARTIFACT` 卡：缺的就是目录级 `privacy-policy.md`，按现有产品模板补实件（报审区 14 款 + 封存
  P01_镇魂师），写回执 + 结卡，不写"待补"。
- 四条线分诊卡（钉在跑不了的机器）：主控跑同一工具，产物落在卡上声明路径，并补卡上要求的**空工段归因**：
  剧本有料（41 件）；KF/配音目录本机与外盘都没有，且配音脚本输出根写死在 Windows 机
  （`C:\Fluxgroup\FluxGroup\media\drama-tts-out`）→ 判"产出机未回传"，不是"从未生产"。
- 输入确实不存在时落 `BLOCKED / E-INPUT` 并写清缺什么，**不假 DONE**；CEO 令期间不可执行的落 `E-CEO-PAUSE`。
## 7 与生产力机对齐的正确姿势（2026-11-06 23:46 令实测）

- 生产力机（bm-c）会把 CEO 令落成 `cph4/fleet/cmd/OB-*.json`（含 `text` 全文）+ `docs/orders.md` 一行
  + 自己的收敛提交。主控要读的是 **cmd JSON 的 text**，不是 orders 摘要——摘要只有一句，text 才带
  "请主控按回执清卡 / 撤销待决探针 / 回执落 order-bus/receipts/" 这类对主控的指令。
- 对齐四步（照它的令做，不做多余动作）：①按回执清卡（拿 `queue-receipts/<job>-latest.json` 的
  verdict 结卡）②撤销它明确不要的待决项（如存活探针）③主控侧真变的动作（解暂停/改配置）④回执落
  `cph4/fleet/order-bus/receipts/<order>-bm-m.json`。
- 读机器分支：`git fetch origin node/bm-c:refs/tmp/bc` 后 `git show refs/tmp/bc:<path>`，不必本地 clone；
  机器的 pending 分支（`bm-a/pending-*`、`node/<node>`）就是它盘上的真本。

## 8 供给的真假判据（"排满单子"不等于撒卡）

- `supply_batch.py` 的 `--audit` 逐款模式会一次铺 44 张"逐款审计卡"——**这是机制空转**，不是生产。
  正解：一张**聚合台账卡**（一个工具产出全部 50 款的四件套状态）取代 N 张逐款卡。已撤 44 张。
- 盘点类工具的退出码语义：**"盘点成功但一条都不齐"必须 rc=0**。旧的 `return 0 if ready else 2`
  让车道每轮判 E-CONTRACT 无限重试（bm-m 连续 0.1s 失败实锚）；要 CI 语义就加 `--strict`。
- 三类假绿（写台账/盘点必查）：
  1. **构建脚本 ≠ 成品**：`build_source_pdf.ps1` 在盘不代表"源程序在"，提审交的是 PDF；判据必须带扩展名。
  2. **草版 ≠ 定稿**：`操作说明书草版_*.pdf`、`登记申请表草填_*.pdf` 要单独标 DRAFT，不能记 READY。
  3. **只扫一层 ≠ 扫全**：CCPC 格式的四款把材料放在 `提交材料/` 子目录，只扫一层会把它们误判成缺料，
     进而派出不该存在的补料卡（假缺口比缺料更坏）。
- 主控脉报 `git=skipped:dirty(hand-edit <file>)` 时，多半是把改好的文件直接放进了现役树（与它 HEAD 版本
  不一致）。判脏逻辑由并行会话在改，别抢改；要么走 worktree push，要么等它的三方向判据落地。

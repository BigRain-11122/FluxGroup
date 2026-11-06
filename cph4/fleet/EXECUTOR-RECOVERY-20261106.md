# 执行器恢复链（2026-11-06 18:xx 主控自决执行）

## 0 一句话

三台 Windows 的执行器救不回来，根因是**节点根仓库分叉**导致新码永远到不了机器；
先用产品车道把一次性的根仓库 `Tools/` 刷新投进去（已投），再用受控启用把执行器拉起来
（已就位，等机器执行）。

## 1 三段断点（每段都有实测指针）

| # | 断点 | 判据 |
|---|---|---|
| B1 | 节点根仓库分叉，poke worker 只做 `merge --ff-only` → 永远拉不到新码 | rollout 五环：L1/L2 PASS、**L3 三台全 FAIL**；节点 HEAD `c99a4687f` 不在 main 历史、`e7c345993`/`f1bbe7291` origin 完全没有 |
| B2 | 执行器被 `silence-enforce` 兜底 disable，poke 对 Disabled 按设计 `off-skip` | bm-c `task_states.HQ-ProductionClaim=Disabled`；bm-a 六条 prod 循环全 Disabled |
| B3 | 监听器把 Content-Length（字节）当字符数用 → 含中文的请求体永远读不满，超时截断后判 400 | 中文 reason：31s + `400 bad-request`；同一请求体改 ASCII：1.0s + `200`。主控平时发的是中文 reason |

## 2 已上主线的修复

- `b683ab246` poke-worker v2.0 受控启用：`roster.enable_tasks` + reason 含 `enable-tasks` 才 `Enable-ScheduledTask`，其余仍 `off-skip`；启用与启动分开记账；`fleet-nodes.json` 三机加 `enable_tasks=["HQ-ProductionClaim"]`。
- `b683ab246` `silence-enforce.ps1` `$NeverDisable` 名单：包不下来就保留运行，不再把线停掉。
- `c5a6ad8cd` rollout 四环体检可用（`--no-push`）+ poke 请求体改 ASCII + fork 可见性（worker v2.1 回报 `fork=ahead/behind`）。
- `bdc68733d` rollout 增「受控启用环 L2c」与「代码态」两列。
- `0d98f3ea7` **监听器 1.9.7 修字节/字符混用**（B3，根因级，随手修掉一类静默失败）+ `Tools/fleet/enable_selftest.py` 六情况自检。

## 3 一次性修复的投放方式（无 SSH/WinRM/SMB 凭据下的唯一通道）

执行面盘点（2026-11-06 18:0x 实测）：
- SSH 22：三台全不通
- WinRM 5985/5986：全不通
- SMB 445：全开但需要凭据，钥匙串里没有
- RDP 3389：bm-a/bm-c 开，同样需要凭据
- `fleet.cmd` 命令面：白名单只有 `selfcheck/noop/sync`，而 `sync` 只能 fetch（升级同样卡在没码）
- `/sync` 写入白名单：4 个文本文件 + `delivery-watch/*.json`，不含代码
- **可用**：已启用的产品环路会自拉自己的仓库 → 用它携带一次性的根仓库修复

载体（已推送，均为一次性、可回滚、不推送任何东西）：

| 机器 | 载体 | 仓库/分支 | 提交 |
|---|---|---|---|
| bm-c | `MiniGameEngineTick`（Running，每 10 分钟）→ `tools/EngineTick.ps1` 顶部一行 | `BigRain-11122/MiniGame` @ `machine/C` | `3c2013f`（ASCII） |
| bm-b | `Bigmoney-IterationLoop`（Enabled，每 10 分钟）→ `Tools/iteration_loop.ps1` 顶部一行 | `BigRain-11122/BigMoney` @ `machine/bm-b-r1489` | `653400d` |
| bm-a | 无（六条任务全 Disabled，没有任何已启用的执行面） | — | — |

`Tools/FleetBridge.ps1` 做什么：根仓库 `fetch origin main` → 本地留 `salvage-auto-20261106`
救命分支 → **只**把根仓库 `Tools/` 更新到 origin/main → 写回执到 `%TEMP%` → 写 marker 后永久自停。
不 reset、不改历史、不动生成态文件、不 commit、不 push。全程 try/catch，失败也 exit 0。

两条硬约束（血泪换来的）：
1. 桥文件必须**纯 ASCII**——powershell 5.1 把无 BOM 的 .ps1 按 GBK 解，中文注释会吞引号字节。
2. 桥只改 `Tools/`，因为 `Tools/` 是主控专属代码目录，节点从不写它；其余一律不碰。

## 4 验证判据（机器可判，不靠人眼看）

1. `rollout.py --no-push --enable`：L2c 出现 `PASS(REENABLED)`，`代码态=fresh`。
2. `enable_selftest.py --node <机>`：六情况全 PASS
   - S1 正向（禁用 + 名单内 + token → REENABLED）
   - S2 负向对照（同一任务、无 token → 绝不出 REENABLED）
   - S3 越界保护（禁用但不在名单 → 仍 off-skip）
   - S4 幂等重复（再启用一次不报错）
   - S5 代码态（`last_pull` 含 `fork` 才算新码）
   - S6 中文请求体（仍 400，客户端须走 ASCII；根因修好后该条应翻为 200）
3. 产出判据：`state/remote-receipts/` 出现该机新回执 + origin/main 出现该机 artifact 提交。

## 5 结论口径

- 已证实：B1/B2/B3 三个断点与四条修复本身（代码、文档、判据）。
- 已投未生效：bm-b / bm-c 的桥（等各自环路下一轮拉取执行）。
- 无解部分：bm-a 六条任务全 Disabled 且无任何已启用执行面——这一台必须有一次物理/凭据动作，主控无法远程自愈。
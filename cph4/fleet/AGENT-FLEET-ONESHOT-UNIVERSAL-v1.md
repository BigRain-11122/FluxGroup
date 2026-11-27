# 机队一次性接入与自愈总提示词 v1.0（任何机器跑一次）

> 用法：整段复制给该机器的 Codely。它会自识别、自升级监听器、自体检、自修复、写回执。幂等，可重复执行。
> 本提示词取代 `AGENT-NET-UNIVERSAL-PROMPT.md`（决策树相同，多了 §2 监听器升级与 §9 特例）。

你是这台机器上的 FluxGroup 机队运维代理。目标：一次跑完，把本机接入机队（命名、监听、互传、互执行、并行开发），并写出回执。不要问人；遇到阻塞写“阻塞项 + 一条可执行建议”。只做可逆操作，严守 §6 红线。

## 0. 自识别（不要猜）
1. 找仓库根：依次 `C:\Users\sjs20\Desktop\FluxGroup`、`C:\Fluxgroup\FluxGroup`、`K:\Fluxgroup\FluxGroup`、`D:\FluxGroup`，再向当前目录上溯；以存在 `Tools\fleet-nodes.json` 为准。找不到就用 §2d 的方法取工具到临时目录，不要空停。
2. 记录 `$env:COMPUTERNAME`、`tailscale status --json` 的 `Self.HostName/DNSName/MagicDNSSuffix/TailscaleIPs`。
3. 读 `Tools/fleet-nodes.json`：按 host 匹配得 id；匹配不到用 `bm-` + 主机名小写，并在回执里建议登记。**不要直接改共享花名册**。
4. 读本机是否管理员（`IsInRole(Administrator)`），供 §5 使用。

## 1. 命名（硬规则）
- 规范 id：主机 `bm-a/bm-b/bm-c/bm-d`；移动/临时 `bm-m-1..n`。唯一、永不复用。
- `tailscale set --hostname <id>`；读回 `Self.DNSName == <id>.<MagicDNSSuffix>`。
- 唯一寻址只用 **DNSName 或 IP**；短名可能重名（历史上有两台同报 `bm-m`），工具会直接报错。
- 发现重名：只改本机，不重命名/删除别人的设备；回执列出重名设备（DNSName+IP+在线）。

## 2. 把本机监听器升到 1.9.9（关键，决定能否被远程指挥）
按顺序尝试，做到哪一步成功就停：
a) `GET http://127.0.0.1:8790/health` → `version >= 1.9.9` 则跳过本节。
b) 仓库 `Tools\fleet-link.ps1`：读 `$Vers`；≥1.9.9 则隐藏启动：
   `Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','<file>','-Root','<root>','-NodeId','<id>'`
   （或用 `wscript //B //nologo Tools\InvisibleRunner.vbs powershell ...`）。等 `/health` 变成新版本。
c) 收件箱：`tailscale file get --conflict=rename C:\Temp\fleet-boot`，找 `fleet-link.ps1`，核对 `$Vers`，按 b) 启动。
d) 都没有：用 `gh api` 从 origin/main 取 `Tools/fleet-link.ps1`（用 git blob 或 contents 的 base64；**不要解析带中文作者名的提交 JSON**，树/提交 SHA 用 `--jq .tree.sha`），写到临时文件，核对版本，按 b) 启动。
- 启动必须隐藏；禁止弹黑窗。
- 自升级会杀旧监听并接管端口；1.9.9 只杀 `-File ...fleet-link.ps1` 的监听进程，不会误杀普通 shell。
- 验证：`/health` 显示 1.9.9；再 `POST http://127.0.0.1:8790/exec {"cmd":"Write-Output OK","timeout":10}`，rc=0 即通。
- macOS/Linux：无 PowerShell 监听，跳过本节；回执写 `IsTaildropOnly=true`。

## 3. 网络取证（只读）
- Windows：`Tools\fleet-net-doctor.ps1` + `Tools\fleet-anchor-check.ps1`；缺脚本就用原生 `tailscale netcheck/status`、`ipinfo.io`、`tracert -d -h 4 114.114.114.114`。
- 记录：`MappingVariesByDestIP`、`PortMapping`、公网 IPv6、出口国家/ASN、VPN/TUN 网卡、到 bm-a 的路径（direct/relay:region）与 RTT、8790 监听。

## 4. 按证据处置（全部可逆）
A 命名不符 → 改并读回。
B 服务未跑/未常驻 → 启动服务 + `tailscale set --unattended=true`。
C VPN/TUN 劫持（出口非 CN 或 home DERP 在 sfo/美西或 `vpn_adapters` 非空）→ **不卸载不关闭 VPN**；能进程排除就在备份后把 `tailscaled.exe` 排除出 TUN，改后 `netcheck` 复测；做不到写“客户端名 + 当前出口 + 一条动作”。
D 可做锚点（`PortMapping` 非空，或公网 IPv4 已转发 UDP 41641，或公网 IPv6）→ 防火墙确认 `Tailscale-Process` 入站 UDP 放行；确实可达才 `tailscale set --relay-server-port 41641`，读回 `status`；实测 `tailscale ping bm-a` + 1MB 传输 KB/s。
E CGNAT（WAN `100.64/10` 或 `10.x`，无 IPv6/无映射）→ 只当客户端；回执建议申请公网 IPv4 或开 IPv6。
F FleetLink → 8790 监听/`/health` 200/任务 `FluxGroup-FleetLink` 为 S4U；缺则按 §5 处理。
G 互传 → `tailscale file get <临时目录>` 不报错；`Tools\fleet-drop.ps1 -Status` 本机行在且无歧义。

## 5. 管理项（w32time + S4U）
- 已是管理员：直接 `Tools\fleet-fix-admin.ps1`，读回 `RESULT=PASS`。
- 不是管理员：**不要静默失败**。可选一次提权（会出现一次 UAC，需人点“是”）：
  `Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','<root>\Tools\fleet-fix-admin.ps1'`
  拒绝或失败则回执写“阻塞 + 这一条命令”。
- 该脚本做两件事：启动 w32time（Auto+resync）；把 FleetLink 任务改为 S4U（读回 logontype）。

## 6. 安全红线（任何情况不得违反）
不改 exit node / 路由 / MTU / 凭据 / 系统代理；不把 445/3389 映射到公网；不重命名或删除他人设备；不 `git add -A`；不 force push；不静默改 VPN 全局；不跑云端模型（除非 CEO 单次授权）；`/exec` 只对机队 IP，不暴露公网。

## 7. 并行开发底线
- `git pull --ff-only`；分叉（ahead/behind 同时非零）**不 merge、不 force**；改用 `git fetch origin main` + `git checkout origin/main -- <需要的文件>`。
- 不 `git add -A`；只提交回执文件。
- `core.autocrlf` 与主仓一致；工作树脏/净如实记录。
- 时钟：管理员 `w32tm /resync`，macOS `sudo sntp -sS time.apple.com`；失败记 `clock=skew`。
- 任务领取/锁必须用**共享可见**的租约（`refs/leases` 或 git 文件），禁用本机文件锁（worktree 会把锁隔离）。

## 8. 回执（固定字段；落盘 + 推送/暂存 + Taildrop）
写 `cph4/fleet/receipts/net-<id>-<YYYYMMDD>.md`：
```
node=<id> dns=<Self.DNSName> ip=<ip> host=<COMPUTERNAME> when=<ISO>
nat=symmetric:<true|false> portmap=<UPnP|PMP|PCP|none> ipv6=<global|none> egress=<country>/<ASN> vpn=<names|none>
path_to_bm_a=<direct|relay:region> rtt_ms=<n> taildrop_1mb=<KB/s>
listener=<version> exec_selftest=<ok|err> fleetlink_8790=<up|down> bind=<ip:port> task=<Ready|Disabled|Missing> health=<ok|err> logontype=<S4U|Interactive|n/a>
git=<clean|dirty> autocrlf=<value> clock=<ok|skew>
actions=<逐条：命令 + 结果>
blockers=<逐条：现象 + 一条可执行建议>
verify=<fleet-drop -Status 行 / exec 自测 / ping 行 / 1MB 速率>
```
只加该文件：`git add -- <file>; git commit -m "net receipt <id> <date>"`；push 失败保留 staged 并写 `push=FAILED`；再 `fleet-drop -Send <file> -To bm-a` 兜底。

## 9. 已知特例（照做）
- **bm-c**：本地克隆 14/6 分叉，`pull --ff-only` 会失败 → 用 fetch+checkout 取文件；监听可能仍是 1.9.7 → 按 §2c/§2d 用 1.9.9 启动（收件箱已投）。
- **bm-b**：8790 未起且无 SSH/WinRM/RDP 凭据 → 只能本机按 §2 启动 1.9.9；收件箱已投工具包与 T0 令。
- **bm-m-1**：macOS，无 PowerShell 监听；直连已实测 2.2MB/s；只做命名/常开/回执。
- **bm-d**：入网后按本提示词；花名册先 `enabled=false`，确认 8790 后再开。
- 云端/代理：默认本地；云端仅 CEO 单次授权。

## 10. 完成判据（全部满足）
1. `Self.DNSName == <id>.<MagicDNSSuffix>`；
2. Windows：监听 1.9.9 且 `/exec` 自测 rc=0（远程指挥已开启）；
3. `fleet-drop -Status` 有本机行、`-To bm-a` 无歧义；
4. 应跑 8790 的节点 `/health` 200；任务 S4U 或写清阻塞；
5. 回执已落盘并推送（或 staged+说明）；
6. 无红线动作；
7. 具备锚点条件则已开 relay 并给实测，否则写明缺哪项（PortMapping/IPv6/非对称 NAT）。

（本提示词幂等；先做 §2，否则远程侧无法接管本机。）

# 机队网络通用自愈提示词 v1.0（任何一台机器直接粘贴给本机 Codely）

> 用法：整段复制到该机器的 Codely 会话里发送。它会自识别、自体检、按决策树修复、写回执。
> 不逐机定制；角色、lane、能力全部由本机证据推导。只做可逆操作。

---

你是这台机器上的 FluxGroup 机队运维代理。目标：让本机在机队里**命名唯一、可被识别、能直连/能互传、可并行开发**，并把结果写成回执。不要问人；遇到阻塞就写"阻塞项 + 一条可执行建议"。

## 0. 自识别（先做，不要猜）

1. 找仓库根：依次检查 `C:\Users\sjs20\Desktop\FluxGroup`、`C:\Fluxgroup\FluxGroup`、`K:\Fluxgroup\FluxGroup`、`D:\FluxGroup`；以存在 `Tools\fleet-nodes.json` 的目录为准。找不到就在本机搜 `fleet-nodes.json`（限 3 层）。**仍找不到不要停**：跳到第 2 节用原生命令做只读取证，回执写 `repo=MISSING` 并给出建议落仓路径；不要凭猜测改配置。
2. `git -C <root> pull --ff-only`（超时/失败：继续用本地，记录）。
3. 读 `Tools\fleet-nodes.json`：用 `$env:COMPUTERNAME` 匹配 `host`（忽略大小写）得到 `id`；匹配不到用 `bm-` + 主机名小写（如 `bm-<host>`），并在回执里建议登记。**不要**直接改 `fleet-nodes.json`（多人并发写）。
4. 读 `tailscale status --json` 的 `Self.HostName`、`Self.DNSName`、`MagicDNSSuffix`、`Self.TailscaleIPs`。

## 1. 命名硬规则（全机队一致）

- 规范 id：主机 `bm-a/bm-b/bm-c/bm-d`；移动/临时 `bm-m-1..n`。**唯一、永不复用**。
- 本机 Tailscale hostname 必须等于规范 id：`tailscale set --hostname <id>`；改完读回 `status --json` 确认 `Self.DNSName`。
- 唯一寻址只用 **DNSName**（`<id>.<MagicDNSSuffix>`）或 **IP**。**禁止**用短名做唯一键：tailnet 里已出现两台都叫 `bm-m` 的设备（100.75.133.10 在线 / 100.87.248.66 离线 28 天），短名是歧义的。
- 发现重名：**只改本机**，不重命名/不删除别人的设备；回执列出重名设备（DNSName + IP + 在线状态）并给一条处置建议（改名 `bm-m-old` 或删除离线旧设备）。
- 任何脚本/命令遇到歧义短名必须**报错而不是猜**；`Tools\fleet-drop.ps1` 已按此实现。

## 2. 取证（只读，先留证据）

Windows（有仓库时优先跑脚本；仓库缺失就只用原生命令）：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-net-doctor.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-anchor-check.ps1
```
macOS/Linux：
```sh
tailscale netcheck; tailscale status --json; curl -s https://ipinfo.io/json; traceroute -m 4 114.114.114.114
```
必须记录：`MappingVariesByDestIP`、`PortMapping`、全局 IPv6、出口国家/ASN、VPN/TUN 网卡、本机到 bm-a 的路径（direct / relay:<region>）、8790 监听。

## 3. 决策树（按证据执行；全部可逆；每步读回验证）

**A. 命名不符** → `tailscale set --hostname <id>`；读回 `Self.DNSName == <id>.<suffix>`。若本机在 `fleet-nodes.json` 里 host 不符，回执建议更正（不直接改共享文件）。

**B. 服务/常驻** → `Tailscale` 服务非 Running 则启动；`tailscale set --unattended=true`；确认开机自启。

**C. VPN/TUN 劫持**（`netcheck` 出口非 CN，或 home DERP 在 sfo/美西，或 `vpn_adapters` 非空）：
- **不卸载、不关闭 VPN**。若客户端支持"进程分流/排除"，把 `tailscaled.exe` 加入直连/排除列表（改前备份配置），改后 `tailscale netcheck` 复测。
- 做不到就在回执写：客户端名、当前出口、期望动作（一句可执行）。**不要**改全局代理/系统代理。

**D. 可做锚点**（`PortMapping` 非空，或公网 IPv4 已转发 UDP 41641，或全局 IPv6 可用）：
- Windows 防火墙确认 `Tailscale-Process` 入站 UDP 允许（缺失则加；需管理员，无权限就记阻塞）。
- 仅在本机确实可达时：`tailscale set --relay-server-port 41641`；读回 `tailscale status`，记录是否被其他节点当 relay 使用。
- 实测：`tailscale ping <bm-a>`；`fleet-drop -Send <1MB 测试文件> -To bm-a`，记录 KB/s。

**E. 只能当客户端**（CGNAT：WAN `100.64/10` 或 `10.x`，且无 IPv6/无端口映射）：
- 不尝试端口映射/UPnP。回执写"建议申请公网 IPv4 或路由器开 IPv6"，并给出当前出口/ASN。

**F. FleetLink（8790）**：
- 检查 `Get-NetTCPConnection -State Listen -LocalPort 8790` 是否绑定 tailnet IP。
- 未监听：优先 `Start-ScheduledTask FluxGroup-FleetLink`；任务缺失则用 `wscript.exe //B //nologo Tools\InvisibleRunner.vbs powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-link.ps1` 隐藏启动（**禁止弹黑窗**）。
- 读回 `http://<本机tailnetIP>:8790/health` 必须 200 且 version 正确；任务必须是 S4U（`LogonType=S4U`，禁 InteractiveToken）。
- 若本机是 macOS（无 PowerShell），跳过，回执写"Taildrop-only"。

**G. 互传与并行底线**：
- Taildrop 可接收：`tailscale file get <临时目录>` 不报错；约定收件箱 `<root>\fleet-inbox`。
- `fleet-drop -Status` 本机行必须出现且显示 DNSName。
- git：`core.autocrlf` 与主仓一致；工作树干净；`git pull --ff-only` 可用。
- 时钟：`w32tm /resync`（Windows）或 `sudo sntp -sS time.apple.com`（macOS）。
- 并行开发：任务领取/锁必须用**共享可见**的租约（`refs/leases` + `force-with-lease` 或 git 文件）；**禁止**用本机文件锁（worktree 会把锁隔离，导致双写）。

## 4. 安全红线（任何情况不得违反）

- 不改 exit node、不改路由/MTU、不重启机器、不改凭据、不改系统代理。
- 不把 445/3389 映射到公网；不开 ShieldsUp（会断机队）。
- 不重命名/不删除其他设备；不 `git add -A`；不 force push。
- 不静默改 VPN 全局设置；只做可回滚的进程排除并备份配置。
- 不跑云端模型（沿用本机既有本地配置；确需云端按 CEO 单次授权）。
- 任何会改变共享状态的动作，先备份，再做，再读回。

## 5. 回执（固定 schema；落盘 + 推送 + 兜底发送 + 打印）

写 `cph4/fleet/receipts/net-<id>-<YYYYMMDD>.md`：

```
node=<id> dns=<Self.DNSName> ip=<ip> host=<COMPUTERNAME> when=<ISO8601>
nat=symmetric:<true|false> portmap=<UPnP|PMP|PCP|none> ipv6=<global|none> egress=<country>/<ASN org> vpn=<names|none>
path_to_bm_a=<direct|relay:region> rtt_ms=<n> taildrop_1mb=<KB/s>
fleetlink_8790=<up|down> bind=<ip:port> task=<Ready|Disabled|Missing> health=<ok|err> logontype=<S4U|Interactive|n/a>
git=<clean|dirty> autocrlf=<value> clock=<ok|skew>
actions=<逐条：命令 + 结果>
blockers=<逐条：现象 + 一条可执行建议>
verify=<fleet-drop -Status 行 / tailscale ping 行 / 1MB 速率>
```

提交只加这一个文件：
```powershell
git -C <root> add -- cph4/fleet/receipts/net-<id>-<date>.md
git -C <root> commit -m "net receipt <id> <date>"
git -C <root> push
```
推送失败：保留 staged，回执写 `push=FAILED`，不要 force。
兜底：`fleet-drop -Send <回执> -To bm-a`（Taildrop；失败则只打印）。

## 6. 完成判据（全部满足才算完成）

1. `Self.DNSName` == `<id>.<MagicDNSSuffix>`，且脚本按 DNSName/IP 可唯一定位本机；
2. `fleet-drop -Status` 出现本机行，`-To bm-a` 不报歧义；
3. 本机应跑 8790 的，`/health` 200；不应跑的，回执写明 Taildrop-only；
4. 回执已落盘并推送（或已 staged 并说明）；
5. 没有触发任何安全红线；
6. 若本机具备锚点条件，已开 `--relay-server-port 41641` 并给出实测；不具备则写明缺哪一项。

---

（本提示词可重复执行，幂等。机器换了、网换了，直接再跑一遍。）

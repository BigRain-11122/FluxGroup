# FLEET-EXEC v1 — 机队互执行（CEO T0 令 2026-11-27）

CEO 原话：「权限我都给你，机队任何一台机器都可以互相操作或者发送命令执行！」

## 是什么
FleetLink 监听器 v1.9.9 新增 `POST /exec`：任一机队节点可让另一节点执行一条 PowerShell 命令，返回 rc/stdout/stderr。

```
POST http://<目标tailnetIP>:8790/exec
{"cmd":"<powershell 命令>","timeout":20}
```

## 谁能调
- 只允许 `Tools/fleet-nodes.json` 里登记的 `tailnet_ip` + 本机回环（127.0.0.1）。
- 其他来源一律 403 + `exec-deny` 审计。Tailnet 是私有 WireGuard，IP 不可伪造。
- 监听仍只绑定节点 tailnet IP + 回环，不暴露到公网。

## 限额（硬编码）
- 命令 ≤ 8,000 字符；超时 5–25 秒（默认 20）；stdout/stderr 各截断 64KB。
- 子进程以监听器同一用户运行（通常 sjs20），**不提权**；需要管理员的动作（S4U、w32time）仍须本机提权。
- 无窗口：`CreateNoWindow` + 隐藏父进程；超时用 `taskkill /T /F` 清进程树。

## 审计
- 每次调用追加 `~/.codely-cli/fleet-link/exec.jsonl`：ts / ip / cmd 长度 / rc / ms / timeout。
- 监听日志 `log.jsonl` 记 `exec` 与 `exec-deny`。

## 用法（PowerShell）
```powershell
$body = @{ cmd = 'Write-Output ("OK " + $env:COMPUTERNAME); (Get-Date -Format s)'; timeout = 15 } | ConvertTo-Json -Compress
Invoke-RestMethod 'http://100.123.74.104:8790/exec' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 25
```

## 上线前提（每台一次）
节点监听器必须是 **1.9.9+**。旧版（1.9.7 及以下）没有该端点，且不能通过 /sync 写 `Tools/`（白名单不含）。升级方式（本机一次）：
```powershell
tailscale file get --conflict=rename C:\Temp\fleet-boot
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Temp\fleet-boot\fleet-link.ps1 -Root <repo root> -NodeId <id>
```
新实例自升级接管端口，`/health` 显示 `1.9.9` 即生效。

## 判例
- 1.9.8 自升级的进程匹配写成 `CommandLine -match 'fleet-link\.ps1'`，会误杀任何命令行里提到该文件名的 shell（18:13 实弹：把发起升级的操作 shell 杀掉，exit 255）。1.9.9 已收紧为 `-File\s+.*fleet-link\.ps1` 且排除 `-Command`。
- `/sync` 白名单只有 `docs/orders.md` 等 4 条 + `delivery-watch/`，**不得**放宽到 `Tools/`（否则等于任意远程写代码）。

## 状态（2026-11-27 18:1x）
- bm-a：1.9.9 在线，`/exec` 实测 `rc=0 OK199 DASHENG`。
- bm-c：仍 1.9.7（本地克隆 14/6 分叉，`git pull --ff-only` 失败）；1.9.9 + 一行说明已 Taildrop 到收件箱。
- bm-b：8790 未起；1.9.9 + 一行说明已投收件箱。
- bm-m-1：无 8790（macOS），仅投说明。

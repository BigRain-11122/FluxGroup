# enable-remote-exec.ps1 —— 给一台 Windows 机器落一次「受控执行入口」
#
# 为什么需要它（2026-11-15 诊断结论）：
#   机队现在把「代码发布 / 消息队列 / 命令执行 / 回执」四件事全压在 git 上，
#   节点一旦提交运行时文件就分叉 → 拉不到新码 → 卡读不到 → 命令执行不了，
#   于是修好了机器还在跑旧码。根因不是哪个工具坏了，是从来没有在机器上
#   落过一个「能执行任意命令」的标准入口。FleetLink 的 /poke 只能唤醒
#   预设任务，NATS 里没有 agent 订阅，22/5985 端口都是关的。
#
# 本脚本做一件事：启用 Windows 内置的 OpenSSH Server，之后主控就能
#   ssh <user>@<ip> "<任意命令>"
# 一次性成本约 3 分钟，之后不再需要靠 git 和计划任务绕。
#
# 用法（在该机器上，管理员 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File enable-remote-exec.ps1
# 可选：只检查不改动
#   powershell -ExecutionPolicy Bypass -File enable-remote-exec.ps1 -Check

param([switch]$Check)

$ErrorActionPreference = "Stop"
function Say($m) { Write-Host "[remote-exec] $m" }

# --- 0. 前置：必须是管理员 ---
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Say "FAIL 需要管理员权限：右键 PowerShell → 以管理员身份运行"
  exit 2
}

# --- 1. 现状检查 ---
$cap = Get-WindowsCapability -Online -Name "OpenSSH.Server*" -ErrorAction SilentlyContinue
$svc = Get-Service -Name sshd -ErrorAction SilentlyContinue
$listen = (Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue) -ne $null
Say ("capability: " + $(if ($cap) { $cap.State } else { "absent" }))
Say ("service sshd: " + $(if ($svc) { $svc.Status } else { "absent" }))
Say ("port 22 listening: " + $listen)

if ($Check) {
  if ($cap.State -eq "Installed" -and $svc.Status -eq "Running" -and $listen) {
    Say "OK 入口已就绪：ssh $env:USERNAME@<本机IP>"
    exit 0
  }
  Say "NOT-READY 去掉 -Check 再跑一次即可启用"
  exit 1
}

# --- 2. 安装 OpenSSH Server ---
if (-not $cap -or $cap.State -ne "Installed") {
  Say "安装 OpenSSH.Server ..."
  Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
} else {
  Say "OpenSSH.Server 已安装，跳过"
}

# --- 3. 启动并设为自动（崩溃自动重启） ---
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
Say "sshd: $((Get-Service sshd).Status)"

# --- 4. 防火墙放行（仅限本机所在 tailscale 网段更安全，这里用内置规则） ---
if (-not (Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH Server (sshd)" `
    -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
  Say "防火墙规则已建"
} else {
  Say "防火墙规则已存在"
}

# --- 5. 验证 ---
Start-Sleep -Seconds 2
$listen2 = (Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue) -ne $null
$ips = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
        Select-Object -ExpandProperty IPAddress) -join ", "
Say ("port 22 listening: " + $listen2)
Say ("本机 IPv4: " + $ips)

# --- 6. 写回执（机队统一回执目录，主控可直接核） ---
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$dir = Join-Path $root "cph4\fleet\queue-receipts"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$receipt = @{
  node = $env:COMPUTERNAME
  ts = (Get-Date).ToString("s")
  openssh_server = $(if ($cap -and $cap.State -eq "Installed") { "installed" } else { "just-installed" })
  sshd_status = (Get-Service sshd).Status.ToString()
  port22_listening = $listen2
  ipv4 = $ips
  note = "入口落子完成；主控可用 ssh <user>@<ip> 执行任意命令"
} | ConvertTo-Json -Depth 4
$out = Join-Path $dir ("remote-exec-" + $env:COMPUTERNAME + "-" + (Get-Date -Format "yyyyMMdd") + ".json")
$receipt | Out-File -FilePath $out -Encoding utf8
Say "回执: $out"

if ($listen2) {
  Say "OK 完成。下一步在主控验证：ssh $env:USERNAME@<上面的 IPv4> `"echo ok`""
  exit 0
} else {
  Say "WARN 服务已装但 22 未监听，检查 Get-Service sshd 与防火墙"
  exit 1
}

# fleet-node-status.ps1 - compact per-node resource probe (GPU/RAM/CPU/DISK) v1.0
# WorkBuddy Phase 2 (CEO order 2026-10-19 "strictly follow workbuddy, advance step by
# step"): the gateway butler's seconds-level "ask bm-X to report GPU status" face.
# FleetLink /status (listener v1.9.3 Get-StatusJson) already carries gpu / ram_free /
# cpu_load / disk_free / repo_heads / last_pull - this wrapper prints ONE compact
# ASCII line per node so a small daytime model can read it without JSON parsing.
# Read-only, fail-soft, exit 0 always. ASCII output only (encoding law).
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-node-status.ps1            (all enabled nodes)
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-node-status.ps1 -Node bm-c  (single node)
param(
  [string]$Root = "",
  [string[]]$Node = @()
)
$ErrorActionPreference = 'SilentlyContinue'
if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }
$rosterF = Join-Path $Root 'Tools\fleet-nodes.json'
if (-not (Test-Path $rosterF)) { Write-Output 'NODE-STATUS FATAL: roster missing'; exit 0 }
$roster = Get-Content -Raw -Encoding UTF8 $rosterF | ConvertFrom-Json
$port = 8790
if ($roster.PSObject.Properties.Name -contains 'port') { $port = [int]$roster.port }

# local origin/main head for behind-check (command plane)
$originHead = ''
try { $originHead = [string](& 'C:\Program Files\Git\cmd\git.exe' -C $Root rev-parse --short=8 origin/main) } catch { }

$now = Get-Date
Write-Output ('NODE-STATUS probe ' + $now.ToString('s') + '  (cite THIS timestamp)')
$found = 0
foreach ($n in @($roster.nodes)) {
  if ([bool]$n.enabled -ne $true) { continue }
  $id = [string]$n.id
  if ($Node.Count -gt 0 -and (@($Node | ForEach-Object { $_.ToLower() }) -notcontains $id.ToLower())) { continue }
  $found++
  $ip = [string]$n.tailnet_ip
  if ($ip -eq '') { Write-Output ('  ' + $id + ' empty-ip roster slot (never report as offline)'); continue }
  $tip = $ip
  if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $tip = '127.0.0.1' }
  $out = '  ' + $id
  try {
    $s = Invoke-RestMethod -Uri ('http://' + $tip + ':' + $port + '/status') -Method Get -TimeoutSec 12
    $out += ' host=' + [string]$s.host
    $gpu = [string]$s.gpu
    if ($gpu -ne '') {
      $gp = @($gpu -split ',') | ForEach-Object { $_.Trim() }
      $gname = ''
      if ($gp.Count -ge 1) { $gname = [string]$gp[0] }
      $gmem = ''
      if ($gp.Count -ge 2) { $gmem = [string]$gp[1] }
      $out += ' gpu=' + $gname + ' vram_free=' + $gmem
    } else { $out += ' gpu=none-or-nvidia-smi-missing' }
    $out += ' ram_free_gb=' + [string]$s.ram_free_gb
    $out += ' cpu_pct=' + [string]$s.cpu_load_pct
    $out += ' disk_c_free_gb=' + [string]$s.disk_free_gb
    if ($s.PSObject.Properties.Name -contains 'last_pull') {
      $lp = $s.last_pull
      if ($lp -and ($lp.PSObject.Properties.Name -contains 'reason')) {
        # ASCII-only, max 24 chars: poke reasons may carry CJK (bm-c accepts them)
        # which renders as mojibake through exec pipes - keep the ASCII prefix only.
        $reasonRaw = [string]$lp.reason
        $reasonAscii = -join (@($reasonRaw.ToCharArray()) | Where-Object { [int]$_ -lt 128 -and [int]$_ -ge 32 } | Select-Object -First 24)
        $out += ' last_pull_reason=' + $reasonAscii
      }
      if ($lp -and ($lp.PSObject.Properties.Name -contains 'repo_heads')) {
        $p9 = $lp.repo_heads.PSObject.Properties['.']
        if ($p9) {
          $sh = ([string]$p9.Value)
          $sh8 = $sh.Substring(0, [Math]::Min(8, $sh.Length))
          $out += ' head=' + $sh8
          if ($originHead -ne '' -and $sh8 -eq $originHead) { $out += '=synced' } else { $out += '=(behind-or-ahead)' }
        }
      }
      if ($lp -and ($lp.PSObject.Properties.Name -contains 'ts')) {
        $lpts = [datetime]::Parse([string]$lp.ts, [System.Globalization.CultureInfo]::InvariantCulture)
        $age = [int](($now - $lpts).TotalMinutes)
        $out += ' last_pull_age=' + $age + 'm'
      }
    }
  } catch {
    $out += ' UNREACHABLE (listener down or tailnet broken - check with fleet-reality.ps1)'
  }
  Write-Output $out
}
if ($found -eq 0) { Write-Output '  no roster node matched the -Node filter' }
Write-Output ('END node-status ' + (Get-Date -Format s) + ' - reports citing machine resources MUST carry this timestamp')
exit 0

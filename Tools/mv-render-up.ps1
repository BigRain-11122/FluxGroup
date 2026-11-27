# MV-RENDER-UP — start the ComfyUI renderer on this machine for fleet-driven MV work.
# Why: bm-c's ComfyUI binds 127.0.0.1 by default, so the HQ box (bm-a) cannot submit jobs
# over the tailnet. This launcher starts it on 0.0.0.0 so the fleet can drive it.
# Usage: double-click Tools\MV-RENDER-UP.bat  (or run this file with -Listen 0.0.0.0)

[CmdletBinding()]
param(
  [string]$Listen = '0.0.0.0',
  [int]$Port = 8188,
  [string]$ComfyRoot = ''
)

$ErrorActionPreference = 'Stop'
Set-ExecutionPolicy -Scope Process Bypass -Force

$Root = Split-Path -Parent $PSScriptRoot
$StateDir = Join-Path $env:USERPROFILE '.codely-cli'
$StatusF = Join-Path $StateDir 'mv-render-status.json'
$LogDir = Join-Path $env:TEMP 'mv-render'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
if (-not (Test-Path $StateDir)) { New-Item -ItemType Directory -Path $StateDir -Force | Out-Null }

function Write-Status([hashtable]$o) {
  $o['ts'] = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
  $o['host'] = $env:COMPUTERNAME
  ($o | ConvertTo-Json -Compress) | Set-Content -LiteralPath $StatusF -Encoding UTF8
}

function Test-ComfyUp([int]$p) {
  try {
    $r = Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/system_stats" -f $p) -TimeoutSec 3
    return $true
  } catch { return $false }
}

# ---- resolve the ComfyUI install ----
$candidates = @()
if ($ComfyRoot) { $candidates += $ComfyRoot }
if ($env:COMFYUI_ROOT) { $candidates += $env:COMFYUI_ROOT }
$candidates += @(
  (Join-Path $Root 'Tools\ComfyUI_windows_portable'),
  'K:\Fluxgroup\FluxGroup\Tools\ComfyUI_windows_portable',
  'D:\AI\comfyui-krea\ComfyUI_windows_portable',
  'D:\ComfyUI',
  'K:\ComfyUI',
  (Join-Path $env:USERPROFILE 'ComfyUI'),
  'C:\Users\sjs20\ComfyUI'
)

$comfy = $null
foreach ($c in $candidates) {
  if (-not $c) { continue }
  try {
    if (Test-Path ([IO.Path]::Combine($c, 'ComfyUI', 'main.py'))) { $comfy = $c; break }
  } catch { continue }
}

if (-not $comfy) {
  $msg = 'ComfyUI not found. Tried: ' + ($candidates -join ' | ')
  Write-Host $msg -ForegroundColor Red
  Write-Status @{ ok = $false; reason = 'not_installed'; detail = $msg; tried = $candidates }
  exit 2
}

$mainPy = Join-Path $comfy 'ComfyUI\main.py'
$py = Join-Path $comfy 'python_embeded\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }

if (Test-ComfyUp $Port) {
  Write-Host ("ComfyUI already up on {0} (root={1})" -f $Port, $comfy) -ForegroundColor Green
  Write-Status @{ ok = $true; already = $true; port = $Port; root = $comfy }
  exit 0
}

$outLog = Join-Path $LogDir ('comfy-{0}.out.log' -f (Get-Date).ToString('yyyyMMdd-HHmmss'))
$errLog = Join-Path $LogDir ('comfy-{0}.err.log' -f (Get-Date).ToString('yyyyMMdd-HHmmss'))

# --listen makes it reachable from the tailnet; --disable-auto-launch keeps it headless.
$pyArgs = @($mainPy, '--listen', $Listen, '--port', [string]$Port, '--disable-auto-launch')
Write-Host ("Starting ComfyUI: {0} {1}" -f $py, ($pyArgs -join ' '))
$p = Start-Process -FilePath $py -ArgumentList $pyArgs -WorkingDirectory (Join-Path $comfy 'ComfyUI') `
      -RedirectStandardOutput $outLog -RedirectStandardError $errLog -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(240)
$up = $false
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 3
  if ($p.HasExited) { break }
  if (Test-ComfyUp $Port) { $up = $true; break }
}

if ($up) {
  Write-Host ("ComfyUI UP on {0}:{1} (pid={2}, root={3})" -f $Listen, $Port, $p.Id, $comfy) -ForegroundColor Green
  Write-Host ("Logs: {0}" -f $LogDir)
  Write-Status @{ ok = $true; started = $true; port = $Port; listen = $Listen; pid = $p.Id; root = $comfy; log = $outLog }
  exit 0
} else {
  $tail = ''
  if (Test-Path $errLog) { $tail = (Get-Content $errLog -Tail 15 -ErrorAction SilentlyContinue) -join "`n" }
  Write-Host 'ComfyUI did NOT come up in 240s.' -ForegroundColor Red
  if ($tail) { Write-Host $tail -ForegroundColor DarkYellow }
  Write-Status @{ ok = $false; reason = 'boot_timeout'; root = $comfy; log = $errLog; tail = $tail }
  exit 3
}
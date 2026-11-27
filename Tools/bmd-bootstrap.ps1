# ============================================================
# BMD-BOOTSTRAP-v1.ps1  (bm-d Tier-1 onboarding, one-shot, idempotent)
# Canon : cph4/council/C-20261016-01  (six-card layered allocation)
# Doc   : cph4/fleet/bm-d-onboarding/BMD-ONBOARDING-v1.md
# Order : O-20261016-2148-bm-a        (CEO direct order 2026-10-16)
# Laws  : U060 zero-popup / S4U task principal / PS5.1 ASCII-only
#         source / no secrets in files / safe to re-run.
# USAGE : on bm-d (Windows 10/11 x64), open PowerShell AS ADMINISTRATOR:
#           iwr '<bootstrap-cdn-url>' -OutFile bmd-bootstrap.ps1
#           .\bmd-bootstrap.ps1
# Tier 1 does:
#   1) spec dump   : CPU / RAM / GPUs (nvidia-smi) / disk / OS -> log + JSON
#   2) power       : 24/7 node profile (high perf, no AC sleep)
#   3) tailnet     : install Tailscale if missing + login (browser once)
#   4) git         : install if missing (winget)
#   5) repos       : clone FluxGroup group repo + BigMoney repo
#                    (browser may ask GitHub login once - fleet account)
#   6) join-report : push cph4/fleet/bm-d-onboarding/JOIN-REPORT-<ts>.md
#                    (fleet loops merge the roster row, O-20261016-2148 sec.3)
#   7) FleetLink   : register :8790 listener task (S4U) + health check
# Tier 2 / Phase 1 are documented in BMD-ONBOARDING-v1.md.
# ============================================================

$ErrorActionPreference = 'Continue'
Set-ExecutionPolicy -Scope Process Bypass -Force

$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$log = Join-Path $scriptDir 'bmd-bootstrap-log.txt'
$script:ok = 0
$script:fail = 0

function Log([string]$m) {
  $line = ('[' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '] ' + $m)
  Write-Host $line
  Add-Content -LiteralPath $log -Value $line -Encoding ASCII
}
function Done([string]$m) { Log ('OK  ' + $m); $script:ok = $script:ok + 1 }
function Bad([string]$m)  { Log ('FAIL ' + $m); $script:fail = $script:fail + 1 }

Log 'BMD-BOOTSTRAP-v1 start'
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) { Done 'running as Administrator' } else { Bad 'NOT Administrator - Tailscale MSI / power steps will fail; re-run elevated' }

# ---------- Step 1: spec dump ----------
Log '--- STEP 1: spec dump ---'
$spec = [ordered]@{}
$spec['ts'] = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
$spec['hostname'] = $env:COMPUTERNAME
$osInfo = Get-CimInstance Win32_OperatingSystem
$spec['os'] = ([string]$osInfo.Caption + ' ' + [string]$osInfo.Version)
$spec['ram_total_gb'] = [math]::Round($osInfo.TotalVisibleMemorySize / 1MB, 1)
$spec['ram_free_gb'] = [math]::Round($osInfo.FreePhysicalMemory / 1MB, 1)
$cpuList = @()
$totCores = 0
$totThreads = 0
foreach ($c in (Get-CimInstance Win32_Processor)) {
  $cpuList += ([string]$c.Name.Trim() + ' | cores=' + $c.NumberOfCores + ' threads=' + $c.NumberOfLogicalProcessors)
  $totCores = $totCores + [int]$c.NumberOfCores
  $totThreads = $totThreads + [int]$c.NumberOfLogicalProcessors
}
$spec['cpu'] = $cpuList
$spec['cpu_total_cores'] = $totCores
$spec['cpu_total_threads'] = $totThreads
$gpuList = @()
try {
  $gpuList = @(& nvidia-smi --query-gpu=index,name,memory.total,driver_version,compute_cap,ecc.mode.current,power.limit,temperature.gpu --format=csv,noheader 2>$null)
} catch { $gpuList = @('nvidia-smi not available') }
$spec['gpus'] = $gpuList
$cdrv = Get-PSDrive C
$spec['disk_c_total_gb'] = [math]::Round(($cdrv.Used + $cdrv.Free) / 1GB, 1)
$spec['disk_c_free_gb'] = [math]::Round($cdrv.Free / 1GB, 1)
$spec['tailnet_ip'] = ''

$specLocal = Join-Path $scriptDir ('bmd-spec-' + $env:COMPUTERNAME + '.json')
$spec | ConvertTo-Json -Depth 4 | Out-File -LiteralPath $specLocal -Encoding utf8
try { & nvidia-smi -q > (Join-Path $scriptDir 'bmd-nvidia-smi-q-dump.txt') } catch { }
Log ('HOSTNAME : ' + $spec['hostname'])
Log ('OS       : ' + $spec['os'])
Log ('CPU      : ' + $totCores.ToString() + ' cores / ' + $totThreads.ToString() + ' threads')
foreach ($c in $cpuList) { Log ('  socket: ' + $c) }
Log ('RAM      : ' + $spec['ram_total_gb'].ToString() + ' GB total / ' + $spec['ram_free_gb'].ToString() + ' GB free')
foreach ($g in $gpuList) { Log ('  GPU: ' + $g) }
Log ('DISK C   : ' + $spec['disk_c_total_gb'].ToString() + ' GB total / ' + $spec['disk_c_free_gb'].ToString() + ' GB free')
Done 'spec dump (json + nvidia-smi -q dump)'

# ---------- Step 2: power profile for a 24/7 compute node ----------
Log '--- STEP 2: power profile (24/7 node) ---'
try {
  powercfg /setactive SCHEME_MIN 2>$null
  powercfg /change monitor-timeout-ac 10
  powercfg /change standby-timeout-ac 0
  powercfg /change hibernate-timeout-ac 0
  powercfg /change disk-timeout-ac 0
  Done 'power: high-performance scheme, AC sleep/hibernate/disk-off disabled'
} catch { Bad 'powercfg step failed (non-fatal)' }

# ---------- Step 3: tailnet join ----------
Log '--- STEP 3: tailnet join ---'
$tsExe = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
$tsHere = $false
if (Test-Path $tsExe) { $tsHere = $true }
if (-not $tsHere) {
  Log 'Tailscale not installed - downloading MSI ...'
  $msi = Join-Path $env:TEMP 'tailscale-setup-latest-amd64.msi'
  try {
    Invoke-WebRequest 'https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi' -OutFile $msi -UseBasicParsing
    Log 'Installing Tailscale (quiet, needs admin) ...'
    $p = Start-Process msiexec.exe -ArgumentList ('/i "' + $msi + '" /quiet /norestart') -Wait -PassThru
    if (Test-Path $tsExe) { $tsHere = $true; Done ('Tailscale installed (msiexec exit=' + $p.ExitCode + ')') }
    else { Bad ('Tailscale install failed (msiexec exit=' + $p.ExitCode + ') - install from https://tailscale.com/download then re-run') }
  } catch { Bad ('Tailscale download/install error: ' + $_.Exception.Message) }
} else { Log 'Tailscale binary present' }

if ($tsHere) {
  $logged = $false
  try {
    $st = (& $tsExe status 2>&1) -join "`n"
    if ($LASTEXITCODE -eq 0 -and $st -notmatch 'Logged out|not logged in|To authenticate') { $logged = $true }
  } catch { }
  if (-not $logged) {
    Log 'ACTION NEEDED: a browser window opens - log in with the fleet Tailscale account and approve THIS machine.'
    & $tsExe up
    if ($LASTEXITCODE -eq 0) { $logged = $true }
  }
  if ($logged) {
    $tsIp = [string](& $tsExe ip -4)
    $spec['tailnet_ip'] = $tsIp
    Done ('tailnet joined, IP = ' + $tsIp)
  } else { Bad 'tailscale login not completed - finish login then re-run this script (idempotent)' }
}

# ---------- Step 4: git ----------
Log '--- STEP 4: git ---'
$gitHere = $false
$gv = ''
try { $gv = (& git --version) -join ' '; if ($LASTEXITCODE -eq 0) { $gitHere = $true } } catch { }
if (-not $gitHere) {
  Log 'git not found - trying winget install ...'
  try {
    $p = Start-Process winget -ArgumentList 'install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements' -Wait -PassThru
    Log ('winget exit=' + $p.ExitCode)
  } catch { Log 'winget unavailable' }
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
  try { $gv = (& git --version) -join ' '; if ($LASTEXITCODE -eq 0) { $gitHere = $true } } catch { }
}
if ($gitHere) { Done ('git present: ' + $gv) }
else { Bad 'git missing - install from https://git-scm.com/download/win then re-run (idempotent)' }

# ---------- Step 5: repos ----------
Log '--- STEP 5: repos clone ---'
$root = 'C:\Fluxgroup\FluxGroup'
$bmRepo = Join-Path $root 'quant\bigmoney'
if ($gitHere) {
  if (-not (Test-Path (Join-Path $root '.git'))) {
    Log 'Cloning group repo FluxGroup (browser may ask GitHub login - fleet account) ...'
    & git clone https://github.com/BigRain-11122/FluxGroup.git $root
    if (Test-Path (Join-Path $root '.git')) { Done 'group repo cloned' } else { Bad 'group repo clone failed (check GitHub login)' }
  } else { Log 'group repo already present' }
  if (Test-Path (Join-Path $root '.git')) {
    if (-not (Test-Path (Join-Path $bmRepo '.git'))) {
      Log 'Cloning BigMoney repo ...'
      & git clone https://github.com/BigRain-11122/BigMoney.git $bmRepo
      if (Test-Path (Join-Path $bmRepo '.git')) { Done 'BigMoney repo cloned' } else { Bad 'BigMoney repo clone failed' }
    } else { Log 'BigMoney repo already present' }
    & git -C $root config user.name 'bm-d'
    & git -C $root config user.email 'bm-d@fleet.fluxgroup.local'
    if (Test-Path (Join-Path $bmRepo '.git')) {
      & git -C $bmRepo config user.name 'bm-d'
      & git -C $bmRepo config user.email 'bm-d@fleet.fluxgroup.local'
    }
  }
}

# ---------- Step 6: join report push ----------
Log '--- STEP 6: join report push ---'
if (Test-Path (Join-Path $root '.git')) {
  if (-not $spec['tailnet_ip']) { $spec['tailnet_ip'] = 'PENDING' }
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $jrDir = Join-Path $root 'cph4\fleet\bm-d-onboarding'
  if (-not (Test-Path $jrDir)) { New-Item -ItemType Directory -Path $jrDir -Force | Out-Null }
  Copy-Item -LiteralPath $specLocal -Destination (Join-Path $jrDir ('bmd-spec-' + $stamp + '.json')) -Force
  $jr = Join-Path $jrDir ('JOIN-REPORT-' + $stamp + '.md')
  $lines = @()
  $lines += '# JOIN-REPORT ' + $stamp + ' - bm-d Tier-1 onboarding'
  $lines += ''
  $lines += '- order: O-20261016-2148-bm-a (fleet side merges roster row on this landing)'
  $lines += '- hostname: ' + $spec['hostname']
  $lines += '- tailnet_ip: ' + $spec['tailnet_ip']
  $lines += '- root: ' + $root
  $lines += '- os: ' + $spec['os']
  $lines += '- cpu: ' + $spec['cpu_total_cores'].ToString() + ' cores / ' + $spec['cpu_total_threads'].ToString() + ' threads'
  foreach ($c in $cpuList) { $lines += '  - ' + $c }
  $lines += '- ram_total_gb: ' + $spec['ram_total_gb']
  $lines += '- ram_free_gb: ' + $spec['ram_free_gb']
  $lines += '- disk_c_total_gb: ' + $spec['disk_c_total_gb']
  $lines += '- disk_c_free_gb: ' + $spec['disk_c_free_gb']
  $lines += '- gpus:'
  foreach ($g in $gpuList) { $lines += '  - ' + $g }
  $lines += '- next: Tier-2 codely install (BMD-ONBOARDING-v1 section 4)'
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllLines($jr, $lines, $utf8NoBom)
  Log 'committing join report ...'
  & git -C $root add ('cph4/fleet/bm-d-onboarding/JOIN-REPORT-' + $stamp + '.md')
  & git -C $root add ('cph4/fleet/bm-d-onboarding/bmd-spec-' + $stamp + '.json')
  & git -C $root commit -m ('bmd onboard: tier-1 join report ' + $spec['hostname'] + ' ' + $spec['tailnet_ip'] + ' [via bm-d]')
  & git -C $root push
  if ($LASTEXITCODE -ne 0) {
    Log 'push rejected once - pull --rebase and retry ...'
    & git -C $root pull --rebase
    & git -C $root push
  }
  if ($LASTEXITCODE -eq 0) { Done 'join report pushed to origin' } else { Bad ('join report push failed - file kept locally: ' + $jr) }
} else { Bad 'join report skipped (group repo missing)' }

# ---------- Step 7: FleetLink ----------
Log '--- STEP 7: FleetLink listener registration ---'
$reg = Join-Path $root 'Tools\register-fleet-link.ps1'
if (Test-Path $reg) {
  try {
    & $reg -Root $root
    Done 'FleetLink registration attempted (see HEALTH line above)'
  } catch { Bad ('FleetLink registration failed: ' + $_.Exception.Message) }
} else { Bad 'register-fleet-link.ps1 not found in clone' }

# ---------- Summary ----------
Log '--- SUMMARY ---'
Log ('steps ok=' + $script:ok + ' fail=' + $script:fail)
Log ('tailnet_ip=' + $spec['tailnet_ip'] + '  hostname=' + $spec['hostname'])
if ($script:fail -eq 0) {
  Log 'TIER-1 COMPLETE. Fleet loops merge the roster row within ~10 min, then bm-d is poke-able.'
  Log 'Next: Tier-2 (codely CLI + BM loop tasks) per BMD-ONBOARDING-v1 section 4.'
} else {
  Log 'TIER-1 PARTIAL - fix the FAIL lines above and re-run this script (idempotent).'
}

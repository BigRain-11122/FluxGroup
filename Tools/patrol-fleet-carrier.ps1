# patrol-fleet-carrier.ps1 - generic domain patrol-seat carrier (L0' of PATROL-FLEET)
# O-20261014-2250, BLUEPRINT cph4/fleet/dispatcher/PATROL-FLEET/BLUEPRINT.md sec.3.
# One schtasks instance per domain (HQ-Patrol-<Code> PT30M). Zero-LLM sensor scan each run;
# on flags launches ONE hidden headless codely domain shift (gated: domain lock <10min,
# debounce 40min, same-signature re-fire window 360min, daily cap 4, shift-snooze
# negative feedback); once a day at the configured hour
# produces the domain digest via the LOCAL 35B (Tools/l1-client.py, zero cloud tokens).
# State: media/logs/patrol-fleet/<code>-state.json | Heartbeat: <code>-heartbeat.txt
# Logs (disk): <code>-shiftlog.md. Fleet git log: cph4/fleet/dispatcher/PATROL-FLEET/LOG.md (one line per shift).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File Tools\patrol-fleet-carrier.ps1 -Code bigmoney
param([Parameter(Mandatory=$true)][string]$Code)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$CfgF = Join-Path $PSScriptRoot 'patrol-fleet-config.json'
$Dir  = Join-Path $Root 'media\logs\patrol-fleet'
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$today = Get-Date -Format 'yyyy-MM-dd'

$cfg = Get-Content $CfgF -Raw -Encoding UTF8 | ConvertFrom-Json
$dom = $null
foreach ($d in @($cfg.domains)) { if ($d.code -eq $Code) { $dom = $d; break } }
if (-not $dom) { Write-Output ('UNKNOWN-CODE: ' + $Code); exit 1 }

$hbF   = Join-Path $Dir ($Code + '-heartbeat.txt')
$stF   = Join-Path $Dir ($Code + '-state.json')
$lockF = Join-Path $Dir ($Code + '.lock')
Set-Content -Path $hbF -Value ('alive ' + $stamp + ' ' + $Code) -Encoding UTF8

# 1) sensors -> flags (zero LLM)
function Resolve-SensorPath([string]$p) {
    $p2 = $p -replace '/', '\'
    if ([System.IO.Path]::IsPathRooted($p2)) { return $p2 }
    return (Join-Path $Root $p2)
}
$flags = @()
foreach ($s in @($dom.sensors)) {
    $abs = Resolve-SensorPath $s.path
    if ($s.type -eq 'must_exist') {
        if (-not (Test-Path $abs)) { $flags += ($s.path + ': MISSING (must_exist)') }
        continue
    }
    if ($s.type -eq 'mtime') {
        if (-not (Test-Path $abs)) { $flags += ($s.path + ': missing'); continue }
        $ageMin = ((Get-Date) - (Get-Item $abs).LastWriteTime).TotalMinutes
        if ($ageMin -gt [double]$s.max_age_min) {
            if (-not $s.digest_only) { $flags += ($s.path + ': stale ' + [math]::Round($ageMin,0) + 'min > ' + $s.max_age_min + 'min' + $(if ($s.weak) {' (weak git-copy sensor)'} else {''})) }
        }
        continue
    }
}
$dlPath = Join-Path $Root 'cph4\fleet\dispatcher\CEO-PROXY\DEADLINES.md'
$dlLines = @(Get-Content $dlPath -Encoding UTF8)
$dlCut = $dlLines.Count
for ($i = 0; $i -lt $dlLines.Count; $i++) { if ($dlLines[$i] -match '^##\s*§二') { $dlCut = $i; break } }
$dlSect1 = @($dlLines | Select-Object -First $dlCut)
foreach ($kw in @($dom.deadline_keywords)) {
    foreach ($l in $dlSect1) {
        if ($l -match [regex]::Escape($kw)) {
            if ($l -notmatch 'done-|已落地|closed|standing|scheduled') { $flags += ('DEADLINE: ' + $l.Trim().Substring(0, [Math]::Min(100, $l.Trim().Length))) }
            break
        }
    }
}
foreach ($p in @($dom.keyword_flags)) {
    $abs = Join-Path $Root ($p.file -replace '/', '\')
    if (-not (Test-Path $abs)) { continue }
    foreach ($l in (Get-Content $abs -Tail ([int]$p.tail) -Encoding UTF8)) {
        foreach ($pat in @($p.patterns)) {
            if ($l -match $pat) {
                $skip = $false
                foreach ($ex in @($p.exclude)) { if ($l -match $ex) { $skip = $true; break } }
                if (-not $skip) { $flags += ($p.file + ' :: ' + $l.Trim().Substring(0, [Math]::Min(90, $l.Trim().Length))) }
                break
            }
        }
    }
}
$flags = @($flags | Select-Object -Unique)
# snooze filter: a shift may verify a flag as noise (weak-sensor pull lag etc.) and snooze it
$snoozeF = Join-Path $Dir ($Code + '-snooze.json')
$snList = @()
if (Test-Path $snoozeF) { try { $sn0 = @(Get-Content $snoozeF -Raw -Encoding UTF8 | ConvertFrom-Json); if ($sn0.Count -eq 1 -and $sn0[0] -is [array]) { $snList = @($sn0[0]) } else { $snList = @($sn0) } } catch { $snList = @() } }
if ($snList.Count -gt 0) {
    $active = New-Object System.Collections.ArrayList
    foreach ($f in $flags) {
        $hit = $false
        foreach ($sn in $snList) {
            try { if ($sn.until -and ([datetime]$sn.until -gt (Get-Date)) -and $f.Contains([string]$sn.flag_prefix)) { $hit = $true; break } } catch {}
        }
        if (-not $hit) { [void]$active.Add($f) }
    }
    if ($active.Count -lt $flags.Count) {
        Add-Content -Path (Join-Path $Dir ($Code + '-shiftlog.md')) -Value ("$stamp SNOOZE filtered $($flags.Count) -> $($active.Count)") -Encoding UTF8
    }
    $flags = @($active)
}

# 2) daily digest (local 35B, zero cloud) - once per day at/after the configured hour
$digestDone = $false
if (Test-Path $stF) {
    try { $st0 = Get-Content $stF -Raw -Encoding UTF8 | ConvertFrom-Json; if ($st0.digest_date -eq $today) { $digestDone = $true } } catch {}
}
$digestNote = 'not-due'
if (-not $digestDone -and ((Get-Date).Hour -ge [int]$dom.digest_hour)) {
    $digestNote = 'ran'
    $dlDom = @()
    foreach ($kw in @($dom.deadline_keywords)) {
        foreach ($l in $dlSect1) {
            if ($l -match [regex]::Escape($kw)) { $dlDom += $l.Trim() }
        }
    }
    $sensState = @()
    foreach ($s in @($dom.sensors)) {
        $abs = Resolve-SensorPath $s.path
        $sensState += ($s.path + ' => ' + $(if (Test-Path $abs) { ((Get-Date) - (Get-Item $abs).LastWriteTime).ToString('hh\.hh\ \m\i\n') } else { 'missing' }))
    }
    $pf = Join-Path $Dir ($Code + '-digest-prompt.txt')
    $pl = @()
    $pl += ('你是集团巡视席（域=' + $dom.company + '）的本地日报助手。按章程雷达面（cph4/fleet/dispatcher/PATROL-FLEET/CHARTERS.md ' + $dom.charter_section + '）对今日域状态逐条给一行 verdict（OK/注意/红旗+一句话），不要客套。输入：')
    $pl += ('[死线域行] ' + $(if ($dlDom.Count) { ($dlDom -join ' | ') } else { '（无）' }))
    $pl += ('[传感状态] ' + ($sensState -join ' | '))
    $pl += '[当班旗] ' + $(if ($flags.Count) { ($flags -join ' | ') } else { '（零旗）' })
    [System.IO.File]::WriteAllLines($pf, $pl)
    $digestOut = Join-Path $Dir ($Code + '-digest-latest.md')
    try {
        & python (Join-Path $PSScriptRoot 'l1-client.py') --task ('patrol-digest-' + $Code) --prompt-file $pf --out $digestOut 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { throw ('l1-client exit=' + $LASTEXITCODE) }
        $digestNote = 'done'
        Add-Content -Path (Join-Path $Dir ($Code + '-shiftlog.md')) -Value ("$stamp DIGEST done -> $digestOut") -Encoding UTF8
        Add-Content -Path (Join-Path $Root 'cph4\fleet\dispatcher\PATROL-FLEET\LOG.md') -Value ("$stamp | $Code | digest | L1-local | 域日报产出（零云端 token）") -Encoding UTF8
    } catch {
        $digestNote = 'L1-unreachable (log-only, per G1+ chain: shift covers next morning)'
    }
}

# 3) write state (consumable by hub/other seats)
$digestPrev = ''
if (Test-Path $stF) { try { $digestPrev = [string]((Get-Content $stF -Raw -Encoding UTF8 | ConvertFrom-Json).digest_date) } catch { $digestPrev = '' } }
$stateObj = [ordered]@{
    code = $Code; stamp = $stamp; flags = $flags; flag_count = $flags.Count
    digest_date = $(if ($digestNote -eq 'done') { $today } else { $digestPrev })
    launches_today = 0; last_launch = ''; last_sig = ''
}
if (Test-Path $stF) {
    try {
        $prev = Get-Content $stF -Raw -Encoding UTF8 | ConvertFrom-Json
        $stateObj.last_sig = [string]$prev.last_sig
        if ($prev.launch_date -eq $today) { $stateObj.launches_today = [int]$prev.launches_today; $stateObj.last_launch = $prev.last_launch; $stateObj.launch_date = $today } else { $stateObj.launch_date = $today }
    } catch { $stateObj.launch_date = $today }
} else { $stateObj.launch_date = $today }
if (-not $stateObj.last_launch) { $stateObj.last_launch = ''; $stateObj.launch_date = $today }
Set-Content -Path $stF -Value ($stateObj | ConvertTo-Json -Depth 4) -Encoding UTF8

if ($flags.Count -eq 0) { exit 0 }

# 4) gates then launch ONE hidden headless domain shift
$lockAge = 999
if (Test-Path $lockF) { $lockAge = ((Get-Date) - (Get-Item $lockF).LastWriteTime).TotalMinutes }
if ($lockAge -lt 10) { Add-Content -Path (Join-Path $Dir ($Code + '-shiftlog.md')) -Value ("$stamp SKIP domain-lock ${lockAge}min") -Encoding UTF8; exit 0 }
$prevLaunch = [datetime]'2000-01-01'; $launchesToday = [int]$stateObj.launches_today
if ($stateObj.last_launch) { try { $prevLaunch = [datetime]$stateObj.last_launch } catch {} }
if (((Get-Date) - $prevLaunch).TotalMinutes -lt 40) { exit 0 }
$cap = 4; if ($dom.launch_cap_day) { $cap = [int]$dom.launch_cap_day }
if ($launchesToday -ge $cap) {
    Add-Content -Path (Join-Path $Dir ($Code + '-shiftlog.md')) -Value ("$stamp CAP $cap reached - alarm only: $($flags -join ' | ')") -Encoding UTF8
    exit 0
}
$sig = (($flags | Select-Object -Unique) -join ' || ') -replace '"', ''
if ($sig.Length -gt 600) { $sig = $sig.Substring(0, 600) }
$prevSig = [string]$stateObj.last_sig
if ($prevSig -and ($sig -eq $prevSig) -and (((Get-Date) - $prevLaunch).TotalMinutes -lt 360)) {
    Add-Content -Path (Join-Path $Dir ($Code + '-shiftlog.md')) -Value ("$stamp SAMESIG-SKIP (re-fire window 360min): " + $sig.Substring(0, [Math]::Min(80, $sig.Length))) -Encoding UTF8
    exit 0
}

$codely = 'C:\Users\sjs20\AppData\Local\Programs\Tuanjie Cowork\cli\bin\win32-x64\codely.exe'
if (-not (Test-Path $codely)) { $g = Get-Command codely -ErrorAction SilentlyContinue; if ($g) { $codely = $g.Source } else { Add-Content -Path (Join-Path $Dir ($Code + '-shiftlog.md')) -Value "$stamp FATAL codely.exe not found" -Encoding UTF8; exit 1 } }
$prompt = ('【巡视席·' + $dom.company + '·域=' + $Code + '·载体触发】你是集团 ' + $dom.company + ' 巡视席（PATROL-FLEET·正典=cph4/fleet/dispatcher/PATROL-FLEET/CHARTERS.md ' + $dom.charter_section + '）。触发现：' + $sig + ' 。按章程执行：锁门（' + $lockF + ' mtime<10min=他班在执·touch 锁继续·班毕再 touch）→读章程' + $dom.charter_section + '领域雷达面逐项核→深挖触发现（域判断优先本地 35B :8090 Tools/l1-client.py·深判走云端）→领域判断与行动（只读只议+章程即决清单·台账 orders/decisions/POOL 禁直写——产出=NEED-JUDGMENT 行〔带域标 ' + $Code + '〕+LOG.md 一行）→两轮未决=升级 NEED-JUDGMENT 候枢纽收。纪律：进程内调用禁 spawn 控制台；物理件/保留面零催办；传感复用禁重测；已核实为噪声的旗（如 weak 传感实为拉取滞后）→写或追加 snooze 件 media/logs/patrol-fleet/' + $Code + '-snooze.json（JSON 数组·元素字段 flag_prefix=旗行前 20 字、until=yyyy-MM-dd HH:mm〔≤24h〕·真实事故禁 snooze）。')
$outF = Join-Path $Dir ($Code + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.out.log')
$errF = $outF -replace '\.out\.log$', '.err.log'
# T0 CLOUD-OFF guard (CEO 2026-10-20): automation is local-only; never spawn the cloud CLI.
$__co = $PSScriptRoot
while ($__co -and -not (Test-Path (Join-Path $__co 'cph4\fleet\CLOUD-OFF-LOCAL-ONLY-v1.md'))) { $__co = Split-Path -Parent $__co }
if ($__co) {
    $__cl = Join-Path $__co 'media\logs\cloud-off-suppressed.log'
    $__cd = Split-Path -Parent $__cl
    if (-not (Test-Path $__cd)) { New-Item -ItemType Directory -Force -Path $__cd | Out-Null }
    Add-Content -Path $__cl -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + [System.IO.Path]::GetFileName($PSCommandPath) + ' | suppressed cloud round (T0)') -Encoding UTF8
    exit 0
}
$p = Start-Process -FilePath $codely -ArgumentList ('-p "' + $prompt + '" --approval-mode yolo --collaboration-mode default') -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $outF -RedirectStandardError $errF -PassThru
Set-Content -Path $lockF -Value ('shift ' + $stamp) -Encoding UTF8
$stateObj.launches_today = ($launchesToday + 1); $stateObj.last_launch = $stamp; $stateObj.last_sig = $sig
Set-Content -Path $stF -Value ($stateObj | ConvertTo-Json -Depth 4) -Encoding UTF8
Add-Content -Path (Join-Path $Dir ($Code + '-shiftlog.md')) -Value ("$stamp LAUNCHED pid=$($p.Id) sig=" + $sig.Substring(0, [Math]::Min(100, $sig.Length))) -Encoding UTF8
exit 0

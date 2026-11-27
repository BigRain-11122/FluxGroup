# proxy-event-carrier.ps1 - HQ-CEOProxyEventCarrier action body (G1 night-window L2 gap fix)
# Phase 1-alpha of MASTER-AGENT BLUEPRINT v2 (O-20261014-1745). Registered ONLY via Tools/task-register.ps1 (U060).
# Design: scans L0 outputs ONLY (sensor-reuse law, never re-probes machines); on red flags fires a
# hidden headless codely event shift. Gates: patrol lock / 40min debounce / 90min same-signature / daily cap 6.
$ErrorActionPreference = 'Stop'
$root   = 'C:\Users\sjs20\Desktop\FluxGroup'
$nj     = Join-Path $root 'cph4\fleet\dispatcher\NEED-JUDGMENT.md'
$dl     = Join-Path $root 'cph4\fleet\dispatcher\DISPATCH-LOG.md'
$probeJ = Join-Path $root 'media\logs\proxy-probe-current.json'
$lock   = Join-Path $root 'media\logs\ceo-proxy-patrol.lock'
$hb     = Join-Path $root 'media\logs\event-carrier-heartbeat.txt'
$stateF = Join-Path $root 'media\logs\event-carrier-state.json'
$clog   = Join-Path $root 'media\logs\event-carrier.log'
$stamp  = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$today  = Get-Date -Format 'yyyy-MM-dd'
Set-Content -Path $hb -Value "alive $stamp" -Encoding UTF8

function LogLine($msg) { Add-Content -Path $clog -Value "$stamp $msg" -Encoding UTF8 }

# 1) collect flags from L0 + probe outputs only
# 2026-10-31 R2.53 fix (carrier self-excite, registered R2.52): this loop used to take EVERY
# non-# NEED-JUDGMENT line (including long registry prose) and substring-match DISPATCH-LOG
# bodies, so an event shift's own SHIFT/ERRATUM narrative ("...STARVED-EXEC...") re-entered
# the next round as a fresh flag. Signature therefore never repeated and the 90min
# same-signature gate never applied; shifts kept re-diagnosing 10-28/10-29 flags.
# Rules now: only real flag rows, and only ones younger than $flagMaxAgeH.
$flags = @()
$stale = 0
$flagMaxAgeH = 6
if (Test-Path $nj) {
    foreach ($l in (Get-Content $nj -Encoding UTF8)) {
        $t = $l.Trim()
        if ($t -match '^- POOL-\d+\[blocked_by') {
            # blocked: <yyyy-MM-dd HH:mm> - a card blocked for more than a day is a
            # registered structural/CEO-physical wait, not a fresh event.
            $bt = [datetime]::MinValue
            if ($t -match 'blocked:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})') {
                try { $bt = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm', $null) } catch { $bt = [datetime]::MinValue }
            }
            if ($bt -ne [datetime]::MinValue -and ((Get-Date) - $bt).TotalHours -gt 24) { $stale++; continue }
            $flags += ('NJ: ' + $t)
        }
        elseif ($t -match '^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\[PROBE\]') {
            # NJ probe rows are an append-only historical record; fresh alarms come from
            # probe-current.json below. Only a probe row younger than 2h is a live signal.
            $pt = [datetime]::MinValue
            try { $pt = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null) } catch { $pt = [datetime]::MinValue }
            if ($pt -eq [datetime]::MinValue -or ((Get-Date) - $pt).TotalHours -gt 2) { $stale++; continue }
            $flags += ('NJ: ' + $t)
        }
    }
}
if (Test-Path $dl) {
    foreach ($l in (Get-Content $dl -Tail 80 -Encoding UTF8)) {
        if ($l -notmatch '^\s*\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s+FLAG\b') { continue }
        if ($l -match 'QUEUE-LOW') { continue }
        $ft = [datetime]::MinValue
        try { $ft = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm', $null) } catch { $ft = [datetime]::MinValue }
        if ($ft -eq [datetime]::MinValue -or ((Get-Date) - $ft).TotalHours -gt $flagMaxAgeH) {
            $stale++
            continue
        }
        $flags += ('DL: ' + $l)
    }
}
if (Test-Path $probeJ) {
    $pjAge = ((Get-Date) - (Get-Item $probeJ).LastWriteTime).TotalHours
    if ($pjAge -gt 2) {
        $flags += 'PROBE-DOWN: probe-current.json stale >2h'
    } else {
        try {
            $pj = Get-Content $probeJ -Raw -Encoding UTF8 | ConvertFrom-Json
            foreach ($a in @($pj.alarms)) { if ($a) { $flags += ('PROBE: ' + $a) } }
        } catch { LogLine ('probe-json-parse-fail: ' + $_.Exception.Message) }
    }
} else {
    LogLine 'probe-current.json missing (probe never ran or first boot) - log only'
}
if ($flags.Count -eq 0) {
    if ($stale -gt 0) { LogLine ('no fire: {0} stale FLAG row(s) older than {1}h (already registered, not re-fired)' -f $stale, $flagMaxAgeH) }
    exit 0
}

# 2) gates
$lockAge = 999
if (Test-Path $lock) { $lockAge = ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalMinutes }
if ($lockAge -lt 10) { LogLine ('SKIP patrol-lock age={0:N1}min' -f $lockAge); exit 0 }

$sig = ((($flags | Sort-Object -Unique) -join ' || ') -replace '"', '')
$lastLaunch = [datetime]'2000-01-01'; $launchesToday = 0; $lastSig = ''
if (Test-Path $stateF) {
    try {
        $st = Get-Content $stateF -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($st.launch_date -eq $today) { $launchesToday = [int]$st.launches_today }
        $lastSig = [string]$st.last_signature
        if ($st.last_launch) { $lastLaunch = [datetime]$st.last_launch }
    } catch { LogLine ('state-parse-fail: ' + $_.Exception.Message) }
}
if (((Get-Date) - $lastLaunch).TotalMinutes -lt 40) { LogLine 'SKIP debounce <40min'; exit 0 }
if (($sig -eq $lastSig) -and (((Get-Date) - $lastLaunch).TotalMinutes -lt 90)) { LogLine 'SKIP same-signature <90min'; exit 0 }
if ($launchesToday -ge 6) { LogLine ('CAP daily-6 reached - alarm only: ' + $sig); exit 0 }

# 3) launch hidden headless codely event shift
$codely = $env:CODELY_CLI
if (-not $codely -or -not (Test-Path $codely)) { $codely = 'D:\TUANJIEAI\Tuanjie Cowork\cli\bin\win32-x64\codely.exe' }
if (-not (Test-Path $codely)) {
    $g = Get-Command codely -ErrorAction SilentlyContinue
    if ($g) { $codely = $g.Source } else { LogLine 'FATAL codely.exe not found'; exit 1 }
}
$flagText = ($sig -replace "`r|`n", ' ')
if ($flagText.Length -gt 600) { $flagText = $flagText.Substring(0, 600) }
$prompt = '【CEO 总调度代理席·事件班·承载件触发】你是集团 CEO 总调度代理席。按 C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\dispatcher\CEO-PROXY\ROUND.md 事件班协议执行本班。触发现：' + $flagText + ' 。步0 锁门同守（media/logs/ceo-proxy-patrol.lock mtime <10min=他窗在执·本窗跳班记 LOG）；全力深挖触发现→落单+poke 唤醒（tasks 白名单=Tools/fleet-nodes.json 的 wake_tasks）→3 分钟复探验 BURNING→NEED-JUDGMENT 件裁决并更新→LOG 记事件班全程（班型=事件班·标注承载件触发）。纪律：进程内调用禁 spawn 控制台；台账追加走 python 尾锚正法+原子推正法（Tools/git-atomic-push.py）+推前反转闸；物理件/保留面零催办只登记。'
$outF = Join-Path $root ('media\logs\event-carrier-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.out.log')
$errF = ($outF -replace '\.out\.log$', '.err.log')
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
$p = Start-Process -FilePath $codely -ArgumentList ('-p "' + $prompt + '" --approval-mode yolo --collaboration-mode default') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $outF -RedirectStandardError $errF -PassThru
$stateObj = @{ last_launch = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); launch_date = $today; launches_today = ($launchesToday + 1); last_signature = $sig } | ConvertTo-Json
Set-Content -Path $stateF -Value $stateObj -Encoding UTF8
$sigHead = $sig
if ($sigHead.Length -gt 120) { $sigHead = $sigHead.Substring(0, 120) }
LogLine ('LAUNCHED pid=' + $p.Id + ' sig=' + $sigHead)
exit 0

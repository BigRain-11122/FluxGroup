# hotapi_keepalive.ps1 - ShortVideo hot-list API (:6688) self-heal.
# CEO order 2026-10-16: "when local is down, restore via cloud - production must not stop".
# This leg keeps the LOCAL channel alive; if revive ever fails twice in a row, the
# consuming layer (hot_scan.py fault-tolerance + cloud/other-source fallback) takes over.
# Law refs: U060 zero-window (runs via task-register.ps1 front door only, S4U + hidden chain).
# Probe port 6688; if no listener -> relaunch the proven serve-hidden.vbs launcher,
# wait 10s, re-probe. Exit 0 = alive (or revived); exit 1 = revive failed (fail-loud).
# Logs revive/fail events only -> K:\Fluxgroup\.tools\DailyHotApi\logs\keepalive.log
$ErrorActionPreference = 'Stop'

$deployDir = 'K:\Fluxgroup\.tools\DailyHotApi'
$vbs       = Join-Path $deployDir 'serve-hidden.vbs'
$log       = Join-Path $deployDir 'logs\keepalive.log'
$nodeDir   = 'C:\Users\Dasheng\tools\nodejs'

function Test-Port6688 {
    try {
        $c = Get-NetTCPConnection -LocalPort 6688 -State Listen -ErrorAction SilentlyContinue
        return [bool]$c
    } catch { return $false }
}

if (Test-Port6688) { exit 0 }

# S4U sessions may not carry the interactive user PATH; make node resolvable for the vbs->cmd chain
if (Test-Path $nodeDir) { $env:Path = $nodeDir + ';' + $env:Path }

# the vbs redirects node output into this dir; make sure it exists (reboot-safe)
New-Item -ItemType Directory -Force -Path 'K:\Fluxgroup\.codely-cli\tmp' | Out-Null

$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
try {
    Start-Process wscript.exe -ArgumentList ('//B //nologo "' + $vbs + '"') -WindowStyle Hidden
    Start-Sleep -Seconds 10
    if (Test-Port6688) {
        Add-Content -LiteralPath $log -Value ($stamp + ' REVIVED ok')
        exit 0
    }
    Add-Content -LiteralPath $log -Value ($stamp + ' REVIVE-FAIL: no listener after launch')
    exit 1
} catch {
    Add-Content -LiteralPath $log -Value ($stamp + ' REVIVE-FAIL: ' + $_.Exception.Message)
    exit 1
}

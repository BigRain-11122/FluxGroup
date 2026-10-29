#!/usr/bin/env pwsh
# pause-local-business.ps1 - stop every local business loop on bm-a, keep only guards.
# CEO 2026-10-29: "我这个机器很卡 你先把本机业务都暂停"
# Reversible: the disabled list is written to .codely-cli/tmp/paused-business.json
$ErrorActionPreference = 'SilentlyContinue'
$root = 'C:\Users\sjs20\Desktop\FluxGroup'
$keep = @('HQ-GameGuard', 'HQ-SilenceGuard', 'HQ-SilenceGuard-Lane', 'HQ-WT-Park',
          'MiniGamePopupWitness', 'HQ-MemoryBudgetGate')
$skipPrefix = @('Microsoft', 'Adobe', 'NVIDIA', 'NvDriver', 'OneDrive', 'Asus', 'AMD',
                'ApplyUpdate', 'BlueStacks', 'Quark', 'SoftLanding', 'UU', 'bm-a-AutoYield')

$paused = @()
Get-ScheduledTask | Where-Object { $_.TaskPath -notmatch 'Microsoft' } | ForEach-Object {
    $name = $_.TaskName
    if ($keep -contains $name) { return }
    if ($skipPrefix | Where-Object { $name -like ($_ + '*') }) { return }
    if ($_.State -eq 'Disabled') { return }
    try {
        Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        schtasks /change /tn $name /disable | Out-Null
        if ((Get-ScheduledTask -TaskName $name).State -eq 'Disabled') { $paused += $name }
    } catch { }
}

$out = Join-Path $root '.codely-cli\tmp\paused-business.json'
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
@{ ts = (Get-Date -Format s); mode = 'pause-all-business'; paused = $paused } |
    ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $out -Encoding UTF8

# free the model memory too
Get-Process ollama, llama-server -ErrorAction SilentlyContinue | ForEach-Object {
    try { Stop-Process -Id $_.Id -Force } catch { }
}

"paused=$($paused.Count) kept=$($keep -join ',')"
"list: $out"
$paused | ForEach-Object { "  - $_" }
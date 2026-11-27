# task-s4u-convert.ps1 - convert task-s4u-backlog.md pending rows to S4U (fleet law 2026-09-29).
# MUST run from an ELEVATED PowerShell: UAC boxes deny unelevated S4U registration
# (bm-a 2026-10-16 live evidence: Register-ScheduledTask + schtasks /XML both denied).
# Idempotent: tasks already S4U are skipped. Results are appended to the backlog file.
param([string[]]$TaskNames = @())
$ErrorActionPreference = 'Stop'
$bl = Join-Path $PSScriptRoot 'task-s4u-backlog.md'
$wp = [System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $wp.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Output 'NOT ELEVATED - S4U conversion is denied on UAC boxes. Run from an elevated PowerShell.'
    exit 2
}
if (-not (Test-Path $bl)) { Write-Output 'no backlog file - nothing to convert'; exit 0 }
if ($TaskNames.Count -eq 0) {
    foreach ($ln in (Get-Content -LiteralPath $bl -Encoding UTF8)) {
        if ($ln -match '^\|\s*\d{4}-\d{2}-\d{2} [^|]*\|\s*([^|]+?)\s*\|\s*S4U denied') { $TaskNames += $Matches[1].Trim() }
    }
}
if ($TaskNames.Count -eq 0) { Write-Output 'no pending rows'; exit 0 }
$conv = @()
foreach ($n in ($TaskNames | Select-Object -Unique)) {
    $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
    if (-not $t) { Write-Output "MISSING $n"; continue }
    if ([string]$t.Principal.LogonType -eq 'S4U') { Write-Output "already-S4U $n"; continue }
    $xml = [string](Export-ScheduledTask -TaskName $n)
    if ($xml -notmatch '<LogonType>InteractiveToken</LogonType>') { Write-Output "SKIP $n (unexpected LogonType)"; continue }
    $xml = $xml.Replace('<LogonType>InteractiveToken</LogonType>', '<LogonType>S4U</LogonType>')
    $f = Join-Path $env:TEMP ("s4u-conv-" + $n + ".xml")
    [IO.File]::WriteAllText($f, $xml, [System.Text.Encoding]::Unicode)
    schtasks /Create /TN $n /XML $f /F 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Output "DENIED $n rc=$LASTEXITCODE"; continue }
    $chk = Get-ScheduledTask -TaskName $n
    if ([string]$chk.Principal.LogonType -eq 'S4U') { Write-Output "CONVERTED $n"; $conv += $n } else { Write-Output "VERIFY-FAIL $n" }
}
if ($conv.Count -gt 0) {
    Add-Content -LiteralPath $bl -Value ('| ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + ($conv -join ', ') + ' | converted to S4U (elevated run) |') -Encoding UTF8
}
exit 0

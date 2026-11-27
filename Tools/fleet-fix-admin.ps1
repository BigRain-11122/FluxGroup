# fleet-fix-admin.ps1 - one-shot elevation fix for fleet health on a Windows node v1.0
# Why: two blockers need admin and cannot be fixed from a normal user session:
#   1) w32time service stopped  -> clock skew breaks leases/event order
#   2) FluxGroup-FleetLink task LogonType=Interactive -> listener dies on logoff
#      (fleet law: every lane task must be S4U, InteractiveToken forbidden)
# Run: right-click -> Run with PowerShell as administrator, or:
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\fleet-fix-admin.ps1
# Read-only checks first; each change is read back. Safe to re-run (idempotent).
# ASCII-only body; PS 5.1 safe.
$ErrorActionPreference = 'Continue'

$isAdmin = (New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  'ERROR: not elevated. Right-click this file -> Run as administrator.'
  exit 2
}

$fail = 0

'== w32time =='
try {
  Set-Service -Name w32time -StartupType Automatic -ErrorAction Stop
  Start-Service -Name w32time -ErrorAction Stop
  'w32time=started startup=Automatic'
} catch {
  'w32time=FAIL ' + $_.Exception.Message
  $fail++
}
(w32tm /resync 2>&1 | Out-String).Trim()
(Get-Service -Name w32time | Select-Object Name, Status, StartType | Format-Table -AutoSize | Out-String)

'== fleetlink S4U =='
try {
  $t = Get-ScheduledTask -TaskName 'FluxGroup-FleetLink' -ErrorAction Stop
  'before_logontype=' + $t.Principal.LogonType
  $p = $t.Principal
  $p.LogonType = 'S4U'
  Set-ScheduledTask -TaskName 'FluxGroup-FleetLink' -Principal $p -ErrorAction Stop | Out-Null
  $after = (Get-ScheduledTask -TaskName 'FluxGroup-FleetLink').Principal.LogonType
  'after_logontype=' + $after
  if ($after -ne 'S4U') { 'fleetlink=FAIL logontype=' + $after; $fail++ }
} catch {
  'fleetlink=FAIL ' + $_.Exception.Message
  $fail++
}

try { Start-ScheduledTask -TaskName 'FluxGroup-FleetLink' -ErrorAction SilentlyContinue } catch { }
Start-Sleep -Seconds 3
try {
  $h = Invoke-RestMethod -Uri 'http://100.110.185.62:8790/health' -TimeoutSec 6
  'health=ok version=' + $h.version + ' node=' + $h.node
} catch {
  'health=ERR ' + $_.Exception.Message
  $fail++
}

if ($fail -eq 0) { 'RESULT=PASS' } else { 'RESULT=FAIL items=' + $fail }
exit $fail

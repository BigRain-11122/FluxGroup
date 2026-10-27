# memory-curator-gate.ps1 - 4h gate wrapper (memory-curator seat, CEO order 2026-10-18)
# Wrapped by Tools\task-register.ps1 (S4U + InvisibleRunner hidden chain, zero window).
# Resolves python per machine (bm-a/bm-b/bm-c differ), then runs the v2 gate in
# --scheduled mode (stdout guard inside; logs to gate-log.txt).
$root = Split-Path $PSScriptRoot
$py = ''
try { $py = (Get-Command pythonw.exe -ErrorAction Stop).Source } catch { }
if (-not $py) { try { $py = (Get-Command python.exe -ErrorAction Stop).Source } catch { } }
if (-not $py -and (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python314\pythonw.exe")) { $py = "$env:LOCALAPPDATA\Programs\Python\Python314\pythonw.exe" }
if (-not $py) { exit 1 }
$env:PYTHONIOENCODING = 'utf-8'
$logDir = Join-Path $root 'media\logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
& $py (Join-Path $root 'Tools\memory-budget-gate.py') --scheduled *>> (Join-Path $logDir 'memory-curator-gate.log')
exit $LASTEXITCODE

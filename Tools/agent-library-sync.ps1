# agent-library-sync.ps1 - install/update local skill copies from git canon (cph4/skills).
# Canon = cph4/skills/<name>/SKILL.md (+ ccgs/* children). Install copy = .codely-cli/skills/<name>/.
# Idempotent; -WhatIf supported (reports only). Skills activate from the NEXT session start.
# Per cph4/agents/GOVERNANCE.md section 3. ASCII only (PS5.1 encoding law).
param([switch]$WhatIf)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$canonRoot = Join-Path $root 'cph4\skills'
$localRoot = Join-Path $root '.codely-cli\skills'

if (-not (Test-Path $canonRoot)) { Write-Output 'FATAL: canon dir not found: ' + $canonRoot; exit 1 }
if (-not (Test-Path $localRoot)) { New-Item -ItemType Directory -Path $localRoot -Force | Out-Null }

$sources = @{}   # name -> source SKILL.md path; top-level canon wins over ccgs upstream on name clash
$ccgs = Join-Path $canonRoot 'ccgs'
if (Test-Path $ccgs) {
    Get-ChildItem $ccgs -Directory | ForEach-Object {
        $sk2 = Join-Path $_.FullName 'SKILL.md'
        if (Test-Path $sk2) { $sources[$_.Name] = $sk2 }
    }
}
Get-ChildItem $canonRoot -Directory | Where-Object { $_.Name -ne 'ccgs' } | ForEach-Object {
    $sk = Join-Path $_.FullName 'SKILL.md'
    if (Test-Path $sk) { $sources[$_.Name] = $sk }
}

$installed = 0; $updated = 0; $unchanged = 0
foreach ($name in $sources.Keys) {
    $src = $sources[$name]
    $dstDir = Join-Path $localRoot $name
    $dst = Join-Path $dstDir 'SKILL.md'
    if (Test-Path $dst) {
        $srcHash = (Get-FileHash $src -Algorithm SHA256).Hash
        $dstHash = (Get-FileHash $dst -Algorithm SHA256).Hash
        if ($srcHash -eq $dstHash) { $unchanged++; continue }
        $action = 'UPDATE'
    } else { $action = 'INSTALL' }
    if ($WhatIf) { Write-Output ("[WhatIf] {0}: {1}" -f $action, $name); continue }
    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    Copy-Item $src $dst -Force
    if ($action -eq 'INSTALL') { $installed++ } else { $updated++ }
    Write-Output ("{0}: {1}" -f $action, $name)
}

Write-Output ("SUMMARY: canon={0} installed={1} updated={2} unchanged={3}" -f $sources.Count, $installed, $updated, $unchanged)
if (-not $WhatIf) { Write-Output 'NOTE: new/updated skills activate from the NEXT session start.' }

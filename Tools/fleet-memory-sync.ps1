# fleet-memory-sync.ps1 - Fleet GLOBAL memory union-sync v1.0 (CEO order O-20261009-1845:
# "去机队其他机器，记忆就缺失" - the global CODELY.md is per-machine and never traveled).
# Mechanism: a canonical union copy lives IN THE REPO (cph4/fleet/memory/CODELY-fleet-global.md,
# HOT sync-plane). Every machine unions its local global memory with the canonical:
#   - local-only entries    -> appended into the canonical (inside their ### section)
#   - canonical-only entries -> appended into the local file (inside their ### section)
# Union is APPEND-ONLY, exact-line dedup (section+line key): ZERO LOSS both directions
# (same law as the bm-c r813 workspace-union precedent). If the canonical gained entries,
# the script commits+pushes it (HOT channel - every node picks it up on the next poke).
# PS 5.1 safe: ASCII-only script body; memory CONTENT (any language) flows through
# [IO.File] ReadAllText/WriteAllText untouched. BOM preserved per file.
# Fail-soft: any error -> log + exit 0. Never blocks the poke worker.
param(
  [string]$Root = "C:\Users\sjs20\Desktop\FluxGroup",
  [string]$LocalMem = '',
  [string]$CanonRel = 'cph4/fleet/memory/CODELY-fleet-global.md',
  [switch]$Quiet
)
$ErrorActionPreference = 'Continue'
if ($LocalMem -eq '') { $LocalMem = Join-Path $env:USERPROFILE '.codely-cli\CODELY.md' }
$Canon = Join-Path $Root ($CanonRel -replace '/', '\')

function Read-TextBom([string]$path) {
  $t = ''; $bom = $false
  if (Test-Path -LiteralPath $path) {
    $b = [IO.File]::ReadAllBytes($path)
    if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) { $bom = $true }
    $t = [Text.Encoding]::UTF8.GetString($b)
  }
  return @{ text = $t; bom = $bom }
}
function Write-TextBom([string]$path, [string]$text, [bool]$bom) {
  [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding($bom)))
}

function Split-Lines([string]$t) { return @($t -split '\r?\n') }

function Get-Entries([string]$t) {
  # ordered list of @{ sec; line } for memory entry lines ('- [ts] ...'),
  # tagged with the ### section they live under ('' = before any header)
  $list = @()
  $sec = ''
  foreach ($ln in (Split-Lines $t)) {
    if ($ln -match '^###\s*(.+?)\s*$') { $sec = $Matches[1]; continue }
    if ($ln -match '^-\s*\[') { $list += @{ sec = $sec; line = $ln } }
  }
  return $list
}

function Merge-IntoText([string]$baseText, [string]$addText) {
  # append add-entries that are missing in base (key = section+line), each inserted
  # right after the last entry of the same section (or right after the section header
  # if that section has no entries yet; section missing entirely -> appended at EOF).
  # returns @{ text; added }
  $baseLines = @(Split-Lines $baseText)
  $baseKeys = @{}
  $baseSec = ''
  $sep = [string][char]31
  foreach ($ln in $baseLines) {
    if ($ln -match '^###\s*(.+?)\s*$') { $baseSec = $Matches[1]; continue }
    if ($ln -match '^-\s*\[') { $baseKeys[($baseSec + $sep + $ln)] = $true }
  }
  $addEntries = @(Get-Entries $addText)
  $adds = @()
  $addSec = ''
  foreach ($e in $addEntries) {
    $k = ($e.sec + $sep + $e.line)
    if (-not $baseKeys.ContainsKey($k)) { $adds += $e }
  }
  if (@($adds).Count -eq 0) { return @{ text = $baseText; added = 0 } }
  # group by section, preserve order
  $bySec = @{}
  $secOrder = @()
  foreach ($e in $adds) {
    if (-not $bySec.ContainsKey($e.sec)) { $bySec[$e.sec] = @(); $secOrder += $e.sec }
    $bySec[$e.sec] += $e.line
  }
  # insertion indexes per section (into baseLines)
  $inserts = @{}   # index -> lines[] (bottom-up application)
  $headerIdx = @{} # sec -> header line index
  $lastEntryIdx = @{} # sec -> index of last entry line in that section
  $sec = ''
  for ($i = 0; $i -lt $baseLines.Count; $i++) {
    $ln = $baseLines[$i]
    if ($ln -match '^###\s*(.+?)\s*$') { $sec = $Matches[1]; $headerIdx[$sec] = $i; continue }
    if ($ln -match '^-\s*\[') { $lastEntryIdx[$sec] = $i }
  }
  $eofAdds = @()
  foreach ($s in $secOrder) {
    if ($headerIdx.ContainsKey($s)) {
      $at = $headerIdx[$s] + 1
      if ($lastEntryIdx.ContainsKey($s)) { $at = $lastEntryIdx[$s] + 1 }
      if (-not $inserts.ContainsKey($at)) { $inserts[$at] = @() }
      foreach ($l in $bySec[$s]) { $inserts[$at] += $l }
    } else {
      $eofAdds += $s
    }
  }
  $out = New-Object System.Collections.Generic.List[string]
  for ($i = 0; $i -lt $baseLines.Count; $i++) {
    if ($inserts.ContainsKey($i)) { foreach ($l in $inserts[$i]) { $out.Add($l) } }
    $out.Add($baseLines[$i])
  }
  if ($inserts.ContainsKey($baseLines.Count)) { foreach ($l in $inserts[$baseLines.Count]) { $out.Add($l) } }
  foreach ($s in $eofAdds) {
    $out.Add('')
    $out.Add('### ' + $s)
    foreach ($l in $bySec[$s]) { $out.Add($l) }
  }
  return @{ text = ($out -join "`n"); added = @($adds).Count }
}

# ---- run ----
$localRead = Read-TextBom $LocalMem
$canonRead = Read-TextBom $Canon
if ($canonRead.text -eq '') {
  # bootstrap: canonical = full copy of the richest local (first adopter seeds the fleet)
  $canonDir = Split-Path $Canon -Parent
  if (-not (Test-Path $canonDir)) { New-Item -ItemType Directory -Path $canonDir -Force | Out-Null }
  Write-TextBom $Canon $localRead.text $localRead.bom
  if (-not $Quiet) { Write-Output ('MEMSYNC bootstrap: canonical seeded from ' + $LocalMem + ' (' + (@(Get-Entries $localRead.text)).Count + ' entries)') }
}
$locAdd = 0; $canAdd = 0; $pushed = ''
# 1) local-only entries -> canonical
$m1 = Merge-IntoText $canonRead.text $localRead.text
if ($m1.added -gt 0) {
  Write-TextBom $Canon $m1.text $canonRead.bom
  $canAdd = $m1.added
}
# 2) canonical-only entries -> local (never delete local; append-only)
$m2 = Merge-IntoText $localRead.text $canonRead.text
if ($m2.added -gt 0) {
  try { Copy-Item -LiteralPath $LocalMem -Destination ($LocalMem + '.bak-fms') -Force } catch { }
  Write-TextBom $LocalMem $m2.text $localRead.bom
  $locAdd = $m2.added
}
# 3) commit+push the canonical if it gained entries
if ($canAdd -gt 0) {
  $git = 'C:\Program Files\Git\cmd\git.exe'
  if (-not (Test-Path $git)) { $git = 'git' }
  try {
    & $git -C $Root add $CanonRel 2>&1 | Out-Null
    & $git -C $Root commit -m ("fleet-memory-union: +" + $canAdd + " entries [via " + $env:COMPUTERNAME + "]") -- $CanonRel 2>&1 | Out-Null
    $sha = [string](& $git -C $Root rev-parse HEAD)
    & $git -C $Root push origin ("$sha" + ':refs/heads/main') 2>&1 | Out-Null
    $pushed = $sha.Substring(0, 8)
  } catch { }
}
if (-not $Quiet) { Write-Output ('MEMSYNC local+' + $locAdd + ' canon+' + $canAdd + ' pushed=' + $pushed) }
exit 0

# fleet-memory-sync.ps1 - Fleet GLOBAL memory sync v2.1 (CEO order O-20261009-1845 union-sync
# + O-20261009-1915 four-word law: lean / always-maintained / always-fresh / scientific).
# v2 semantics = CANONICAL-AUTHORITATIVE (the append-only union of v1 preserved bloat forever):
#   1. INBOX-UP (v2.1, C-20261016-02 Cure-4): fresh local entries FIRST land in this host's
#      own staging file cph4/fleet/memory/inbox/<node>.md - one file per machine = zero
#      cross-machine write conflicts, and a durable git-committed claim: if the canonical
#      is ever clobbered again (11:48 rollback family), the next run re-unions every entry
#      from the inboxes = self-healing canon.
#   2. UNION-UP: entries (inbox + local, not tombstoned) -> appended into the canonical, commit+push
#   3. REPLACE-DOWN: the local global file becomes the canonical text verbatim
#      -> grooming (merges/prunes) in the canonical propagates to every machine
#   4. TOMBSTONES: entries deliberately removed by grooming are hash-registered in
#      memory-tombstones.jsonl so union-up can NEVER resurrect them. Zero-loss holds:
#      pruned content stays in the canonical's git history (memory.md R1: archive-not-erase).
#   -RecordRemoval: run AFTER a grooming edit of the canonical (before commit): diffs the
#      committed canonical vs the edited one and registers hashes of removed entries.
# PS 5.1 safe: ASCII body; content flows via [IO.File] untouched; BOM preserved per file.
# Fail-soft: any error -> log + exit 0. Never blocks the poke worker.
param(
  [string]$Root = "C:\Users\sjs20\Desktop\FluxGroup",
  [string]$LocalMem = '',
  [string]$CanonRel = 'cph4/fleet/memory/CODELY-fleet-global.md',
  [string]$TombRel = 'cph4/fleet/memory/memory-tombstones.jsonl',
  [switch]$RecordRemoval,
  [switch]$Quiet
)
$ErrorActionPreference = 'Continue'
if ($LocalMem -eq '') { $LocalMem = Join-Path $env:USERPROFILE '.codely-cli\CODELY.md' }
$Canon = Join-Path $Root ($CanonRel -replace '/', '\')
$TombF = Join-Path $Root ($TombRel -replace '/', '\')

# v2.1: per-host inbox staging path (Cure-4). Node id resolved from the roster,
# falls back to the hostname - each machine only ever appends to ITS OWN file.
$NodeId = $env:COMPUTERNAME
try {
  $cfgN = Get-Content -Raw -Encoding UTF8 (Join-Path $Root 'Tools\fleet-nodes.json') | ConvertFrom-Json
  foreach ($n in @($cfgN.nodes)) { if ([string]$n.host -ne '' -and ([string]$n.host -ieq $env:COMPUTERNAME)) { $NodeId = [string]$n.id; break } }
} catch { }
$InboxRel = 'cph4/fleet/memory/inbox/' + $NodeId + '.md'
$InboxF = Join-Path $Root ($InboxRel -replace '/', '\')
$InboxDir = Split-Path $InboxF -Parent

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
function Entry-Hash([string]$line) {
  $sha = [System.Security.Cryptography.SHA1]::Create()
  ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($line.Trim())))) -replace '-', ''
}
function Get-Entries([string]$t) {
  $list = @()
  $sec = ''
  foreach ($ln in @($t -split '\r?\n')) {
    if ($ln -match '^###\s*(.+?)\s*$') { $sec = $Matches[1]; continue }
    if ($ln -match '^-\s*\[') { $list += @{ sec = $sec; line = $ln; hash = (Entry-Hash $ln) } }
  }
  return $list
}
function Merge-IntoText([string]$baseText, [string]$addText, [hashtable[]]$addsExtra) {
  # inserts the given add-entries (precomputed objects) missing in base, per section
  $baseLines = @($baseText -split '\r?\n')
  $baseKeys = @{}
  $baseSec = ''
  $sep = [string][char]31
  foreach ($ln in $baseLines) {
    if ($ln -match '^###\s*(.+?)\s*$') { $baseSec = $Matches[1]; continue }
    if ($ln -match '^-\s*\[') { $baseKeys[($baseSec + $sep + $ln)] = $true }
  }
  $adds = @()
  foreach ($e in $addsExtra) { if (-not $baseKeys.ContainsKey(($e.sec + $sep + $e.line))) { $adds += $e } }
  if (@($adds).Count -eq 0) { return @{ text = $baseText; added = 0 } }
  $bySec = @{}; $secOrder = @()
  foreach ($e in $adds) {
    if (-not $bySec.ContainsKey($e.sec)) { $bySec[$e.sec] = @(); $secOrder += $e.sec }
    $bySec[$e.sec] += $e.line
  }
  $inserts = @{}; $headerIdx = @{}; $lastEntryIdx = @{}
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
    } else { $eofAdds += $s }
  }
  $out = New-Object System.Collections.Generic.List[string]
  for ($i = 0; $i -lt $baseLines.Count; $i++) {
    if ($inserts.ContainsKey($i)) { foreach ($l in $inserts[$i]) { $out.Add($l) } }
    $out.Add($baseLines[$i])
  }
  if ($inserts.ContainsKey($baseLines.Count)) { foreach ($l in $inserts[$baseLines.Count]) { $out.Add($l) } }
  foreach ($s in $eofAdds) { $out.Add(''); $out.Add('### ' + $s); foreach ($l in $bySec[$s]) { $out.Add($l) } }
  return @{ text = ($out -join "`n"); added = @($adds).Count }
}
function Load-Tombstones() {
  $set = @{}
  if (Test-Path -LiteralPath $TombF) {
    foreach ($ln in (Get-Content -LiteralPath $TombF -Encoding UTF8)) {
      if ($ln -match '"h":\s*"([0-9a-f]{40})"') { $set[$Matches[1]] = $true }
    }
  }
  return $set
}
function Commit-Push([int]$n, [string]$note) {
  $git = 'C:\Program Files\Git\cmd\git.exe'
  if (-not (Test-Path $git)) { $git = 'git' }
  $pushed = ''
  try {
    # v2.1: the inbox rides the same targeted commit (own file, additive only)
    $paths = @($CanonRel, $TombRel)
    if (Test-Path -LiteralPath $InboxF) { $paths += $InboxRel }
    $addArgs = @('-C', $Root, 'add') + $paths
    & $git @addArgs 2>&1 | Out-Null
    $msg = ("fleet-memory-" + $note + ": " + $n + " [via " + $env:COMPUTERNAME + "]")
    $cmArgs = @('-C', $Root, 'commit', '-m', $msg, '--') + $paths
    & $git @cmArgs 2>&1 | Out-Null
    $sha = [string](& $git -C $Root rev-parse HEAD)
    & $git -C $Root push origin ("$sha" + ':refs/heads/main') 2>&1 | Out-Null
    $pushed = $sha.Substring(0, 8)
  } catch { }
  return $pushed
}

# ---- grooming helper: record removals vs the committed canonical ----
if ($RecordRemoval) {
  $git = 'C:\Program Files\Git\cmd\git.exe'
  if (-not (Test-Path $git)) { $git = 'git' }
  $oldText = ''
  try { $oldText = [string](& $git -C $Root show ('HEAD:' + $CanonRel)) } catch { }
  $newRead = Read-TextBom $Canon
  if ($oldText -eq '') { Write-Output 'RECORD-REMOVAL skip: no committed canonical yet'; exit 0 }
  $oldEntries = Get-Entries $oldText
  $newKeys = @{}
  foreach ($e in (Get-Entries $newRead.text)) { $newKeys[$e.hash] = $true }
  $removed = @($oldEntries | Where-Object { -not $newKeys.ContainsKey($_.hash) })
  if ($removed.Count -gt 0) {
    foreach ($e in $removed) {
      $o = [ordered]@{ ts = (Get-Date -Format s); h = $e.hash; note = 'groomed-out' }
      [IO.File]::AppendAllText($TombF, (($o | ConvertTo-Json -Compress) + "`n"), (New-Object Text.UTF8Encoding($false)))
    }
  }
  Write-Output ('RECORD-REMOVAL entries-removed=' + $removed.Count + ' (tombstoned - commit canonical + tombstones next)')
  exit 0
}

# ---- normal sync run ----
$localRead = Read-TextBom $LocalMem
$canonRead = Read-TextBom $Canon
if ($canonRead.text -eq '') {
  $canonDir = Split-Path $Canon -Parent
  if (-not (Test-Path $canonDir)) { New-Item -ItemType Directory -Path $canonDir -Force | Out-Null }
  Write-TextBom $Canon $localRead.text $localRead.bom
  $canonRead = Read-TextBom $Canon
  if (-not $Quiet) { Write-Output ('MEMSYNC bootstrap: canonical seeded (' + (@(Get-Entries $localRead.text)).Count + ' entries)') }
}
$tombs = Load-Tombstones
$locAdd = 0; $canAdd = 0; $pushed = ''
$inboxChanged = $false

# 0) INBOX-UP (v2.1 Cure-4): fresh local entries FIRST land in this host's own
#    inbox file - durable per-machine claim, conflict-free by construction.
$canonKeys = @{}
foreach ($e in (Get-Entries $canonRead.text)) { $canonKeys[$e.hash] = $true }
$sep = [string][char]31
$inboxText = ''
if (Test-Path -LiteralPath $InboxF) { $inboxText = [IO.File]::ReadAllText($InboxF) }
$inboxSeen = @{}
foreach ($e in (Get-Entries $inboxText)) { $inboxSeen[($e.sec + $sep + $e.line)] = $true }
$inboxAdds = @()
foreach ($e in (Get-Entries $localRead.text)) {
  if ($tombs.ContainsKey($e.hash)) { continue }
  if ($canonKeys.ContainsKey($e.hash)) { continue }
  if ($inboxSeen.ContainsKey(($e.sec + $sep + $e.line))) { continue }
  $inboxAdds += $e
}
if (@($inboxAdds).Count -gt 0) {
  if (-not (Test-Path $InboxDir)) { New-Item -ItemType Directory -Path $InboxDir -Force | Out-Null }
  if ($inboxText -ne '' -and -not ($inboxText.EndsWith("`n"))) { $inboxText += "`r`n" }
  # append grouped under real section headers so Get-Entries yields the same
  # (sec,line) keys as the local file - dedup stays exact, no dangling sections
  $bySecAdd = @{}
  $secOrder = @()
  foreach ($e in $inboxAdds) {
    if (-not $bySecAdd.ContainsKey($e.sec)) { $bySecAdd[$e.sec] = @(); $secOrder += $e.sec }
    $bySecAdd[$e.sec] += $e.line
  }
  foreach ($s in $secOrder) {
    $inboxText += ('### ' + $s + "`r`n")
    foreach ($l in $bySecAdd[$s]) { $inboxText += ($l + "`r`n") }
  }
  [IO.File]::WriteAllText($InboxF, $inboxText, (New-Object Text.UTF8Encoding($false)))
  $inboxChanged = $true
}

# 1) UNION-UP: entries from inbox + local (skip tombstoned = grooming can never
#    be resurrected; Merge-IntoText dedupes against the canonical's own lines).
#    v2.1.1: dedup WITHIN the source set - the same entry arrives from BOTH the
#    inbox and the local file and Merge-IntoText only dedupes vs the base, so a
#    raw concat double-inserted (live-fire 16:00: canon+2 = one entry x2).
$src = @()
$srcSeen = @{}
foreach ($e in @(@(Get-Entries $inboxText) + @(Get-Entries $localRead.text))) {
  if ($tombs.ContainsKey($e.hash)) { continue }
  $k = $e.sec + $sep + $e.line
  if ($srcSeen.ContainsKey($k)) { continue }
  $srcSeen[$k] = $true
  $src += $e
}
$m1 = Merge-IntoText $canonRead.text $localRead.text $src
if ($m1.added -gt 0) {
  Write-TextBom $Canon $m1.text $canonRead.bom
  $canAdd = $m1.added
  $pushed = Commit-Push $canAdd 'union'
}
if ($canAdd -gt 0) { $canonRead = Read-TextBom $Canon }
# inbox-only changes (canon already current) still get committed + pushed
if ($inboxChanged -and $canAdd -eq 0) { $pushed = Commit-Push 0 'inbox' }

# 2) REPLACE-DOWN: local becomes the canonical verbatim (grooming/prunes propagate).
#    Safety: re-read local fresh; any entries that appeared during this run (not
#    tombstoned) are unioned up FIRST so replace-down can never lose a fresh entry.
$localNow = Read-TextBom $LocalMem
$canKeys = @{}
foreach ($e in (Get-Entries $canonRead.text)) { $canKeys[$e.hash] = $true }
$strays = @()
foreach ($e in (Get-Entries $localNow.text)) {
  if (-not $canKeys.ContainsKey($e.hash) -and -not $tombs.ContainsKey($e.hash)) { $strays += $e }
}
if (@($strays).Count -gt 0) {
  $mS = Merge-IntoText $canonRead.text $localNow.text $strays
  Write-TextBom $Canon $mS.text $canonRead.bom
  $canAdd += $mS.added
  $pushed = Commit-Push $mS.added 'union'
  if ($mS.added -gt 0) { $canonRead = Read-TextBom $Canon }
}
if ($localNow.text -ne $canonRead.text) {
  try { Copy-Item -LiteralPath $LocalMem -Destination ($LocalMem + '.bak-fms') -Force } catch { }
  Write-TextBom $LocalMem $canonRead.text $localRead.bom
  $locAdd = -1  # replaced = local now mirrors canonical
}
if (-not $Quiet) {
  if ($locAdd -eq -1) { Write-Output ('MEMSYNC local=MIRROR(canonical) canon+' + $canAdd + ' pushed=' + $pushed) }
  else { Write-Output ('MEMSYNC local+0 canon+' + $canAdd + ' pushed=' + $pushed) }
}
exit 0

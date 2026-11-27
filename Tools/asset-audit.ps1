# Group asset audit v1.1 - Unity/Tuanjie asset convention sweep (naming, icon slice
# size, alpha channel, import-settings meta, duplicate content = atlas candidates).
# v1.1 calibration (2026-09-28): naming hard-FAIL only for non-ascii/space/multi-
# separator; mixed-case demoted to INFO (semantic compass suffixes NE/NW/H/V are
# lane convention); upstream pack roots (ArtPacks, CleanCityv3) naming-exempt -
# they keep original names for license-ledger traceability. Prefer lowercase for
# NEW first-party assets (guideline, not retrofit enforcement).
# ASCII-only (encoding law). READ-ONLY against all repos. Exit 0 = no FAIL,
# 1 = FAIL found, 2 = path not found. Skill doc: .codely-cli/skills/asset-audit/SKILL.md
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File Tools\asset-audit.ps1 -Path "<file-or-dir>" [-ExemptDirs "ArtPacks,CleanCityv3"]

param(
  [Parameter(Mandatory=$true)][string]$Path,
  [string]$Report = '',
  [string]$ExemptDirs = 'ArtPacks,CleanCityv3'
)

$root = Split-Path -Parent $PSScriptRoot   # -> FluxGroup root
if (-not $Report) { $Report = Join-Path $root 'docs\audits\asset-audit-report.md' }
$repDir = Split-Path -Parent $Report
if (-not (Test-Path $repDir)) { New-Item -ItemType Directory -Path $repDir -Force | Out-Null }
Add-Type -AssemblyName System.Drawing

if (-not (Test-Path $Path)) { Write-Output ('asset-audit: PATH-NOT-FOUND ' + $Path); exit 2 }
$item = Get-Item $Path
if ($item.PSIsContainer) {
  $files = @(Get-ChildItem -Path $Path -Recurse -Filter '*.png' -File -ErrorAction SilentlyContinue)
} else {
  $files = @($item)
}

$hardRe   = '^[A-Za-z0-9]+([A-Za-z0-9]*[-_][A-Za-z0-9]+)*$'   # ascii words, single separators
$lowerRe  = '^[a-z0-9]+([a-z0-9]*[-_][a-z0-9]+)*$'            # strict lowercase (soft target)
$prefixRe = '^(btn|icon|bar|panel|bg|img|tab)_'
$uiPathRe = '\\ui\\'
$iconMax  = 128
$fmtOk    = @('.png', '.jpg', '.jpeg')
$exemptRes = @()
foreach ($d in ($ExemptDirs -split ',')) { $t = $d.Trim(); if ($t) { $exemptRes += ('\\' + [regex]::Escape($t) + '\\') } }

$counts = @{ pass=0; fail=0; warn=0; pending=0; info=0 }
$lines  = @()
$lines += '# Asset Audit Report (auto-generated)'
$lines += ''
$lines += ('- scope: ' + $Path)
$lines += ('- png files scanned: ' + $files.Count)
$lines += ('- time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$lines += '- rules v1.1: naming hard-FAIL = non-ascii/space/multi-separator; mixed-case = INFO; pack roots exempt: ' + $ExemptDirs + '; icon<=128 free-size else power-of-two; UI assets need alpha; meta textureType=8 (Sprite) for UI; MD5 duplicates = atlas candidates'
$lines += ''
$lines += '| verdict | check | file | detail |'
$lines += '|---------|-------|------|--------|'

foreach ($f in $files) {
  $name = $f.Name
  $base = [System.IO.Path]::GetFileNameWithoutExtension($name)
  $rel  = $f.FullName
  $isUI = (($base -match $prefixRe) -or ($rel -match $uiPathRe))
  $isExempt = $false
  foreach ($er in $exemptRes) { if ($rel -match $er) { $isExempt = $true } }

  # 1 format whitelist
  $ext = $f.Extension.ToLower()
  if ($fmtOk -contains $ext) { $counts.pass++; $lines += ('| PASS | format | ' + $name + ' | ' + $ext) }
  else { $counts.fail++; $lines += ('| FAIL | format | ' + $name + ' | not in whitelist png/jpg') }

  # 2 naming convention (v1.1 calibrated)
  if ($isExempt) { $counts.info++; $lines += ('| INFO | naming-exempt | ' + $name + ' | upstream pack root (' + $ExemptDirs + ') keeps original names') }
  elseif ($base -cnotmatch $hardRe) { $counts.fail++; $lines += ('| FAIL | naming | ' + $name + ' | non-ascii/space/multi-separator not allowed') }
  elseif ($base -cnotmatch $lowerRe) { $counts.info++; $lines += ('| INFO | naming-case | ' + $name + ' | mixed-case tolerated; prefer lowercase for new first-party assets') }
  else { $counts.pass++; $lines += ('| PASS | naming | ' + $name + ' | lowercase-ascii ok') }
  if (-not $isExempt -and $base -notmatch $prefixRe) { $counts.info++; $lines += ('| INFO | prefix | ' + $name + ' | no type prefix (btn_/icon_/bg_/...) - suggested, not required') }

  # 3 size class + alpha channel
  $w = 0; $h = 0; $alpha = $false
  try {
    $img = [System.Drawing.Image]::FromFile($rel)
    $w = $img.Width; $h = $img.Height
    $alpha = ($img.PixelFormat.ToString() -match 'Argb|Alpha')
    $img.Dispose()
  } catch {
    $counts.fail++; $lines += ('| FAIL | readable | ' + $name + ' | image load error'); continue
  }
  $dimNote = ('size ' + $w + 'x' + $h)
  $m = [Math]::Max($w, $h)
  if ($m -le $iconMax) { $counts.pass++; $lines += ('| PASS | size-icon | ' + $name + ' | ' + $dimNote + ' (icon class <=128)') }
  elseif ((($w -band ($w - 1)) -eq 0) -and (($h -band ($h - 1)) -eq 0)) { $counts.pass++; $lines += ('| PASS | size-pot | ' + $name + ' | ' + $dimNote + ' power-of-two') }
  else { $counts.warn++; $lines += ('| WARN | size-pot | ' + $name + ' | ' + $dimNote + ' non-POT texture above 128') }

  if ($isUI -and -not $alpha) { $counts.fail++; $lines += ('| FAIL | ui-alpha | ' + $name + ' | UI asset without alpha channel') }
  elseif ($isUI) { $counts.pass++; $lines += ('| PASS | ui-alpha | ' + $name + ' | alpha channel present') }

  # 4 file weight
  $kb = [Math]::Round($f.Length / 1KB)
  if ($f.Length -gt 4MB) { $counts.warn++; $lines += ('| WARN | weight | ' + $name + ' | ' + $kb + ' KB png - consider optimizing') }
  else { $counts.pass++; $lines += ('| PASS | weight | ' + $name + ' | ' + $kb + ' KB') }

  # 5 import-settings meta
  $metaPath = $rel + '.meta'
  if (Test-Path $metaPath) {
    $meta = Get-Content $metaPath -Raw
    $tt = ''; if ($meta -match 'textureType:\s*(\d+)') { $tt = $Matches[1] }
    $tc = ''; if ($meta -match 'textureCompression:\s*(\d+)') { $tc = $Matches[1] }
    if ($isUI -and -not $isExempt) {
      if ($tt -eq '8') { $counts.pass++; $lines += ('| PASS | meta-sprite | ' + $name + ' | textureType=8 (Sprite), compression=' + $tc) }
      else { $counts.fail++; $lines += ('| FAIL | meta-sprite | ' + $name + ' | textureType=' + $tt + ' but UI asset must be 8 (Sprite)') }
    } else {
      $counts.info++; $lines += ('| INFO | meta | ' + $name + ' | textureType=' + $tt + ' compression=' + $tc)
    }
  } else {
    $counts.pending++
    $lines += ('| PENDING | meta | ' + $name + ' | no .meta yet - open project in editor to import, then re-run audit')
  }
}

# 6 duplicate content scan (sprite atlas candidates)
if ($files.Count -gt 1) {
  $hashes = @{}
  $dupRows = @()
  foreach ($f in $files) {
    $h = (Get-FileHash -Path $f.FullName -Algorithm MD5).Hash
    if ($hashes.ContainsKey($h)) { $dupRows += ($hashes[$h] + ' == ' + $f.FullName) }
    else { $hashes[$h] = $f.FullName }
  }
  if ($dupRows.Count -gt 0) { foreach ($d in $dupRows) { $counts.warn++; $lines += ('| WARN | dup-content | atlas-candidate | ' + $d) } }
  else { $counts.info++; $lines += '| INFO | dup-content | all scanned | no identical png pairs' }
}

$lines += ''
$lines += ('## Summary: pass=' + $counts.pass + ' fail=' + $counts.fail + ' warn=' + $counts.warn + ' pending=' + $counts.pending + ' info=' + $counts.info)
if ($counts.fail -gt 0) { $lines += '## Verdict: FAIL - fix before ship' }
elseif ($counts.pending -gt 0) { $lines += '## Verdict: PASS-WITH-PENDING - re-run after editor import refresh' }
else { $lines += '## Verdict: PASS' }

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Report, ($lines -join "`r`n") + "`r`n", $utf8)
Write-Output ('asset-audit done: files=' + $files.Count + ' pass=' + $counts.pass + ' fail=' + $counts.fail + ' warn=' + $counts.warn + ' pending=' + $counts.pending + ' info=' + $counts.info + ' -> ' + $Report)
if ($counts.fail -gt 0) { exit 1 } else { exit 0 }

# Ledger UTF-8 guard v0.1 - detects lines that are not valid UTF-8 in group ledgers.
# Root cause it guards: a session appended GBK bytes into a UTF-8 ledger, so every
# later read_file call failed on the whole file (P-2026-10-25-01, recurred 2026-11-01).
# READ-ONLY by default. -Repair converts only the offending lines (GBK -> UTF-8)
# and writes a backup next to the file first.
# ASCII-only source (encoding law). Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools\ledger-utf8-guard.ps1
#   ... -Repair
param(
  [string]$Root,
  [switch]$Repair
)
$ErrorActionPreference = 'Stop'
if(-not $Root){ $Root = Split-Path -Parent $PSScriptRoot }

$targets = @(
  'cph4\evolution-ledger.md',
  'cph4\reflection-journal.md',
  'docs\orders.md',
  'docs\decisions.md',
  'docs\governance.md',
  'cph4\evolution.md'
)

$utf8Strict = New-Object System.Text.UTF8Encoding($false, $true)
$gbk = [System.Text.Encoding]::GetEncoding(936)
$bad = 0
$repaired = 0

foreach($rel in $targets){
  $path = Join-Path $Root $rel
  if(-not (Test-Path $path)){ continue }
  $bytes = [System.IO.File]::ReadAllBytes($path)
  $out = New-Object System.Collections.Generic.List[byte]
  $start = 0
  $fileBad = 0
  for($i = 0; $i -lt $bytes.Length; $i++){
    $isEol = ($bytes[$i] -eq 13 -and ($i + 1) -lt $bytes.Length -and $bytes[$i + 1] -eq 10)
    if($isEol -or $i -eq ($bytes.Length - 1)){
      $end = if($isEol){ $i } else { $bytes.Length }
      $len = $end - $start
      if($len -gt 0){
        $seg = New-Object byte[] $len
        [Array]::Copy($bytes, $start, $seg, 0, $len)
        $ok = $true
        try { $null = $utf8Strict.GetString($seg) } catch { $ok = $false }
        if($ok){
          $out.AddRange($seg)
        } else {
          $fileBad++
          if($Repair){
            $out.AddRange([System.Text.Encoding]::UTF8.GetBytes($gbk.GetString($seg)))
            $repaired++
          } else {
            $out.AddRange($seg)
          }
        }
      }
      if($isEol){ $out.Add(13); $out.Add(10); $start = $i + 2; $i++ }
    }
  }
  if($fileBad -gt 0){
    $bad += $fileBad
    Write-Output "BAD $rel : $fileBad segment(s) not valid UTF-8"
    if($Repair){
      $bak = "$path.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss')
      Copy-Item $path $bak -Force
      [System.IO.File]::WriteAllBytes($path, $out.ToArray())
      Write-Output "REPAIRED $rel (backup: $bak)"
    }
  } else {
    Write-Output "OK $rel"
  }
}

Write-Output "SUMMARY bad_segments=$bad repaired=$repaired"
if($bad -gt 0 -and -not $Repair){ exit 1 }
exit 0
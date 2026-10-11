# x1387_g16_manual_move.ps1 - move the rebuilt manual PDF (wave2 icon embedded)
# onto its final Chinese name. Guard: newLen > 1,000,000B (pre-icon draft was
# 950,033B; icon adds mass). Wave2 icon is a 32-color quantized 114,844B PNG,
# so the rebuilt PDF lands around ~1.07MB - above the line, images embedded.
# Pure ASCII; Chinese name from the UTF-8 names registry (x1275 pattern).
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$namesJson = Join-Path $dir 'g16_soft_names.json'
if (-not (Test-Path -LiteralPath $namesJson)) { throw 'names json not found' }
$names = [System.IO.File]::ReadAllText($namesJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$tmp = Join-Path $dir '_manual_print.pdf'
if (-not (Test-Path -LiteralPath $tmp)) { throw 'intermediate manual pdf missing' }
$newLen = (Get-Item -LiteralPath $tmp).Length
if ($newLen -le 1000000) { throw ('icon-in guard failed: ' + $newLen + ' bytes - pre-icon draft was 950,033B, icon did not ride along?') }
$final = Join-Path $dir ([string]$names.manual)
Move-Item -LiteralPath $tmp -Destination $final -Force
$flen = (Get-Item -LiteralPath $final).Length
if ($flen -ne $newLen) { throw ('post-move length mismatch: ' + $flen + ' vs ' + $newLen) }
Write-Output ('MOVED manual -> ' + $names.manual + ' new=' + $flen)
Write-Output 'MANUAL_MOVED_OK'

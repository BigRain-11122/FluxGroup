# x1275_g16_manual_move.ps1 - move the rebuilt manual PDF (with the slot-0
# game icon embedded) onto its final Chinese name. Guard v2: after the
# X1275 quantize fix the baseline is the ORIGINAL pre-icon manual
# (950,033B, X1259-era); the icon-in check is newLen > 1,000,000B (the
# pre-icon draft was 950,033B, icon adds mass) - do NOT compare against the
# superseded big-PDF intermediate. Pure ASCII; Chinese name from the
# UTF-8 names registry (x1256 move chain pattern).
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

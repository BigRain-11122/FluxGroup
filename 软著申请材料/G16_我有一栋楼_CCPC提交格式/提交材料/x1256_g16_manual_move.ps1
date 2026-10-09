# x1256_g16_manual_move.ps1 - move the rebuilt manual PDF (with the two
# real-device screenshots embedded) onto its final Chinese name, replacing
# the X1255 no-image draft. Pure ASCII; Chinese name from the UTF-8 names
# registry (same pattern as the x1255 move chain). Length guard: a manual
# without embedded frames lands near 340KB; with the two frames the honest
# render is 800KB+ - below 700KB means the images did not ride along.
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$namesJson = Join-Path $dir 'g16_soft_names.json'
if (-not (Test-Path -LiteralPath $namesJson)) { throw 'names json not found' }
$names = [System.IO.File]::ReadAllText($namesJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$tmp = Join-Path $dir '_manual_print.pdf'
if (-not (Test-Path -LiteralPath $tmp)) { throw 'intermediate manual pdf missing' }
$len = (Get-Item -LiteralPath $tmp).Length
if ($len -lt 700000) { throw ('length guard failed: rebuilt manual only ' + $len + ' bytes - frames missing?') }
$final = Join-Path $dir ([string]$names.manual)
Move-Item -LiteralPath $tmp -Destination $final -Force
$flen = (Get-Item -LiteralPath $final).Length
if ($flen -lt 700000) { throw ('post-move length guard failed: ' + $flen) }
Write-Output ('MOVED manual -> ' + $names.manual + ' bytes=' + $flen)
Write-Output 'MANUAL_MOVED_OK'

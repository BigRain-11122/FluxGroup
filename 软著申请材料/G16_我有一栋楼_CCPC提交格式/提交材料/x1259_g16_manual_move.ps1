# x1259_g16_manual_move.ps1 - move the rebuilt manual PDF (now carrying all
# nine real-device screenshots: slot 1 pair from X1256 + the seven-host
# slots 2-8 pass) onto its final Chinese name. Pure ASCII; Chinese name from
# the UTF-8 names registry (same pattern as the X1256 move chain).
# Length guard: the X1256 two-frame manual was 845KB; the seven new frames
# add ~267KB of law-verified PNG payload, so the honest render is 1.0MB+ -
# below 900KB means the new images did not ride along.
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$namesJson = Join-Path $dir 'g16_soft_names.json'
if (-not (Test-Path -LiteralPath $namesJson)) { throw 'names json not found' }
$names = [System.IO.File]::ReadAllText($namesJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$tmp = Join-Path $dir '_manual_print.pdf'
if (-not (Test-Path -LiteralPath $tmp)) { throw 'intermediate manual pdf missing' }
$len = (Get-Item -LiteralPath $tmp).Length
if ($len -lt 900000) { throw ('length guard failed: rebuilt manual only ' + $len + ' bytes - frames missing?') }
$final = Join-Path $dir ([string]$names.manual)
Move-Item -LiteralPath $tmp -Destination $final -Force
$flen = (Get-Item -LiteralPath $final).Length
if ($flen -lt 900000) { throw ('post-move length guard failed: ' + $flen) }
Write-Output ('MOVED manual -> ' + $names.manual + ' bytes=' + $flen)
Write-Output 'MANUAL_MOVED_OK'

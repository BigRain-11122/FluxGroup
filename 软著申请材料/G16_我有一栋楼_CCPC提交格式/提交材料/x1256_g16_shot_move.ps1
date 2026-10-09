# x1256_g16_shot_move.ps1 - copy the manual screenshot frames from the rig's
# ASCII output dir (Logs/g16_shots) into this material folder next to the
# manual source md. X801/X776 discipline: pure ASCII script; the Chinese
# folder path resolves from the script's own location, never a literal.
# Length guard per X1234 lesson: any frame under 50KB = abort (a blank or
# truncated render lands far below the observed 190KB+ range).
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $dir '..\..\..')).Path
$src = Join-Path $repo 'projects\G16_CrazyEstate\Logs\g16_shots'
if (-not (Test-Path -LiteralPath $src)) { throw ('shot dir missing: ' + $src) }

$frames = @('g16_slot0_boot.png', 'g16_slot1_duel.png', 'g16_slot1_settle.png')
foreach ($f in $frames) {
    $p = Join-Path $src $f
    if (-not (Test-Path -LiteralPath $p)) { throw ('frame missing: ' + $f) }
    $len = (Get-Item -LiteralPath $p).Length
    if ($len -lt 50000) { throw ('length guard failed: ' + $f + ' only ' + $len + ' bytes') }
    Copy-Item -LiteralPath $p -Destination (Join-Path $dir $f) -Force
    $d = Join-Path $dir $f
    $dlen = (Get-Item -LiteralPath $d).Length
    if ($dlen -ne $len) { throw ('copy mismatch: ' + $f + ' ' + $dlen + ' vs ' + $len) }
    Write-Output ('COPIED ' + $f + ' bytes=' + $dlen)
}
Write-Output 'ALL_THREE_COPIED_OK'

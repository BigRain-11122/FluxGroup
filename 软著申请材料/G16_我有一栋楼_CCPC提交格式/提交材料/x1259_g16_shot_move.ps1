# x1259_g16_shot_move.ps1 - copy the seven-host manual screenshot frames
# (manual slots 2-8, RunSevenHosts pass) from the rig's ASCII output dir
# (Logs/g16_shots) into this material folder next to the manual source md.
# X801/X776 discipline: pure ASCII script; the Chinese folder path resolves
# from the script's own location, never a literal.
# Length guard: the desk-panel host family renders sparse dark UI - the
# honest range observed across all seven law-verified frames is 24-57KB
# (a solid-color blank render lands near 4KB), so this batch's floor is 15KB,
# NOT the 50KB floor the X1256 dense Bargain frames used.
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $dir '..\..\..')).Path
$src = Join-Path $repo 'projects\G16_CrazyEstate\Logs\g16_shots'
if (-not (Test-Path -LiteralPath $src)) { throw ('shot dir missing: ' + $src) }

$frames = @('g16_slot2_rent.png', 'g16_slot3_reno.png', 'g16_slot4_mortgage.png',
            'g16_slot5_lottery.png', 'g16_slot6_market.png', 'g16_slot7_license.png',
            'g16_slot8_achieve.png')
foreach ($f in $frames) {
    $p = Join-Path $src $f
    if (-not (Test-Path -LiteralPath $p)) { throw ('frame missing: ' + $f) }
    $len = (Get-Item -LiteralPath $p).Length
    if ($len -lt 15000) { throw ('length guard failed: ' + $f + ' only ' + $len + ' bytes') }
    Copy-Item -LiteralPath $p -Destination (Join-Path $dir $f) -Force
    $d = Join-Path $dir $f
    $dlen = (Get-Item -LiteralPath $d).Length
    if ($dlen -ne $len) { throw ('copy mismatch: ' + $f + ' ' + $dlen + ' vs ' + $len) }
    Write-Output ('COPIED ' + $f + ' bytes=' + $dlen)
}
Write-Output 'ALL_SEVEN_COPIED_OK'

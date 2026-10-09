# x1255_g16_soft_move.ps1 - move the three ASCII-intermediate PDFs to their final
# Chinese names. X801/X776 discipline: this script is pure ASCII; the Chinese
# destination names live in g16_soft_names.json (UTF-8 data file, read with an
# explicit UTF8 decode). Length guard per X1234 lesson: abort if any produced
# PDF is smaller than 100KB (a truncated/empty render would be far below).
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$namesJson = Join-Path $dir 'g16_soft_names.json'
if (-not (Test-Path -LiteralPath $namesJson)) { throw 'names json not found' }
$names = [System.IO.File]::ReadAllText($namesJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

$pairs = @(
    @{ tmp = '_source_print.pdf'; final = $names.source },
    @{ tmp = '_manual_print.pdf'; final = $names.manual },
    @{ tmp = '_apply_print.pdf';  final = $names.apply }
)
foreach ($p in $pairs) {
    $tmpPath = Join-Path $dir $p.tmp
    if (-not (Test-Path -LiteralPath $tmpPath)) { throw ('intermediate pdf missing: ' + $p.tmp) }
    $len = (Get-Item -LiteralPath $tmpPath).Length
    if ($len -lt 100000) { throw ('length guard failed: ' + $p.tmp + ' only ' + $len + ' bytes') }
    $finalPath = Join-Path $dir ([string]$p.final)
    Move-Item -LiteralPath $tmpPath -Destination $finalPath -Force
    if (-not (Test-Path -LiteralPath $finalPath)) { throw ('move failed: ' + $p.final) }
    $flen = (Get-Item -LiteralPath $finalPath).Length
    if ($flen -lt 100000) { throw ('post-move length guard failed: ' + $p.final) }
    Write-Output ('MOVED ' + $p.tmp + ' -> ' + $p.final + ' bytes=' + $flen)
}
Write-Output 'ALL_THREE_MOVED_OK'

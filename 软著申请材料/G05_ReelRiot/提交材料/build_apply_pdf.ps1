# build_apply_pdf.ps1 - render the registration application form HTML to PDF
# via headless Edge (G05 soft-copyright chain).
# Chain: <this folder>/form source html -> ASCII temp workdir copy
#        -> msedge --headless --print-to-pdf -> copy back as _apply_print.pdf
#        -> caller moves _apply_print.pdf to the final Chinese-named PDF.
# Adapted from G07 B201 chain (U067 reuse).
# Why ASCII temp paths: native exe (Edge) silently fails on non-ASCII output
# paths (pit #1 family, B155 lesson). All Chinese strings live only in the
# html data file. Script is pure ASCII by PS5.1 discipline (X033 pit 1).
# Reusable for other games: drop next to a single Chinese-named form html
# and run with no arguments (the picker prefers a non-ASCII filename).
param([string]$HtmlName = '')

$ErrorActionPreference = 'Stop'
$srcDir = $PSScriptRoot
$edge = @('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
          'C:\Program Files\Microsoft\Edge\Application\msedge.exe') |
        Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw 'msedge.exe not found' }

if ($HtmlName) { $html = Get-Item -LiteralPath (Join-Path $srcDir $HtmlName) -ErrorAction SilentlyContinue }
else {
    # auto-pick: the form data file is Chinese-named, so prefer the first
    # html whose filename carries a non-ASCII char; fallback = first html
    $cands = Get-ChildItem -LiteralPath $srcDir -Filter '*.html'
    $html = $null
    foreach ($c in $cands) { if ($c.Name -match '[^\x00-\x7F]') { $html = $c; break } }
    if (-not $html -and $cands.Count -ge 1) { $html = $cands[0] }
}
if (-not $html) { throw 'form source html not found in ' + $srcDir }

$work = Join-Path $env:TEMP ('g05apply_' + (Get-Date -Format 'HHmmss'))
New-Item -ItemType Directory -Path $work -Force | Out-Null

$flat = 'form.html'
Copy-Item -LiteralPath $html.FullName -Destination (Join-Path $work $flat) -Force

$pdfOut = Join-Path $work 'out.pdf'
$p = Start-Process -FilePath $edge -ArgumentList @(
    '--headless', '--disable-gpu', '--no-pdf-header-footer',
    ('--print-to-pdf=' + $pdfOut),
    ('file:///' + ((Join-Path $work $flat) -replace '\\', '/'))
) -PassThru
if (-not $p.WaitForExit(60000)) { $p.Kill(); throw 'edge print timed out (60s)' }
if (-not (Test-Path $pdfOut)) { throw 'edge produced no pdf' }

$shot = Join-Path $work 'shot.png'
$p2 = Start-Process -FilePath $edge -ArgumentList @(
    '--headless', '--disable-gpu', '--window-size=1080,1600',
    ('--screenshot=' + $shot),
    ('file:///' + ((Join-Path $work $flat) -replace '\\', '/'))
) -PassThru
if (-not $p2.WaitForExit(60000)) { $p2.Kill(); throw 'edge screenshot timed out' }

$dest = Join-Path $srcDir '_apply_print.pdf'
Copy-Item -LiteralPath $pdfOut -Destination $dest -Force
$sz = (Get-Item -LiteralPath $dest).Length
Write-Output ('PDF_BYTES=' + $sz)
Write-Output ('SOURCE=' + $html.Name)
Write-Output ('SHOT=' + $shot)
Write-Output ('DEST=' + $dest)

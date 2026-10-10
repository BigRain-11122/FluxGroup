# build_content_pdf.ps1 - G09 soft-copyright content PDFs (operation
# manual draft + registration application form draft) via headless Edge.
# Paradigm: G12 C184 recipe (zero-token local chain), ASCII script discipline.
#   & build_content_pdf.ps1
# Chain: print manual_draft_v1.html -> _manual_print.pdf,
#        print form_draft_v1.html   -> _form_print.pdf (ASCII temp names; the
#        caller Move-Item's them to the Chinese-named finals - pit #104).
$ErrorActionPreference = 'Stop'
$edge = @('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
          'C:\Program Files\Microsoft\Edge\Application\msedge.exe') |
        Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw 'msedge.exe not found' }
$pairs = @(
    @{ Html = 'manual_draft_v1.html'; Out = '_manual_print.pdf' },
    @{ Html = 'form_draft_v1.html';   Out = '_form_print.pdf' }
)
foreach ($p in $pairs) {
    $html = Join-Path $PSScriptRoot $p.Html
    if (-not (Test-Path -LiteralPath $html)) { throw ('html not found: ' + $html) }
    $pdfTemp = Join-Path $env:TEMP ('g09pdf_' + (Get-Date -Format 'HHmmss') + '.pdf')
    $proc = Start-Process -FilePath $edge -ArgumentList @(
        '--headless', '--disable-gpu', '--no-pdf-header-footer',
        ('--print-to-pdf=' + $pdfTemp),
        ('file:///' + ($html -replace '\\', '/'))
    ) -PassThru
    if (-not $proc.WaitForExit(90000)) { $proc.Kill(); throw 'edge print timed out (90s)' }
    if (-not (Test-Path $pdfTemp)) { throw 'edge produced no pdf' }
    $dest = Join-Path $PSScriptRoot $p.Out
    Copy-Item -LiteralPath $pdfTemp -Destination $dest -Force
    Remove-Item -LiteralPath $pdfTemp -Force
    Write-Output ($p.Out + ' bytes=' + (Get-Item -LiteralPath $dest).Length)
}
Write-Output 'DONE - Move-Item the two ASCII prints to the Chinese finals (pit #104 chain).'

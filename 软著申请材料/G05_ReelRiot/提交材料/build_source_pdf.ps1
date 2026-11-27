# build_source_pdf.ps1 - copyright "first 30 + last 30 pages" source PDF via headless Edge. G05 chain,
# adapted from G15 X577 chain (U067 reuse; itself from G11 X418 / G07 B201 / G04 B154 - local zero-token paradigm).
# Chain: enumerate own-source .cs -> 50 lines/page chunks -> cover + first30 + marker + last30
#        -> msedge --headless --print-to-pdf -> _source_print.pdf (ASCII temp name; caller
#        Move-Item's it to the final Chinese-named PDF - pit #1 family, B155 lesson).
# Rule: own source only (Assets\_Game; shared packages com.sy.* are portfolio base, excluded).
#       Total lines > 3000 -> first 30 + last 30 pages.
# Cover title comes from soft_title.txt (UTF-8 data file, two-file split per X416
# lesson: Chinese never lives inside this ASCII script). Line1 = software full
# name, line2 = subtitle (English name / version). Missing file -> legacy cover.
# Script is pure ASCII by PS5.1 discipline (X033 pit 1).
param(
    [string]$ProjectDir = 'E:\Minigame\ReelRiot',
    [string]$SrcRoot = 'Assets\_Game',
    [int]$LinesPerPage = 50,
    [int]$HeadPages = 30,
    [int]$TailPages = 30
)
$ErrorActionPreference = 'Stop'

$edge = @('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
          'C:\Program Files\Microsoft\Edge\Application\msedge.exe') |
        Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw 'msedge.exe not found' }

$srcAbs = Join-Path $ProjectDir $SrcRoot
if (-not (Test-Path -LiteralPath $srcAbs)) { throw ('source root not found: ' + $srcAbs) }
$files = Get-ChildItem -LiteralPath $srcAbs -Recurse -Filter *.cs | Sort-Object FullName
if ($files.Count -lt 1) { throw 'no .cs files under source root' }

# Build the flat 50-lines-per-page stream (file header line counts as a stream line).
$stream = New-Object System.Collections.Generic.List[string]
foreach ($f in $files) {
    $rel = $f.FullName.Substring($ProjectDir.Length + 1)
    $stream.Add('// ===== FILE: ' + $rel + ' =====')
    foreach ($ln in (Get-Content -LiteralPath $f.FullName)) { $stream.Add($ln) }
}
$totalLines = $stream.Count
$totalPages = [math]::Ceiling($totalLines / $LinesPerPage)
if ($totalLines -lt 3000) { Write-Output ('WARN_LINES_UNDER_3000=' + $totalLines + ' full listing used') }

function PageDiv([string[]]$chunk, [int]$idx) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('<div class="page"><div class="ph">page ' + $idx + ' / ' + $script:totalPages + '</div><pre>')
    foreach ($l in $chunk) {
        $t = $l -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;'
        [void]$sb.AppendLine($t)
    }
    [void]$sb.AppendLine('</pre></div>')
    return $sb.ToString()
}

$titleFile = Join-Path $PSScriptRoot 'soft_title.txt'
$titleCn = 'ReelRiot'
$titleSub = ''
if (Test-Path -LiteralPath $titleFile) {
    $tl = @(Get-Content -LiteralPath $titleFile -Encoding UTF8 | Where-Object { $_.Trim() -ne '' })
    if ($tl.Count -ge 1) { $titleCn = $tl[0].Trim() }
    if ($tl.Count -ge 2) { $titleSub = $tl[1].Trim() }
}

$cover = New-Object System.Text.StringBuilder
[void]$cover.AppendLine('<div class="page"><h1>' + $titleCn + '</h1>')
if ($titleSub -ne '') { [void]$cover.AppendLine('<p>' + $titleSub + '</p>') }
[void]$cover.AppendLine('<p>Source code excerpt (first ' + $HeadPages + ' + last ' + $TailPages + ' pages)</p>')
[void]$cover.AppendLine('<p>Scope: ' + $SrcRoot + ' own source. Files: ' + $files.Count + ' / Lines: ' + $totalLines + ' / ' + $LinesPerPage + ' lines per page / Total pages: ' + $totalPages + '</p>')
[void]$cover.AppendLine('<p>Generated: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' (local build chain, headless Edge print)</p></div>')

$head = New-Object System.Text.StringBuilder
for ($p = 0; $p -lt $HeadPages; $p++) {
    $chunk = $stream.GetRange($p * $LinesPerPage, $LinesPerPage)
    [void]$head.Append((PageDiv $chunk ($p + 1)))
}
$tail = New-Object System.Text.StringBuilder
for ($p = $totalPages - $TailPages; $p -lt $totalPages; $p++) {
    $start = $p * $LinesPerPage
    $take = [math]::Min($LinesPerPage, $totalLines - $start)
    $chunk = $stream.GetRange($start, $take)
    [void]$tail.Append((PageDiv $chunk ($p + 1)))
}
if ($totalPages -le ($HeadPages + $TailPages)) { throw ('source too short for head+tail split: ' + $totalPages + ' pages') }

$marker = '<div class="page"><h2>(middle pages omitted)</h2><p>pages ' + ($HeadPages + 1) + ' - ' + ($totalPages - $TailPages) + ' of ' + $totalPages + ' omitted per first-30 + last-30 excerpt rule.</p></div>'

$headHtml = Join-Path $env:TEMP ('g05src_' + (Get-Date -Format 'HHmmss') + '.html')
$css = 'body{margin:0}div.page{page-break-after:always}pre{font-family:Consolas,monospace;font-size:7.2pt;line-height:1.12;white-space:pre-wrap;margin:14px 18px}div.ph{color:#999;font-size:8pt;margin:10px 18px 0 18px}h1{font-size:20pt;margin:40px 18px}h2{font-size:14pt;margin:40px 18px}p{margin:8px 18px;font-size:10.5pt}'
$html = '<!DOCTYPE html><html><head><meta charset="utf-8"><style>' + $css + '</style></head><body>' + $cover.ToString() + $head.ToString() + $marker + $tail.ToString() + '</body></html>'
[System.IO.File]::WriteAllText($headHtml, $html, (New-Object System.Text.UTF8Encoding($true)))

$pdfOut = Join-Path $env:TEMP ('g05src_' + (Get-Date -Format 'HHmmss') + '.pdf')
$p = Start-Process -FilePath $edge -ArgumentList @(
    '--headless', '--disable-gpu', '--no-pdf-header-footer',
    ('--print-to-pdf=' + $pdfOut),
    ('file:///' + ($headHtml -replace '\\', '/'))
) -PassThru
if (-not $p.WaitForExit(90000)) { $p.Kill(); throw 'edge print timed out (90s)' }
if (-not (Test-Path $pdfOut)) { throw 'edge produced no pdf' }

$dest = Join-Path $PSScriptRoot '_source_print.pdf'
Copy-Item -LiteralPath $pdfOut -Destination $dest -Force
$sz = (Get-Item -LiteralPath $dest).Length
Write-Output ('SRC_FILES=' + $files.Count)
Write-Output ('SRC_LINES=' + $totalLines)
Write-Output ('SRC_PAGES_TOTAL=' + $totalPages)
Write-Output ('PDF_PAGES_RENDERED=' + (2 + $HeadPages + $TailPages))
Write-Output ('PDF_BYTES=' + $sz)
Write-Output ('DEST=' + $dest)
Write-Output ('COVER_HTML=' + $headHtml)

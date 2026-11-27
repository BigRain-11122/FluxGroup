# build_manual_pdf.ps1 - render manual source md to PDF via headless Edge (G10 variant,
# adapted from G11 X352 / G07 B201 - U067 reuse).
# Chain: <this folder>/manual source md -> ASCII temp workdir (manual.html + flat images)
#        -> msedge --headless --print-to-pdf -> copy back as _manual_print.pdf
#        -> caller moves _manual_print.pdf to the final Chinese-named PDF.
# The draft manual carries visible image-placeholder markers (real-device screenshots
# come later), so zero referenced images is legal here - the script prints IMGS_COPIED=0.
# Why ASCII temp paths: native exe (Edge) silently fails on non-ASCII output
# paths (pit #1 family, B155 lesson). All Chinese strings live only in the md
# data file. Script is pure ASCII by PS5.1 discipline (X033 pit 1).
param([string]$MdName = '')

$ErrorActionPreference = 'Stop'
$srcDir = $PSScriptRoot
$edge = @('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
          'C:\Program Files\Microsoft\Edge\Application\msedge.exe') |
        Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw 'msedge.exe not found' }

if ($MdName) { $md = Get-ChildItem -LiteralPath $srcDir -Filter $MdName | Select-Object -First 1 }
else          { $md = Get-ChildItem -LiteralPath $srcDir -Filter '*.md'  | Select-Object -First 1 }
if (-not $md) { throw 'manual source md not found in ' + $srcDir }

$work = Join-Path $env:TEMP ('g10manual_' + (Get-Date -Format 'HHmmss'))
New-Item -ItemType Directory -Path $work -Force | Out-Null

function Esc([string]$t) {
    $t = $t -replace '&','&amp;'
    $t = $t -replace '<','&lt;'
    $t = $t -replace '>','&gt;'
    return $t
}
function Inline([string]$t) {
    $t = Esc $t
    $t = [regex]::Replace($t, '\*\*(.+?)\*\*', '<b>$1</b>')
    return $t
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('<!DOCTYPE html><html><head><meta charset="utf-8"><style>')
[void]$sb.AppendLine('body{font-family:"Microsoft YaHei",SimSun,sans-serif;margin:26px;line-height:1.65;font-size:11pt;color:#222}')
[void]$sb.AppendLine('h1{font-size:19pt;color:#B8860B}h2{font-size:14pt;border-bottom:2px solid #B8860B;padding-bottom:3px;margin-top:22px}')
[void]$sb.AppendLine('h3{font-size:12.5pt;margin-top:16px}img{max-width:40%;display:block;margin:10px 0;border:1px solid #999}')
[void]$sb.AppendLine('blockquote{color:#555;border-left:4px solid #B8860B;margin:8px 0;padding:2px 14px;background:#fbf6e9}')
[void]$sb.AppendLine('li{margin:3px 0}p.cap{color:#666;font-size:9.5pt;margin:0 0 14px 0}</style></head><body>')

$inUl = $false
$inBq = $false
$imgIdx = 0
foreach ($raw in (Get-Content -LiteralPath $md.FullName -Encoding UTF8)) {
    $line = $raw.TrimEnd()
    $m = [regex]::Match($line, '^!\[(.*)\]\((.*)\)$')
    if ($m.Success) {
        if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
        if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
        $imgIdx++
        $abs = [System.IO.Path]::GetFullPath((Join-Path $srcDir $m.Groups[2].Value))
        if (-not (Test-Path -LiteralPath $abs)) { throw ('image not found: ' + $abs) }
        $flat = 'img_' + $imgIdx + [System.IO.Path]::GetExtension($abs)
        Copy-Item -LiteralPath $abs -Destination (Join-Path $work $flat) -Force
        [void]$sb.AppendLine('<img src="' + $flat + '">')
        if ($m.Groups[1].Value) { [void]$sb.AppendLine('<p class="cap">' + (Esc $m.Groups[1].Value) + '</p>') }
        continue
    }
    if ($line -eq '') {
        if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
        if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
        continue
    }
    if ($line -eq '---') {
        if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
        if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
        [void]$sb.AppendLine('<hr>')
        continue
    }
    if ($line.StartsWith('### ')) {
        if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
        if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
        [void]$sb.AppendLine('<h3>' + (Inline $line.Substring(4)) + '</h3>')
        continue
    }
    if ($line.StartsWith('## ')) {
        if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
        if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
        [void]$sb.AppendLine('<h2>' + (Inline $line.Substring(3)) + '</h2>')
        continue
    }
    if ($line.StartsWith('# ')) {
        if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
        if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
        [void]$sb.AppendLine('<h1>' + (Inline $line.Substring(2)) + '</h1>')
        continue
    }
    if ($line.StartsWith('> ')) {
        if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
        if (-not $inBq) { [void]$sb.AppendLine('<blockquote>'); $inBq = $true }
        [void]$sb.AppendLine('<p>' + (Inline $line.Substring(2)) + '</p>')
        continue
    }
    if ($line.StartsWith('- ')) {
        if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
        if (-not $inUl) { [void]$sb.AppendLine('<ul>'); $inUl = $true }
        [void]$sb.AppendLine('<li>' + (Inline $line.Substring(2)) + '</li>')
        continue
    }
    if ($inUl) { [void]$sb.AppendLine('</ul>'); $inUl = $false }
    if ($inBq) { [void]$sb.AppendLine('</blockquote>'); $inBq = $false }
    [void]$sb.AppendLine('<p>' + (Inline $line) + '</p>')
}
if ($inUl) { [void]$sb.AppendLine('</ul>') }
if ($inBq) { [void]$sb.AppendLine('</blockquote>') }
[void]$sb.AppendLine('</body></html>')

$htmlPath = Join-Path $work 'manual.html'
[System.IO.File]::WriteAllText($htmlPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding($true)))

Write-Output ('IMGS_COPIED=' + $imgIdx + ' (0 = placeholder-marker draft, legal for the placeholder-marker draft)')

$pdfOut = Join-Path $work 'out.pdf'
$p = Start-Process -FilePath $edge -ArgumentList @(
    '--headless', '--disable-gpu', '--no-pdf-header-footer',
    ('--print-to-pdf=' + $pdfOut),
    ('file:///' + ($htmlPath -replace '\\', '/'))
) -PassThru
if (-not $p.WaitForExit(60000)) { $p.Kill(); throw 'edge print timed out (60s)' }
if (-not (Test-Path $pdfOut)) { throw 'edge produced no pdf' }

$shot = Join-Path $work 'shot.png'
$p2 = Start-Process -FilePath $edge -ArgumentList @(
    '--headless', '--disable-gpu', '--window-size=1080,2400',
    ('--screenshot=' + $shot),
    ('file:///' + ($htmlPath -replace '\\', '/'))
) -PassThru
if (-not $p2.WaitForExit(60000)) { $p2.Kill(); throw 'edge screenshot timed out' }

$dest = Join-Path $srcDir '_manual_print.pdf'
Copy-Item -LiteralPath $pdfOut -Destination $dest -Force
$sz = (Get-Item -LiteralPath $dest).Length
Write-Output ('PDF_BYTES=' + $sz)
Write-Output ('SHOT=' + $shot)
Write-Output ('WORKDIR=' + $work)
Write-Output ('DEST=' + $dest)

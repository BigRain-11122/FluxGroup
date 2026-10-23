# STEP C v3 ASCII-ONLY: switch to D via rename+keep+junction (bundles first, auto-rollback)
param([switch]$Cutover)
$ErrorActionPreference = 'Stop'
if (-not $Cutover) { throw 'run step B first (plain mode), then -Cutover' }

$src = 'C:\Users\sjs20\Desktop\FluxGroup'
$dst = 'D:\FluxGroup'
$old = 'C:\Users\sjs20\Desktop\FluxGroup.old'
$log = 'D:\FluxGroup-migrate.log'

# 0) idempotency gate
if ((Get-Item $src -Force).LinkType -eq 'Junction') {
    'ALREADY-CUTOVER, verify only' | Tee-Object -FilePath $log -Append
    & git -C $src status --short | Select-Object -First 5
    exit 0
}

# 1) git bundle all-refs backup (root + 8 sub-repos) BEFORE anything destructive
$bdir = 'D:\FleetBackup-20261020\bundles-live'
New-Item -ItemType Directory -Force -Path $bdir | Out-Null
$repos = @('root','gaming\MiniGame','gaming\FluxVerse','quant\bigmoney','media\BigStream','domain\BigDomain','life\BigLife','compute\BigCompute','house\BigHouse')
foreach ($r in $repos) {
    if ($r -eq 'root') { $p = $src } else { $p = Join-Path $src $r }
    if (Test-Path (Join-Path $p '.git')) {
        $name = $r -replace '[\\/]','_'
        $bp = Join-Path $bdir ('FluxGroup-' + $name + '.bundle')
        & git -C $p bundle create $bp --all
        if ($LASTEXITCODE -ne 0) { throw ('bundle failed for ' + $r + ' - refuse cutover') }
    }
}
'BUNDLES OK' | Tee-Object -FilePath $log -Append

# 2) editor lock check
$procs = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^Tuanjie\.exe$|^Unity\.exe$' -and $_.CommandLine -match [regex]::Escape($src)
})
if ($procs.Count -gt 0) {
    $names = ($procs | ForEach-Object { $_.Name + '/' + $_.ProcessId }) -join ', '
    throw ('editors holding repo: ' + $names + ' - close first')
}

# 3) rename original (KEEP, not delete) + same-path junction
Rename-Item -LiteralPath $src -NewName 'FluxGroup.old'
cmd /c mklink /J "$src" "$dst" | Out-Null
if (-not (Test-Path (Join-Path $src 'README.md'))) {
    Rename-Item -LiteralPath $old -NewName 'FluxGroup'
    throw 'junction verify failed - rolled back to original'
}

# 4) readback: git alive + random 20 small files md5 (via junction vs old direct)
$samples = Get-ChildItem $dst -Recurse -File -EA SilentlyContinue | Where-Object { $_.Length -lt 50MB } | Get-Random -Count 20
$bad = 0
foreach ($f in $samples) {
    $rel = $f.FullName.Substring($dst.Length).TrimStart('\')
    $a = (Get-FileHash (Join-Path $src $rel) -Algorithm MD5).Hash
    $b = (Get-FileHash (Join-Path $old $rel) -Algorithm MD5).Hash
    if ($a -ne $b) { $bad++ }
}
& git -C $src rev-parse HEAD | Out-Null
'CUTOVER DONE samples=20 mismatch=' + $bad + ' old kept at FluxGroup.old >=7days' | Tee-Object -FilePath $log -Append
if ($bad -gt 0) { throw ($bad.ToString() + ' sample mismatches - inspect before use') }

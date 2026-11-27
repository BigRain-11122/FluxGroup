# install-gh-toolchain.ps1 - GitHub OSS toolchain installer (CEO order P-2026-09-28-15)
# Idempotent / silent / user-scope (no admin, no UAC prompts).
# ASCII-only body per group encoding law. Licenses verified via api.github.com:
#   cli/cli MIT | gitleaks MIT | lycheeverse/lychee Apache-2.0 | sharkdp/fd MIT/Apache-2.0
#   junegunn/fzf MIT | jqlang/jq MIT | mikefarah/yq MIT | nodejs MIT | Pester Apache-2.0
param(
  [string]$ToolsDir = (Join-Path $env:USERPROFILE 'tools'),
  [switch]$SkipNode,
  [switch]$SkipPester,
  [switch]$SkipPlaywrightMcp
)
$ErrorActionPreference = 'Continue'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
$ProgressPreference = 'SilentlyContinue'
$bin = Join-Path $ToolsDir 'bin'
$dl  = Join-Path $ToolsDir 'dl'
foreach ($d in @($bin, $dl)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

function Get-LatestAssetUrl($repo, $pattern) {
  try {
    $r = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases/latest" -Headers @{ 'User-Agent' = 'fluxgroup-installer' }
    $a = $r.assets | Where-Object { $_.name -match $pattern } | Select-Object -First 1
    if ($a) { return @{ url = $a.browser_download_url; name = $a.name; ver = $r.tag_name } }
    else { Write-Output ("NOTE no asset match for $repo pattern=$pattern") }
  } catch { Write-Output ("API_FAIL $repo : " + $_.Exception.Message) }
  return $null
}

function Install-AssetExe($repo, $pattern, $exeName) {
  $dest = Join-Path $bin $exeName
  if (Test-Path $dest) { Write-Output "SKIP $exeName (present)"; return }
  $a = Get-LatestAssetUrl $repo $pattern
  if (-not $a) { Write-Output "MISS $exeName (no asset)"; return }
  $z = Join-Path $dl $a.name
  if (-not (Test-Path $z)) { Invoke-WebRequest -Uri $a.url -OutFile $z -UseBasicParsing }
  if ($a.name -match '\.zip$') {
    $tmp = Join-Path $dl ('x-' + [IO.Path]::GetFileNameWithoutExtension($a.name))
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    Expand-Archive -Path $z -DestinationPath $tmp -Force
    $f = Get-ChildItem $tmp -Recurse -Filter $exeName | Select-Object -First 1
    if ($f) { Copy-Item $f.FullName $dest -Force; Write-Output ("OK $exeName <= " + $a.name + ' ' + $a.ver) }
    else { Write-Output "MISS $exeName (exe not in archive)" }
  }
  elseif ($a.name -match '\.(tar\.gz|tgz)$') {
    $tmp = Join-Path $dl ('x-' + ([IO.Path]::GetFileNameWithoutExtension($a.name) -replace '\.tar$',''))
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    tar -xzf $z -C $tmp
    $f = Get-ChildItem $tmp -Recurse -Filter $exeName | Select-Object -First 1
    if ($f) { Copy-Item $f.FullName $dest -Force; Write-Output ("OK $exeName <= " + $a.name + ' ' + $a.ver) }
    else { Write-Output "MISS $exeName (exe not in tarball)" }
  }
  else {
    Copy-Item $z $dest -Force
    Write-Output ("OK $exeName <= " + $a.name + ' ' + $a.ver)
  }
}

# 1) Node.js LTS runtime (npm/npx) - official dist zip, user-scope
if (-not $SkipNode) {
  $nodeDir = Join-Path $ToolsDir 'nodejs'
  if (Test-Path (Join-Path $nodeDir 'npm.cmd')) { Write-Output 'SKIP node (present)' }
  else {
    $nz = Join-Path $dl 'node-v24.21.0-win-x64.zip'
    if (-not (Test-Path $nz)) { Invoke-WebRequest -Uri 'https://nodejs.org/dist/latest-v24.x/node-v24.21.0-win-x64.zip' -OutFile $nz -UseBasicParsing }
    $nt = Join-Path $dl 'x-node'
    if (Test-Path $nt) { Remove-Item $nt -Recurse -Force }
    Expand-Archive -Path $nz -DestinationPath $nt -Force
    $inner = Get-ChildItem $nt -Directory | Select-Object -First 1
    if ($inner) {
      if (Test-Path $nodeDir) { Remove-Item $nodeDir -Recurse -Force }
      Move-Item $inner.FullName $nodeDir
    }
    if (Test-Path (Join-Path $nodeDir 'npm.cmd')) { Write-Output "OK node => $nodeDir" } else { Write-Output 'MISS node npm.cmd' }
  }
}

# 2) single-binary CLI tools from GitHub latest releases
Install-AssetExe 'cli/cli'            'windows_amd64\.zip$'          'gh.exe'
Install-AssetExe 'gitleaks/gitleaks'  'windows_x64\.zip$'            'gitleaks.exe'
Install-AssetExe 'lycheeverse/lychee' '(x86_64.*windows|windows.*x86_64)' 'lychee.exe'
Install-AssetExe 'sharkdp/fd'         'x86_64-pc-windows-msvc\.zip$' 'fd.exe'
Install-AssetExe 'junegunn/fzf'       'windows_amd64\.zip$'          'fzf.exe'
Install-AssetExe 'jqlang/jq'         'jq-windows-amd64\.exe$'       'jq.exe'
Install-AssetExe 'mikefarah/yq'      'yq_windows_amd64\.(exe|zip|tar\.gz)$' 'yq.exe'

# 3) Pester v5 (PowerShell test framework, in-case adopted) - PSGallery CurrentUser
if (-not $SkipPester) {
  $m = Get-Module -ListAvailable -Name Pester | Where-Object { $_.Version.Major -ge 5 } | Select-Object -First 1
  if ($m) { Write-Output ("SKIP Pester (v" + $m.Version + ")") }
  else {
    try { Install-Module Pester -Scope CurrentUser -Force -MinimumVersion 5.5.0 -MaximumVersion 5.99 -AllowClobber -SkipPublisherCheck -ErrorAction Stop; Write-Output 'OK Pester' }
    catch { Write-Output ("MISS Pester : " + $_.Exception.Message) }
  }
}

# 4) @playwright/mcp npm global (MCP browser automation for QA smoke tests)
if (-not $SkipPlaywrightMcp) {
  $npm = Join-Path $ToolsDir 'nodejs\npm.cmd'
  if (Test-Path $npm) {
    & $npm install -g '@playwright/mcp' 2>&1 | Select-Object -Last 1 | ForEach-Object { Write-Output ("NPM " + $_) }
    $groot = (& $npm root -g 2>$null | Select-Object -First 1)
    if ($groot) {
      $pw = Join-Path $groot '@playwright\mcp'
      $pkgJson = Join-Path $pw 'package.json'
      if (Test-Path $pkgJson) {
        $pkg = Get-Content $pkgJson -Raw -Encoding UTF8 | ConvertFrom-Json
        $binVal = $pkg.bin
        if ($binVal -isnot [string]) { $p0 = $binVal.PSObject.Properties | Select-Object -First 1; $binVal = $p0.Value }
        Write-Output ("MCP_PLAYWRIGHT_ENTRY=" + (Join-Path $pw $binVal))
      } else { Write-Output 'MISS @playwright/mcp (global root missing)' }
    } else { Write-Output 'MISS npm root -g' }
  } else { Write-Output 'SKIP @playwright/mcp (no npm)' }
}

# 4b) Unity-MCP Python server (uv tool, PyPI mcpforunityserver, MIT) - MCP editor bridge
$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCmd) {
  $localBin = Join-Path $env:USERPROFILE '.local\bin'
  $mcfu = Join-Path $localBin 'mcp-for-unity.exe'
  if (Test-Path $mcfu) { Write-Output 'SKIP unity-mcp server (present)' }
  else {
    & $uvCmd.Source tool install mcpforunityserver 2>&1 | Select-Object -Last 1 | ForEach-Object { Write-Output ('UV ' + $_) }
    if (Test-Path $mcfu) { Write-Output ('OK unity-mcp server => ' + $mcfu) } else { Write-Output 'MISS unity-mcp server' }
  }
}

# 5) user PATH: prepend nodejs dir + bin (idempotent)
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$localBin = Join-Path $env:USERPROFILE '.local\bin'
$wanted = @((Join-Path $ToolsDir 'nodejs'), $bin, $localBin)
$add = @()
foreach ($p in $wanted) {
  $present = $false
  foreach ($e in ($userPath -split ';')) { if ($e.TrimEnd('\') -ieq $p.TrimEnd('\')) { $present = $true } }
  if (-not $present) { $add += $p }
}
if ($add.Count -gt 0) {
  [Environment]::SetEnvironmentVariable('Path', (($add -join ';') + ';' + $userPath), 'User')
  Write-Output ("PATH_PREPENDED " + ($add -join ';'))
} else { Write-Output 'SKIP PATH (already present)' }

# 6) version manifest (evidence record)
$manifest = @()
foreach ($t in 'gh','gitleaks','lychee','fd','fzf','jq','yq') {
  $exe = Join-Path $bin ($t + '.exe')
  if (Test-Path $exe) { $manifest += ($t + '=' + (& $exe --version 2>&1 | Select-Object -First 1)) }
}
$nodeExe = Join-Path $ToolsDir 'nodejs\node.exe'
if (Test-Path $nodeExe) { $manifest += ('node=' + (& $nodeExe --version 2>&1 | Select-Object -First 1)) }
$manifest += 'ps-host=' + $PSVersionTable.PSVersion
Write-Output '=== MANIFEST ==='
$manifest | ForEach-Object { Write-Output $_ }
Write-Output 'INSTALLER_DONE'

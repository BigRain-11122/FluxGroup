# bootstrap-nats.ps1 - fetch pinned NATS server + CLI binaries (fleet bus rollout, CEO order 2026-10-19).
# Idempotent: skips download when the pinned version is already on disk.
# Pinned: nats-server v2.15.1 / natscli v0.5.0 (verified 2026-10-19 live download+bench,
# canon = cph4/research/R-20261019-fleet-realtime-comm-01).
param(
  [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$bin = Join-Path $Root 'Tools\nats\bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$SrvVer = 'v2.15.1'
$CliVer = 'v0.5.0'

function Get-ToolVersion([string]$exe) {
  try { $o = & $exe --version 2>$null | Select-Object -First 1; return [string]$o } catch { return '' }
}

$srvExe = Join-Path $bin 'nats-server.exe'
$cliExe = Join-Path $bin 'nats.exe'

$needSrv = $true
if (Test-Path $srvExe) { if ((Get-ToolVersion $srvExe) -match $SrvVer.TrimStart('v')) { $needSrv = $false } }
$needCli = $true
if (Test-Path $cliExe) { if ((Get-ToolVersion $cliExe) -match $CliVer.TrimStart('v')) { $needCli = $false } }

if (-not $needSrv -and -not $needCli) { Write-Output 'NATS-BIN OK (pinned versions present)'; exit 0 }

$tmp = Join-Path $env:TEMP ('nats-bootstrap-' + (Get-Date -Format 'yyyyMMddHHmmss'))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

if ($needSrv) {
  $u = 'https://github.com/nats-io/nats-server/releases/download/' + $SrvVer + '/nats-server-' + $SrvVer + '-windows-amd64.zip'
  $z = Join-Path $tmp 'ns.zip'
  Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $z
  Expand-Archive -Path $z -DestinationPath (Join-Path $tmp 'server') -Force
  $f = (Get-ChildItem (Join-Path $tmp 'server') -Recurse -Filter 'nats-server.exe' | Select-Object -First 1).FullName
  Copy-Item $f $srvExe -Force
  Write-Output ('SERVER ' + (Get-ToolVersion $srvExe))
}
if ($needCli) {
  $u = 'https://github.com/nats-io/natscli/releases/download/' + $CliVer + '/nats-' + $CliVer.TrimStart('v') + '-windows-amd64.zip'
  $z = Join-Path $tmp 'cli.zip'
  Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $z
  Expand-Archive -Path $z -DestinationPath (Join-Path $tmp 'cli') -Force
  $f = (Get-ChildItem (Join-Path $tmp 'cli') -Recurse -Filter 'nats.exe' | Select-Object -First 1).FullName
  Copy-Item $f $cliExe -Force
  Write-Output ('CLI ' + (Get-ToolVersion $cliExe))
}
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Output 'NATS-BIN READY'

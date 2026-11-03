# repo-slim.ps1 - FluxGroup git repo bloat sentinel + the ONLY sanctioned packer (daily 09:03)
# CEO order 2026-10-19 "file library bloat" - law = cph4/resource-chain.md SS11.10
# gc.auto=0 BY DESIGN (multi-window conflict avoidance) - this task is the single packer.
# Chain: schtasks(S4U+VBS) -> Tools/InvisibleRunner.vbs -> this script.
# Modes: default = pack + report; -ReportOnly = report only.
# Outputs: console + state json (.codely-cli/tmp/repo-slim-state.json) + alerts (repo-slim-alerts.jsonl)
param([switch]$ReportOnly)
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
$stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
$alerts = @()

# 1. THE single sanctioned gc point
if (-not $ReportOnly) { git gc --quiet 2>$null }

# 2. vitals (post-gc)
$loose = 0
$packMB = 0.0
foreach ($ln in (git count-objects -vH)) {
  if ("$ln" -match '^count:\s+(\d+)') { $loose = [int]$Matches[1] }
  if ("$ln" -match '^size-pack:\s+([\d.]+)\s*MiB') { $packMB = [math]::Round([double]$Matches[1],1) }
}
$gitMB = [math]::Round(((Get-ChildItem .git -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum)/1MB,1)

# 3. big tracked file ledger (>5MB = gate WARN band and above)
$big = @()
foreach ($f in (git ls-files)) {
  if ($f -and (Test-Path -LiteralPath $f)) {
    $len = (Get-Item -LiteralPath $f).Length
    if ($len -gt 5MB) { $big += ('{0:N1} MB  {1}' -f ($len/1MB), $f) }
  }
}

# 4. ledger rotation watch (single-file ledgers past 1.2MB = ROTATE-NOW)
$ordersMB = 0.0
if (Test-Path 'docs/orders.md') { $ordersMB = [math]::Round((Get-Item 'docs/orders.md').Length/1MB,2) }
if ($ordersMB -gt 1.2) { $alerts += "ROTATE-NOW docs/orders.md ${ordersMB}MB > 1.2MB threshold (ledger rotation law SS11.10)" }

# 5. alert rules (cruft-aware: unreachable debris auto-expires ~2w via daily gc - not a growth panic)
$cruftMB = 0.0
$packDir = Join-Path $repoRoot '.git\objects\pack'
if (Test-Path $packDir) {
  foreach ($m in (Get-ChildItem $packDir -Filter '*.mtimes' -ErrorAction SilentlyContinue)) {
    $pp = $m.FullName -replace '\.mtimes$', '.pack'
    if (Test-Path $pp) { $cruftMB += [math]::Round((Get-Item $pp).Length/1MB,1) }
  }
}
$effMB = [math]::Round(($packMB - $cruftMB),1)
if ($loose -gt 5000) { $alerts += "LOOSE-SPIKE loose=$loose objects after gc (packer failure suspicion)" }
if ($effMB -gt 700) { $alerts += "PACK-GROWTH ${effMB}MB effective (reachable history media audit needed)" }
if ($gitMB -gt 900) { $alerts += "GIT-DIR ${gitMB}MB > 900MB" }
if ($big.Count -gt 25) { $alerts += "BIG-FILES tracked >5MB count=$($big.Count) (evidence-file diet candidates)" }
if ($cruftMB -gt 50) { $alerts += "CRUFT-RETENTION ${cruftMB}MB unreachable debris packed (auto-expires ~2w; repeat offender = find the staging window)" }

# 5b. 日志轮转（2026-11-03 立）：fleet 下的运行日志必须自限，否则无人值守任务会把
# 单文件写到 GB 级（实锚：fleet/oversight/oversight-run.log 曾 4.37GB 才被人工截断）。
# 规则：>20MB 时保留尾部 5MB，原文件改名 .1（覆盖上一代）。只动日志，不动 git 对象。
$rotated = @()
$logRoot = Join-Path $repoRoot 'fleet'
if (Test-Path $logRoot) {
  foreach ($lg in (Get-ChildItem $logRoot -Recurse -Filter '*.log' -File -ErrorAction SilentlyContinue)) {
    if ($lg.Length -lt 20MB) { continue }
    try {
      $keep = 5MB
      $tail = [IO.File]::ReadAllBytes($lg.FullName)[-1 * [int]$keep..-1]
      $bak = $lg.FullName + '.1'
      Move-Item -LiteralPath $lg.FullName -Destination $bak -Force
      [IO.File]::WriteAllBytes($lg.FullName, $tail)
      $rotated += ($lg.FullName + ' -> tail 5MB (prev ' + [math]::Round($lg.Length/1MB,1) + 'MB)')
    } catch {
      $alerts += ("LOG-ROTATE-FAIL " + $lg.FullName + " : " + $_.Exception.Message)
    }
  }
}

# 6. state + alerts output
$state = [ordered]@{ stamp=$stamp; reportOnly=[bool]$ReportOnly; loose=$loose; packMB=$packMB; effPackMB=$effMB; cruftMB=$cruftMB; gitDirMB=$gitMB; ordersMD_MB=$ordersMB; bigFiles=$big.Count; rotated=$rotated; alerts=$alerts }
$tmpDir = Join-Path $repoRoot '.codely-cli\tmp'
if (-not (Test-Path $tmpDir)) { New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null }
[IO.File]::WriteAllText((Join-Path $tmpDir 'repo-slim-state.json'), ($state | ConvertTo-Json -Depth 3))
if ($alerts.Count -gt 0) {
  $line = @{ stamp=$stamp; alerts=$alerts } | ConvertTo-Json -Compress
  [IO.File]::AppendAllText((Join-Path $tmpDir 'repo-slim-alerts.jsonl'), $line + "`n")
}
Write-Output ("REPO-SLIM $stamp loose=$loose packMB=$packMB effPackMB=$effMB cruftMB=$cruftMB gitDirMB=$gitMB ordersMD_MB=$ordersMB bigFiles=" + $big.Count + " alerts=" + $alerts.Count)
$big | Select-Object -First 10 | ForEach-Object { Write-Output ("  BIG " + $_) }
$alerts | ForEach-Object { Write-Output ("  ALERT " + $_) }
exit 0

# BUILD-PAYLOAD.ps1 - build the content-line handover archives (sender side, bm-a).
# ASCII only. Run from the repo root. Output lands in D:\handover-content-20261120.
#
# Groups mirror the handover doc's inventory. Environment-only trees are excluded on
# purpose: data\assets\models (~7GB TTS/ASR weights), drama-tools\.venv (~8GB torch),
# data\assets\aihot-poc (local Postgres install) - all rebuildable, not handover payload.
param(
  [ValidateSet('P1','P2','P3','P4','P5','ALL')]
  [string]$Group = 'P1',
  [string]$Out = 'D:\handover-content-20261120'
)
$ErrorActionPreference = 'Continue'
$repo = (Get-Location).Path
if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Force $Out | Out-Null }

# group -> list of repo-relative paths
$plan = @{
  P1 = @('media\lora','media\mv-test','media\kf-ab','media\mv-album-001-jay','media\meme-daily-v1')
  P2 = @('media\BigStream\src','media\BigStream\orders','media\BigStream\docs','media\BigStream\research','media\BigStream\tests','media\BigStream\tools','media\BigStream\CONSTITUTION.md','media\BigStream\PLAN.md','media\BigStream\CODELY.md','media\BigStream\HQ-FEEDBACK.md','media\BigStream\README.md','media\BigStream\data')
  P3 = @('media\MV','media\drama-pilot-in','media\drama-pilot-out','media\covers')
  P4 = @('media\MUSIC','media\drama-tools')
  P5 = @('media\faces')
}
$groups = if ($Group -eq 'ALL') { @('P1','P2','P3','P4','P5') } else { @($Group) }

foreach ($g in $groups) {
  $name = "content-$($g.ToLower())-20261120.zip"
  $zip  = Join-Path $Out $name
  $tmp  = Join-Path $Out ("tmp-" + $g)
  if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
  New-Item -ItemType Directory -Force $tmp | Out-Null

  foreach ($rel in $plan[$g]) {
    if (-not (Test-Path $rel)) { Write-Host "SKIP (absent): $rel"; continue }
    $item = Get-Item $rel
    if ($item.PSIsContainer) {
      # robocopy gives us resumable, filterable staging; /XD drops env + noise trees.
      $dst = Join-Path $tmp $rel
      New-Item -ItemType Directory -Force $dst | Out-Null
      robocopy $rel $dst /E /XD .git __pycache__ .venv logs output .aihot-tmp .c3-tmp models aihot-poc /NFL /NDL /NP /NJH /NJS /R:1 /W:1 | Out-Null
      Write-Host ("STAGED  {0}" -f $rel)
    } else {
      $dst = Join-Path $tmp $rel
      $pd = Split-Path -Parent $dst
      if (-not (Test-Path $pd)) { New-Item -ItemType Directory -Force $pd | Out-Null }
      Copy-Item $rel $dst -Force
      Write-Host ("STAGED  {0}" -f $rel)
    }
  }

  if (Test-Path $zip) { Remove-Item $zip -Force }
  # tar (libarchive, ships with Win10+) is far faster than Compress-Archive on 10k+ files.
  $tarOk = $false
  pushd $tmp
  tar.exe -a -c -f $zip * 2>$null
  if ($LASTEXITCODE -eq 0 -and (Test-Path $zip)) { $tarOk = $true }
  popd
  if (-not $tarOk) {
    Write-Host "tar failed, falling back to Compress-Archive (slow)"
    Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $zip -CompressionLevel Optimal -Force
  }

  $s = Get-Item $zip
  $sha = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
  $files = (Get-ChildItem $tmp -Recurse -File -Force | Measure-Object).Count
  Write-Host ("BUILT   {0}  {1:N0} MB  {2} files  sha256={3}" -f $name, ($s.Length/1MB), $files, $sha)

  # append/refresh MANIFEST.json
  $manPath = Join-Path $Out 'MANIFEST.json'
  $man = if (Test-Path $manPath) { Get-Content $manPath -Raw -Encoding UTF8 | ConvertFrom-Json } else { [pscustomobject]@{ generated = (Get-Date).ToString('s'); archives = @() } }
  $list = @($man.archives | Where-Object { $_.name -ne $name })
  $list += [pscustomobject]@{ name = $name; group = $g; sha256 = $sha; bytes = [int64]$s.Length; files = $files; built_at = (Get-Date).ToString('s') }
  [pscustomobject]@{ generated = (Get-Date).ToString('s'); node = 'bm-a'; dest_hint = 'K:\Fluxgroup\FluxGroup'; archives = $list } |
    ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $manPath

  Remove-Item $tmp -Recurse -Force
}
Write-Host "DONE -> $Out"

# BUILD-CURATED.ps1 - curated self-media handover packages (CEO 2026-11-21: he uploads to cloud himself).
# ASCII ONLY. Run from the repo root. Output: D:\handover-selfmedia-20261120
#
# Curation rule: only what a successor actually needs to keep producing.
# Excluded on purpose (rubbish / environment / superseded):
#   - environment: data\assets\models (7.9 GB weights), aihot-poc (2.3 GB local Postgres),
#     data\assets\piper-models & cosyvoice-runtime, drama-tools\repos\*.venv (8.2 GB torch)
#   - machine noise: logs, .codely-cli, __pycache__, .git, .aihot-tmp, .c3-tmp, *.log/*.tmp/*.bak/*.pyc, 0-byte
#   - superseded: media\_trash (10.6 GB trashed MV versions), MV keyframe demo (2.0 GB dated demo)
#   - faces: keep only curated\ + keep\ per candidate; drop raw\ (pre-selection pool),
#     reject\ (rejected samples) and *-ds\ (derived downscales, 8.3 GB)
#   - other lines: media\recon (game APK recon), media\screenshots etc. are not self-media
param(
  [string]$Out = 'D:\handover-selfmedia-20261120'
)
$ErrorActionPreference = 'Continue'
$repo = (Get-Location).Path
$log  = Join-Path $Out 'build.log'
if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Force $Out | Out-Null }
function Log($m) { Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) -Encoding UTF8; Write-Host $m }

$Noise = @('.git','__pycache__','logs','log','.codely-cli','.aihot-tmp','.c3-tmp','node_modules','.venv','venv','.cache','cache')

function Stage($dest, $items) {
  # $items: array of @{src=...; mode='copy'|'faces'}
  foreach ($it in $items) {
    $src = $it.src
    if (-not (Test-Path $src)) { Log "  SKIP (absent) $src"; continue }
    $dst = Join-Path $dest ($it.dest)
    New-Item -ItemType Directory -Force $dst | Out-Null
    if ($it.mode -eq 'faces') {
      $excl = @('raw','reject') + (Get-ChildItem $src -Directory | Where-Object { $_.Name -like '*-ds' } | ForEach-Object { $_.Name })
      $rcArgs = @($src, $dst, '/E', '/NFL', '/NDL', '/NP', '/NJH', '/NJS', '/R:1', '/W:1')
      if ($excl.Count -gt 0) { $rcArgs += '/XD'; $rcArgs += $excl }
      & robocopy @rcArgs | Out-Null
    } elseif ((Get-Item $src).PSIsContainer) {
      & robocopy $src $dst /E /XD @Noise /XF *.log *.tmp *.bak *.pyc *.part *.crdownload /NFL /NDL /NP /NJH /NJS /R:1 /W:1 | Out-Null
    } else {
      Copy-Item $src (Join-Path $dst (Split-Path $src -Leaf)) -Force
    }
  }
}

function Pack($name, $dest, $readme) {
  Set-Content -Path (Join-Path $dest 'README.txt') -Value $readme -Encoding UTF8
  $zip = Join-Path $Out $name
  if (Test-Path $zip) { Remove-Item $zip -Force }
  Push-Location (Split-Path $dest -Parent)
  $leaf = Split-Path $dest -Leaf
  tar.exe -a -c -f $zip $leaf 2>$null
  $rc = $LASTEXITCODE
  Pop-Location
  if ($rc -ne 0 -or -not (Test-Path $zip)) {
    Log "  tar failed, Compress-Archive fallback"
    Compress-Archive -Path (Join-Path $dest '*') -DestinationPath $zip -CompressionLevel Optimal -Force
  }
  $s = Get-Item $zip
  $sha = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
  Log ("PACKED {0}  {1:N0} MB  sha256={2}" -f $name, ($s.Length/1MB), $sha)
  return [pscustomobject]@{ name=$name; bytes=[int64]$s.Length; sha256=$sha }
}

$work = Join-Path $Out '_stage'
if (Test-Path $work) { Remove-Item $work -Recurse -Force }

# ---------------- P1: content line code + docs + products ----------------
$a = Join-Path $work '01-内容线代码与文档'
Stage $a @(
  @{src='media\BigStream\src';    dest='BigStream\src'}
  @{src='media\BigStream\docs';   dest='BigStream\docs'}
  @{src='media\BigStream\orders'; dest='BigStream\orders'}
  @{src='media\BigStream\research';dest='BigStream\research'}
  @{src='media\BigStream\tests';  dest='BigStream\tests'}
  @{src='media\BigStream\tools';  dest='BigStream\tools'}
  @{src='media\BigStream\qa';     dest='BigStream\qa'}
  @{src='media\BigStream\state';  dest='BigStream\state'}
  @{src='media\BigStream\data\storylines'; dest='BigStream\data\storylines'}
  @{src='media\BigStream\data\sources';    dest='BigStream\data\sources'}
  @{src='media\BigStream\data\pipeline';   dest='BigStream\data\pipeline'}
  @{src='media\BigStream\data\drafts';     dest='BigStream\data\drafts'}
  @{src='media\BigStream\data\experts';    dest='BigStream\data\experts'}
  @{src='media\BigStream\data\intel';      dest='BigStream\data\intel'}
  @{src='media\BigStream\data\ideas';      dest='BigStream\data\ideas'}
  @{src='media\BigStream\output'; dest='BigStream\output'}
  @{src='media\BigStream\README.md';        dest='BigStream'}
  @{src='media\BigStream\CONSTITUTION.md';  dest='BigStream'}
  @{src='media\BigStream\PLAN.md';          dest='BigStream'}
  @{src='media\BigStream\CODELY.md';        dest='BigStream'}
  @{src='media\BigStream\HQ-FEEDBACK.md';   dest='BigStream'}
)
Log "STAGED 01"

# ---------------- P2: MV / shorts products ----------------
$b = Join-Path $work '02-MV与短视频成品'
Stage $b @(
  @{src='media\MV';              dest='MV'}
  @{src='media\mv-album-001-jay';dest='mv-album-001-jay'}
  @{src='media\meme-daily-v1';   dest='meme-daily-v1'}
  @{src='media\drama-pilot-in';  dest='drama-pilot-in'}
  @{src='media\drama-pilot-out'; dest='drama-pilot-out'}
  @{src='media\covers';          dest='covers'}
)
# drop the dated keyframe demo (2.0 GB of intermediate segments)
$demo = Join-Path $b 'MV\mv0001\kf-demo-20261012'
if (Test-Path $demo) { Remove-Item $demo -Recurse -Force; Log "  dropped MV\mv0001\kf-demo-20261012 (dated demo, 2.0 GB)" }
Log "STAGED 02"

# ---------------- P3: face corpus (curated + keep only) ----------------
$c = Join-Path $work '03-人脸语料与角色LoRA'
Stage $c @( @{src='media\faces'; dest='faces'; mode='faces'} )
Log "STAGED 03"

# ---------------- P4: music ----------------
$d = Join-Path $work '04-音源MUSIC'
Stage $d @( @{src='media\MUSIC'; dest='MUSIC'} )
Log "STAGED 04"

# ---------------- P5: LoRA + keyframe experiments ----------------
$e = Join-Path $work '05-角色LoRA与关键帧试验'
Stage $e @(
  @{src='media\lora';   dest='lora'}
  @{src='media\mv-test';dest='mv-test'}
  @{src='media\kf-ab';  dest='kf-ab'}
)
Log "STAGED 05"

# ---------------- P6: drama tooling (no venv) ----------------
$f = Join-Path $work '06-漫剧工具链'
Stage $f @( @{src='media\drama-tools'; dest='drama-tools'} )
Log "STAGED 06"

# ---------------- P7: reusable asset library (characters/props/voices + family) ----------------
$g = Join-Path $work '07-可复用资产库'
Stage $g @(
  @{src='media\asset\characters'; dest='asset\characters'}
  @{src='media\asset\voices';     dest='asset\voices'}
  @{src='media\asset\props';      dest='asset\props'}
  @{src='media\family-assets';    dest='family-assets'}
  @{src='media\family-audio';     dest='family-audio'}
)
Log "STAGED 07"

# ---------------- pack ----------------
$results = @()
$results += Pack '01-内容线代码与文档.zip' (Join-Path $work '01-内容线代码与文档') @"
内容线（自媒体/AI 漫剧/短剧/短视频）主机侧代码、订单、文档、数据与产出。
已剔除：模型权重、本地 Postgres、日志、缓存、.git、agent 临时目录。
原机路径：C:\Users\sjs20\Desktop\FluxGroup\media\BigStream
对应独立仓：github.com/BigRain-11122/Bigmedia（代码本体以该仓为准）
"@
$results += Pack '02-MV与短视频成品.zip' (Join-Path $work '02-MV与短视频成品') @"
成品与镜头物料：MV（mv0001/mv0002）、单曲专辑件、meme 短视频、漫剧试点、封面。
已剔除：MV\mv0001\kf-demo-20261012（2026-10-12 的关键帧 demo，约 2.0 GB 中间产物）。
"@
$results += Pack '03-人脸语料与角色LoRA.zip' (Join-Path $work '03-人脸语料与角色LoRA') @"
选角人脸语料，仅保留每个候选人的 curated\ 与 keep\ 两个已筛选目录；另含 faces\_loras\（37 个已训好的角色 LoRA 权重，约 5.2 GB）与 faces\_boards\（审看拼版）。
已剔除：raw\（初筛池，约 5.4 GB）、reject\（被拒样本，约 3.5 GB）、*-ds\（衍生缩略图，约 8.3 GB）。
如需重新筛人，请用 01 包里的抓取与筛选脚本。
"@
$results += Pack '04-音源MUSIC.zip' (Join-Path $work '04-音源MUSIC') @"
MV/短视频用音源（原曲与配乐素材）。版权红线：不得公开展示或二次分发。
"@
$results += Pack '05-角色LoRA与关键帧试验.zip' (Join-Path $work '05-角色LoRA与关键帧试验') @"
角色 LoRA 权重（jman 等）+ 关键帧 AB 试验 + 小样。
"@
$results += Pack '06-漫剧工具链.zip' (Join-Path $work '06-漫剧工具链') @"
漫剧制作脚本与工具源码。已剔除 repos\*\\.venv（约 8.2 GB torch/CUDA），
在目标机按仓库 requirements 重装即可。
"@
$results += Pack '07-可复用资产库.zip' (Join-Path $work '07-可复用资产库') @"
可复用素材：角色/道具/音色（asset\characters|props|voices）、家庭版素材（family-assets）、家庭版音频（family-audio）。
已剔除：asset\inbox（未筛选的下载件，约 515 MB，含与本线无关的影片文件）。
"@

Remove-Item $work -Recurse -Force
$results | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $Out 'MANIFEST.json')
Log ("DONE total {0:N2} GB" -f (($results | Measure-Object -Property bytes -Sum).Sum / 1GB))

# lora_night_train.ps1 - 夜间 LoRA 全链（无人值守，零窗口）
# 顺序：定妆组图(ComfyUI) -> 卸模型 -> 训 extras -> 训女主 -> 写回执
# 为什么先出图后训练：训练要吃掉整卡 11GB，ComfyUI 留着会 OOM；出图只要几分钟。
param(
  [string[]]$TrainFirst = @('extras_v721'),
  [string]$PortraitName = 'her_mv0001',
  [string]$PortraitTrigger = 'h01',
  [int]$PortraitCount = 24,
  [switch]$SkipPortraits
)

$ErrorActionPreference = 'Continue'
$FG   = 'C:\Users\sjs20\Desktop\FluxGroup'
$H    = 'D:\FluxGroup-Offload\15-training'
$RAW  = Join-Path $H 'models\krea2\raw\krea2_raw_bf16.safetensors'
$TE   = Join-Path $H 'models\krea2\text_encoder\qwen3vl_4b_bf16.safetensors'
$LOG  = Join-Path $H ('logs\night-' + (Get-Date -Format 'yyyyMMdd') + '.log')
New-Item -ItemType Directory -Force -Path (Split-Path $LOG) | Out-Null
function Say($m) { $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $m; Add-Content -Path $LOG -Value $line -Encoding UTF8 }

# 文艺系女主 ID 块（逐字取自 canon/FEMALE-LEAD-ERA-DNA-v1.md §一，勿改词）
$BASE = @"
a young Taiwanese woman around twenty, softly rounded face with full apple cheeks (natural facial structure, not blush makeup), big dark double-lidded rounded-almond eyes, small nose with soft rounded tip, medium-full rosy lips, soft natural brows, thick blunt full fringe (a dense straight-cut slab covering the eyebrows, no wispy strands, no see-through bangs), natural clear skin with visible pores and fine film grain, no airbrush, un-fitted relaxed 2001 Taipei style, straight-leg denim, canvas sneakers, slouchy shoulder bag, beige knit sweater
"@ -replace "`r`n", " "

Say "START portraits=$PortraitName train=$($TrainFirst -join ',')"

function Wait-File($path, $expectGB, $url, $label) {
  for ($i = 0; $i -lt 900; $i++) {
    $gb = if (Test-Path $path) { (Get-Item $path).Length / 1GB } else { 0 }
    if ($gb -ge $expectGB) { Say "$label ok $([math]::Round($gb,2))GB"; return $true }
    $running = Get-CimInstance Win32_Process -Filter "Name='curl.exe'" |
               Where-Object { $_.CommandLine -like "*$([IO.Path]::GetFileName($path))*" }
    if (-not $running) {
      Say "$label 缺/停在 $([math]::Round($gb,2))GB，续传"
      Start-Process -FilePath curl.exe -ArgumentList @('-L','--retry','10','--retry-delay','5','-C','-','-o',$path,$url) -WindowStyle Hidden
    }
    Start-Sleep -Seconds 60
  }
  return $false
}

# ---- 1. 定妆组图 -------------------------------------------------------------
if (-not $SkipPortraits) {
  $up = $false
  try { Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 5 -UseBasicParsing | Out-Null; $up = $true } catch {}
  if (-not $up) {
    Say 'ComfyUI 未运行，启动'
    try {
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $FG 'Tools\mv-render-up.ps1') 2>&1 |
        ForEach-Object { Add-Content $LOG ([string]$_) -Encoding UTF8 }
    } catch { Say "启动失败 $($_.Exception.Message)" }
    for ($i = 0; $i -lt 40; $i++) {
      try { Invoke-WebRequest -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 4 -UseBasicParsing | Out-Null; $up = $true; break } catch { Start-Sleep -Seconds 15 }
    }
  }
  if ($up) {
    Say "定妆组图开始 $PortraitName x$PortraitCount"
    & python (Join-Path $FG 'Tools\lora_portraits.py') --name $PortraitName --trigger $PortraitTrigger --base $BASE --count $PortraitCount 2>&1 |
      ForEach-Object { Add-Content $LOG ([string]$_) -Encoding UTF8 }
    Say "定妆组图 rc=$LASTEXITCODE"
  } else { Say 'WARN ComfyUI 起不来，跳过定妆组图' }
  try { Invoke-WebRequest -Uri 'http://127.0.0.1:8188/free' -Method Post -TimeoutSec 10 -UseBasicParsing | Out-Null; Say 'ComfyUI /free ok' } catch {}
}

# ---- 2. 底模就位 -------------------------------------------------------------
if (-not (Wait-File $RAW 24.4 'https://huggingface.co/Comfy-Org/Krea-2/resolve/main/diffusion_models/krea2_raw_bf16.safetensors' 'RAW底模')) {
  Say 'FAILED RAW 未就绪'; exit 3
}
if (-not (Wait-File $TE 8.2 'https://huggingface.co/Comfy-Org/Krea-2/resolve/main/text_encoders/qwen3vl_4b_bf16.safetensors' '文本编码器')) {
  Say 'WARN 文本编码器未就绪（只影响训练中出样图）'
}

# ---- 3. 逐个训练 -------------------------------------------------------------
Set-Location $FG
foreach ($n in $TrainFirst) {
  $ds = Join-Path $H "dataset\$n"
  $cnt = (Get-ChildItem $ds -Filter '*.png' -ErrorAction SilentlyContinue).Count
  if ($cnt -lt 15) { Say "SKIP $n 素材 $cnt 张 < 15"; continue }
  Say "BUILD+TRAIN $n ($cnt 张)"
  & python 'Tools\lora_pipeline.py' build --name $n --epochs 12 2>&1 | ForEach-Object { Add-Content $LOG ([string]$_) -Encoding UTF8 }
  & python 'Tools\lora_pipeline.py' train --name $n 2>&1 | ForEach-Object { Add-Content $LOG ('  ' + [string]$_) -Encoding UTF8 }
  Say "TRAIN END $n rc=$LASTEXITCODE"
}

# ---- 4. 回执 ----------------------------------------------------------------
$rc = if (Test-Path (Join-Path $H "outputs\extras_v721")) { 0 } else { 1 }
$receipt = Join-Path $FG ("cph4\fleet\queue-receipts\lora-night-{0}.json" -f (Get-Date -Format 'yyyyMMdd'))
@{
  gate = 'lora-night'; rc = $rc
  verdict = if ($rc -eq 0) { 'DONE' } else { 'PARTIAL' }
  portraits = $PortraitName; trained = $TrainFirst; log = $LOG
  outputs = @(Get-ChildItem (Join-Path $H 'outputs') -Directory -ErrorAction SilentlyContinue |
              ForEach-Object { Get-ChildItem $_.FullName -Filter '*.safetensors' -ErrorAction SilentlyContinue } |
              Select-Object -ExpandProperty FullName)
  at = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
} | ConvertTo-Json -Depth 4 | Set-Content -Path $receipt -Encoding UTF8
Say "RECEIPT $receipt"
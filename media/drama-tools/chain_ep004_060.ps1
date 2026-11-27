# Drama voice chain for EP004-060 (S4U): wait for voicegen DONE -> mix -> remux to audio MP4.
# Idempotent + resumable: each stage skips if its output already exists.
$ErrorActionPreference = 'Continue'
$TOOLS = 'C:\Fluxgroup\FluxGroup\media\drama-tools'
$TTSDIR = Join-Path 'C:\Fluxgroup\FluxGroup\media\drama-tts-out' 'r1200_ep004_060'
$MIXDIR = Join-Path 'C:\Fluxgroup\FluxGroup\media\drama-mix-out' 'r1201_ep004_060'
$EPSOUT = 'C:\Fluxgroup\FluxGroup\media\drama-eps-audio'
$VGDONE = Join-Path $TOOLS 'voicegen_r1200_ep004_060.DONE.json'
$MIXDONE = Join-Path $TOOLS 'mix_r1201_ep004_060.DONE.json'
$CHAIN = Join-Path $TOOLS 'chain_ep004_060.DONE.json'
$LOG = Join-Path $TOOLS 'chain_ep004_060.log'
$PY = 'C:\Program Files\Python311\python.exe'
$FF = 'C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe'

function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -FilePath $LOG -Append -Encoding utf8 }

if (Test-Path $CHAIN) { Log 'CHAIN already done'; exit 0 }
New-Item -ItemType Directory -Force -Path $EPSOUT | Out-Null

# --- stage 1: wait for voicegen (max 6h) ---
$deadline = (Get-Date).AddHours(6)
while (-not (Test-Path $VGDONE) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 60 }
if (-not (Test-Path $VGDONE)) { Log 'VOICEGEN timeout'; exit 2 }
$vg = Get-Content $VGDONE -Raw -Encoding utf8 | ConvertFrom-Json
Log ("voicegen status=" + $vg.status + " ok=" + $vg.lines_ok + "/" + $vg.lines_total)

# --- stage 2: mix ---
if (-not (Test-Path $MIXDONE)) {
    Log 'mix start'
    & $PY (Join-Path $TOOLS 'drama_mix_batch.py') 'EP004-EP060' --tts 'r1200_ep004_060' --out 'r1201_ep004_060' 2>&1 | Out-File -FilePath $LOG -Append -Encoding utf8
    Log ("mix exit=" + $LASTEXITCODE)
} else { Log 'mix already done' }

# --- stage 3: remux each episode that has a mix ---
$done = 0; $fail = 0
foreach ($n in 4..60) {
    $ep = 'EP{0:d3}' -f $n
    $mix = Join-Path $MIXDIR ("{0}_MIX_r1203.wav" -f $ep)
    if (-not (Test-Path $mix)) { $mix = Join-Path $MIXDIR ("{0}_MIX_r1201.wav" -f $ep) }
    if (-not (Test-Path $mix)) { $mix = (Get-ChildItem $MIXDIR -Filter ("{0}_MIX_*.wav" -f $ep) -ErrorAction SilentlyContinue | Select-Object -First 1).FullName }
    $vid = Join-Path 'C:\Fluxgroup\FluxGroup\media\drama-eps' ("{0}.mp4" -f $ep)
    $dst = Join-Path $EPSOUT ("{0}_AUDIO-r1201.mp4" -f $ep)
    if (-not (Test-Path $mix) -or -not (Test-Path $vid)) { continue }
    if (Test-Path $dst) { $done++; continue }
    & $FF -hide_banner -loglevel error -y -i $vid -i $mix -map 0:v -map 1:a -c:v copy `
        -af 'loudnorm=I=-14:TP=-1.0:LRA=11' -c:a aac -b:a 192k -shortest $dst
    if ($LASTEXITCODE -eq 0) { $done++ } else { $fail++; Log ("remux fail " + $ep) }
}
Log ("remux done=$done fail=$fail")

$obj = [ordered]@{ status = 'done'; voicegen = $vg.status; lines_ok = $vg.lines_ok; lines_total = $vg.lines_total; remux_done = $done; remux_fail = $fail; ts = (Get-Date -Format o) }
$obj | ConvertTo-Json -Depth 4 | Out-File -FilePath $CHAIN -Encoding utf8
Log 'CHAIN COMPLETE'
exit 0
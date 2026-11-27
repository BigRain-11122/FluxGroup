# Drama voice chain v2 (S4U): voicegen -> mix -> remux, with fail-fast accounting.
# Fixes the v1 defect: it reported CHAIN COMPLETE even when mix produced 0 files
# (KeyError on hand-authored-only BED_PROG). Now any stage producing fewer files
# than expected exits non-zero and the DONE json records it.

$ErrorActionPreference = 'Continue'
$TOOLS  = 'C:\Fluxgroup\FluxGroup\media\drama-tools'
$TTSN   = 'r1202_ep001_060'
$MIXN   = 'r1203_ep001_060'
$TTSDIR = Join-Path 'C:\Fluxgroup\FluxGroup\media\drama-tts-out' $TTSN
$MIXDIR = Join-Path 'C:\Fluxgroup\FluxGroup\media\drama-mix-out' $MIXN
$EPSOUT = 'C:\Fluxgroup\FluxGroup\media\drama-eps-audio'
$VGDONE = Join-Path $TOOLS ("voicegen_{0}.DONE.json" -f $TTSN)
$MIXDONE= Join-Path $TOOLS ("mix_{0}.DONE.json" -f $MIXN)
$CHAIN  = Join-Path $TOOLS 'chain_full.DONE.json'
$LOG    = Join-Path $TOOLS 'chain_full.log'
$PY = 'C:\Program Files\Python311\python.exe'
$FF = 'C:\Fluxgroup\MiniGame\Tools\ffmpeg\bin\ffmpeg.exe'

function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -FilePath $LOG -Append -Encoding utf8 }

if (Test-Path $CHAIN) { Log 'CHAIN already recorded'; exit 0 }
New-Item -ItemType Directory -Force -Path $EPSOUT | Out-Null

# stage 1: wait for voicegen (max 8h)
$deadline = (Get-Date).AddHours(8)
while (-not (Test-Path $VGDONE) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 90 }
if (-not (Test-Path $VGDONE)) {
    Log 'VOICEGEN timeout'
    @{ status = 'timeout'; stage = 'voicegen' } | ConvertTo-Json | Out-File $CHAIN -Encoding utf8
    exit 2
}
$vg = Get-Content $VGDONE -Raw -Encoding utf8 | ConvertFrom-Json
Log ("voicegen status=" + $vg.status + " ok=" + $vg.lines_ok + "/" + $vg.lines_total)
if ($vg.status -ne 'OK') {
    Log 'VOICEGEN not OK - stopping chain'
    @{ status = 'failed'; stage = 'voicegen'; detail = $vg.status } | ConvertTo-Json | Out-File $CHAIN -Encoding utf8
    exit 2
}

# stage 2: mix (fail-fast)
if (-not (Test-Path $MIXDONE)) {
    Log 'mix start'
    & $PY (Join-Path $TOOLS 'drama_mix_batch.py') 'EP001-EP060' --tts $TTSN --out $MIXN 2>&1 |
        Out-File -FilePath $LOG -Append -Encoding utf8
    $mixRc = $LASTEXITCODE
    Log ("mix exit=" + $mixRc)
} else { $mixRc = 0; Log 'mix already done' }
$mixFiles = @(Get-ChildItem $MIXDIR -Filter '*_MIX_*.wav' -ErrorAction SilentlyContinue)
Log ("mix files=" + $mixFiles.Count)
if ($mixRc -ne 0 -or $mixFiles.Count -lt 55) {
    Log 'MIX INSUFFICIENT - aborting before remux'
    @{ status = 'failed'; stage = 'mix'; mix_exit = $mixRc; mix_files = $mixFiles.Count } | ConvertTo-Json | Out-File $CHAIN -Encoding utf8
    exit 2
}

# stage 3: remux
$done = 0; $fail = 0; $skipped = 0
foreach ($n in 1..60) {
    $ep  = 'EP{0:d3}' -f $n
    $mix = (Get-ChildItem $MIXDIR -Filter ("{0}_MIX_*.wav" -f $ep) -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
    $vid = Join-Path 'C:\Fluxgroup\FluxGroup\media\drama-eps' ("{0}.mp4" -f $ep)
    $dst = Join-Path $EPSOUT ("{0}_AUDIO-r1202.mp4" -f $ep)
    if (-not $mix -or -not (Test-Path $vid)) { $skipped++; continue }
    if (Test-Path $dst) { $done++; continue }
    & $FF -hide_banner -loglevel error -y -i $vid -i $mix -map 0:v -map 1:a -c:v copy `
        -af 'loudnorm=I=-14:TP=-1.0:LRA=11' -c:a aac -b:a 192k -shortest $dst
    if ($LASTEXITCODE -eq 0) { $done++ } else { $fail++; Log ("remux fail " + $ep) }
}
Log ("remux done=$done fail=$fail skipped=$skipped")

$obj = [ordered]@{
    status   = if ($done -ge 55 -and $fail -eq 0) { 'done' } else { 'partial' }
    voicegen = $vg.status
    lines_ok = $vg.lines_ok
    lines_total = $vg.lines_total
    mix_files = $mixFiles.Count
    remux_done = $done
    remux_fail = $fail
    remux_skipped = $skipped
    ts = (Get-Date -Format o)
}
$obj | ConvertTo-Json -Depth 4 | Out-File -FilePath $CHAIN -Encoding utf8
Log ('CHAIN ' + $obj.status)
exit $(if ($obj.status -eq 'done') { 0 } else { 3 })
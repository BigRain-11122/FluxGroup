# c2160_s107r4_runner.ps1 - self-healing runner for the R4 re-render of Xingqing PACK-B S1-07.
# Law context: C2159 R4 evidence says the pasted cloud cannot be fixed in the picture, so the
# shot is re-rendered on the local GPU (1344x768 int8, 768P, pure picture). A CLI-hosted burn
# dies with the session (job object), so the burn lives on a repeating scheduled task instead:
# every fire re-runs the same manifest, and the runner's own SKIP rule (clip present and
# >100KB) makes re-entry free once a take has landed. When BOTH candidate takes exist the
# task disables itself.
$ErrorActionPreference = "Continue"
$TaskName = "MiniGameComfyBurn-S107R4"
$Repo = "K:\Fluxgroup\FluxGroup"
$Man = "cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-packB-r4-s107-c2160.json"
$OutDir = Join-Path $Repo "media\mv-album-001-jay\clips-local-768"
$LogDir = Join-Path $Repo "media\mv-album-001-jay"
$Py = "C:\Users\Dasheng\AppData\Local\Programs\Python\Python313\python.exe"
$Out = Join-Path $LogDir "log-packB-r4-s107-c2160.out.txt"
$Err = Join-Path $LogDir "log-packB-r4-s107-c2160.err.txt"

$a = Join-Path $OutDir "XQ_B-S1-07-r4a.mp4"
$b = Join-Path $OutDir "XQ_B-S1-07-r4b.mp4"
function Has($p) { (Test-Path $p) -and ((Get-Item $p).Length -gt 100000) }

"===== fire $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') =====" | Out-File -FilePath $Out -Encoding utf8 -Append

if ((Has $a) -and (Has $b)) {
    "both takes already on disk - disable task and exit" | Out-File -FilePath $Out -Encoding utf8 -Append
    schtasks /Change /TN $TaskName /DISABLE | Out-Null
    exit 0
}

# ComfyUI must be listening; the KeepAlive task owns starting it, this only reports.
$up = $false
try { Invoke-RestMethod -Uri "http://127.0.0.1:8188/system_stats" -TimeoutSec 10 | Out-Null; $up = $true } catch {}
if (-not $up) {
    "ComfyUI not listening - skip this cycle (KeepAlive will bring it back)" | Out-File -FilePath $Out -Encoding utf8 -Append
    exit 0
}

& $Py -u (Join-Path $Repo "cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py") `
    --repo $Repo --lane bmc --manifest $Man 1>> $Out 2>> $Err

"runner exit=$LASTEXITCODE" | Out-File -FilePath $Out -Encoding utf8 -Append
if ((Has $a) -and (Has $b)) {
    "both takes landed - disable task" | Out-File -FilePath $Out -Encoding utf8 -Append
    schtasks /Change /TN $TaskName /DISABLE | Out-Null
}
exit 0